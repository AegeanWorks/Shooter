"""Level proofs: the spawn lane to the pickup is not blocked by the centre cover.

Baseline: the player spawns at (0, 0.9, 8) facing -Z; the centre cover sits
at (0, 0), 8 m ahead, directly on the spawn-to-pickup line. The first view is
a brown box and the surge pickup is hidden behind it.
"""

from keystone.math3d import Vec3
from keystone.physics import Ray, ray_aabb

from shooter.sim import Sim


def test_spawn_forward_lane_is_clear():
    s = Sim(seed=1)
    origin = s.eye()
    forward = s.forward()
    for box in s.cover_boxes:
        distance = ray_aabb(Ray(origin, forward, t_max=15.0), box)
        assert distance is None or distance > 12.0, distance


def test_spawn_to_pickup_lane_is_clear():
    s = Sim(seed=1)
    spot = s.levels["pickup"]
    origin = s.eye()
    target = Vec3(float(spot["x"]), float(spot["y"]), float(spot["z"]))
    vec = Vec3(target.x - origin.x, target.y - origin.y, target.z - origin.z)
    ray = Ray(origin, vec.normalized(), t_max=vec.length())
    for box in s.cover_boxes:
        distance = ray_aabb(ray, box)
        assert distance is None or distance > vec.length(), distance
