"""Keystone testbed proof: the shooter is served by the web session API.

GameSession is the in-memory backend behind /api/describe, /api/scene,
/api/editor and POST /api/simulate. These tests drive it directly so the
AI/editor surface stays covered without opening a socket.
"""

from keystone.replay import FIXED_STEP
from keystone.web.server import GameSession

from shooter.game import ShooterGame


def _session() -> GameSession:
    return GameSession(ShooterGame())


def test_describe_exposes_the_shooter_contract():
    doc = _session().describe()
    assert doc["schema"] >= 1
    assert doc["game"] == "shooter"
    assert "fire" in doc["actions"]["buttons"]
    assert "overdrive" in doc["actions"]["buttons"]
    assert len(doc["capabilities"]) >= 30
    assert "player" in doc["snapshot"]


def test_scene_document_contains_the_arena_and_prefab_nodes():
    doc = _session().scene()
    assert doc["game"] == "shooter"
    assert doc["node_count"] > 100
    ids = {node["id"] for node in doc["nodes"]}
    assert {"floor", "platform-pad", "pickup:surge-pickup", "warden-core"} <= ids


def test_editor_selects_a_shooter_node():
    session = _session()
    doc = session.editor()
    assert doc["schema"] >= 1
    assert doc["game"] == "shooter"
    assert doc["nodes"]
    session.editor_action({"action": "select", "id": "platform-pad"})
    assert session.selected_id == "platform-pad"
    assert session.editor()["selection_count"] == 1


def test_simulate_matches_the_cli_transcript():
    result = _session().simulate(120, [], FIXED_STEP, False)
    assert result["hash"] == "7e4b602e029d12d68672790318d119cd"
    assert result["final"]["outcome"] == "ongoing"
    assert result["final"]["wave"] == 1
    assert result["final"]["player"]["hp"] == 100
