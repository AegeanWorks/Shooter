"""Enemies proof: the target-health bar yields to the death screen.

The crosshair bar was drawn even with `sim.alive=False`, so a brute
under the crosshair put `BRUTE 120/120` over `YOU DIED`. The bar is
presentation only; hiding it while dead changes no state.
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


def _sim(alive: bool) -> Sim:
    s = Sim(seed=1)
    s.alive = alive
    s.hp = 100 if alive else 0
    s.enemies = [
        _Enemy(etype="brute", pos=Vec3(0.0, 0.7, 2.0), hp=120, max_hp=120)
    ]
    return s


def _labels(sim: Sim) -> list[str]:
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), sim)
    return [str(t[2]) for t in canvas.texts]


def test_dead_player_has_no_target_health_bar():
    labels = _labels(_sim(False))
    assert not any(label.startswith("BRUTE 120/120") for label in labels), labels
    assert any(label == "YOU DIED" for label in labels), labels


def test_alive_player_still_sees_the_target_bar():
    labels = _labels(_sim(True))
    assert any(label.startswith("BRUTE 120/120") for label in labels), labels
