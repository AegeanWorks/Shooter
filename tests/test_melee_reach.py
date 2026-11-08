"""Enemy proofs: short melee enemies cannot bite through a raised platform.

The mite is 1.0 m tall and the jumpable platform top is 0.7 m, so a player
standing on it (feet at 1.6 m) is above the mite's reach. The baseline sim
checked horizontal distance only and dealt 8 damage anyway. Brutes (1.4 m)
and the 2.2 m warden still reach the platform edge; ground-level bites and
the existing LOS rules are unchanged.
"""

import math

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.sim import Sim, _Enemy


def _sim(player_y: float, player_z: float, etype: str, enemy_z: float,
         enemy_y: float, hp: int) -> Sim:
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.player_pos = Vec3(-16.0, player_y, player_z)
    s.body = s.body.__class__(
        position=Vec3(-16.0, player_y, player_z), half_extents=s.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    s.yaw = math.pi
    s.enemies = [_Enemy(etype=etype, pos=Vec3(-16.0, enemy_y, enemy_z),
                        hp=hp, max_hp=hp)]
    return s


def test_mite_cannot_bite_a_player_on_the_platform():
    s = _sim(1.6001, 17.5, "mite", 18.6, 0.5, 30)
    events = s.step(1.0 / 60.0, ActionState())
    assert int(s.hp) == 100, (s.hp, events)
    assert "hurt" not in events, events


def test_mite_still_bites_at_ground_level():
    # Open floor away from the platform: same 1.1 m gap as the high-ground case.
    s = _sim(0.9002, 10.0, "mite", 11.1, 0.5, 30)
    events = s.step(1.0 / 60.0, ActionState())
    assert int(s.hp) == 92, (s.hp, events)
    assert "hurt" in events, events


def test_brute_still_reaches_the_platform_edge():
    s = _sim(1.6001, 17.5, "brute", 18.8, 0.7, 120)
    events = s.step(1.0 / 60.0, ActionState())
    assert int(s.hp) == 80, (s.hp, events)
    assert "hurt" in events, events


def test_melee_vertical_reach_is_data_owned():
    s = Sim(seed=1)
    for etype in ("mite", "brute", "warden"):
        assert "reach_up" in s.enemy_defs[etype], etype
    assert float(s.enemy_defs["mite"]["reach_up"]) < float(
        s.enemy_defs["brute"]["reach_up"]
    )
    # the gate is presentation of DATA, not a hidden height rule
    assert float(s.enemy_defs["mite"]["reach_up"]) >= 0.0
