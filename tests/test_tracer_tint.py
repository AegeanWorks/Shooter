"""Graphics proofs: each weapon's tracer and muzzle flash carry its tint.

The tracer pool and flash node used one yellow/white material, so pulse,
scatter, lance and surge fire looked identical. The tints are presentation
only; the sim records the firing weapon on the (non-snapshot) tracer dict.
"""

from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import Sim, _Enemy

WEAPONS = ("pulse", "scatter", "lance", "surge")


def _fire_sim(wid: str) -> Sim:
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.weapon = wid
    s.enemies = [
        _Enemy(etype="brute", pos=Vec3(0.0, 0.7, 2.0), hp=600, max_hp=600,
               attack_cd=10.0)
    ]
    s._fire(s.weapons[wid], [])
    return s


def test_each_tracer_records_the_firing_weapon():
    for wid in WEAPONS:
        s = _fire_sim(wid)
        assert s.tracers[-1]["weapon"] == wid, (wid, s.tracers[-1])


def test_tracer_node_uses_the_weapon_material():
    g = ShooterGame()
    g.build_scene()
    for wid in WEAPONS:
        g.sim.tracers = [{
            "x0": 0.0, "y0": 1.0, "z0": 8.0,
            "x1": 0.0, "y1": 1.0, "z1": 2.0,
            "life": 0.1, "weapon": wid,
        }]
        g._sync_scene()
        expected = g.assets.require(f"material.tracer_{wid}").payload
        assert g._tracer_nodes[0].material is expected, wid


def test_flash_node_uses_the_weapon_material():
    g = ShooterGame()
    g.build_scene()
    for wid in WEAPONS:
        g.sim.weapon = wid
        g.sim.flash_t = 0.05
        g._sync_scene()
        expected = g.assets.require(f"material.flash_{wid}").payload
        assert g._flash.material is expected, wid


def test_weapon_tints_are_distinct():
    g = ShooterGame()
    g.build_scene()
    colors = []
    for wid in WEAPONS:
        mat = g.assets.require(f"material.tracer_{wid}").payload
        colors.append((round(mat.color.x, 3), round(mat.color.y, 3), round(mat.color.z, 3)))
    assert len(set(colors)) == 4, colors
