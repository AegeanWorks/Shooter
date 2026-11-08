"""Combat-feel proofs: a kill gets its own crosshair marker.

A non-lethal hit expands the crosshair; a kill uses the same feedback plus
sound/feed/hitstop. The kill marker adds four red corner ticks so the final
hit is readable at the aim point. Presentation only, not in the snapshot.
"""

from keystone.input import ActionState
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


def _hit(hp: int) -> Sim:
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=hp, max_hp=30)]
    s._fire(s.weapons["pulse"], [])
    return s


def test_kill_sets_killmark_timer():
    s = _hit(12)
    assert s.killmark_t > 0.0, s.killmark_t
    assert "killmark_t" not in s.snapshot()


def test_nonlethal_hit_does_not_set_killmark():
    s = _hit(30)
    assert s.killmark_t == 0.0


def test_killmark_draws_red_corner_ticks():
    s = Sim(seed=1)
    s.killmark_t = 0.1
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    cx, cy = _Hud.width // 2, _Hud.height // 2
    red = [
        r for r in canvas.rects
        if r[4][0] >= 0.9 and r[4][1] <= 0.35
        and abs(r[0] + r[2] / 2 - cx) <= 40
        and abs(r[1] + r[3] / 2 - cy) <= 40
    ]
    assert len(red) >= 4, red


def test_killmark_expires():
    s = _hit(12)
    for _ in range(30):
        s.step(1.0 / 60.0, ActionState())
    assert s.killmark_t == 0.0
