"""Graphics proof: a kill leaves a brief shrinking death silhouette.

The kill already had a burst, feed, sound, hitstop and crosshair marker,
but the enemy node disappeared on the kill frame. A 0.15 s white-hot
shrink gives the body a readable exit; it is presentation-only.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import Sim, _Enemy


def _kill_sim() -> Sim:
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=12, max_hp=30)]
    s._fire(s.weapons["pulse"], [])
    return s


def test_kill_sets_death_timer():
    s = _kill_sim()
    enemy = s.enemies[0]
    assert not enemy.alive
    assert enemy.death_t > 0.0, enemy.death_t
    assert "death_t" not in s.snapshot()


def test_death_timer_expires():
    s = _kill_sim()
    for _ in range(30):
        s.step(1.0 / 60.0, ActionState())
    assert s.enemies[0].death_t == 0.0


def test_scene_shows_a_shrinking_death():
    g = ShooterGame()
    g.build_scene()
    g.sim.enemies = [
        _Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=0, max_hp=30,
               alive=False, death_t=0.1)
    ]
    g._sync_scene()
    node = g._enemy_nodes[0]
    assert node.visible is True
    assert 0.0 < node.transform.scale.x < 1.0, node.transform.scale
    assert node.material is g.assets.require("material.enemy_hit").payload
    g.sim.enemies[0].death_t = 0.0
    g._sync_scene()
    assert node.visible is False
