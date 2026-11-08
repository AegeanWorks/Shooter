"""Keystone mechanics testbed: editor scene operations and prefab instances.

Covers GameSession editor actions for additive scene groups, layer
visibility, node locking/hiding, and prefab override/nested-instance
behavior on top of the shooter's assets and prefab library.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from keystone.math3d import Vec3
from keystone.scene import Node, Scene, Transform
from keystone.scene_library import SceneLibrary
from keystone.web.server import GameSession, WebProblem

from shooter.game import ShooterGame

DATA = Path(__file__).parent.parent / "shooter" / "data"


def _shooter_scene(g: ShooterGame) -> Scene:
    scene = Scene()
    cache = Node(
        "cache", id="cache",
        mesh=g.assets.require("mesh.pickup").payload,
        material=g.assets.require("material.cache").payload,
        tags={"loot"}, layer="props",
        transform=Transform(position=Vec3(1.0, 2.0, 3.0)),
    )
    scene.add(cache)
    halo = Node(
        "halo", id="halo",
        mesh=g.assets.require("mesh.wall").payload,
        material=g.assets.require("material.cache").payload,
        transform=Transform(position=Vec3(0.0, 0.5, 0.0)),
    )
    cache.add_child(halo)
    return scene


def test_scene_group_add_save_and_unload():
    g = ShooterGame()
    g.build_scene()
    with tempfile.TemporaryDirectory() as directory:
        SceneLibrary(directory, registry=g.assets).save("level", _shooter_scene(g))
        session = GameSession(ShooterGame(), scene_dir=directory)
        doc = session.editor_action({"action": "add_scene", "name": "level"})
        assert doc["scene_group_count"] == 1, doc["scene_groups"]
        group = doc["scene_groups"][0]
        assert group["name"] == "level"
        assert group["node_count"] == 2
        assert group["roots"] == ["cache"], group["roots"]

        saved = session.editor_action(
            {"action": "save_scene_group", "id": group["id"]}
        )
        assert saved["scene_group_count"] == 1
        after = session.editor_action(
            {"action": "unload_scene", "id": group["id"]}
        )
        assert after["scene_group_count"] == 0


def test_layer_visibility_lock_and_hide():
    session = GameSession(ShooterGame())
    doc = session.editor_action(
        {"action": "set_node", "id": "platform-pad", "layer": "props"}
    )
    assert any(layer["name"] == "props" and layer["count"] >= 1 for layer in doc["layers"])

    hidden = session.editor_action(
        {"action": "set_layer_visible", "name": "props", "visible": False}
    )
    assert hidden["hidden_layers"] == ["props"]
    shown = session.editor_action(
        {"action": "set_layer_visible", "name": "props", "visible": True}
    )
    assert shown["hidden_layers"] == []

    locked = session.editor_action(
        {"action": "set_nodes_locked", "ids": ["platform-pad"], "locked": True}
    )
    assert locked["locked_count"] == 1
    assert locked["locked_ids"] == ["platform-pad"]
    node = next(item for item in locked["nodes"] if item["id"] == "platform-pad")
    assert node["locked"] is True
    with pytest.raises(WebProblem):
        session.editor_action(
            {"action": "transform", "id": "platform-pad", "position": [0.0, 0.0, 0.0]}
        )

    unlocked = session.editor_action(
        {"action": "set_nodes_locked", "ids": ["platform-pad"], "locked": False}
    )
    assert unlocked["locked_count"] == 0

    session.editor_action({"action": "select", "id": "platform-pad"})
    hidden_node = session.editor_action({"action": "toggle_selection_visible"})
    node = next(item for item in hidden_node["nodes"] if item["id"] == "platform-pad")
    assert node["visible"] is False
    shown_node = session.editor_action({"action": "toggle_selection_visible"})
    node = next(item for item in shown_node["nodes"] if item["id"] == "platform-pad")
    assert node["visible"] is True


def test_prefab_override_and_revert():
    session = GameSession(ShooterGame(), prefab_dir=DATA)
    doc = session.editor_action(
        {"action": "insert_prefab", "name": "pickup_beacon", "instance": "test"}
    )
    links = {(item["name"], item["instance"]) for item in doc["prefab_instances"]}
    assert ("pickup_beacon", "test") in links
    assert doc["prefab_instance_count"] == 1
    assert doc["prefab_override_count"] == 0

    overridden = session.editor_action(
        {
            "action": "transform",
            "id": "test:surge-pickup",
            "position": [1.0, 0.5, -6.0],
        }
    )
    assert overridden["prefab_override_count"] == 1, overridden["prefab_overrides"]
    report = next(
        item for item in overridden["prefab_overrides"]
        if item["prefab"] == "pickup_beacon" and item["instance"] == "test"
    )
    field = report["nodes"][0]["fields"]["transform.position"]
    assert field["instance"] == [1.0, 0.5, -6.0]

    reverted = session.editor_action(
        {
            "action": "revert_prefab_override",
            "id": "test:surge-pickup",
            "field": "transform.position",
        }
    )
    assert reverted["prefab_override_count"] == 0
    node = next(item for item in reverted["nodes"] if item["id"] == "test:surge-pickup")
    assert node["transform"]["position"] == [0.0, 0.5, -6.0]


def test_nested_prefab_instance_links_rebase():
    with tempfile.TemporaryDirectory() as directory:
        shutil.copyfile(
            DATA / "pickup_beacon.kprefab",
            Path(directory) / "pickup_beacon.kprefab",
        )
        session = GameSession(ShooterGame(), prefab_dir=directory)
        session.editor_action(
            {"action": "insert_prefab", "name": "pickup_beacon", "instance": "inner"}
        )
        session.editor_action({"action": "create_node", "name": "crate", "id": "crate"})
        session.editor_action(
            {"action": "reparent_node", "id": "inner:surge-pickup", "parent": "crate"}
        )
        session.editor_action(
            {"action": "save_prefab", "id": "crate", "name": "crate_prefab"}
        )
        session.editor_action({"action": "delete_node", "id": "crate"})
        doc = session.editor_action(
            {"action": "insert_prefab", "name": "crate_prefab", "instance": "outer"}
        )

    links = {(item["name"], item["instance"]) for item in doc["prefab_instances"]}
    assert ("crate_prefab", "outer") in links, links
    assert ("pickup_beacon", "outer.inner") in links, links
    assert doc["prefab_instance_count"] == 2
    ids = {item["id"] for item in doc["nodes"]}
    assert {"outer:crate", "outer.inner:surge-pickup", "outer.inner:surge-beam",
            "outer.inner:surge-orb"} <= ids, ids
    assert doc["prefab_override_count"] == 0
