"""Testbed consistency: one JSON-safe serializer for sampled poses.

enemy_state_preview (cycle 187) and enemy_blend_report (cycle 185) each carried
the same nine-line position/rotation/scale rounding block. These tests pin one
shared serializer and prove both animation reports actually call it.
"""

import json

from keystone.math3d import Quat, Vec3
from keystone.replay import stable_hash
from keystone.scene import Transform

import shooter.game as game_module
from shooter.game import ShooterGame, _pose_json


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_the_serializer_keeps_all_three_channels_with_stable_rounding():
    pose = {
        "subject": Transform(
            position=Vec3(0.1234567, -0.5, 2.0000004),
            rotation=Quat(0.9999999, 0.0, 0.0000004, 0.0),
            scale=Vec3(1.0555555, 1.0, 1.0),
        )
    }
    result = _pose_json(pose)
    entry = result["subject"]
    assert set(entry) == {"position", "rotation", "scale"}
    assert entry["position"] == [0.123457, -0.5, 2.0]
    assert len(entry["rotation"]) == 4 and len(entry["scale"]) == 3
    assert entry["scale"][0] == 1.055556


def test_both_animation_reports_use_the_shared_serializer(monkeypatch):
    sentinel = {"subject": {"sentinel": True}}
    monkeypatch.setattr(game_module, "_pose_json", lambda pose: sentinel)
    g = _game()
    assert g.enemy_blend_report(parameter=0.5)["pose"] == sentinel
    assert g.enemy_state_preview(threat=0.5)["pose"] == sentinel


def test_both_reports_still_produce_json_safe_poses():
    g = _game()
    for report in (g.enemy_blend_report(parameter=0.5), g.enemy_state_preview(threat=0.5)):
        assert json.loads(json.dumps(report)) == report
        assert "subject" in report["pose"]


def test_serializing_poses_never_touches_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    g.enemy_blend_report(parameter=0.75)
    g.enemy_state_preview(threat=0.75)
    assert stable_hash(g.snapshot()) == before
