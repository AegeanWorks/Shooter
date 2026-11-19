"""Keystone testbed: enemy steering built from live sim state.

`steering` was one of nine Keystone modules a corrected coverage scan found the
testbed never imported. `enemy_steering_report()` turns real enemy positions,
radii and DATA speeds into seek/arrive/separation vectors and a clamped wish —
an on-demand AI/soak query that never drives a body or writes sim state.
"""

from keystone.math3d import Vec3
from keystone.replay import stable_hash
from keystone.steering import arrive, seek, separation

from shooter.game import ShooterGame
from shooter.sim import _Enemy


def _game(enemies=()) -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.enemies = list(enemies)
    return g


def _mite(x: float, z: float) -> _Enemy:
    return _Enemy(etype="mite", pos=Vec3(x, 0.5, z), hp=30, max_hp=30)


def test_no_enemies_reports_no_subject():
    report = _game().enemy_steering_report()
    assert report["schema"] == 1 and report["subject"] is None
    assert report["neighbours"] == 0


def test_seek_points_at_the_player_and_stays_within_the_data_speed():
    g = _game([_mite(0.0, 2.0)])
    report = g.enemy_steering_report()
    subject = report["subject"]
    assert subject["schema"] == 1 and subject["max_speed"] == 4.2
    assert subject["speed"] <= subject["max_speed"] + 1e-6
    wish = subject["wish"]
    to_player = g.sim.player_pos - g.sim.enemies[0].pos
    assert wish[0] * to_player.x + wish[2] * to_player.z > 0.0


def test_arrive_slows_down_near_the_target():
    g = _game([_mite(0.0, 2.0)])
    position = g.sim.enemies[0].pos
    far = seek(position, g.sim.player_pos, 4.2)
    near = arrive(position, g.sim.player_pos, 4.2, slow_radius=10.0)
    assert near.length() < far.length()
    report = g.enemy_steering_report()
    assert len(report["arrive"]) == 3


def test_a_close_neighbour_contributes_separation():
    g = _game([_mite(0.0, 2.0), _mite(0.1, 2.0)])
    report = g.enemy_steering_report()
    assert report["neighbours"] == 1
    assert any(component != 0.0 for component in report["separation"])
    assert report["subject"]["wish"] != report["seek"]
    # the same force is available as a standalone pure query
    push = separation(Vec3(0.0, 0.5, 2.0), [(Vec3(0.1, 0.5, 2.0), 0.5)], 0.5, margin=0.02)
    assert push.length() > 0.0


def test_reporting_steering_never_touches_the_sim():
    g = _game([_mite(0.0, 2.0), _mite(0.1, 2.0)])
    before = stable_hash(g.snapshot())
    first = g.enemy_steering_report()
    assert g.enemy_steering_report() == first
    assert stable_hash(g.snapshot()) == before
