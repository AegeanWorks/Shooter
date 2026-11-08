"""Keystone mechanics testbed: glTF scene import adapter.

Covers suffix detection, triangle/textured prefab imports, registry asset
registration, library saves, name overrides/re-imports and validation.
"""

import base64
import json
import struct
from pathlib import Path

import pytest

from keystone.assets import AssetRegistry
from keystone.gltf_import import GLTF_SUFFIXES, import_gltf_prefab, is_gltf_asset
from keystone.math3d import Vec3
from keystone.png import png_bytes
from keystone.prefab_library import PrefabLibrary


def _data_uri(data):
    return "data:application/octet-stream;base64," + base64.b64encode(
        data
    ).decode("ascii")


def _image_uri(data):
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


def _triangle(texture=False, color=(0.2, 0.4, 0.6)):
    positions = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    data = struct.pack("<9f", *positions)
    document = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "tri", "mesh": 0}],
        "meshes": [
            {"primitives": [{"attributes": {"POSITION": 0}, "material": 0}]}
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": 3,
                "type": "VEC3",
            }
        ],
        "bufferViews": [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": len(data),
                "target": 34962,
            }
        ],
        "buffers": [{"uri": _data_uri(data), "byteLength": len(data)}],
        "materials": [
            {
                "pbrMetallicRoughness": {
                    "baseColorFactor": [*color, 1.0],
                    "roughnessFactor": 0.25,
                }
            }
        ],
    }
    if texture:
        png = png_bytes(1, 1, bytes((255, 0, 0, 255)), flip_vertical=False)
        document["images"] = [
            {
                "uri": _image_uri(png),
                "mimeType": "image/png",
                "name": "swatch",
            }
        ]
        document["textures"] = [{"source": 0}]
        document["materials"][0]["pbrMetallicRoughness"][
            "baseColorTexture"
        ] = {"index": 0}
    return document


def _write_gltf(root, name, document):
    path = root / f"{name}.gltf"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_is_gltf_asset_suffixes_and_types():
    assert GLTF_SUFFIXES == (".gltf", ".glb")
    assert is_gltf_asset("model.gltf") is True
    assert is_gltf_asset(Path("model.GLB")) is True
    assert is_gltf_asset("model.Glb") is True
    assert is_gltf_asset("model.obj") is False
    assert is_gltf_asset("model") is False
    with pytest.raises(TypeError, match="string or Path"):
        is_gltf_asset(3)


def test_import_gltf_prefab_registers_and_saves(tmp_path):
    path = _write_gltf(tmp_path, "tri", _triangle())
    registry = AssetRegistry()
    library = PrefabLibrary(tmp_path / "prefabs", registry=registry)
    prefab = import_gltf_prefab(path, registry, library)
    assert prefab.name == "tri"
    assert prefab.node_count == 1
    assert len(prefab.roots) == 1
    assert [entry.name for entry in library.entries()] == ["tri"]
    assert library.path_for("tri").is_file()

    mesh = registry.require("gltf.tri.mesh.0")
    material = registry.require("gltf.tri.material.0")
    assert mesh.kind == "mesh"
    assert material.kind == "material"
    assert mesh.payload.triangle_count() == 1
    assert material.payload.color == Vec3(0.2, 0.4, 0.6)
    assert library.load("tri").node_count == 1


def test_import_gltf_texture_registration(tmp_path):
    path = _write_gltf(tmp_path, "textured", _triangle(texture=True))
    registry = AssetRegistry()
    library = PrefabLibrary(tmp_path / "prefabs", registry=registry)
    prefab = import_gltf_prefab(path, registry, library, name="custom")
    assert prefab.name == "custom"
    assert [entry.name for entry in library.entries()] == ["custom"]
    texture = registry.require("gltf.custom.texture.0")
    material = registry.require("gltf.custom.material.0")
    mesh = registry.require("gltf.custom.mesh.0")
    assert texture.kind == "texture"
    assert texture.payload.name == "swatch"
    assert material.payload.texture is texture.payload
    assert mesh.payload.triangle_count() == 1


def test_import_gltf_name_override_reimport_and_errors(tmp_path):
    path = _write_gltf(tmp_path, "tri", _triangle())
    registry = AssetRegistry()
    library = PrefabLibrary(tmp_path / "prefabs", registry=registry)
    first = import_gltf_prefab(path, registry, library, name="custom")
    second = import_gltf_prefab(path, registry, library, name="custom")
    assert first.name == second.name == "custom"
    assert [entry.name for entry in library.entries()] == ["custom"]
    ids = sorted(record.id for record in registry)
    assert ids == ["gltf.custom.material.0", "gltf.custom.mesh.0"]

    with pytest.raises(ValueError, match="non-blank"):
        import_gltf_prefab(
            path,
            registry,
            library,
            name=" ",
        )
    obj = tmp_path / "mesh.obj"
    obj.write_text("v 0 0 0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must use .gltf or .glb"):
        import_gltf_prefab(
            obj, registry, PrefabLibrary(tmp_path / "other", registry=registry)
        )
    with pytest.raises(FileNotFoundError):
        import_gltf_prefab(
            tmp_path / "missing.gltf",
            registry,
            PrefabLibrary(tmp_path / "missing-lib", registry=registry),
        )
    with pytest.raises(TypeError, match="AssetRegistry"):
        import_gltf_prefab(path, object(), library)
    with pytest.raises(TypeError, match="PrefabLibrary"):
        import_gltf_prefab(path, registry, object())
    with pytest.raises(ValueError, match="needs an AssetRegistry"):
        import_gltf_prefab(
            path, AssetRegistry(), PrefabLibrary(tmp_path / "no-registry")
        )


def test_import_gltf_prefab_scene_and_library_contents(tmp_path):
    path = _write_gltf(tmp_path, "tri", _triangle())
    registry = AssetRegistry()
    library = PrefabLibrary(tmp_path / "prefabs", registry=registry)
    import_gltf_prefab(path, registry, library)
    loaded = library.load("tri")
    assert loaded.node_count == 1
    assert len(loaded.roots) == 1
    assert loaded.roots[0].mesh is not None
    assert loaded.roots[0].mesh.triangle_count() == 1
    assert loaded.roots[0].name == "tri"
    document = json.loads(library.path_for("tri").read_text(encoding="utf-8"))
    assert document["name"] == "tri"
    assert len(document["roots"]) == 1
