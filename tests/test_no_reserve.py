"""UI proof: the low-ammo panel names an empty reserve.

The cycle-55 panel shows `LOW AMMO <mag>`, but with zero reserve rounds the
player cannot reload. The near-crosshair warning should say so instead of
looking like an ordinary low-magazine warning; the full counts stay in the
engine status panel.
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


def _draw(mag: int, reserve: int) -> tuple[list[str], _Canvas]:
    s = Sim(seed=1)
    s.weapon = "pulse"
    s.ammo["pulse"] = mag
    s.reserve["pulse"] = reserve
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    return [str(t[2]) for t in canvas.texts], canvas


def test_empty_reserve_is_named_at_the_crosshair():
    labels, canvas = _draw(3, 0)
    assert "LOW AMMO 3" in labels, labels
    assert "NO RESERVE" in labels, labels
    assert any(r[2] == 150 and r[3] == 40 for r in canvas.rects), canvas.rects


def test_reserve_rounds_keep_the_short_warning():
    labels, canvas = _draw(3, 12)
    assert "LOW AMMO 3" in labels, labels
    assert "NO RESERVE" not in labels, labels
    assert any(r[2] == 150 and r[3] == 22 for r in canvas.rects), canvas.rects
