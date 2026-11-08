"""Graphics proof: the surge pickup pops when it is collected.

The beacon orb and beam vanish the instant the trigger fires; the only
feedback is the SURGE ACQUIRED caption. The existing orb should burst
upward for a short, deterministic window so the pickup has a world-space
payoff without new nodes or draws.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame


def _collect() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    g.sim.wave = 2
    g.sim.pickup_active = True
    g.sim.pickup_taken = False
    rest_y = float(g.sim.player_pos.y)
    g.sim.player_pos = Vec3(0.0, rest_y, -6.0)
    g.sim.body = g.sim.body.__class__(
        position=Vec3(0.0, rest_y, -6.0),
        half_extents=g.sim.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    g.update(1.0 / 60.0, ActionState())
    return g


def test_pickup_collection_starts_an_orb_burst():
    g = _collect()
    assert g.sim.weapon == "surge"
    assert g.sim.pickup_active is False
    assert g._pickup_fx_t > 0.0
    assert g._pickup_orb is not None and g._pickup_orb.visible is True
    assert g._pickup_beam is not None and g._pickup_beam.visible is False


def test_orb_burst_expands_then_clears():
    g = _collect()
    first = g._pickup_orb.transform.scale.x
    for _ in range(6):
        g.update(1.0 / 60.0, ActionState())
    grown = g._pickup_orb.transform.scale.x
    assert grown > first > 1.0, (first, grown)
    for _ in range(40):
        g.update(1.0 / 60.0, ActionState())
    assert g._pickup_fx_t == 0.0
    assert g._pickup_orb.visible is False
