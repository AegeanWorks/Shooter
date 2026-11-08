"""Levels proof: an off-screen surge pickup gets a directional edge tag.

The pickup beacon and the SURGE PICKUP READY label name the reward, but
when the player faces away there is no direction. The tag is presentation
only; the pickup trigger and sim state are untouched.
"""

import math

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


def _sim(yaw: float, active: bool = True) -> Sim:
    s = Sim(seed=1)
    s.player_pos = Vec3(0.0, 0.9002, 8.0)
    s.yaw = yaw
    s.pickup_active = active
    return s


def _tags(canvas: _Canvas) -> list[tuple]:
    return [t for t in canvas.texts if str(t[2]) == "SURGE"]


def test_offscreen_pickup_gets_an_edge_tag():
    s = _sim(math.pi)
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    tags = _tags(canvas)
    assert len(tags) == 1, tags
    x, y = int(tags[0][0]), int(tags[0][1])
    assert 400 <= x <= 560 and y >= 300, (x, y)
    assert any(str(t[2]) == "SURGE PICKUP READY" for t in canvas.texts)


def test_pickup_ahead_has_no_edge_tag():
    s = _sim(0.0)
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    assert not _tags(canvas), _tags(canvas)


def test_inactive_pickup_has_no_edge_tag():
    s = _sim(math.pi, active=False)
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    assert not _tags(canvas), _tags(canvas)
