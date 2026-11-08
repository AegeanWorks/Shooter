"""Graphics proofs: the first-person gun follows the camera and weapon.

The baseline had no viewmodel: the crosshair and floating muzzle flash were
the only weapon presence. These tests pin the two gun nodes, camera follow,
weapon tint and the death hide.
"""

from keystone.math3d import Vec3

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_viewmodel_exists_and_follows_camera():
    g = _game()
    assert g._view_body is not None and g._view_body.visible is True
    assert g._view_barrel is not None and g._view_barrel.visible is True
    eye = g.sim.eye()
    body = g._view_body.transform.position
    assert 0.2 < Vec3(body.x - eye.x, body.y - eye.y, body.z - eye.z).length() < 1.0
    before = body
    g.sim.yaw = 1.5707963267948966
    g._sync_scene()
    after = g._view_body.transform.position
    assert after.x > before.x + 0.1, (before, after)


def test_viewmodel_tints_with_active_weapon():
    g = _game()
    for wid in ("pulse", "scatter", "lance"):
        g.sim.weapon = wid
        g._sync_scene()
        expected = g.assets.require(f"material.gun_{wid}").payload
        assert g._view_body.material is expected, wid
        assert g._view_barrel.material is expected, wid


def test_viewmodel_hides_on_death():
    g = _game()
    g.sim.alive = False
    g._sync_scene()
    assert g._view_body.visible is False
    assert g._view_barrel.visible is False
