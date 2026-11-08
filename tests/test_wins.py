"""Progression proofs: campaign wins are persisted and shown.

Schema 2 adds ``wins`` to the profile. Schema 1 files migrate without losing
bests; a campaign clear increments and saves the count; the clear banner
shows it.
"""

import json

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.profile import ProfileStore, default_profile
from shooter.sim import _Enemy


class _Canvas:
    def __init__(self) -> None:
        self.rects: list[tuple] = []
        self.texts: list[tuple] = []

    def rect(self, *args) -> None:
        self.rects.append(args)

    def text(self, *args) -> None:
        self.texts.append(args)


class _Hud:
    width = 960
    height = 540


def test_schema_one_migrates_with_zero_wins(tmp_path):
    path = tmp_path / "profile.json"
    path.write_text(
        json.dumps({"schema": 1, "best_score": 77, "best_kills": 4,
                    "best_wave": 3, "best_streak": 2, "runs": 5}),
        encoding="utf-8",
    )
    profile = ProfileStore(path).load()
    assert profile["schema"] == 3
    assert profile["wins"] == 0
    assert profile["history"] == []
    assert profile["best_score"] == 77
    assert profile["runs"] == 5


def _clear_game(tmp_path) -> ShooterGame:
    g = ShooterGame(profile_path=tmp_path / "profile.json")
    g.build_scene()
    g.sim.spawn_queue = []
    g.sim.spawn_t = 999.0
    g.sim.pickup_taken = True
    g.sim.wave = 3
    g.sim.enemies = [
        _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 2.0), hp=12, max_hp=600,
               summon_cd=999.0)
    ]
    g.update(1.0 / 60.0, ActionState(held=frozenset({"fire"})))
    return g


def test_campaign_clear_persists_wins(tmp_path):
    g = _clear_game(tmp_path)
    assert g.campaign_cleared is True
    assert g.profile["wins"] == 1
    saved = ProfileStore(tmp_path / "profile.json").load()
    assert saved["schema"] == 3
    assert saved["wins"] == 1
    assert saved["best_wave"] >= 4


def test_win_banner_shows_campaign_wins(tmp_path):
    g = _clear_game(tmp_path)
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    labels = [str(t[2]) for t in canvas.texts]
    assert any("CAMPAIGN CLEAR" in label for label in labels), labels
    assert any("CAMPAIGNS WON 1" in label for label in labels), labels
