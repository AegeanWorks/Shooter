"""Levels proof: the jump platform is framed at its base as well as its top.

The dark side face merged into the floor from the approach; the top rim
marked the landing edge but not the 0.7 m step. The existing frame mesh now
carries a matching base perimeter in the same node and draw.
"""

from shooter.game import ShooterGame


def _frame():
    g = ShooterGame()
    g.build_scene()
    platform = next(
        c for c in g.sim.levels["arena"]["covers"] if float(c["h"]) < 1.0
    )
    node = g._platform_rim[0]
    return g, platform, node


def test_platform_frame_includes_base_strips():
    g, platform, node = _frame()
    mesh = node.mesh
    assert len(mesh.positions) == 192  # eight cubes of 24 vertices
    world_bottom = node.transform.position.y + min(p[1] for p in mesh.positions)
    assert world_bottom <= 0.1, world_bottom
    assert max(p[0] for p in mesh.positions) > float(platform["w"]) / 2.0 + 0.05
    assert node.material is g.assets.require("material.trim").payload


def test_platform_frame_keeps_the_top_edge():
    _g, platform, node = _frame()
    world_top = node.transform.position.y + max(p[1] for p in node.mesh.positions)
    assert world_top >= float(platform["h"]), world_top
