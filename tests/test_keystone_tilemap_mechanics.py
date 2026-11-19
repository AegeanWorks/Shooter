"""Keystone testbed: the shipped arena authored as a TileMap document.

`tilemap` was one of the Keystone modules the shooter had never imported.
`arena_tile_report()` derives an immutable tile map from levels.json, proves its
document round-trips, and exposes collider and merged-mesh counts for AI/soak
consumers. It is an on-demand query: no renderer, no sim state, no hash change.
"""

from keystone.replay import stable_hash
from keystone.tilemap import TileMap, tilemap_report

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_arena_tile_report_has_the_shipped_shape():
    report = _game().arena_tile_report()
    tiles = report["tiles"]
    assert report["schema"] == 1
    assert tiles["width"] == tiles["height"] == 40
    assert tiles["tile_size"] == 1.0
    assert tiles["solid"] > 0 and tiles["free"] > 0
    assert tiles["solid"] + tiles["free"] == 1600


def test_cover_cells_are_marked_solid():
    report = _game().arena_tile_report()
    solid = {tuple(cell) for cell in report["solid_cells"]}
    assert (22, 20) in solid, "the centre cover at (2.5, 0) must occupy cells"
    assert report["tiles"]["solid"] == len(solid)


def test_the_document_round_trips_to_an_equal_tile_map():
    report = _game().arena_tile_report()
    document = report["document"]
    assert document["schema"] == 1
    rebuilt = TileMap.from_dict(document)
    assert rebuilt == TileMap.from_dict(rebuilt.to_dict())
    assert tilemap_report(rebuilt) == report["tiles"]


def test_colliders_and_merged_mesh_are_reported():
    report = _game().arena_tile_report()
    assert report["colliders"] > 0
    assert report["mesh"]["vertices"] > 0
    assert report["mesh"]["triangles"] > 0


def test_repeated_reports_are_stable_and_never_touch_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    first = g.arena_tile_report()
    assert g.arena_tile_report() == first
    assert stable_hash(g.snapshot()) == before
