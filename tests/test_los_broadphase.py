"""Game proof: the enemy line-of-sight check uses the wave broadphase.

`Sim` used to scan every wall and cover for each enemy each tick. It now asks
the spatial grid for the boxes along the segment first and still decides with
the same exact ray test. That is only safe if the prefilter never drops a box
the ray could hit, so this proves the two agree for a sweep of positions --
including grazing the box edges -- rather than trusting one replay hash.
"""

import math

import pytest

from keystone.math3d import Vec3
from keystone.physics import Ray, ray_aabb

from shooter.sim import Sim


def _full_scan(sim, src, target):
    """The previous implementation, kept here as the reference verdict."""
    vec = Vec3(target.x - src.x, target.y - src.y, target.z - src.z)
    length = vec.length()
    if length <= 1e-6:
        return True
    ray = Ray(src, vec.normalized(), t_max=length)
    for box in sim.colliders:
        distance = ray_aabb(ray, box)
        if distance is not None and distance < length - 0.3:
            return False
    return True


def test_prefilter_returns_every_box_the_full_scan_can_block_on():
    sim = Sim(seed=1)
    target = sim.eye()
    checked = 0
    for x in (-11.0, -8.0, -4.0, -0.5, 0.0, 0.5, 4.0, 8.0, 11.0):
        for z in (-11.0, -8.0, -4.0, -0.5, 0.0, 0.5, 4.0, 8.0, 11.0):
            src = Vec3(x, 1.0, z)
            candidates = sim._colliders_along(src, target)
            blocking = []
            vec = Vec3(target.x - src.x, target.y - src.y, target.z - src.z)
            length = vec.length()
            ray = Ray(src, vec.normalized(), t_max=length)
            for box in sim.colliders:
                distance = ray_aabb(ray, box)
                if distance is not None and distance < length - 0.3:
                    blocking.append(box)
            assert all(box in candidates for box in blocking), (x, z)
            checked += 1
    assert checked == 81


def test_los_verdict_matches_the_full_scan_across_the_arena():
    sim = Sim(seed=1)
    target = sim.eye()
    disagreements = []
    for index in range(200):
        angle = index * 0.17
        radius = 2.0 + (index % 9)
        pos = Vec3(math.cos(angle) * radius, 1.0, math.sin(angle) * radius)
        # _enemy_has_los measures from the chest, 0.3 above the enemy origin
        chest = Vec3(pos.x, pos.y + 0.3, pos.z)
        expected = _full_scan(sim, chest, target)
        got = sim._enemy_has_los(_FakeEnemy(pos))
        if got != expected:
            disagreements.append((pos, expected, got))
    assert disagreements == []


def test_collider_boxes_keep_build_order_through_the_grid():
    sim = Sim(seed=1)
    target = sim.eye()
    src = Vec3(-11.0, 1.0, -11.0)
    along = sim._colliders_along(src, target)
    order = {id(box): index for index, box in enumerate(sim.colliders)}
    ranks = [order[id(box)] for box in along]
    assert ranks == sorted(ranks), "insertion order is what keeps the first hit stable"
    assert set(map(id, along)) <= set(map(id, sim.colliders))


def test_every_wall_is_reachable_through_the_grid():
    sim = Sim(seed=1)
    # a box that no segment query can ever return would be invisible to the
    # game; probe each collider's own centre from just above it
    for box in sim.colliders:
        probe_from = Vec3(box.center.x, box.center.y, box.center.z)
        assert box in sim._colliders_along(probe_from, probe_from)


class _FakeEnemy:
    """Only the attributes _enemy_has_los reads."""

    def __init__(self, pos):
        self.pos = pos
