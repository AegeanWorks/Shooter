"""Effects proof: the warden dies as an ember collapse, not a white block.

The shared white-hot death silhouette scaled with the 2.2 m warden cube and
filled the campaign-clear frame. The boss now uses a warm death material and a
per-type scale cap while every other enemy keeps the white shrink.
"""

from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import _Enemy


def _game() -> ShooterGame:
    game = ShooterGame()
    game.build_scene()
    game.sim.spawn_queue = ["mite"]
    game.sim.spawn_t = 999.0
    return game


def test_warden_death_uses_ember_material_and_a_scale_cap():
    game = _game()
    game.sim.enemies = [
        _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 2.0), hp=0, max_hp=600,
               alive=False, death_t=0.1, summon_cd=999.0)
    ]
    game._sync_scene()
    node = game._enemy_nodes[0]
    assert node.visible is True
    boss_flash = game.assets.require("material.boss_death").payload
    assert node.material is boss_flash
    assert node.material is not game.assets.require("material.enemy_hit").payload
    assert 0.0 < node.transform.scale.x <= 0.46, node.transform.scale


def test_small_enemy_death_keeps_the_white_shrink():
    game = _game()
    game.sim.enemies = [
        _Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=0, max_hp=30,
               alive=False, death_t=0.1)
    ]
    game._sync_scene()
    node = game._enemy_nodes[0]
    assert node.material is game.assets.require("material.enemy_hit").payload
    assert 0.0 < node.transform.scale.x < 1.0


def test_boss_death_material_is_warm():
    game = _game()
    material = game.assets.require("material.boss_death").payload
    assert material.color.x > material.color.z * 2.0
    assert material.emissive.x > material.emissive.z * 2.0
