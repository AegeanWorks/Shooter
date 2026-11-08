"""UI proof: the streak line shows the score bonus, not just the count.

Streak scoring is a stake (10% per kill, capped at 50%, broken on hurt).
The HUD showed `STREAK xN`; the bonus hidden behind it is now exposed.
"""

from shooter.sim import Sim
from shooter.ui import draw_shooter


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


def test_streak_bonus_scales_and_caps():
    s = Sim(seed=1)
    s.streak = 0
    assert s.streak_bonus() == 0.0
    s.streak = 3
    assert abs(s.streak_bonus() - 0.3) < 1e-6
    s.streak = 10
    assert abs(s.streak_bonus() - 0.5) < 1e-6


def test_streak_line_shows_the_bonus():
    s = Sim(seed=1)
    s.streak = 7
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    labels = [str(t[2]) for t in canvas.texts]
    assert any("STREAK x7" in label and "+50%" in label for label in labels), labels
