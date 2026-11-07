"""Graphics proofs: the muzzle flash is small and off the aim line.

The baseline flash was a 0.10 cube centred 0.70 m ahead at eye level; at
960x540 it covered the crosshair and the target. The fix offsets it down and
right and uses the DATA scale.
"""

import math

from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import Sim


def _flash_state() -> tuple[Sim, Vec3, Vec3]:
    s = Sim(seed=1)
    s._fire(s.weapons["pulse"], [])
    right = Vec3(math.cos(s.yaw), 0.0, math.sin(s.yaw))
    return s, s.eye(), right


def test_muzzle_flash_is_small_and_off_the_aim_line():
    s, eye, right = _flash_state()
    offset = Vec3(
        s.flash_pos.x - eye.x,
        s.flash_pos.y - eye.y,
        s.flash_pos.z - eye.z,
    )
    lateral = offset.x * right.x + offset.z * right.z
    assert lateral >= 0.10, (lateral, s.flash_pos)
    assert offset.y <= -0.05, offset
    assert 0.8 <= math.hypot(offset.x, offset.z) <= 1.1, offset


def test_muzzle_flash_node_uses_small_scale():
    g = ShooterGame()
    g.build_scene()
    g.sim.flash_t = 0.1
    g.sim.flash_pos = Vec3(0.0, 1.5, 7.0)
    g._sync_scene()
    assert g._flash is not None and g._flash.visible is True
    assert g._flash.transform.scale.x <= 0.07, g._flash.transform.scale
    assert g._flash.transform.scale.x == g._flash.transform.scale.y
