"""Testbed consistency: one authoritative nav grid for every report.

Cycles 182 and 193 built two different nav grids from the same shipped level:
cover-only rasterization (143 blocked cells) and Keystone collider authoring
(244 blocked cells including walls). Two AI consumers asking different
questions got different answers. These tests pin the unified contract.
"""

from keystone.replay import stable_hash

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_the_two_nav_reports_agree_on_the_blocked_set():
    g = _game()
    plan = g.nav_plan_report()
    authoring = g.nav_authoring_report(clearance=0.0)
    assert plan["grid"]["blocked_cells"] == authoring["blocked"]
    assert plan["grid"]["width"] == authoring["width"]


def test_both_routes_still_exist_and_agree():
    g = _game()
    plan = g.nav_plan_report()["pathfinding"]
    authoring = g.nav_authoring_report(clearance=0.0)["path"]
    assert plan["found"] is True and authoring["found"] is True
    assert plan["start"] == authoring["start"] and plan["goal"] == authoring["goal"]
    assert plan["steps"] == authoring["steps"]


def test_the_shared_helper_is_the_authority_for_both():
    g = _game()
    blocked = len(g._nav_grid(0.0).blocked)
    assert blocked == g.nav_plan_report()["grid"]["blocked_cells"]
    assert blocked == g.nav_authoring_report(clearance=0.0)["blocked"]


def test_unifying_the_grid_never_touches_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    g.nav_plan_report()
    g.nav_authoring_report()
    g._nav_grid(0.5)
    assert stable_hash(g.snapshot()) == before
