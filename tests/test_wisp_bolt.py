"""Combat-feel proof: a wisp attack draws a bolt from the wisp to the player.

The wisp's ranged hit was invisible until the damage cue. The bolt is a
presentation tracer (not in the snapshot); damage and LOS are unchanged.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import Sim, _Enemy


def _sim() -> Sim:
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.player_pos = Vec3(0.0, 0.9002, 8.0)
    s.body = s.body.__class__(
        position=Vec3(0.0, 0.9002, 8.0), half_extents=s.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    s.enemies = [
        _Enemy(etype="wisp", pos=Vec3(5.0, 0.4, 4.0), hp=20, max_hp=20,
               attack_cd=0.0)
    ]
    return s


def test_wisp_attack_traces_a_bolt_to_the_player():
    s = _sim()
    events = s.step(1.0 / 60.0, ActionState())
    assert int(s.hp) == 94, (s.hp, events)
    bolts = [t for t in s.tracers if t.get("weapon") == "wisp"]
    assert len(bolts) == 1, s.tracers
    bolt = bolts[0]
    assert abs(bolt["x0"] - s.enemies[0].pos.x) < 1e-6
    assert abs(bolt["z0"] - s.enemies[0].pos.z) < 1e-6
    assert abs(bolt["x1"] - s.player_pos.x) < 1e-6
    assert abs(bolt["z1"] - s.player_pos.z) < 1e-6
    assert bolt["life"] > 0.0


def test_wisp_bolt_uses_its_material():
    g = ShooterGame()
    g.build_scene()
    g.sim.tracers = [{
        "x0": 5.0, "y0": 1.0, "z0": 4.0,
        "x1": 0.0, "y1": 1.0, "z1": 8.0,
        "life": 0.1, "weapon": "wisp",
    }]
    g._sync_scene()
    assert g._tracer_nodes[0].material is g.assets.require(
        "material.tracer_wisp"
    ).payload
