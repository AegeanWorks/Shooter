"""Progression proofs: bounded run history survives saves.

Schema 3 adds a newest-first `history` list (max five runs). Schema 2
migrates with an empty history; each death appends and trims; the debrief
shows the recent scores.
"""

import json

from shooter.game import ShooterGame
from shooter.profile import ProfileStore, default_profile


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


def test_schema_two_migrates_with_empty_history(tmp_path):
    path = tmp_path / "profile.json"
    path.write_text(
        json.dumps({"schema": 2, "best_score": 9, "wins": 2,
                    "runs": 4, "last_run": None}),
        encoding="utf-8",
    )
    profile = ProfileStore(path).load()
    assert profile["schema"] == 3
    assert profile["history"] == []
    assert profile["wins"] == 2


def test_death_history_appends_newest_first_and_caps(tmp_path):
    path = tmp_path / "profile.json"
    for index in range(6):
        g = ShooterGame(profile_path=path)
        g.build_scene()
        g.sim.score = 100 + index
        g.sim.kills = index
        g.sim.best_streak = index
        g._finish_run()
    saved = ProfileStore(path).load()
    assert len(saved["history"]) == 5
    assert [item["score"] for item in saved["history"]] == [105, 104, 103, 102, 101]
    assert saved["last_run"]["score"] == 105


def test_debrief_shows_recent_scores(tmp_path):
    path = tmp_path / "profile.json"
    seeded = default_profile()
    seeded["history"] = [
        {"score": 980, "kills": 8, "wave": 3, "best_streak": 5,
         "time_s": 41, "outcome": "lose"},
        {"score": 740, "kills": 6, "wave": 2, "best_streak": 3,
         "time_s": 30, "outcome": "lose"},
    ]
    ProfileStore(path).save(seeded)
    g = ShooterGame(profile_path=path)
    g.build_scene()
    g.last_run = {"score": 1500, "kills": 9, "wave": 2, "best_streak": 4,
                  "time_s": 10, "outcome": "lose"}
    g.sim.alive = False
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    labels = [str(t[2]) for t in canvas.texts]
    assert any("RECENT 980 / 740" in label for label in labels), labels
