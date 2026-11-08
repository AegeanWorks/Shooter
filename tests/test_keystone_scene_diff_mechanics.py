"""Keystone mechanics testbed: structured scene-document diffs.

Covers empty diffs, added/removed/changed nodes, camera/environment/root
sections, validation errors and deterministic JSON-safe output over real
scene snapshots.
"""

import json

import pytest

from keystone.math3d import Vec3
from keystone.scene import Node, Scene, Transform
from keystone.scene_diff import SCENE_DIFF_SCHEMA_VERSION, diff_scene_documents
from keystone.scene_snapshot import scene_to_dict


def _scene():
    scene = Scene()
    scene.camera.position = Vec3(1.0, 2.0, 3.0)
    scene.ambient = Vec3(0.1, 0.2, 0.3)
    scene.add(Node("a", id="a", tags={"x"}, layer="one"))
    scene.add(
        Node(
            "b",
            id="b",
            transform=Transform(position=Vec3(0.0, 0.0, 0.0)),
        )
    )
    return scene


def test_identical_documents_produce_empty_diff():
    document = scene_to_dict(_scene())
    diff = diff_scene_documents(document, document)
    assert diff == {
        "schema": SCENE_DIFF_SCHEMA_VERSION,
        "added": [],
        "removed": [],
        "changed": [],
        "camera": {},
        "environment": {},
        "root": {},
        "has_changes": False,
    }


def test_node_added_removed_and_changed_fields():
    before = {
        "nodes": [
            {"id": "a", "name": "A", "tags": ["x"]},
            {"id": "b", "name": "B", "layer": "one", "extra": 1},
        ]
    }
    after = {
        "nodes": [
            {
                "id": "b",
                "name": "B2",
                "tags": ["y"],
                "layer": "two",
                "visible": False,
                "extra": 2,
            },
            {"id": "c", "name": "C"},
        ]
    }
    diff = diff_scene_documents(before, after)
    assert diff["added"] == ["c"]
    assert diff["removed"] == ["a"]
    assert diff["changed"] == [
        {
            "id": "b",
            "fields": {
                "name": {"before": "B", "after": "B2"},
                "tags": {"before": None, "after": ["y"]},
                "layer": {"before": "one", "after": "two"},
                "visible": {"before": None, "after": False},
            },
        }
    ]
    assert "extra" not in diff["changed"][0]["fields"]
    assert diff["has_changes"] is True


def test_section_diffs_camera_environment_root():
    before = {
        "nodes": [],
        "camera": {"position": [0.0, 0.0, 0.0], "yaw": 0.0},
        "environment": {
            "ambient": [0.0, 0.0, 0.0],
            "shadow": {"enabled": True},
        },
        "root": {"visible": True, "transform": {"position": [0.0, 0.0, 0.0]}},
    }
    after = {
        "nodes": [],
        "camera": {"position": [1.0, 0.0, 0.0], "yaw": 0.5},
        "environment": {
            "ambient": [0.1, 0.0, 0.0],
            "shadow": {"enabled": False},
        },
        "root": {"visible": False, "transform": {"position": [0.0, 1.0, 0.0]}},
    }
    diff = diff_scene_documents(before, after)
    assert diff["camera"] == {
        "position": {"before": [0.0, 0.0, 0.0], "after": [1.0, 0.0, 0.0]},
        "yaw": {"before": 0.0, "after": 0.5},
    }
    assert diff["environment"] == {
        "ambient": {"before": [0.0, 0.0, 0.0], "after": [0.1, 0.0, 0.0]},
        "shadow": {"before": {"enabled": True}, "after": {"enabled": False}},
    }
    assert diff["root"] == {
        "visible": {"before": True, "after": False},
        "transform": {
            "before": {"position": [0.0, 0.0, 0.0]},
            "after": {"position": [0.0, 1.0, 0.0]},
        },
    }
    assert diff["has_changes"] is True

    added_section = diff_scene_documents(
        {"nodes": []}, {"nodes": [], "camera": {"yaw": 1.0}}
    )
    assert added_section["camera"] == {
        "yaw": {"before": None, "after": 1.0}
    }


def test_diff_validation_errors():
    with pytest.raises(TypeError):
        diff_scene_documents([], {})
    with pytest.raises(TypeError):
        diff_scene_documents({"nodes": {}}, {"nodes": []})
    with pytest.raises(TypeError):
        diff_scene_documents({"nodes": [1]}, {"nodes": []})
    with pytest.raises(ValueError, match="non-blank"):
        diff_scene_documents({"nodes": [{}]}, {"nodes": []})
    with pytest.raises(ValueError, match="non-blank"):
        diff_scene_documents({"nodes": [{"id": ""}]}, {"nodes": []})
    with pytest.raises(ValueError, match="duplicate"):
        diff_scene_documents(
            {"nodes": [{"id": "a"}, {"id": "a"}]}, {"nodes": []}
        )


def test_diff_is_deterministic_json_safe_and_uses_snapshots():
    before_scene = _scene()
    after_scene = _scene()
    after_scene.camera.position = Vec3(9.0, 9.0, 9.0)
    node_b = after_scene.find_by_id("b")
    node_b.transform = Transform(position=Vec3(1.0, 2.0, 3.0))
    node_b.add_tag("new")
    node_b.layer = "two"
    after_scene.add(Node("c", id="c"))
    after_scene.root.remove_child(after_scene.find_by_id("a"))

    before = scene_to_dict(before_scene)
    after = scene_to_dict(after_scene)
    diff = diff_scene_documents(before, after)
    assert diff["schema"] == 4
    assert diff["added"] == ["c"]
    assert diff["removed"] == ["a"]
    assert [item["id"] for item in diff["changed"]] == ["b"]
    fields = diff["changed"][0]["fields"]
    assert {"tags", "layer", "transform"} <= set(fields)
    assert diff["camera"]["position"] == {
        "before": [1.0, 2.0, 3.0],
        "after": [9.0, 9.0, 9.0],
    }
    assert json.loads(json.dumps(diff)) == diff
    assert diff_scene_documents(before, after) == diff
