"""Levels proof: the jump-platform launch spot is marked on the floor.

The rim marks the platform top; a single flat lit pad before the south
edge marks where to jump from. Decoration only, one node, budget-safe.
"""

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_approach_pad_exists_and_uses_trim():
    g = _game()
    pad = g._approach_pad
    assert pad is not None
    assert pad.visible is True
    assert pad.material is g.assets.require("material.trim").payload


def test_approach_pad_sits_before_the_platform():
    g = _game()
    pad = g._approach_pad
    platform = next(
        c for c in g.sim.levels["arena"]["covers"] if float(c["h"]) < 1.0
    )
    px, pz = float(platform["x"]), float(platform["z"])
    assert abs(pad.transform.position.x - px) < 0.1
    assert pz - 4.0 < pad.transform.position.z < pz - 2.0
    assert pad.transform.scale.x >= 1.0
    assert pad.transform.scale.y <= 0.05
