"""Graphics proofs: the first-person gun follows the camera and weapon.

The viewmodel is now a Keystone CameraRig: the gun parts hold camera-space
offsets and the rig root carries the camera pose. These tests pin the three
parts, rig follow, weapon tint and the death hide.
"""

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_viewmodel_exists_and_the_rig_follows_camera():
    g = _game()
    assert g._view_body is not None and g._view_body.visible is True
    assert g._view_barrel is not None and g._view_barrel.visible is True
    body = g._view_body.transform.position
    assert 0.2 < body.length() < 1.0, body
    local = (body.x, body.y, body.z)
    root = g._view_rig.root.transform
    camera = g.scene.camera
    assert (root.position.x, root.position.y, root.position.z) == (
        camera.position.x, camera.position.y, camera.position.z
    )
    g.sim.yaw = 1.5707963267948966
    g._sync_scene()
    after = g._view_body.transform.position
    assert (after.x, after.y, after.z) == local, "camera-space offsets must not move with yaw"
    moved = g._view_rig.root.transform
    assert (moved.position.x, moved.position.y, moved.position.z) == (
        camera.position.x, camera.position.y, camera.position.z
    )
    assert moved.rotation != root.rotation


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
