"""Keystone testbed: camera_shaker composes the damage jolt onto the base pose.

Cycle 142 adopted CameraShake for the deterministic noise but the shooter still
added the sampled offset to the sim eye by hand. This module proves the testbed
now consumes CameraShaker: Keystone owns the composition, the base pose is
immutable, and the AI-visible report distinguishes base from shaken pose.
"""

from keystone.input import ActionState
from keystone.replay import stable_hash

from shooter.game import ShooterGame

STEP = 1.0 / 60.0


def _shaking_game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = []
    g.sim.enemies = []
    g._shake.add(0.9)
    g.update(STEP, ActionState())
    return g


def test_the_rendered_camera_is_the_shaker_pose():
    g = _shaking_game()
    posed = g._shaker.pose()
    cam = g.scene.camera
    assert (cam.position.x, cam.position.y, cam.position.z) == (
        posed.position.x, posed.position.y, posed.position.z
    )
    assert cam.yaw == posed.yaw and cam.pitch == posed.pitch
    assert g._shake.trauma > 0.0


def test_the_base_pose_stays_on_the_sim_eye_across_frames():
    g = _shaking_game()
    for _ in range(12):
        g.update(STEP, ActionState())
        eye = g.sim.eye()
        base = g._base_camera
        assert (base.position.x, base.position.y, base.position.z) == (eye.x, eye.y, eye.z)
        assert base.yaw == g.sim.yaw
        assert base.pitch == max(-1.55, min(1.55, g.sim.pitch + g.sim.kick))


def test_the_report_distinguishes_the_base_from_the_shaken_pose():
    g = _shaking_game()
    report = g.camera_shaker_report
    assert report is not None and report["schema"] == 1
    assert report["local"] is False
    assert report["shake"]["trauma"] > 0.0
    assert report["base"]["position"] != report["pose"]["position"]
    assert report["base"]["yaw"] != report["pose"]["yaw"] or report["pose"]["yaw"] != g.sim.yaw
    for _ in range(120):
        g.update(STEP, ActionState())
    assert g.camera_shaker_report is None


def test_the_shaker_reports_keep_the_sim_out_of_the_picture():
    g = _shaking_game()
    before = stable_hash(g.sim.snapshot())
    posed = g._shaker.pose()
    assert posed is not g._base_camera
    assert stable_hash(g.sim.snapshot()) == before


def test_build_scene_and_a_cinematic_clear_the_shaker_report():
    g = _shaking_game()
    assert g.camera_shaker_report is not None
    g.build_scene()
    assert g.camera_shaker_report is None

    g._shake.add(0.9)
    g._sync_scene(STEP)
    assert g.camera_shaker_report is not None

    original_step = g.sim.step
    pending = ["died"]

    def step(dt, actions):
        events = list(original_step(dt, actions))
        if pending:
            pending.pop()
            g.sim.hp = 0
            g.sim.alive = False
            events.append("died")
        return events

    g.sim.step = step
    g.update(STEP, ActionState())
    assert g._death_camera is not None
    assert g.camera_shaker_report is None
