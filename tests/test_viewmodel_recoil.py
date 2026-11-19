"""Combat-feel proof: the viewmodel punches with the existing fire kick.

Firing already tilts the camera through `sim.kick`, but the gun was rigidly
camera-parented: it never moved relative to the view, so recoil read as the
world tilting rather than the weapon kicking. The fix offsets the two
existing gun nodes along the view basis, driven by DATA.
"""

from __future__ import annotations

from keystone.input import ActionState

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    g.update(1.0 / 60.0, ActionState())
    return g


def _forward_projection(g: ShooterGame, point) -> float:
    # Camera space looks down -Z, so forward distance is simply -local z.
    return -point.z


def test_firing_pulls_the_viewmodel_toward_the_player():
    g = _game()
    g.sim.weapon = "scatter"
    g.sim.ammo["scatter"] = 6
    before = _forward_projection(g, g._view_barrel.transform.position)
    g.update(1.0 / 60.0, ActionState(pressed=frozenset({"fire"})))
    assert g.sim.kick > 0.0
    after = _forward_projection(g, g._view_barrel.transform.position)
    assert after < before - 0.02, (before, after)


def test_recoil_returns_to_rest_with_the_kick():
    g = _game()
    g.sim.weapon = "scatter"
    g.sim.ammo["scatter"] = 6
    before = _forward_projection(g, g._view_barrel.transform.position)
    g.update(1.0 / 60.0, ActionState(pressed=frozenset({"fire"})))
    assert g.sim.kick > 0.0
    for _ in range(120):
        g.update(1.0 / 60.0, ActionState())
    assert g.sim.kick == 0.0
    after = _forward_projection(g, g._view_barrel.transform.position)
    assert abs(after - before) < 0.001, (before, after)


def test_recoil_amount_is_data_driven():
    g = ShooterGame()
    g.build_scene()
    cfg = g.sim.juice["viewmodel"]
    assert float(cfg.get("recoil_back", 0.0)) > 0.0
    assert float(cfg.get("recoil_up", 0.0)) > 0.0
