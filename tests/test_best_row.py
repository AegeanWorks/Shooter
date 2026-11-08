"""Progression proof: the debrief shows career bests, not only the run.

The profile tracks best_score/best_kills/best_wave/best_streak. The top
BEST line exposed the score; the debrief showed the current run's streak
and time. A career-bests row makes the persisted records visible.
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


def _game(tmp_path, kills: int, wave: int, streak: int) -> ShooterGame:
    path = tmp_path / "profile.json"
    seeded = default_profile()
    seeded.update({
        "runs": 4, "wins": 1, "best_score": 1000,
        "best_kills": kills, "best_wave": wave, "best_streak": streak,
    })
    ProfileStore(path).save(seeded)
    g = ShooterGame(profile_path=path)
    g.build_scene()
    g.last_run = {"score": 1500, "kills": 9, "wave": 2, "best_streak": 4,
                  "time_s": 10, "outcome": "lose"}
    g.sim.alive = False
    return g


def test_debrief_shows_career_bests(tmp_path):
    g = _game(tmp_path, 12, 4, 6)
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    labels = [str(t[2]) for t in canvas.texts]
    assert any(
        "BEST KILLS 12" in label and "WAVE 4" in label and "STREAK 6" in label
        for label in labels
    ), labels


def test_debrief_omits_bests_at_zero(tmp_path):
    g = _game(tmp_path, 0, 0, 0)
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    labels = [str(t[2]) for t in canvas.texts]
    assert not any(label.startswith("BEST KILLS ") for label in labels), labels
