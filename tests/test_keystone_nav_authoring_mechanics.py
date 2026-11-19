"""Keystone testbed: nav grid authored from the live collision boxes.

`nav_authoring` was one of the Keystone modules the corrected coverage scan
still found unconsumed. `nav_authoring_report()` rasterizes the sim's wall and
cover AABBs into a NavGrid with Keystone's clearance rule, explicitly excluding
the arena floor (which would otherwise block all 1600 cells). It is an
on-demand query: no sim state, no scene writes.
"""

from keystone.replay import stable_hash

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_the_authored_grid_has_open_endpoints_and_a_route():
    report = _game().nav_authoring_report()
    assert report["schema"] == 1
    assert report["width"] == report["height"] == 40
    assert report["start_open"] is True and report["goal_open"] is True
    assert report["path"]["found"] is True
    assert report["path"]["steps"] > 0


def test_the_arena_floor_is_explicitly_excluded():
    report = _game().nav_authoring_report()
    assert report["floor_excluded"] == 1
    assert report["boxes"] == len(_game().sim.colliders) - 1
    assert 0 < report["blocked"] < 1600


def test_more_clearance_blocks_more_cells():
    g = _game()
    narrow = g.nav_authoring_report(clearance=0.0)
    wide = g.nav_authoring_report(clearance=0.5)
    assert wide["blocked"] > narrow["blocked"]


def test_the_report_is_reproducible():
    g = _game()
    assert g.nav_authoring_report() == g.nav_authoring_report()


def test_authoring_a_grid_never_touches_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    g.nav_authoring_report(clearance=0.4)
    assert stable_hash(g.snapshot()) == before
