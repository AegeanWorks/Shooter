"""Graphics proof: dropped ammo caches are visible in the arena.

The sim drops a cache on 3% of kills for eight seconds, but no scene node
represented it. A pool of shared glowing cubes now marks each active drop;
cache lifetime, pickup and reward RNG are untouched.
"""

from keystone.math3d import Vec3

from shooter.game import ShooterGame

MAX_CACHES = 4


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    return g


def test_cache_pool_renders_the_active_drop():
    g = _game()
    g.sim.caches = [{"x": 0.0, "y": 0.5, "z": -3.0, "ttl": 8.0}]
    g._sync_scene()
    nodes = list(g._cache_nodes)
    assert len(nodes) == MAX_CACHES, len(nodes)
    active = [node for node in nodes if node.visible]
    assert len(active) == 1, [node.visible for node in nodes]
    assert abs(active[0].transform.position.x) < 1e-6
    assert abs(active[0].transform.position.z + 3.0) < 1e-6
    assert active[0].mesh is g.assets.require("mesh.pickup").payload


def test_cache_nodes_share_the_glowing_material():
    g = _game()
    material = g.assets.require("material.cache").payload
    mesh = g.assets.require("mesh.pickup").payload
    assert all(node.material is material for node in g._cache_nodes)
    assert all(node.mesh is mesh for node in g._cache_nodes)
    assert material.emissive.x > material.color.x * 0.5


def test_cache_pool_hides_after_collection():
    g = _game()
    g.sim.caches = [
        {"x": 1.0, "y": 0.5, "z": -2.0, "ttl": 8.0},
        {"x": -2.0, "y": 0.5, "z": -4.0, "ttl": 8.0},
    ]
    g._sync_scene()
    assert sum(node.visible for node in g._cache_nodes) == 2
    g.sim.caches = []
    g._sync_scene()
    assert not any(node.visible for node in g._cache_nodes)
