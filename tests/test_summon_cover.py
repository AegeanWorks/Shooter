"""Enemy proof: warden escorts never materialize inside arena covers.

`_summon_mites` picked a random ring around the boss and clamped only to
the arena bounds, so mites could spawn inside the low platform or a cover
box and stay stuck there. The baseline test catches blocked positions for
multiple seeds.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.sim import Sim, _Enemy


def _seed_with_summon(seed: int) -> Sim:
    s = Sim(seed=seed)
    s.wave = 3
    s.spawn_queue = []
    s.spawn_t = 999.0
    s.player_pos = Vec3(-16.0, 0.9002, 18.0)
    s.enemies = [
        _Enemy(etype="warden", pos=Vec3(-16.0, 1.1, 11.0), hp=600,
               max_hp=600, summon_cd=0.0)
    ]
    events = s.step(1.0 / 60.0, ActionState())
    assert "boss_summon" in events, (seed, events)
    return s


def test_summons_never_land_inside_cover():
    for seed in range(1, 21):
        s = _seed_with_summon(seed)
        assert s.summon_positions, seed
        radius = float(s.enemy_defs["mite"]["radius"])
        blocked = [
            (round(p.x, 2), round(p.z, 2))
            for p in s.summon_positions
            if s._enemy_blocked_at(p.x, p.z, radius)
        ]
        assert not blocked, (seed, blocked)
