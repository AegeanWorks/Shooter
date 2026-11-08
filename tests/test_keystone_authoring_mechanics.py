"""Keystone mechanics testbed: editor authoring workflows.

Covers GameSession undo/redo, play start/step/stop snapshot restoration,
material save/assign/delete/restore, animation key set/remove, and scene
diff/validation, using a small scene built from the shooter's assets.
"""

import tempfile

import pytest

from keystone.animation import AnimationClip
from keystone.math3d import Vec3
from keystone.scene import Node, Scene, Transform
from keystone.web.server import GameSession, WebProblem

from shooter.game import ShooterGame


class _SceneGame:
    """Minimal editable game: one pad/child scene on the shooter assets."""

    name = "shooter_scene"

    def __init__(self, assets, scene: Scene) -> None:
        self.assets = assets
        self.scene = scene
        self.updates = 0

    def build_scene(self) -> Scene:
        return self.scene

    def update(self, dt, actions) -> None:
        self.updates += 1
        node = self.scene.find_by_id("pad")
        node.transform = Transform(position=Vec3(float(self.updates), 1.0, 0.0))

    def snapshot(self) -> dict:
        return {"outcome": "ongoing", "player": {"hp": 100, "alive": True}}

    def actions(self) -> dict:
        return {"axes": [], "buttons": []}


def _game() -> _SceneGame:
    shooter = ShooterGame()
    shooter.build_scene()
    assets = shooter.assets
    scene = Scene()
    pad = Node(
        "pad", id="pad",
        mesh=assets.require("mesh.pickup").payload,
        material=assets.require("material.cache").payload,
        transform=Transform(position=Vec3(0.0, 1.0, 0.0)),
    )
    scene.add(pad)
    child = Node(
        "child", id="child",
        mesh=assets.require("mesh.wall").payload,
        material=assets.require("material.cache").payload,
        transform=Transform(position=Vec3(0.0, 0.5, 0.0)),
    )
    pad.add_child(child)
    return _SceneGame(assets, scene)


def _node(doc: dict, node_id: str) -> dict:
    return next(item for item in doc["nodes"] if item["id"] == node_id)


def test_undo_and_redo_a_node_edit():
    session = GameSession(_game())
    doc = session.editor_action({"action": "set_node", "id": "pad", "name": "pad-edit"})
    assert _node(doc, "pad")["name"] == "pad-edit"
    assert doc["history"]["undo"] >= 1

    undone = session.editor_action({"action": "undo"})
    assert _node(undone, "pad")["name"] == "pad"
    assert undone["history"]["redo"] >= 1
    redone = session.editor_action({"action": "redo"})
    assert _node(redone, "pad")["name"] == "pad-edit"


def test_play_mode_steps_and_restores_the_scene():
    game = _game()
    session = GameSession(game)
    before = _node(session.editor(), "pad")["transform"]["position"]
    assert before == [0.0, 1.0, 0.0]

    started = session.editor_action({"action": "play_start"})
    assert started["play"]["active"] is True
    assert started["play"]["frames"] == 0

    stepped = session.editor_action({"action": "play_step", "frames": 3})
    assert stepped["play"]["frames"] == 3
    assert game.updates == 3
    assert _node(stepped, "pad")["transform"]["position"][0] == 3.0

    stopped = session.editor_action({"action": "play_stop"})
    assert stopped["play"]["active"] is False
    assert stopped["play"]["frames"] == 0
    assert _node(stopped, "pad")["transform"]["position"] == before


def test_material_save_assign_delete_and_restore():
    game = _game()
    with tempfile.TemporaryDirectory() as directory:
        session = GameSession(game, material_dir=directory)
        saved = session.editor_action(
            {
                "action": "save_material",
                "name": "gold",
                "color": [1.0, 0.8, 0.2],
                "emissive": [0.2, 0.1, 0.0],
                "specular": 0.5,
                "shininess": 32.0,
            }
        )
        assert "gold" in [item["name"] for item in saved["materials"]]
        gold = game.assets.require("material.gold").payload
        assert gold.color == Vec3(1.0, 0.8, 0.2)

        assigned = session.editor_action(
            {"action": "assign_material", "id": "pad", "name": "gold"}
        )
        assert _node(assigned, "pad")["material"] == "material.gold"
        with pytest.raises(WebProblem):
            session.editor_action({"action": "delete_material", "name": "gold"})

        session.editor_action(
            {"action": "assign_material", "id": "pad", "name": None}
        )
        deleted = session.editor_action({"action": "delete_material", "name": "gold"})
        assert "gold" not in [item["name"] for item in deleted["materials"]]
        trash = deleted["trash"]["materials"]
        assert any(item["name"] == "gold" for item in trash)

        restored = session.editor_action(
            {"action": "restore_material", "trash": trash[0]["trash"]}
        )
        assert "gold" in [item["name"] for item in restored["materials"]]
        game.assets.require("material.gold")


def test_animation_key_authoring():
    game = _game()
    with tempfile.TemporaryDirectory() as directory:
        session = GameSession(game, animation_dir=directory)
        clip = AnimationClip(name="author_test")
        saved = session.editor_action(
            {"action": "save_animation", "name": "author_test", "clip": clip.to_dict()}
        )
        assert "author_test" in [item["name"] for item in saved["animations"]]

        keyed = session.editor_action(
            {
                "action": "set_animation_key",
                "name": "author_test",
                "id": "pad",
                "channel": "position",
                "time": 0.5,
                "value": [1.0, 2.0, 3.0],
            }
        )
        info = keyed["animation_key"]
        assert info["action"] == "set_animation_key"
        assert info["node"] == "pad"
        assert info["channel"] == "position"
        assert info["keys"] == 1

        removed = session.editor_action(
            {
                "action": "remove_animation_key",
                "name": "author_test",
                "id": "pad",
                "channel": "position",
                "time": 0.5,
            }
        )
        info = removed["animation_key"]
        assert info["action"] == "remove_animation_key"
        assert info["removed"] == 1
        assert info["keys"] == 0


def test_scene_diff_and_validation():
    game = _game()
    with tempfile.TemporaryDirectory() as directory:
        session = GameSession(game, scene_dir=directory)
        saved = session.editor_action({"action": "save_scene", "name": "level"})
        assert saved["saved_scene"] == "level"

        session.editor_action(
            {"action": "set_node", "id": "pad", "name": "pad-renamed"}
        )
        diff = session.editor_action({"action": "diff_scene", "name": "level"})
        report = diff["diff"]
        assert report["has_changes"] is True
        changed = next(item for item in report["changed"] if item["id"] == "pad")
        assert "name" in changed["fields"]
        assert changed["fields"]["name"]["after"] == "pad-renamed"

        validated = session.editor_action({"action": "validate_scene"})
        validation = validated["validation"]
        assert validation["ok"] is True
        assert validation["errors"] == 0
        assert validation["node_count"] == 2
