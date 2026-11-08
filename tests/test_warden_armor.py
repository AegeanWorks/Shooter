"""Visual proof: the warden body carries an armor texture, not a flat slab."""

from keystone.math3d import Vec3

from shooter.game import ShooterGame, _warden_armor_texture
from shooter.sim import _Enemy


def _pixel(texture, x: int, y: int) -> int:
    return texture.rgba[(y * texture.width + x) * 4]


def test_armor_texture_is_deterministic_and_plated():
    first = _warden_armor_texture()
    second = _warden_armor_texture()
    assert (first.width, first.height) == (64, 64)
    assert first.name == "warden-armor"
    assert first.sha256() == second.sha256()
    assert _pixel(first, 0, 0) < _pixel(first, 10, 10)   # seam darker than plate
    assert _pixel(first, 4, 4) > _pixel(first, 10, 10)   # rivet brighter than plate


def test_warden_material_wraps_the_armor_texture():
    game = ShooterGame()
    game.build_scene()
    material = game.assets.require("material.warden").payload
    texture = game.assets.require("texture.warden").payload
    assert material.texture is texture
    assert material.checker_scale > 0.0
    assert texture.name == "warden-armor"


def test_live_warden_uses_the_textured_material():
    game = ShooterGame()
    game.build_scene()
    game.sim.enemies = [
        _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 2.0), hp=600, max_hp=600,
               summon_cd=999.0)
    ]
    game._sync_scene()
    node = game._enemy_nodes[0]
    assert node.mesh is game.assets.require("mesh.warden").payload
    assert node.material is game.assets.require("material.warden").payload
