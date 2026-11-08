"""Level proof: the west side of the jump platform is a real path.

The platform sat 0.5 m from the west wall — narrower than the 0.7 m player
body — so the visible rear strip was an impassable dead end.
"""

import math

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.sim import Sim


def _platform() -> dict:
    return next(
        c for c in Sim(seed=1).levels["arena"]["covers"] if float(c["h"]) < 1.0
    )


def test_west_gap_is_player_width():
    p = _platform()
    gap = 19.5 - (abs(float(p["x"])) + float(p["w"]) / 2.0)
    assert gap >= 0.9, gap


def test_player_can_walk_behind_the_platform():
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.enemies = []
    s.player_pos = Vec3(-19.0, 0.9002, 9.0)
    s.body = s.body.__class__(
        position=Vec3(-19.0, 0.9002, 9.0), half_extents=s.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    s.hvel = Vec3()
    s.yaw = math.pi  # face +Z, behind the platform
    for _ in range(240):
        s.step(1.0 / 60.0, ActionState(forward=1.0))
    assert s.player_pos.z > 18.2, s.player_pos
