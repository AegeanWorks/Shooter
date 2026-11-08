"""Progression proof: the death debrief shows career runs and wins.

The profile tracks lifetime runs/wins, but the debrief only showed bests
and recent runs; the clear banner was the only wins display. A career row
makes the persisted totals visible on the run-over screen.
"""

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


def _game(tmp_path, runs: int, wins: int) -> ShooterGame:
    path = tmp_path / "profile.json"
    seeded = default_profile()
    seeded.update({"runs": runs, "wins": wins, "best_score": 1000})
    ProfileStore(path).save(seeded)
    g = ShooterGame(profile_path=path)
    g.build_scene()
    g.last_run = {"score": 1500, "kills": 9, "wave": 2, "best_streak": 4,
                  "time_s": 10, "outcome": "lose"}
    g.sim.alive = False
    return g


def test_debrief_shows_career_runs_and_wins(tmp_path):
    g = _game(tmp_path, 4, 2)
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    labels = [str(t[2]) for t in canvas.texts]
    assert any("RUNS 4" in label and "WINS 2" in label for label in labels), labels


def test_debrief_omits_career_row_without_runs(tmp_path):
    g = _game(tmp_path, 0, 0)
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    labels = [str(t[2]) for t in canvas.texts]
    assert not any(label.startswith("RUNS ") for label in labels), labels
