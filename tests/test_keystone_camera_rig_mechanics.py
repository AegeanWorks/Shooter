"""Keystone testbed: the viewmodel is a CameraRig, not hand-composed world nodes.

`keystone.camera_rig` was one of the Keystone modules the shooter had never
imported. The gun parts are now overlay-layer children that declare camera-space
offsets; the rig root copies the camera pose each frame in _sync_scene.
"""

from keystone.replay import stable_hash
from keystone.scene import OVERLAY_LAYER

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g._sync_scene()
    return g


def test_the_rig_and_its_parts_live_on_the_overlay_layer():
    g = _game()
    rig = g._view_rig
    assert rig.root.layer == OVERLAY_LAYER
    assert rig.root.parent is g.scene.root
    for node in (g._view_body, g._view_barrel, g._view_grip):
        assert node.layer == OVERLAY_LAYER
        assert node.parent is rig.root


def test_the_root_follows_the_camera_and_a_missing_sync_is_visible():
    g = _game()
    root = g._view_rig.root
    camera = g.scene.camera
    before = (root.transform.position.x, root.transform.position.y, root.transform.position.z)
    camera.position = camera.position.__class__(3.0, 2.0, 4.0)
    assert (root.transform.position.x, root.transform.position.y, root.transform.position.z) == before
    g._view_rig.sync()
    assert (root.transform.position.x, root.transform.position.y, root.transform.position.z) == (3.0, 2.0, 4.0)


def test_parts_declare_camera_space_offsets():
    g = _game()
    body = g._view_body.transform.position
    grip = g._view_grip.transform.position
    assert 0.20 <= body.x <= 0.35 and -0.30 <= body.y <= -0.15
    assert -0.90 <= body.z <= -0.50
    assert grip.y < body.y, (body, grip)


def test_syncing_the_rig_never_reaches_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    g.scene.camera.position = g.scene.camera.position.__class__(1.0, 2.0, 3.0)
    g._view_rig.sync()
    assert stable_hash(g.snapshot()) == before
