"""Testbed consistency: one reset path for camera-shake presentation state.

The same three lines (trauma reset + two report clears) appeared in build_scene
and both cinematic starts. Cycle 176 found a missing clear in that pattern once;
this pins one helper so future shake state cannot be forgotten at one caller.
"""

from keystone.input import ActionState
from keystone.replay import stable_hash

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def _shaking(g: ShooterGame) -> None:
    g._shake.add(0.9)
    g._sync_scene(1.0 / 60.0)
    assert g.camera_shake_report is not None
    assert g.camera_shaker_report is not None


def _assert_clean(g: ShooterGame) -> None:
    assert g._shake.trauma == 0.0
    assert g.camera_shake_report is None
    assert g.camera_shaker_report is None


def test_the_helper_clears_trauma_and_both_reports():
    g = _game()
    _shaking(g)
    g._clear_shake_reports()
    _assert_clean(g)


def test_build_scene_uses_the_shared_reset():
    g = _game()
    _shaking(g)
    g.build_scene()
    _assert_clean(g)


def test_the_death_cinematic_uses_the_shared_reset():
    g = _game()
    _shaking(g)
    original_step = g.sim.step

    def dying_step(dt, actions):
        events = list(original_step(dt, actions))
        g.sim.hp = 0
        g.sim.alive = False
        return events + ["died"]

    g.sim.step = dying_step
    g.update(1.0 / 60.0, ActionState())
    assert g._death_camera is not None
    _assert_clean(g)


def test_the_victory_cinematic_uses_the_shared_reset():
    g = _game()
    _shaking(g)
    g.sim.wave = int(g.sim.levels["win_wave"])
    g.update(1.0 / 60.0, ActionState())
    assert g._clear_camera is not None
    _assert_clean(g)


def test_repeated_resets_are_idempotent_and_never_touch_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    g._clear_shake_reports()
    g._clear_shake_reports()
    _assert_clean(g)
    assert stable_hash(g.snapshot()) == before
