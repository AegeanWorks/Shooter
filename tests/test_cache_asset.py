"""Gameplay proof: the ammo cache is a file-backed OBJ asset.

The testbed proved obj_loader and asset_io hot reload, but every game mesh
was built in code. The cache crate now loads through AssetRegistry.register_file
and refreshes from the loop, with the old cube as an explicit fallback.
"""

from pathlib import Path

from keystone.assets import AssetRegistry
from keystone.primitives import cube

from shooter.asset_pipeline import CACHE_CRATE, register_cache_crate
from shooter.game import ShooterGame

DATA = Path(__file__).parent.parent / "shooter" / "data"


def test_cache_crate_registers_from_obj_with_faces():
    assets = AssetRegistry()
    fallback = cube(0.6)
    assert register_cache_crate(assets, DATA, fallback) is True
    mesh = assets.require(CACHE_CRATE).payload
    assert mesh is not fallback
    assert mesh.triangle_count() == 24
    sources = assets.describe()["sources"]
    assert any(
        entry["id"] == CACHE_CRATE and entry["kind"] == "mesh" for entry in sources
    )


def test_missing_obj_falls_back_to_the_old_cube(tmp_path):
    assets = AssetRegistry()
    fallback = cube(0.6)
    assert register_cache_crate(assets, tmp_path, fallback) is False
    assert assets.require(CACHE_CRATE).payload is fallback


def test_game_cache_nodes_render_the_file_backed_crate():
    game = ShooterGame()
    game.build_scene()
    crate = game.assets.require(CACHE_CRATE).payload
    assert all(node.mesh is crate for node in game._cache_nodes)
    assert crate is not game.assets.require("mesh.pickup").payload


def test_reload_assets_reports_unchanged_and_keeps_a_json_safe_report():
    game = ShooterGame()
    game.build_scene()
    report = game.reload_assets()
    assert report.ok is True
    assert CACHE_CRATE in report.unchanged
    assert game.asset_reload_report["checked"] >= 1
    assert game.asset_reload_report["ok"] is True
