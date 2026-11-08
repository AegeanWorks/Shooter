"""Keystone mechanics testbed: public API and schema contracts.

Covers top-level exports and lazy Engine loading, schema/version constants,
editor-action parity with describe_game, CubeDemo determinism and module
__all__ re-exports.
"""

from collections.abc import Mapping

import pytest

import keystone
import keystone.batch as batch
import keystone.culling as culling
import keystone.export as export
import keystone.gltf_import as gltf_import
import keystone.scene_diff as scene_diff
from keystone import schema
from keystone.analysis import REPORT_SCHEMA
from keystone.export import EXPORT_SCHEMA_VERSION
from keystone.gltf_import import GLTF_SUFFIXES, is_gltf_asset
from keystone.headless import run_simulation
from keystone.input import ActionState
from keystone.plugin import describe_game
from keystone.playtest import PLAYTEST_REPORT_SCHEMA, TRANSCRIPT_SCHEMA
from keystone.replay import FIXED_STEP
from keystone.samples import CubeDemo
from keystone.scene import Scene
from keystone.scene_diff import SCENE_DIFF_SCHEMA_VERSION
from keystone.scene_snapshot import SCENE_SNAPSHOT_VERSION


def test_public_exports_resolve_and_engine_lazy_load():
    assert isinstance(keystone.__version__, str) and keystone.__version__
    assert len(keystone.__all__) >= 80
    assert len(keystone.__all__) == len(set(keystone.__all__))
    missing = [
        name for name in keystone.__all__ if not hasattr(keystone, name)
    ]
    assert missing == []
    for name in (
        "Scene",
        "Node",
        "Engine",
        "load_gltf",
        "run_bot",
        "plan_batches",
        "scene_to_dict",
        "apply_pose",
    ):
        assert name in keystone.__all__
        assert getattr(keystone, name) is not None
    assert keystone.Engine.__module__ == "keystone.app"
    with pytest.raises(AttributeError, match="has no attribute"):
        getattr(keystone, "definitely_missing")


def test_schema_versions_and_editor_actions():
    assert schema.WEB_API_VERSION == 1
    assert schema.SCENE_SCHEMA_VERSION == 2
    assert schema.EDITOR_SCHEMA_VERSION == 59
    assert schema.PREFAB_SCHEMA_VERSION == 2
    assert len(schema.EDITOR_ACTIONS) == len(set(schema.EDITOR_ACTIONS))
    assert len(schema.EDITOR_ACTIONS) >= 80
    for action in (
        "select",
        "transform",
        "set_component",
        "play_start",
        "preview_blend_space",
        "save_scene",
        "delete_scene",
        "import_gltf",
        "build_project",
        "undo",
        "redo",
    ):
        assert action in schema.EDITOR_ACTIONS

    assert REPORT_SCHEMA["version"] == 11
    assert SCENE_SNAPSHOT_VERSION == 6
    assert SCENE_DIFF_SCHEMA_VERSION == 4
    assert EXPORT_SCHEMA_VERSION == 1
    assert PLAYTEST_REPORT_SCHEMA == 1
    assert TRANSCRIPT_SCHEMA == 1


def test_describe_game_matches_schema_actions():
    info = describe_game(CubeDemo())
    assert info["game"] == "cube-demo"
    editor = info["capabilities"]["editor"]
    assert editor["schema"] == schema.EDITOR_SCHEMA_VERSION
    assert tuple(editor["actions"]) == schema.EDITOR_ACTIONS
    capabilities = info["capabilities"]
    assert capabilities["agents"] is True
    assert capabilities["prefabs"] is True
    assert capabilities["report_schema"]["version"] == REPORT_SCHEMA["version"]
    assert capabilities["web"]["api_version"] == schema.WEB_API_VERSION
    assert "/api" in capabilities["web"]["endpoints"]
    assert {"forward", "right", "up", "look_yaw", "look_pitch"} <= set(
        info["actions"]["axes"]
    )
    assert "quit" in info["actions"]["buttons"]


def test_cube_demo_contract_and_determinism():
    demo = CubeDemo()
    assert isinstance(demo.build_scene(), Scene)
    before = demo.snapshot()
    assert isinstance(before, Mapping)
    spec = demo.actions()
    assert isinstance(spec, Mapping)
    assert "forward" in spec["axes"] and "right" in spec["axes"]
    assert "quit" in spec["buttons"]
    demo.update(FIXED_STEP, ActionState(forward=1.0))
    after = demo.snapshot()
    assert isinstance(after, Mapping)
    assert after["time"] > before["time"]

    first = run_simulation(CubeDemo(), frames=4, actions=[])
    second = run_simulation(CubeDemo(), frames=4, actions=[])
    assert first["hash"] == second["hash"]
    assert first["frames"] == 4
    assert first["ok"] is True


def test_module_all_exports_and_reexports():
    for module in (culling, batch, scene_diff, export, gltf_import):
        exported = getattr(module, "__all__", ())
        assert exported
        for name in exported:
            assert hasattr(module, name)
    for name in culling.__all__:
        assert name in keystone.__all__
    for name in batch.__all__:
        assert name in keystone.__all__
    assert GLTF_SUFFIXES == (".gltf", ".glb")
    assert is_gltf_asset("model.gltf") is True
    assert is_gltf_asset("model.obj") is False
