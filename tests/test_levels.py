"""Level affordance proofs: the surge pickup beacon is visible over cover.

Baseline: at wave 2 the pickup sits at (0, -6) behind the 1.2 m centre cover;
from the spawn eye (0, 1.62, 8) the 0.6 m green cube is completely hidden.
The beacon is presentation-only; the pickup trigger and ammo economy do not
move.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
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


def test_pickup_beacon_hidden_at_wave_one_spawn():
    g = ShooterGame()
    g.build_scene()
    g._sync_scene()
    assert g._pickup_beam is not None and g._pickup_beam.visible is False
    assert g._pickup_orb is not None and g._pickup_orb.visible is False


def test_pickup_beacon_visible_only_while_active():
    g = ShooterGame()
    g.build_scene()
    spot = g.sim.levels["pickup"]
    g.sim.pickup_active = True
    g._sync_scene()
    assert g._pickup_beam.visible is True
    assert g._pickup_orb.visible is True
    beam = g._pickup_beam.transform
    orb = g._pickup_orb.transform
    assert abs(beam.position.x - float(spot["x"])) < 1e-6
    assert abs(beam.position.z - float(spot["z"])) < 1e-6
    assert beam.scale.y > beam.scale.x * 5.0
    assert orb.position.y > beam.position.y
    g.sim.pickup_active = False
    g.sim.pickup_taken = True
    g._sync_scene()
    assert g._pickup_beam.visible is False
    assert g._pickup_orb.visible is False


def test_hud_pickup_label_only_when_close_and_active():
    s = Sim(seed=1)
    s.pickup_active = True
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)  # spawn is 14 m from the spot
    assert any("SURGE PICKUP READY" in str(t[2]) for t in canvas.texts), canvas.texts
    s.player_pos = Vec3(19.0, 0.9, 19.0)  # far corner: beyond the 18 m prompt
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    assert not any("SURGE PICKUP READY" in str(t[2]) for t in canvas.texts), canvas.texts
    s.pickup_active = False
    s.player_pos = Vec3(0.0, 0.9, 8.0)
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    assert not any("SURGE PICKUP READY" in str(t[2]) for t in canvas.texts), canvas.texts


def test_beacon_does_not_touch_the_pickup_trigger():
    s = Sim(seed=1)
    s.pickup_active = True
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.enemies = []
    before = (bool(s.pickup_active), int(s.weapon != "surge"))
    rest_y = float(s.player_pos.y)  # keeps the 0.0002 floor skin gap
    s.player_pos = Vec3(0.0, rest_y, -6.0)
    s.body = s.body.__class__(
        position=Vec3(0.0, rest_y, -6.0), half_extents=s.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    s.step(1.0 / 60.0, ActionState())
    assert before == (True, 1)
    assert s.weapon == "surge"
    assert s.pickup_active is False and s.pickup_taken is True
