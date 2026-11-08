"""Keystone mechanics testbed: disk-backed asset sources and reload reports.

Covers default loader selection, suffix-to-kind inference, file
fingerprints, payload kind checks, AssetSource validation and JSON-safe
ReloadReport summaries.
"""

import json

import pytest

from keystone.asset_io import (
    AssetSource,
    ReloadReport,
    asset_kind,
    default_loader,
    fingerprint,
    kind_from_suffix,
    load_asset,
)
from keystone.geometry import Material, MeshData
from keystone.math3d import Vec3
from keystone.obj_loader import load_obj
from keystone.png import write_png
from keystone.prefab import Prefab
from keystone.primitives import cube
from keystone.scene import Node
from keystone.texture import TextureData

OBJ_TEXT = """v 0 0 0
v 1 0 0
v 0 1 0
f 1 2 3
"""


def test_default_loader_and_suffix_kinds():
    assert default_loader("mesh") is load_obj
    assert default_loader("texture").__func__ is TextureData.from_png.__func__
    assert default_loader("prefab").__func__ is Prefab.load.__func__
    with pytest.raises(ValueError, match="no default loader for material"):
        default_loader("material")
    with pytest.raises(ValueError, match="asset kind must be one of"):
        default_loader("bogus")

    assert kind_from_suffix("model.OBJ") == "mesh"
    assert kind_from_suffix("skin.PNG") == "texture"
    assert kind_from_suffix("pickup.kprefab") == "prefab"
    with pytest.raises(ValueError, match="cannot infer"):
        kind_from_suffix("notes.txt")


def test_fingerprint_and_load_asset_sources(tmp_path):
    assert fingerprint(tmp_path / "missing.obj") is None
    obj = tmp_path / "tri.obj"
    obj.write_text(OBJ_TEXT, encoding="utf-8")
    first = fingerprint(obj)
    assert isinstance(first, tuple) and len(first) == 2
    assert all(isinstance(value, int) for value in first)
    assert first[1] == obj.stat().st_size
    with obj.open("ab") as handle:
        handle.write(b"\n")
    second = fingerprint(obj)
    assert second[1] == first[1] + 1
    assert second != first

    mesh = load_asset("mesh", obj)
    assert isinstance(mesh, MeshData)
    assert mesh.triangle_count() == 1

    png = tmp_path / "swatch.png"
    write_png(png, 2, 2, bytes((1, 2, 3, 255)) * 4, flip_vertical=False)
    texture = load_asset("texture", png)
    assert isinstance(texture, TextureData)
    assert (texture.width, texture.height) == (2, 2)

    prefab_path = tmp_path / "pickup.kprefab"
    Prefab.from_node(Node("pickup"), "pickup").save(prefab_path)
    prefab = load_asset("prefab", prefab_path)
    assert isinstance(prefab, Prefab)
    assert prefab.node_count == 1

    material = load_asset(
        "material", tmp_path / "material.json", loader=lambda path: Material()
    )
    assert isinstance(material, Material)

    with pytest.raises(TypeError, match="loader returned a material, expected a mesh"):
        load_asset("mesh", obj, loader=lambda path: Material())
    with pytest.raises(ValueError, match="asset kind must be one of"):
        load_asset("bogus", obj)


def test_asset_kind_accepts_only_supported_payloads():
    mesh = cube(1.0)
    material = Material(color=Vec3(1.0, 0.5, 0.2))
    texture = TextureData(1, 1, bytes((0, 0, 0, 255)), name="one")
    prefab = Prefab.from_node(Node("pickup"), "pickup")
    assert asset_kind(mesh) == "mesh"
    assert asset_kind(material) == "material"
    assert asset_kind(texture) == "texture"
    assert asset_kind(prefab) == "prefab"
    with pytest.raises(TypeError, match="payload must be"):
        asset_kind(object())


def test_asset_source_validates_fields(tmp_path):
    path = tmp_path / "tri.obj"
    source = AssetSource(path, "mesh", load_obj, (1, 2))
    assert source.path == path
    assert source.kind == "mesh"
    assert source.loader is load_obj
    assert source.fingerprint == (1, 2)
    assert source.error is None

    with pytest.raises(TypeError, match="path"):
        AssetSource(str(path), "mesh", load_obj, (1, 2))
    with pytest.raises(ValueError, match="kind"):
        AssetSource(path, "bogus", load_obj, (1, 2))
    with pytest.raises(TypeError, match="loader"):
        AssetSource(path, "mesh", None, (1, 2))
    with pytest.raises(TypeError, match="fingerprint"):
        AssetSource(path, "mesh", load_obj, (1,))
    with pytest.raises(TypeError, match="error"):
        AssetSource(path, "mesh", load_obj, (1, 2), 3)


def test_reload_report_ok_and_describe():
    empty = ReloadReport(0)
    assert empty.ok is True
    assert empty.describe() == {
        "checked": 0,
        "reloaded": [],
        "unchanged": [],
        "failed": [],
        "missing": [],
        "ok": True,
    }

    clean = ReloadReport(2, ("a",), ("b",))
    assert clean.ok is True

    report = ReloadReport(
        3,
        ("a",),
        ("b",),
        (("c", "boom"),),
        ("d",),
    )
    assert report.ok is False
    described = report.describe()
    assert described == {
        "checked": 3,
        "reloaded": ["a"],
        "unchanged": ["b"],
        "failed": [{"id": "c", "error": "boom"}],
        "missing": ["d"],
        "ok": False,
    }
    assert json.loads(json.dumps(described)) == described
