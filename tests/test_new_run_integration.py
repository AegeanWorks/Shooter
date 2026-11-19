"""Integration proof: a real run, a real end, and a real restart.

`test_new_run.py` drives the restart with synthetic events. This suite uses the
shipped bot and the shipped sim so the whole loop is exercised the way a player
reaches it: play to the campaign seal (or stand still until something kills
you), press Enter, and play a second run. It also checks the saved profile, so
a restart that quietly dropped the first run's record would fail here.
"""

from pathlib import Path

import pytest

from keystone.input import ActionState

from shooter.bot import kite_step
from shooter.game import ShooterGame
from shooter.profile import ProfileStore

STEP = 1.0 / 60.0
ENTER = ActionState(pressed=frozenset({"confirm"}))
IDLE = ActionState()


def _finish_death_cinematic(game, limit=400):
    """Advance until the death cinematic has clapped out on its final pose."""
    for _ in range(limit):
        if game._death_camera is None or game._death_camera.done:
            return True
        game.update(STEP, IDLE)
    return False


def _game(tmp_path) -> ShooterGame:
    game = ShooterGame(profile_path=tmp_path / "profile.json")
    game.build_scene()
    return game


def _play_until_campaign_seal(game, limit=4000):
    for _ in range(limit):
        game.update(STEP, kite_step(game.sim))
        if game.campaign_cleared:
            return True
    return False


def _run_out_the_banner(game, limit=400):
    for _ in range(limit):
        if game.campaign_clear_t <= 0.0:
            return True
        game.update(STEP, IDLE)
    return False


def test_win_then_restart_then_play_a_second_run(tmp_path):
    game = _game(tmp_path)
    assert _play_until_campaign_seal(game), "the bot should clear the campaign"
    first = {"score": int(game.sim.score), "kills": int(game.sim.kills)}
    assert first["kills"] > 0
    assert _run_out_the_banner(game)

    game.update(STEP, ENTER)

    assert game.sim.alive is True
    assert game.sim.tick == 0
    assert (game.sim.score, game.sim.kills, int(game.sim.wave)) == (0, 0, 1)
    assert game.campaign_cleared is False
    assert game._clear_camera is None

    for _ in range(1500):
        game.update(STEP, kite_step(game.sim))

    assert game.sim.tick == 1500
    assert int(game.sim.wave) > 1, "the second run must actually progress"
    assert int(game.sim.kills) > 0
    # the first run is the record; the second is still in progress
    assert int(game.profile["wins"]) == 1
    assert int(game.profile["runs"]) == 1
    assert game.last_run is None

    saved = ProfileStore(tmp_path / "profile.json").load()
    assert saved["wins"] == 1
    assert saved["history"][0]["outcome"] == "win"
    assert saved["history"][0]["score"] == first["score"]


def test_a_real_death_restarts_into_a_live_second_run(tmp_path):
    game = _game(tmp_path)
    for _ in range(20000):
        game.update(STEP, IDLE)
        if not game.sim.alive:
            break
    assert not game.sim.alive, "standing still in wave 1 should be fatal"
    death = {
        "wave": int(game.sim.wave),
        "score": int(game.sim.score),
        "outcome": game.last_run["outcome"],
    }
    assert death["outcome"] == "lose"

    assert _finish_death_cinematic(game), "the death cinematic should finish"
    game.update(STEP, ENTER)
    assert game.sim.alive is True
    assert game.last_run is None, "the debrief must clear on restart"

    for _ in range(300):
        game.update(STEP, IDLE)
    assert game.sim.tick == 300
    assert game.sim.alive is True

    saved = ProfileStore(tmp_path / "profile.json").load()
    assert saved["runs"] == 1, "restarting must not record a phantom run"
    assert [(item["score"], item["outcome"]) for item in saved["history"]] == [
        (death["score"], "lose")
    ]


def test_restarting_twice_keeps_a_single_history_entry_per_finished_run(tmp_path):
    game = _game(tmp_path)
    for _ in range(20000):
        game.update(STEP, IDLE)
        if not game.sim.alive:
            break
    assert not game.sim.alive

    for _ in range(2):
        assert _finish_death_cinematic(game)
        game.update(STEP, ENTER)
        assert game.sim.alive is True
        for _ in range(20000):
            game.update(STEP, IDLE)
            if not game.sim.alive:
                break
        assert not game.sim.alive

    saved = ProfileStore(tmp_path / "profile.json").load()
    assert saved["runs"] == 3, f"three deaths should be three runs, saw {saved['runs']}"
    assert len(saved["history"]) == 3
    assert all(item["outcome"] == "lose" for item in saved["history"])
