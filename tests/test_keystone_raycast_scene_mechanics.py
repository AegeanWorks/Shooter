"""Keystone mechanics testbed: rays, sphere collision and scene serialization.

Covers Ray/ray_aabb/ray_sphere distances, filtered raycasts, sphere pushout
and AABB overlap, plus a SceneLibrary save/load round trip built from the
shooter's registered mesh/material assets.
"""

import tempfile

from keystone.math3d import Vec3
from keystone.physics import (
    AABB,
    Ray,
    Sphere,
    aabb_overlap,
    ray_aabb,
    ray_sphere,
    raycast,
    resolve_sphere_aabb,
    sphere_aabb_overlap,
)
from keystone.scene import Node, Scene, Transform
from keystone.scene_library import SceneLibrary

from shooter.game import ShooterGame
from shooter.sim import Sim


def _cover_box() -> AABB:
    cover = next(
        c for c in Sim(seed=1).levels["arena"]["covers"] if float(c["h"]) >= 1.0
    )
    return AABB(
        Vec3(float(cover["x"]), float(cover["h"]) / 2.0, float(cover["z"])),
        Vec3(float(cover["w"]) / 2.0, float(cover["h"]) / 2.0, float(cover["d"]) / 2.0),
    )


def test_ray_aabb_distances_misses_and_t_max():
    ray = Ray(Vec3(0, 0, 0), Vec3(0, 0, 1))
    near = AABB(Vec3(0, 0, 5), Vec3(1, 1, 1))
    assert ray_aabb(ray, near) == 4.0
    assert ray_aabb(Ray(Vec3(0, 0, 0), Vec3(0, 1, 0)), near) is None
    assert ray_aabb(Ray(Vec3(0, 0, 0), Vec3(0, 0, 1), t_max=3.0), near) is None
    assert ray_aabb(Ray(Vec3(0, 0, 5), Vec3(0, 0, 1)), near) == 0.0
    assert ray_sphere(ray, Sphere(Vec3(0, 0, 5), 1.0)) == 4.0
    assert ray_sphere(ray, Sphere(Vec3(0, 0, 5), 1.0)) < float("inf")
    assert ray_sphere(Ray(Vec3(0, 0, 0), Vec3(0, 1, 0)), Sphere(Vec3(0, 0, 5), 1.0)) is None
    assert ray_sphere(Ray(Vec3(0, 0, 0), Vec3(0, 0, 1)), Sphere(Vec3(0, 0, 0), 1.0)) == 0.0


def test_filtered_raycast_nearest_and_skip():
    ray = Ray(Vec3(0, 0, 0), Vec3(0, 0, 1))
    near = AABB(Vec3(0, 0, 2), Vec3(0.5, 0.5, 0.5))
    far = AABB(Vec3(0, 0, 5), Vec3(1, 1, 1))
    hit = raycast(ray, [("far", far), ("near", near)])
    assert hit is not None and hit.key == "near" and hit.distance == 1.5
    filtered = raycast(
        ray, [("near", near), ("far", far)], predicate=lambda key, _box: key == "far"
    )
    assert filtered is not None and filtered.key == "far"
    assert raycast(
        ray, [("near", near), ("far", far)], predicate=lambda _key, _box: False
    ) is None


def test_sphere_pushout_and_aabb_overlap_pairs():
    cover = _cover_box()
    assert aabb_overlap(cover, cover) is True
    far = AABB(Vec3(15.0, 15.0, 15.0), Vec3(0.5, 0.5, 0.5))
    assert aabb_overlap(cover, far) is False

    center = Vec3(cover.high().x + 0.2, cover.center.y, cover.center.z)
    sphere = Sphere(center, 0.5)
    assert sphere_aabb_overlap(sphere, cover) is True
    pushed = resolve_sphere_aabb(sphere, cover)
    assert pushed == Vec3(cover.high().x + 0.5, cover.center.y, cover.center.z)
    assert sphere_aabb_overlap(Sphere(pushed, 0.5), cover) is False
    outside = Sphere(Vec3(15.0, 15.0, 15.0), 0.5)
    assert resolve_sphere_aabb(outside, cover) == outside.center


def test_scene_library_round_trip_with_shooter_assets():
    g = ShooterGame()
    g.build_scene()
    pickup_mesh = g.assets.require("mesh.pickup").payload
    wall_mesh = g.assets.require("mesh.wall").payload
    cache_mat = g.assets.require("material.cache").payload

    scene = Scene()
    cache = Node(
        "cache", id="cache", mesh=pickup_mesh, material=cache_mat,
        tags={"loot"}, layer="props",
        transform=Transform(position=Vec3(1.0, 2.0, 3.0)),
    )
    scene.add(cache)
    halo = Node(
        "halo", id="halo", mesh=wall_mesh, material=cache_mat,
        transform=Transform(position=Vec3(0.0, 0.5, 0.0), scale=Vec3(0.2, 0.2, 0.2)),
    )
    cache.add_child(halo)

    with tempfile.TemporaryDirectory() as directory:
        library = SceneLibrary(directory, registry=g.assets)
        entry = library.save("cache_level", scene)
        assert entry.name == "cache_level"
        assert entry.node_count == 2
        assert entry.error is None
        loaded = library.load("cache_level")
        described = library.entries()
        assert [item.name for item in described] == ["cache_level"]
        document = library.document("cache_level")
        assert document["name"] == "cache_level"

    node = loaded.find_by_id("cache")
    assert node is not None
    assert node.mesh is pickup_mesh
    assert node.material is cache_mat
    assert node.tags == {"loot"}
    assert node.layer == "props"
    assert node.transform.position == Vec3(1.0, 2.0, 3.0)
    child = loaded.find_by_id("halo")
    assert child is not None and child.parent is node
    assert child.mesh is wall_mesh
    assert child.transform.scale == Vec3(0.2, 0.2, 0.2)
