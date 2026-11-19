"""Combat-feel proof: taking damage jolts the camera through Keystone shake.

The hurt sound and directional cue already existed. The camera jolt is now a
`keystone.camera_shake.CameraShake` offset: the game adds trauma on the "hurt"
event, Keystone samples deterministic sine noise, and this game keeps ownership
of its own pose by composing the offset onto the sim eye. The sim, the aim ray
and the snapshot stay untouched -- the jolt is presentation only.
"""

from keystone.input import ActionState
from keystone.replay import stable_hash

from shooter.game import ShooterGame

STEP = 1.0 / 60.0


def _cam(game: ShooterGame) -> tuple[float, float, float]:
    position = game.scene.camera.position
    return (position.x, position.y, position.z)


def _hurt_once(game: ShooterGame) -> None:
    """Make the next update() report one real "hurt" event."""
    original_step = game.sim.step
    pending = ["hurt"]

    def step(dt, actions):
        events = list(original_step(dt, actions))
        if pending:
            pending.pop()
            events.append("hurt")
        return events

    game.sim.step = step


def _death_once(game: ShooterGame) -> None:
    """Make the next update() report one real "died" event."""
    original_step = game.sim.step
    pending = ["died"]

    def step(dt, actions):
        events = list(original_step(dt, actions))
        if pending:
            pending.pop()
            game.sim.hp = 0
            game.sim.alive = False
            events.append("died")
        return events

    game.sim.step = step


def _quiet(game: ShooterGame) -> None:
    """Remove attackers so decay is measured without a second hit."""
    game.sim.spawn_queue = []
    game.sim.enemies = []


def test_camera_jolts_after_taking_damage_and_settles_when_trauma_decays():
    game = ShooterGame()
    game.build_scene()
    eye = game.sim.eye()
    steady = (eye.x, eye.y, eye.z)
    assert _cam(game) == steady

    _hurt_once(game)
    _quiet(game)
    game.update(STEP, ActionState())

    assert game._shake.trauma > 0.0
    assert _cam(game) != steady, "taking damage must move the camera"
    assert game.camera_shake_report is not None
    assert game.camera_shake_report["schema"] == 1
    assert game.camera_shake_report["trauma"] > 0.0

    # trauma decays linearly to exactly zero, and the camera returns to the eye
    # (the idle player's eye drifts a fraction of a millimetre, so compare live)
    for _ in range(120):
        game.update(STEP, ActionState())
    assert game._shake.trauma == 0.0
    assert game.camera_shake_report is None
    settled = game.sim.eye()
    assert _cam(game) == (settled.x, settled.y, settled.z)


def test_the_jolt_composes_onto_the_sim_pose_without_replacing_it():
    game = ShooterGame()
    game.build_scene()
    _hurt_once(game)
    _quiet(game)
    game.update(STEP, ActionState())

    offset = game._shake.sample()
    eye = game.sim.eye()
    cam = game.scene.camera
    assert cam.position.x == eye.x + offset.position.x
    assert cam.position.y == eye.y + offset.position.y
    assert cam.position.z == eye.z + offset.position.z
    assert cam.yaw == game.sim.yaw + offset.yaw
    # the sim still owns aim: the look offset is the shake, nothing else
    assert cam.pitch != game.sim.pitch or offset.pitch == 0.0


def test_camera_jolt_does_not_change_sim():
    game = ShooterGame()
    game.build_scene()
    game._shake.add(0.6)
    before = stable_hash(game.sim.snapshot())
    game._sync_scene(STEP)
    assert game._shake.trauma > 0.0
    after = stable_hash(game.sim.snapshot())
    assert before == after


def test_build_scene_clears_trauma():
    game = ShooterGame()
    game.build_scene()
    _hurt_once(game)
    _quiet(game)
    game.update(STEP, ActionState())
    assert game._shake.trauma > 0.0

    game.build_scene()
    assert game._shake.trauma == 0.0
    assert game.camera_shake_report is None

def test_a_cinematic_owns_the_camera_and_clears_live_trauma():
    """A hit on the killing blow must not freeze mid-decay behind a path."""
    game = ShooterGame()
    game.build_scene()
    game._shake.add(0.9)
    game._sync_scene(STEP)
    assert game.camera_shake_report is not None

    _death_once(game)
    _quiet(game)
    game.update(STEP, ActionState())

    assert game._death_camera is not None, "the death cinematic must own the camera"
    assert game._shake.trauma == 0.0, "trauma must not freeze behind a cinematic"
    assert game.camera_shake_report is None, "no shake may be reported while a path drives"


def test_the_victory_cinematic_also_clears_trauma():
    game = ShooterGame()
    game.build_scene()
    game.sim.wave = int(game.sim.levels.get("win_wave", 4))
    game._shake.add(0.9)
    game._sync_scene(STEP)
    assert game.camera_shake_report is not None

    game.update(STEP, ActionState())

    assert game._clear_camera is not None
    assert game._shake.trauma == 0.0
    assert game.camera_shake_report is None
