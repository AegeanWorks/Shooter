"""Progression proofs: campaign clears become run-history entries.

`_record_campaign_clear` used to only increment `wins`; `last_run` and
`history` were written by death alone. A win therefore vanished from the
record. The debrief also printed scores without their outcome.
"""

from keystone.input import ActionState

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


def _clear_game(tmp_path) -> ShooterGame:
    g = ShooterGame(profile_path=tmp_path / "profile.json")
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    g.sim.wave = 4
    g.update(1.0 / 60.0, ActionState())
    return g


def test_campaign_clear_records_a_win_run(tmp_path):
    g = _clear_game(tmp_path)
    assert g.campaign_cleared
    assert g.profile["wins"] == 1, g.profile
    assert g.profile["runs"] == 1, g.profile
    assert g.last_run["outcome"] == "win", g.last_run
    assert g.profile["history"][0]["outcome"] == "win", g.profile["history"]
    saved = ProfileStore(tmp_path / "profile.json").load()
    assert saved["history"][0]["outcome"] == "win", saved["history"]


def test_later_death_does_not_duplicate_the_win(tmp_path):
    g = _clear_game(tmp_path)
    g.sim.hp = 0
    g.sim.alive = False
    g._finish_run()
    assert g.profile["runs"] == 1, g.profile
    assert len(g.profile["history"]) == 1, g.profile["history"]
    assert g.last_run["outcome"] == "win", g.last_run


def test_death_still_records_a_loss(tmp_path):
    g = ShooterGame(profile_path=tmp_path / "profile.json")
    g.build_scene()
    g.sim.score = 1500
    g.sim.alive = False
    g._finish_run()
    assert g.profile["history"][0]["outcome"] == "lose", g.profile["history"]
    assert g.profile["runs"] == 1, g.profile


def test_debrief_marks_wins_and_losses(tmp_path):
    path = tmp_path / "profile.json"
    seeded = default_profile()
    seeded["wins"] = 1
    seeded["history"] = [
        {"score": 980, "kills": 8, "wave": 3, "best_streak": 5,
         "time_s": 41, "outcome": "win"},
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
    assert any("RECENT 980W / 740L" in label for label in labels), labels
