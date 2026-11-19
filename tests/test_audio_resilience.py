"""Game proof: an audio refusal is counted, never fatal.

`_play_clip` promises "audio must never crash gameplay" and counts refusals in
`dropped_sfx` so a soak report can see them. `Mixer.play` raises **two** kinds
of refusal -- `TypeError` for a non-clip, `ValueError` for a mismatched sample
rate, an unknown bus, or a bad gain/pitch -- but the guard caught only the
second, so a `TypeError` from the audio layer killed the frame.

The mixer is software-only (Keystone needs no playback device), so the reachable
failure is a refusal, not a missing sound card. These tests make the mixer raise
each type and assert the game keeps running, counts the drop, and leaves the
deterministic sim untouched.
"""

import pytest

from keystone.audio import Mixer
from keystone.input import ActionState
from keystone.replay import stable_hash

from shooter.game import ShooterGame

STEP = 1.0 / 60.0
FIRE = ActionState(pressed=frozenset({"fire"}), held=frozenset({"fire"}))


def _game(tmp_path) -> ShooterGame:
    game = ShooterGame(profile_path=tmp_path / "profile.json")
    game.build_scene()
    return game


@pytest.mark.parametrize("failure", [TypeError, ValueError])
def test_a_mixer_refusal_is_counted_and_the_frame_survives(tmp_path, monkeypatch, failure):
    game = _game(tmp_path)

    def refuse(self, clip, bus="sfx", gain=1.0, pitch=1.0):
        raise failure("device refused")

    monkeypatch.setattr(Mixer, "play", refuse)

    game.update(STEP, FIRE)  # must not raise

    assert game.dropped_sfx >= 1, "a refusal must be visible, not swallowed"
    assert game.sim.shots >= 1, "the shot itself still had to resolve"


def test_the_drop_counter_does_not_touch_the_deterministic_sim(tmp_path, monkeypatch):
    game = _game(tmp_path)
    before = stable_hash(game.sim.snapshot())

    def refuse(self, clip, bus="sfx", gain=1.0, pitch=1.0):
        raise TypeError("refused")

    monkeypatch.setattr(Mixer, "play", refuse)
    game._sync_scene(STEP)          # presentation step only; no sim advance
    game._play_clip(object(), 0.5)  # a bad clip through the guarded path

    assert game.dropped_sfx == 1
    assert stable_hash(game.sim.snapshot()) == before
    assert "dropped_sfx" not in game.sim.snapshot(), (
        "the SFX counter belongs to presentation, not the sim record"
    )


def test_a_healthy_mixer_counts_nothing(tmp_path):
    game = _game(tmp_path)
    for _ in range(5):
        game.update(STEP, FIRE)
    assert game.dropped_sfx == 0, "a working mixer must not report drops"


def test_the_counter_appears_in_the_snapshot_for_soak_reports(tmp_path):
    game = _game(tmp_path)
    assert game.snapshot()["dropped_sfx"] == game.dropped_sfx == 0
