"""Levels proof: the jumpable platform has a readable lit rim.

Cycle 12 added the 0.7 m platform, but cycle 05 skipped its lit cap because
the top is walkable. Four shared trim strips mark the edge without adding
colliders; the jump/landing behavior is unchanged.
"""

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_platform_rim_has_two_shared_trim_nodes():
    g = _game()
    nodes = list(g._platform_rim)
    assert len(nodes) == 2, len(nodes)
    trim = g.assets.require("material.trim").payload
    assert all(node.visible for node in nodes)
    assert all(node.material is trim for node in nodes)


def test_platform_rim_sits_on_the_low_platform_edges():
    g = _game()
    platform = next(
        c for c in g.sim.levels["arena"]["covers"] if float(c["h"]) < 1.0
    )
    px, pz = float(platform["x"]), float(platform["z"])
    half_w = float(platform["w"]) / 2.0
    half_d = float(platform["d"]) / 2.0
    for node in g._platform_rim:
        assert abs(node.transform.position.x - px) <= half_w + 0.1
        assert abs(node.transform.position.z - pz) <= half_d + 0.1
        assert node.transform.scale.y <= 0.12
