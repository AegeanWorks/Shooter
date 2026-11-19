"""Testbed consistency: one rebuild reset for presentation state.

build_scene cleared two camera paths, two camera reports, both shake reports and
the spatial audio report one line at a time. Cycle 198 unified the shake triple;
this pins a single rebuild reset that reuses it.
"""

from keystone.replay import stable_hash

import shooter.game as game_module
from shooter.game import ShooterGame

FIELDS = (
    "_death_camera", "death_camera_report",
    "_clear_camera", "campaign_camera_report",
    "camera_shake_report", "camera_shaker_report",
    "spatial_audio_report",
)


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def _dirty(g: ShooterGame) -> None:
    for name in FIELDS:
        setattr(g, name, {"schema": 1})
    g._shake.add(0.9)


def _assert_clean(g: ShooterGame) -> None:
    for name in FIELDS:
        assert getattr(g, name) is None, name
    assert g._shake.trauma == 0.0


def test_the_helper_clears_every_presentation_field():
    g = _game()
    _dirty(g)
    g._reset_presentation_reports()
    _assert_clean(g)


def test_build_scene_uses_the_shared_helper(monkeypatch):
    g = _game()
    calls = []
    original = g._reset_presentation_reports

    def spy(self):
        calls.append(1)
        return original()

    monkeypatch.setattr(game_module.ShooterGame, "_reset_presentation_reports", spy)
    g.build_scene()
    assert calls == [1]
    _assert_clean(g)


def test_a_rebuild_after_a_cinematic_clears_everything():
    g = _game()
    _dirty(g)
    g.build_scene()
    _assert_clean(g)


def test_resetting_presentation_never_touches_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    _dirty(g)
    g._reset_presentation_reports()
    assert stable_hash(g.snapshot()) == before
