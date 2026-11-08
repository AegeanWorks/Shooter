"""Combat-feel proof: the low-health edge warning pulses.

The <=30 HP warning was a static translucent red edge, so critical health
looked identical at every moment. A deterministic sine alpha now pulses it.
"""

import math

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


def _edge_alphas(hp: int, t: float) -> list[float]:
    s = Sim(seed=1)
    s.hp = hp
    s.time = t
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    return [
        float(rect[4][3])
        for rect in canvas.rects
        if (rect[2] == 960 and rect[3] == 6) or (rect[2] == 6 and rect[3] == 540)
    ]


def test_low_health_edges_pulse_with_time():
    dim = _edge_alphas(30, 0.0)
    bright = _edge_alphas(30, math.pi / 12.0)  # sin(6t) = 1
    assert dim and bright
    assert max(bright) > max(dim) + 0.05, (dim, bright)


def test_healthy_player_has_no_edge_warning():
    assert _edge_alphas(31, 0.0) == []
