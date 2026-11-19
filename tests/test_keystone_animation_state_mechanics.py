"""Keystone testbed: a parameter-driven enemy animation state preview.

`animation_state` was one of 21 Keystone modules the testbed never imported.
`enemy_state_preview()` authors a small AnimationStateMachine from the shipped
idle clips, drives it with the live threat level and returns a JSON report.
It is an on-demand query: no scene node, sim state or replay hash is touched.
"""

from keystone.math3d import Vec3
from keystone.replay import stable_hash

from shooter.game import ShooterGame
from shooter.sim import _Enemy


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_the_preview_reports_the_authored_states_and_transitions():
    report = _game().enemy_state_preview(threat=0.0)["report"]
    assert report["schema"] == 1
    assert report["states"] == ["aggressive", "alert", "calm"]
    assert report["transitions"] == 3
    assert report["parameters"] == {"threat": 0.0}
    assert report["current"] == "calm"


def test_threat_drives_the_active_state():
    results = {
        threat: _game().enemy_state_preview(threat=threat)["report"]["current"]
        for threat in (0.0, 0.5, 0.9)
    }
    assert results == {0.0: "calm", 0.5: "alert", 0.9: "aggressive"}


def test_the_sampled_pose_is_json_safe():
    result = _game().enemy_state_preview(threat=0.9, frames=30)
    assert set(result["pose"]) == {"subject"}
    transform = result["pose"]["subject"]
    assert set(transform) == {"position", "rotation", "scale"}
    assert all(len(values) in (3, 4) for values in transform.values())


def test_the_default_parameter_comes_from_the_alive_threat():
    g = _game()
    assert g.enemy_state_preview()["parameter"] == 0.0
    g.sim.enemies = [
        _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 5.0), hp=600, max_hp=600)
    ]
    assert g.enemy_state_preview()["parameter"] == 1.0
    assert g.enemy_state_preview()["report"]["current"] == "aggressive"


def test_previewing_a_state_never_touches_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    first = g.enemy_state_preview(threat=0.5)
    assert g.enemy_state_preview(threat=0.5) == first
    assert stable_hash(g.snapshot()) == before
