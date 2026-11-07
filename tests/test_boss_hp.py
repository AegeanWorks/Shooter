"""UI readability proofs: the warden bar has a numeric HP readout.

The bar's red fill gives only a rough fraction; at 300/600 the player cannot
tell the exact remaining health. This pins the numbers beside the WARDEN
label.
"""

from keystone.math3d import Vec3

from shooter.sim import Sim, _Enemy
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


def test_warden_bar_shows_numeric_hp():
    s = Sim(seed=1)
    s.enemies = [_Enemy(etype="warden", pos=Vec3(0.0, 1.1, 3.5), hp=300, max_hp=600)]
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    labels = [str(t[2]) for t in canvas.texts]
    assert "300/600" in labels, labels


def test_warden_bar_numbers_update():
    s = Sim(seed=1)
    s.enemies = [_Enemy(etype="warden", pos=Vec3(0.0, 1.1, 3.5), hp=150, max_hp=600)]
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    labels = [str(t[2]) for t in canvas.texts]
    assert "150/600" in labels, labels
