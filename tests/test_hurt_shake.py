"""Combat-feel proof: taking damage jolts the camera.

The hurt sound and directional cue already existed, but the camera did
not move. A short deterministic offset driven by `hurt_t` adds a physical
jolt; the sim, aim and snapshot are untouched.
"""

from keystone.replay import stable_hash

from shooter.game import ShooterGame


def _cam(g: ShooterGame) -> tuple[float, float, float]:
    p = g.scene.camera.position
    return (p.x, p.y, p.z)


def test_camera_jolts_while_hurt_timer_runs():
    g = ShooterGame()
    g.build_scene()
    eye = g.sim.eye()
    steady = (eye.x, eye.y, eye.z)
    g.sim.hurt_t = 0.4
    g._sync_scene()
    assert _cam(g) != steady
    g.sim.hurt_t = 0.0
    g._sync_scene()
    assert _cam(g) == steady


def test_camera_jolt_does_not_change_sim():
    g = ShooterGame()
    g.build_scene()
    g.sim.hurt_t = 0.4
    before = stable_hash(g.sim.snapshot())
    g._sync_scene()
    after = stable_hash(g.sim.snapshot())
    assert before == after
