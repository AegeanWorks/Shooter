"""Progression proof: the debrief shows all five stored runs.

The profile keeps a five-run history, but the debrief rendered only the
first three. The remaining two are shown on a second HISTORY line; the
dynamic panel contains both.
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


def test_debrief_shows_all_five_history_entries(tmp_path):
    path = tmp_path / "profile.json"
    seeded = default_profile()
    seeded["history"] = [
        {"score": 1500 - index * 100, "kills": 9 - index, "wave": 3,
         "best_streak": 5, "time_s": 40, "outcome": "lose"}
        for index in range(5)
    ]
    ProfileStore(path).save(seeded)
    g = ShooterGame(profile_path=path)
    g.build_scene()
    g.last_run = {"score": 2000, "kills": 10, "wave": 3, "best_streak": 6,
                  "time_s": 50, "outcome": "lose"}
    g.sim.alive = False
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    labels = [str(t[2]) for t in canvas.texts]
    joined = " ".join(labels)
    for score in (1500, 1400, 1300, 1200, 1100):
        assert str(score) in joined, labels
    assert any(label.startswith("HISTORY ") for label in labels), labels
