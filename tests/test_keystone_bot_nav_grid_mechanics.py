"""Testbed consistency: the bot preview plans on the authoritative nav grid.

Cycle 196 unified nav_plan_report and nav_authoring_report on one collider-derived
grid, but bot_nav_preview still built a cover-only grid from the tile report and
mixed it with a goal from the unified grid. These tests pin the shared contract.
"""

from keystone.replay import stable_hash

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_bot_preview_uses_the_authoritative_blocked_set():
    g = _game()
    preview = g.bot_nav_preview()
    assert preview["blocked_cells"] == len(g._nav_grid(0.0).blocked)
    assert preview["blocked_cells"] == g.nav_authoring_report(clearance=0.0)["blocked"]


def test_bot_preview_goal_matches_the_route_plan():
    g = _game()
    assert g.bot_nav_preview()["goal"] == g.nav_plan_report()["pathfinding"]["goal"]


def test_bot_preview_follows_a_resized_arena():
    g = _game()
    g.sim.levels["arena"]["size"] = 20.0
    preview = g.bot_nav_preview()
    assert preview["blocked_cells"] == len(g._nav_grid(0.0).blocked)
    assert preview["goal"] == g.nav_plan_report()["pathfinding"]["goal"]


def test_bot_preview_never_touches_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    g.bot_nav_preview(frames=30)
    assert stable_hash(g.snapshot()) == before
