"""Testbed consistency: one arena layout for every grid-shaped report.

Cycles 184, 191, 193 and 196 each recomputed the same size/cell/origin math
before building a TileMap, NavGrid or route. These tests pin a single shared
layout and cell conversion so a level-size edit cannot desynchronise them.
"""

from keystone.math3d import Vec3
from keystone.replay import stable_hash

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_the_shared_layout_matches_the_shipped_arena():
    width, cell, origin = _game()._arena_layout()
    assert width == 40 and cell == 1.0
    assert (origin.x, origin.y, origin.z) == (-20.0, 0.0, -20.0)


def test_the_shared_cell_conversion_matches_spawn_and_pickup():
    g = _game()
    assert g._to_cell(0.0, 8.0) == (20, 28)
    pickup = g.sim.levels["pickup"]
    assert g._to_cell(float(pickup["x"]), float(pickup["z"])) == (20, 14)


def test_a_resized_arena_propagates_to_every_report():
    g = _game()
    g.sim.levels["arena"]["size"] = 20.0
    width, _cell, origin = g._arena_layout()
    assert width == 20 and origin.x == -10.0
    assert g.nav_plan_report()["grid"]["width"] == width
    assert g.nav_authoring_report()["width"] == width
    assert g.arena_tile_report()["tiles"]["width"] == width
    grid = g._nav_grid(0.0)
    assert grid.width == width and grid.height == width
    assert len(grid.blocked) <= width * width


def test_the_layout_helpers_never_touch_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    g._arena_layout()
    g._to_cell(1.0, 2.0)
    assert stable_hash(g.snapshot()) == before
