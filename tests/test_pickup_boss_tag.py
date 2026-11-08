"""UI proof: the pickup edge tag survives a boss fight.

The top label sits where the warden bar needs room, so it must stay
suppressed; the edge chip sits at the screen edge and can still point to
an active pickup during the boss fight.
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


def _sim(boss: bool = True, active: bool = True) -> Sim:
    s = Sim(seed=1)
    s.player_pos = Vec3(0.0, 0.9002, 8.0)
    s.yaw = math.pi
    s.pickup_active = active
    if boss:
        s.enemies = [
            _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 2.0), hp=600, max_hp=600)
        ]
    return s


def _labels(sim: Sim) -> list[str]:
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), sim)
    return [str(t[2]) for t in canvas.texts]


def test_boss_suppresses_top_label_but_keeps_edge_tag():
    labels = _labels(_sim())
    assert not any(label.startswith("SURGE PICKUP READY") for label in labels), labels
    assert any(label == "SURGE" for label in labels), labels


def test_no_boss_keeps_both_cues():
    labels = _labels(_sim(boss=False))
    assert any(label.startswith("SURGE PICKUP READY") for label in labels), labels
    assert any(label == "SURGE" for label in labels), labels


def test_inactive_pickup_has_no_tag():
    labels = _labels(_sim(active=False))
    assert not any(label == "SURGE" for label in labels), labels
