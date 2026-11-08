"""Enemy proof: warden escorts keep clear of the boss and each other.

Cycle 60 rejected cover-blocked ring positions, but the candidate could
still land inside the warden cube (ring radius starts at 1.2 m while the
warden radius is 1.0 m and the mite radius 0.4 m) or overlap a previously
placed escort.
"""

import math

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.sim import Sim, _Enemy


def _summon(seed: int) -> Sim:
    s = Sim(seed=seed)
    s.wave = 3
    s.spawn_queue = []
    s.spawn_t = 999.0
    s.enemies = [
        _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 0.0), hp=600,
               max_hp=600, summon_cd=0.0)
    ]
    events = s.step(1.0 / 60.0, ActionState())
    assert "boss_summon" in events, (seed, events)
    return s


def test_summons_keep_clear_of_boss_and_each_other():
    for seed in range(1, 41):
        s = _summon(seed)
        boss = next(e for e in s.enemies if e.etype == "warden")
        r_boss = float(s.enemy_defs["warden"]["radius"])
        r_mite = float(s.enemy_defs["mite"]["radius"])
        positions = list(s.summon_positions)
        assert len(positions) == 2, (seed, len(positions))
        for p in positions:
            gap = math.hypot(p.x - boss.pos.x, p.z - boss.pos.z)
            assert gap >= r_boss + r_mite + 0.04, (seed, gap, p)
        for i, p in enumerate(positions):
            for q in positions[i + 1:]:
                gap = math.hypot(p.x - q.x, p.z - q.z)
                assert gap >= 2.0 * r_mite + 0.04, (seed, gap, p, q)
