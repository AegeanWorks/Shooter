"""Enemies proof: the enemy under the crosshair shows its health.

Only the warden had a health bar. A read-only aim ray finds the nearest
live non-boss enemy and the HUD draws a compact TYPE hp/max bar above the
crosshair; the warden keeps its dedicated top bar.
"""

import math

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


def _sim(etype: str = "mite", hp: int = 18, yaw: float = 0.0) -> Sim:
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.yaw = yaw
    s.enemies = [_Enemy(etype=etype, pos=Vec3(0.0, 0.5, 2.0), hp=hp,
                        max_hp=30 if etype == "mite" else 600)]
    return s


def test_aim_target_is_the_enemy_under_the_crosshair():
    s = _sim()
    assert s.aim_target() is s.enemies[0]


def test_target_bar_shows_type_and_hp():
    s = _sim()
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    labels = [str(t[2]) for t in canvas.texts]
    assert any("MITE 18/30" in label for label in labels), labels


def test_no_target_bar_when_facing_away():
    s = _sim(yaw=math.pi)
    assert s.aim_target() is None
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    labels = [str(t[2]) for t in canvas.texts]
    assert not any("MITE 18/30" in label for label in labels), labels


def test_warden_keeps_its_own_bar():
    s = _sim(etype="warden", hp=600)
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    labels = [str(t[2]) for t in canvas.texts]
    assert not any("WARDEN 600/600" in label for label in labels), labels
