"""Enemy proof: melee crowds keep their footprint instead of stacking.

Movement is cover-aware but has no enemy-enemy term, so mites converge
from every heading onto the same ring point. Four mites end up at one
coordinate and read as a single blob. A deterministic soft-separation
pass now keeps alive enemies at least their DATA radii apart.
"""

import math

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.sim import Sim, _Enemy


def _sim(count: int = 4) -> Sim:
    s = Sim(seed=1)
    s.wave = 2
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.player_pos = Vec3(0.0, 0.9002, 8.0)
    s.body = s.body.__class__(
        position=Vec3(0.0, 0.9002, 8.0), half_extents=s.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    s.enemies = [
        _Enemy(etype="mite", pos=Vec3(0.0, 0.5, 6.2), hp=30, max_hp=30,
               attack_cd=999.0)
        for _ in range(count)
    ]
    return s


def test_melee_crowd_keeps_its_footprint():
    s = _sim()
    for _ in range(60):
        s.step(1.0 / 60.0, ActionState())
    radii = [float(s.enemy_defs[e.etype]["radius"]) for e in s.enemies]
    for i, a in enumerate(s.enemies):
        for j in range(i + 1, len(s.enemies)):
            b = s.enemies[j]
            gap = math.hypot(a.pos.x - b.pos.x, a.pos.z - b.pos.z)
            assert gap >= radii[i] + radii[j] - 0.05, (
                i, j, round(gap, 3),
                [(round(e.pos.x, 2), round(e.pos.z, 2)) for e in s.enemies],
            )


def test_separation_is_data_owned():
    s = Sim(seed=1)
    cfg = s.levels.get("enemy_separation", {})
    assert float(cfg.get("strength", 0.0)) > 0.0, cfg
    assert float(cfg.get("clearance", 0.0)) >= 0.0, cfg
    assert int(cfg.get("passes", 0)) >= 1, cfg
