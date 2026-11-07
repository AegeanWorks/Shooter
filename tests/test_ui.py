"""UI readability proofs: single HP/ammo source and a readable crosshair.

Baseline: the engine status panel (top-left) and the game's bottom-left panel
both printed HP/ammo; the white crosshair vanished against the white muzzle
flash in the burst route. These tests pin the de-duplicated HUD and the dark
crosshair backing, without touching sim state.
"""

from keystone.math3d import Vec3

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


def test_hud_does_not_duplicate_hp_or_ammo():
    s = Sim(seed=1)
    s.hp = 77
    s.weapon = "pulse"
    s.ammo["pulse"] = 12
    s.reserve["pulse"] = 99
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    labels = [str(t[2]) for t in canvas.texts]
    assert not any(label.startswith("HP ") for label in labels), labels
    assert not any("PULSE" in label for label in labels), labels
    # the rest of the HUD still speaks: wave/score stays in the game layer
    assert any(label.startswith("WAVE ") for label in labels), labels


def test_crosshair_has_dark_backing_around_each_arm():
    s = Sim(seed=1)
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    cx, cy = _Hud.width // 2, _Hud.height // 2
    dark = [
        r for r in canvas.rects
        if r[4][0] <= 0.05 and r[4][1] <= 0.05 and r[4][2] <= 0.05
        and abs(r[0] + r[2] / 2 - cx) <= 30 and abs(r[1] + r[3] / 2 - cy) <= 30
    ]
    assert len(dark) >= 5, dark
    # each arm still has its bright core drawn after the backing
    bright = [
        r for r in canvas.rects
        if r[4][0] >= 0.9 and r[4][1] >= 0.9 and r[4][2] >= 0.9
        and abs(r[0] + r[2] / 2 - cx) <= 30 and abs(r[1] + r[3] / 2 - cy) <= 30
    ]
    assert len(bright) >= 5, bright


def test_low_hp_edge_warning_is_still_drawn():
    s = Sim(seed=1)
    s.hp = 10
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    red_edges = [
        r for r in canvas.rects
        if r[4][0] >= 0.9 and r[4][1] <= 0.3
        and (r[0] == 0 or r[1] == 0)
    ]
    assert red_edges, canvas.rects


def test_hud_reads_only_presentation_state():
    s = Sim(seed=1)
    s.hurt_t = 0.5
    s.hurt_from = Vec3(5.0, 0.5, 8.0)
    before = (int(s.hp), int(s.shots), tuple(s.ammo.values()))
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    after = (int(s.hp), int(s.shots), tuple(s.ammo.values()))
    assert before == after
