"""Keystone mechanics testbed: the spatial-grid broadphase contract.

The grid is a performance structure with a correctness guarantee: "cell size
is a performance trade-off, not a correctness setting", and results come back
in insertion order so a consumer's output stays deterministic. This suite
asserts those two properties directly -- the same scene must produce identical
``query`` and ``pairs`` answers at wildly different cell sizes -- and pins the
degradation and allocation limits that keep a pathological scene from hanging.
"""

import pytest

from keystone.broadphase import MAX_PROXY_CELLS, SpatialGrid
from keystone.math3d import Vec3
from keystone.physics import AABB


def _box(x, y, z, half=0.5):
    return AABB(Vec3(x, y, z), Vec3(half, half, half))


def _populated():
    """A scene whose cells overlap in every interesting way."""
    grid = SpatialGrid(cell_size=2.0)
    grid.insert("center", _box(0.0, 0.0, 0.0, 1.0))
    grid.insert("east", _box(1.5, 0.0, 0.0, 1.0))
    grid.insert("north", _box(0.0, 1.5, 0.0, 1.0))
    grid.insert("diagonal", _box(1.5, 1.5, 0.0, 1.0))
    grid.insert("far", _box(40.0, 0.0, 0.0, 1.0))
    grid.insert("above", _box(0.0, 20.0, 0.0, 1.0))
    return grid


def test_cell_size_changes_no_answer():
    queries = (
        _box(0.0, 0.0, 0.0, 2.0),
        _box(1.5, 1.5, 0.0, 0.25),
        _box(40.0, 0.0, 0.0, 0.25),
        _box(-30.0, -30.0, -30.0, 1.0),
    )
    points = (Vec3(0.0, 0.0, 0.0), Vec3(1.5, 1.5, 0.0), Vec3(40.0, 0.0, 0.0))
    baseline = None
    for cell_size in (0.05, 0.5, 2.0, 16.0, 1024.0):
        grid = SpatialGrid(cell_size=cell_size)
        for key, box in (
            ("center", _box(0.0, 0.0, 0.0, 1.0)),
            ("east", _box(1.5, 0.0, 0.0, 1.0)),
            ("north", _box(0.0, 1.5, 0.0, 1.0)),
            ("diagonal", _box(1.5, 1.5, 0.0, 1.0)),
            ("far", _box(40.0, 0.0, 0.0, 1.0)),
            ("above", _box(0.0, 20.0, 0.0, 1.0)),
        ):
            grid.insert(key, box)
        observed = (
            [grid.query(box) for box in queries],
            [grid.query_point(point) for point in points],
            grid.pairs(),
        )
        if baseline is None:
            baseline = observed
        assert observed == baseline, f"cell_size={cell_size} changed the answer"


def test_a_large_proxy_is_found_from_an_edge_cell():
    # A proxy is registered in every cell it spans, so a query touching only a
    # far edge -- never the centre cell -- must still find it. Registering just
    # the centre cell passes a centre-only test and fails this one.
    for cell_size in (0.5, 1.0, 2.0):
        grid = SpatialGrid(cell_size=cell_size)
        grid.insert("wide", AABB(Vec3(0.0, 0.0, 0.0), Vec3(2.5, 2.5, 2.5)))
        assert grid.query(_box(2.0, 0.0, 0.0, 0.05)) == ["wide"], cell_size
        assert grid.query(_box(0.0, -2.4, 0.0, 0.05)) == ["wide"], cell_size
        assert grid.query(_box(2.4, 2.4, 2.4, 0.05)) == ["wide"], cell_size
        assert grid.query(_box(2.6, 0.0, 0.0, 0.05)) == [], cell_size


def test_results_follow_insertion_order_not_spatial_order():
    grid = SpatialGrid(cell_size=4.0)
    # inserted in the reverse of their x position on purpose; half extent 10
    # makes all three cover the origin so only ordering can explain the result
    for key, x in (("c", 8.0), ("b", 0.0), ("a", -8.0)):
        grid.insert(key, _box(x, 0.0, 0.0, 10.0))
    assert grid.query(_box(0.0, 0.0, 0.0, 20.0)) == ["c", "b", "a"]
    assert grid.query_point(Vec3(0.0, 0.0, 0.0)) == ["c", "b", "a"]
    assert grid.pairs() == [("c", "b"), ("c", "a"), ("b", "a")]


def test_reinserting_a_key_keeps_its_original_rank():
    grid = SpatialGrid(cell_size=1.0)
    grid.insert("first", _box(0.0, 0.0, 0.0))
    grid.insert("second", _box(0.0, 0.0, 0.0))
    grid.insert("third", _box(0.0, 0.0, 0.0))
    # move the oldest proxy far away, then back: identity, not recency, ranks it
    grid.update("first", _box(50.0, 50.0, 50.0))
    grid.update("first", _box(0.0, 0.0, 0.0))
    assert grid.query_point(Vec3(0.0, 0.0, 0.0)) == ["first", "second", "third"]
    assert len(grid) == 3, "an update must replace, never duplicate"
    assert grid.get("first") == _box(0.0, 0.0, 0.0)


def test_insert_replaces_bounds_and_drops_stale_cells():
    grid = SpatialGrid(cell_size=1.0)
    grid.insert("mover", _box(0.0, 0.0, 0.0))
    grid.insert("mover", _box(100.0, 0.0, 0.0))
    assert grid.query_point(Vec3(0.0, 0.0, 0.0)) == [], "stale cell still holds it"
    assert grid.query_point(Vec3(100.0, 0.0, 0.0)) == ["mover"]
    assert len(grid) == 1


def test_remove_clear_and_membership():
    grid = _populated()
    assert "center" in grid and "missing" not in grid
    assert grid.get("missing") is None
    assert grid.remove("center") is True
    assert grid.remove("center") is False
    assert "center" not in grid
    assert grid.query_point(Vec3(0.0, 0.0, 0.0)) == [], "neighbours still overlap"

    grid.clear()
    assert len(grid) == 0
    assert grid.query(_box(0.0, 0.0, 0.0, 1000.0)) == []
    assert grid.pairs() == []

    # a cleared grid accepts fresh proxies at the original ranks
    grid.insert("again", _box(0.0, 0.0, 0.0))
    assert grid.query_point(Vec3(0.0, 0.0, 0.0)) == ["again"]


def test_empty_and_degenerate_inputs():
    grid = SpatialGrid()
    assert len(grid) == 0
    assert grid.query(_box(0.0, 0.0, 0.0)) == []
    assert grid.query_point(Vec3(1.0, 2.0, 3.0)) == []
    assert grid.pairs() == []

    # a zero-extent point proxy is legal and still filters exactly
    grid.insert("point", _box(0.0, 0.0, 0.0, 0.0))
    assert grid.query_point(Vec3(0.0, 0.0, 0.0)) == ["point"]
    assert grid.query_point(Vec3(0.001, 0.0, 0.0)) == []


def test_cell_size_validation():
    for bad in (0.0, -1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="cell_size must be positive and finite"):
            SpatialGrid(cell_size=bad)
    with pytest.raises(TypeError, match="cell_size must be a real number"):
        SpatialGrid(cell_size="2")
    with pytest.raises(TypeError, match="cell_size must be a real number"):
        SpatialGrid(cell_size=True)


def test_proxy_cell_budget_is_inclusive_and_names_the_limit():
    grid = SpatialGrid(cell_size=1.0)
    # exactly MAX_PROXY_CELLS cells: 1000 x 10 x 10
    at_limit = AABB(Vec3(500.0, 5.0, 5.0), Vec3(499.9, 4.9, 4.9))
    grid.insert("at-limit", at_limit)
    assert "at-limit" in grid

    # one cell over the budget is refused, and nothing is left behind
    over = AABB(Vec3(500.0, 5.0, 5.0), Vec3(500.0, 4.9, 4.9))
    with pytest.raises(ValueError, match=f"limit {MAX_PROXY_CELLS}"):
        grid.insert("over", over)
    assert "over" not in grid
    assert len(grid) == 1


def test_an_oversized_query_degrades_to_a_linear_scan():
    grid = SpatialGrid(cell_size=1.0)
    grid.insert("near", _box(0.0, 0.0, 0.0))
    grid.insert("far", _box(5000.0, 0.0, 0.0))
    huge = AABB(Vec3(0.0, 0.0, 0.0), Vec3(1e6, 1e6, 1e6))
    # correctness never depends on cell_size, so the query still answers exactly
    assert grid.query(huge) == ["near", "far"]
    assert grid.query(_box(0.0, 0.0, 0.0, 0.0)) == ["near"]


def test_non_finite_bounds_never_reach_the_grid():
    # AABB validates finiteness in its own constructor, so the grid's defensive
    # "broadphase bounds must be finite" guard is unreachable through the public
    # physics type. That is the reason the testbed asserts the AABB message: a
    # consumer can never hand the grid a NaN or infinite box.
    grid = SpatialGrid(cell_size=1.0)
    with pytest.raises(ValueError, match="must be finite"):
        AABB(Vec3(float("nan"), 0.0, 0.0), Vec3(1.0, 1.0, 1.0))
    with pytest.raises(ValueError, match="must be finite"):
        AABB(Vec3(0.0, 0.0, 0.0), Vec3(float("inf"), 1.0, 1.0))
    assert len(grid) == 0


def test_two_grids_agree_and_repeat_calls_are_stable():
    first, second = _populated(), _populated()
    box = _box(0.0, 0.0, 0.0, 3.0)
    assert first.query(box) == second.query(box)
    assert first.pairs() == second.pairs()
    assert first.query(box) == first.query(box), "query must not mutate the grid"
