"""Keystone testbed: the arena's nav plan comes from pathfinding + navigation.

Neither module was imported by the shooter before this cycle. `nav_plan_report()`
derives a NavGrid from the shipped cover layout, runs A* from spawn to the surge
pickup, smooths the cells into world waypoints and exposes a follower report.
It is an on-demand query: no sim state, no per-frame cost, no replay-hash change.
"""

from keystone.replay import stable_hash

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_nav_plan_reports_a_route_from_spawn_to_pickup():
    report = _game().nav_plan_report()
    assert report["schema"] == 1
    path = report["pathfinding"]
    assert path["schema"] == 1 and path["found"] is True
    assert len(path["start"]) == 2 and len(path["goal"]) == 2
    assert path["steps"] > 0 and path["expanded"] > 0
    # smooth_path collapses the cell route into a few world waypoints
    assert 0 < len(report["waypoints"]) <= len(path["path"])


def test_the_grid_marks_the_shipped_covers_as_blocked():
    grid = _game().nav_plan_report()["grid"]
    assert grid["width"] == grid["height"] == 40
    assert grid["cell_size"] == 1.0
    assert grid["blocked_cells"] > 0, grid


def test_waypoints_are_world_points_near_the_endpoints():
    g = _game()
    report = g.nav_plan_report()
    points = report["waypoints"]
    assert points and all(len(point) == 3 for point in points)
    spawn = g.sim.levels["player"]["spawn"]
    pickup = g.sim.levels["pickup"]
    assert abs(points[0][0] - spawn[0]) < 2.0 and abs(points[0][2] - spawn[2]) < 2.0
    assert abs(points[-1][0] - pickup["x"]) < 2.0
    assert abs(points[-1][2] - pickup["z"]) < 2.0


def test_a_blocked_goal_reports_no_route():
    g = _game()
    g.sim.levels["pickup"] = {"x": 2.5, "y": 0.5, "z": 0.0}  # centre cover
    report = g.nav_plan_report()
    assert report["pathfinding"]["found"] is False
    assert report["waypoints"] == []


def test_building_a_nav_plan_never_touches_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    for _ in range(3):
        g.nav_plan_report()
    assert stable_hash(g.snapshot()) == before
