"""Enemies/bosses proofs: the warden slam radius is visible during windup.

The boss swells and the caption/audio warn of the slam, but the 4.5 m range
had no ground cue. A ring of shared cubes marks the exact radius; it is
presentation-only and hidden whenever no live warden is winding up.
"""

import math

from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import _Enemy


class _Hud:
    width = 960
    height = 540


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    return g


def _warden(windup: float = 0.5) -> _Enemy:
    return _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 5.0), hp=600, max_hp=600,
                  summon_cd=999.0, windup_t=windup)


def test_windup_shows_a_ground_ring_at_the_slam_radius():
    g = _game()
    g.sim.enemies = [_warden()]
    g._sync_scene()
    visible = [n for n in g._slam_ring if n.visible]
    segments = int(g.sim.juice["slam_ring"]["segments"])
    assert len(visible) == segments, (len(visible), segments)
    radius = float(g.sim.enemy_defs["warden"]["range"])
    for node in visible:
        distance = math.hypot(node.transform.position.x - 0.0,
                              node.transform.position.z - 5.0)
        assert abs(distance - radius) < 1e-6, (distance, radius)


def test_ring_is_hidden_without_a_windup():
    g = _game()
    g.sim.enemies = [_warden(windup=0.0)]
    g._sync_scene()
    assert not any(n.visible for n in g._slam_ring)


def test_ring_is_hidden_without_a_warden():
    g = _game()
    g.sim.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0),
                            hp=30, max_hp=30)]
    g._sync_scene()
    assert not any(n.visible for n in g._slam_ring)


def test_slam_ring_is_data_owned():
    g = _game()
    for key in ("segments", "width", "height"):
        assert key in g.sim.juice["slam_ring"], key
