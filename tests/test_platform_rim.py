"""Levels proof: the jumpable platform has a readable lit rim.

Cycle 12 added the 0.7 m platform, but cycle 05 skipped its lit cap because
the top is walkable. Cycle 40 marked only the two long edges even though its
proof names four strips. One shared frame mesh now draws all four edges and
replaces two separate rim nodes, so the landing perimeter reads from every
approach without adding shadow calls.
"""

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_platform_rim_is_one_four_strip_frame():
    g = _game()
    nodes = list(g._platform_rim)
    assert len(nodes) == 1, len(nodes)
    trim = g.assets.require("material.trim").payload
    assert nodes[0].visible
    assert nodes[0].material is trim
    assert len(nodes[0].mesh.positions) == 192  # eight cubes of 24 vertices
    assert len(nodes[0].mesh.indices) == 288


def test_platform_rim_frame_reaches_all_four_edges():
    g = _game()
    platform = next(
        c for c in g.sim.levels["arena"]["covers"] if float(c["h"]) < 1.0
    )
    px, pz = float(platform["x"]), float(platform["z"])
    half_w = float(platform["w"]) / 2.0
    half_d = float(platform["d"]) / 2.0
    node = g._platform_rim[0]
    assert abs(node.transform.position.x - px) < 1e-6
    assert abs(node.transform.position.z - pz) < 1e-6
    assert node.transform.position.y > float(platform["h"])
    xs = [p[0] for p in node.mesh.positions]
    zs = [p[2] for p in node.mesh.positions]
    assert abs(max(xs) - half_w) <= 0.11 and abs(min(xs) + half_w) <= 0.11
    assert abs(max(zs) - half_d) <= 0.11 and abs(min(zs) + half_d) <= 0.11
