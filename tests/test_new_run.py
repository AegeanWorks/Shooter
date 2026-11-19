"""Game proof: a finished run can be restarted without relaunching.

The long soak exposed the gap: 60000 frames past the campaign seal produced no
further waves, kills or score, and a death left the debrief up forever -- the
only way out was ESC and relaunching. Enter (`confirm` in the engine keymap)
now starts a new run, while the profile keeps the record of the old one.
"""

import pytest

from keystone.input import ActionState

from shooter.game import ShooterGame

STEP = 1.0 / 60.0
ENTER = ActionState(pressed=frozenset({"confirm"}))


def _finish_death_cinematic(game, limit=400):
    """Advance until the death cinematic has clapped out on its final pose."""
    for _ in range(limit):
        if game._death_camera is None or game._death_camera.done:
            return True
        game.update(STEP, ActionState())
    return False


def _tick(game, actions, frames=1):
    for _ in range(frames):
        game.update(STEP, actions)


def _step_with(game, events_once):
    """Wrap sim.step so the next update also reports the given events."""
    original = game.sim.step
    pending = list(events_once)

    def step(dt, actions):
        events = list(original(dt, actions))
        if pending:
            events.extend(pending)
            pending.clear()
        return events

    game.sim.step = step


def _dying_game(tmp_path):
    """A game that dies during its first update, the way a real hit does."""
    game = ShooterGame(profile_path=tmp_path / "profile.json")
    game.build_scene()
    game.sim.score = 900
    game.sim.kills = 4
    original = game.sim.step
    pending = ["died"]

    def step(dt, actions):
        events = list(original(dt, actions))
        if pending:
            pending.pop()
            game.sim.hp = 0
            game.sim.alive = False
            events.append("died")
        return events

    game.sim.step = step
    return game


def _winning_game(tmp_path):
    game = ShooterGame(profile_path=tmp_path / "profile.json")
    game.build_scene()
    game.sim.wave = int(game.sim.levels.get("win_wave", 4))
    return game


def test_enter_after_death_starts_a_new_run_and_keeps_the_record(tmp_path):
    game = _dying_game(tmp_path)
    _tick(game, ActionState())
    assert game.sim.alive is False
    assert game.last_run is not None
    runs_before = int(game.profile["runs"])

    assert _finish_death_cinematic(game), "the death cinematic should finish"
    tick_before = game.sim.tick
    _tick(game, ENTER)

    assert game.sim.alive is True, "a new run must start"
    assert game.sim.tick == 0, "the sim clock restarts (the restart frame steps nothing)"
    assert tick_before > 0
    assert game.last_run is None, "the debrief belongs to the finished run"
    assert game.profile["runs"] == runs_before, "restarting must not record another run"
    assert len(game.profile["history"]) >= 1, "history survives the restart"


def test_enter_after_victory_starts_a_new_run(tmp_path):
    game = _winning_game(tmp_path)
    _tick(game, ActionState())
    assert game.campaign_cleared is True
    assert game._clear_camera is not None
    _tick(game, ActionState(), frames=260)  # let the 4 s banner expire
    assert game.campaign_clear_t == 0.0

    _tick(game, ENTER)

    assert game.sim.alive is True
    assert game.campaign_cleared is False, "the sealed campaign must clear"
    assert game._clear_camera is None, "the victory cinematic must not survive"
    assert int(game.profile["wins"]) == 1, "the win stays in the profile"
    assert game.profile["history"][0]["outcome"] == "win"


def test_enter_during_the_victory_banner_is_ignored(tmp_path):
    game = _winning_game(tmp_path)
    _tick(game, ActionState())
    assert game.campaign_clear_t > 0.0
    _tick(game, ENTER)
    assert game.campaign_cleared is True, "the banner must not be skipped"
    assert game._clear_camera is not None


def test_enter_mid_run_does_nothing(tmp_path):
    game = ShooterGame(profile_path=tmp_path / "profile.json")
    game.build_scene()
    _tick(game, ActionState(), frames=30)
    tick = game.sim.tick
    score = game.sim.score

    _tick(game, ENTER)

    assert game.sim.tick == tick + 1, "the run must continue"
    assert game.sim.score >= score
    assert game.sim.alive is True


def test_enter_on_the_death_frame_does_not_skip_the_debrief(tmp_path):
    game = _dying_game(tmp_path)
    # the death is reported by this update; the confirm arrives too late to act
    _tick(game, ENTER)
    assert game.sim.alive is False
    assert game.last_run is not None, "the debrief must still have its run"
    # and once the cinematic has played out, the next press does restart
    assert _finish_death_cinematic(game)
    _tick(game, ENTER)
    assert game.sim.alive is True


def test_enter_during_the_death_cinematic_is_ignored(tmp_path):
    """A player mashing confirm while dying must still see the debrief."""
    game = _dying_game(tmp_path)
    _tick(game, ActionState())
    assert game._death_camera is not None
    assert game.last_run is not None

    for _ in range(30):
        _tick(game, ENTER)
        assert game.sim.alive is False, "the cinematic must not be skipped"
        assert game._death_camera is not None

    # once it finishes, the same press restarts the run
    assert _finish_death_cinematic(game)
    _tick(game, ENTER)
    assert game.sim.alive is True


def test_a_death_without_a_cinematic_is_restartable_at_once(tmp_path, monkeypatch):
    """A failed cinematic build must not leave the player stuck on the debrief."""
    game = _dying_game(tmp_path)
    monkeypatch.setattr(ShooterGame, "_start_death_camera", lambda self: None)
    _tick(game, ActionState())
    assert game._death_camera is None
    _tick(game, ENTER)
    assert game.sim.alive is True, "a missing cinematic must not block the restart"


def test_restart_resets_transient_presentation_state(tmp_path):
    game = _dying_game(tmp_path)
    _tick(game, ActionState())
    game._shake.add(0.7)
    game._sync_scene(STEP)
    assert game._death_camera is not None

    assert _finish_death_cinematic(game)
    _tick(game, ENTER)

    assert game._death_camera is None
    assert game.death_camera_report is None
    assert game._shake.trauma == 0.0
    assert game.camera_shake_report is None
    assert game.kill_feed == []
    assert game.campaign_cleared is False
