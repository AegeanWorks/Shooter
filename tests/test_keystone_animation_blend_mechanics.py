"""Keystone testbed: enemy idle clips as a real 1D blend space.

`animation_blend` was one of 21 Keystone modules the testbed never imported.
The shooter already ships four .kanim idle clips and publishes each enemy's HP;
`enemy_blend_report()` anchors the clips at those HP thresholds and samples a
pose for the current alive threat. It is an on-demand query: no sim state, no
per-frame cost, no replay-hash change.
"""

from keystone.math3d import Vec3
from keystone.replay import stable_hash

from shooter.game import ShooterGame
from shooter.sim import _Enemy


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def _pose(sample: dict) -> dict:
    t = sample["subject"]
    return {
        "position": [round(t.position.x, 6), round(t.position.y, 6), round(t.position.z, 6)],
        "rotation": [round(t.rotation.w, 6), round(t.rotation.x, 6),
                     round(t.rotation.y, 6), round(t.rotation.z, 6)],
        "scale": [round(t.scale.x, 6), round(t.scale.y, 6), round(t.scale.z, 6)],
    }


def test_blend_report_uses_shipped_clips_and_hp_thresholds():
    report = _game().enemy_blend_report(parameter=0.0)
    assert report["schema"] == 1 and report["round_trip"] is True
    blend = report["blend"]
    assert [item["clip"] for item in blend["samples"]] == [
        "wisp_idle", "mite_idle", "brute_idle", "warden_idle"
    ]
    assert blend["thresholds"] == [20.0, 30.0, 120.0, 600.0]


def test_low_and_high_parameters_pick_exact_clips():
    g = _game()
    low = g.enemy_blend_report(parameter=0.0, time=0.7)["pose"]["subject"]
    high = g.enemy_blend_report(parameter=600.0, time=0.7)["pose"]["subject"]
    assert low == _pose(g._enemy_anim.clips["wisp_idle"].sample(0.7))
    assert high == _pose(g._enemy_anim.clips["warden_idle"].sample(0.7))
    assert low != high


def test_a_mid_parameter_blends_the_neighbouring_poses():
    g = _game()
    mid = g.enemy_blend_report(parameter=75.0, time=0.7)["pose"]["subject"]
    mite = _pose(g._enemy_anim.clips["mite_idle"].sample(0.7))
    brute = _pose(g._enemy_anim.clips["brute_idle"].sample(0.7))
    assert mid != mite and mid != brute


def test_the_alive_threat_drives_the_default_parameter():
    g = _game()
    assert g.enemy_blend_report()["parameter"] == 0.0
    g.sim.enemies = [
        _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 5.0), hp=600, max_hp=600)
    ]
    assert g.enemy_blend_report()["parameter"] == 600.0


def test_reporting_a_blend_never_touches_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    for parameter in (0.0, 75.0, 600.0):
        g.enemy_blend_report(parameter=parameter, time=1.25)
    assert stable_hash(g.snapshot()) == before
