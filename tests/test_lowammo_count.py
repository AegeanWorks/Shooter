"""UI proof: the low-ammo panel shows the exact magazine count.

The warning was binary `LOW AMMO`; the exact count lived only in the
top-left engine status, far from the aim point. The count in the panel
makes the reload decision readable at a glance.
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


def _draw(mag: int) -> tuple[list[str], _Canvas]:
    s = Sim(seed=1)
    s.weapon = "pulse"
    s.ammo["pulse"] = mag
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    return [str(t[2]) for t in canvas.texts], canvas


def test_low_ammo_panel_shows_mag_count():
    labels, canvas = _draw(3)
    assert "LOW AMMO 3" in labels, labels
    panels = [r for r in canvas.rects if r[2] == 150 and r[3] == 22]
    assert panels, canvas.rects


def test_low_ammo_count_tracks_the_magazine():
    labels, _canvas = _draw(1)
    assert "LOW AMMO 1" in labels, labels


def test_no_low_panel_above_threshold():
    labels, _canvas = _draw(8)
    assert not any("LOW AMMO" in label for label in labels), labels
