"""Enemy proofs: brute slams respect line of sight.

Melee attacks checked only distance; a brute parked on the far side of a
thin cover could damage the player through it. The open-field case must keep
working.
"""

import math

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.sim import Sim, _Enemy


def _sim(player_z: float, brute_z: float, x: float = -6.0) -> Sim:
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.player_pos = Vec3(x, 0.9002, player_z)
    s.body = s.body.__class__(
        position=Vec3(x, 0.9002, player_z), half_extents=s.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    s.yaw = math.pi
    s.enemies = [_Enemy(etype="brute", pos=Vec3(x, 0.7, brute_z), hp=120, max_hp=120)]
    return s


def test_brute_cannot_slam_through_cover():
    s = _sim(3.8, 6.2)
    events = s.step(1.0 / 60.0, ActionState())
    assert int(s.hp) == 100, (s.hp, events)
    assert "hurt" not in events


def test_brute_still_slams_in_the_open():
    s = _sim(0.0, 2.0, x=10.0)
    events = s.step(1.0 / 60.0, ActionState())
    assert int(s.hp) == 80, (s.hp, events)
    assert "hurt" in events
