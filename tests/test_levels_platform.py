"""Level proofs: the arena has a low platform the jump can actually reach.

The baseline covers are all 1.2 m or taller; the jump apex is about 1.08 m,
so `E`/`up` was decorative. The new 0.7 m platform is low enough to land on
and high enough to be a real vantage point.
"""

import math

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.sim import Sim


def _covers() -> list[dict]:
    return list(Sim(seed=1).levels["arena"]["covers"])


def test_level_has_a_jumpable_platform():
    jumpable = [
        c for c in _covers()
        if float(c["h"]) <= 0.9 and float(c["w"]) >= 4.0 and float(c["d"]) >= 4.0
    ]
    assert jumpable, [(c["w"], c["h"], c["d"]) for c in _covers()]


def test_player_can_jump_onto_the_low_platform():
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.player_pos = Vec3(-16.0, 0.9002, 9.5)
    s.body = s.body.__class__(
        position=Vec3(-16.0, 0.9002, 9.5), half_extents=s.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    s.yaw = math.pi  # face +Z, toward the rear-left platform
    landed = False
    for index in range(120):
        action = (
            ActionState(forward=1.0, up=1.0)
            if index < 45
            else ActionState(forward=1.0)
        )
        s.step(1.0 / 60.0, action)
        if s.player_pos.y > 1.3 and s.body.on_ground:
            landed = True
            break
    assert landed, (s.player_pos.x, s.player_pos.y, s.player_pos.z)
    assert 12.0 < s.player_pos.z < 18.0, s.player_pos
    assert abs(s.player_pos.x + 16.0) < 0.3, s.player_pos
    assert abs(s.player_pos.y - 1.6001) < 0.01, s.player_pos
