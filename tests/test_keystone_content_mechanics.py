"""Keystone testbed: content digests for the shooter's registered assets.

`content` was one of the Keystone modules the shooter had never imported even
though its batching is content-keyed. `asset_digest_report()` exposes stable
SHA-256 digests for a fixed set of shipped meshes and materials so an AI can
tell whether two registries hold the same payload without object identity.
"""

from keystone.content import material_digest, mesh_digest
from keystone.geometry import Material
from keystone.math3d import Vec3
from keystone.primitives import cube
from keystone.replay import stable_hash

from shooter.game import DIGEST_ASSETS, ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_digest_report_covers_the_shipped_render_assets():
    report = _game().asset_digest_report()
    assert report["schema"] == 1
    assert report["count"] == len(DIGEST_ASSETS)
    assert set(report["digests"]) == set(DIGEST_ASSETS)
    assert all(len(digest) == 64 for digest in report["digests"].values())


def test_equal_payloads_share_a_digest_without_object_identity():
    a, b = _game(), _game()
    wall_a = a.assets.require("mesh.wall").payload
    wall_b = b.assets.require("mesh.wall").payload
    assert wall_a is not wall_b
    assert mesh_digest(wall_a) == mesh_digest(wall_b)
    assert a.asset_digest_report()["digests"] == b.asset_digest_report()["digests"]


def test_different_content_produces_a_different_digest():
    assert mesh_digest(cube(1.0)) != mesh_digest(cube(2.0))
    assert material_digest(Material(color=Vec3(1.0, 0.0, 0.0))) != material_digest(
        Material(color=Vec3(0.0, 1.0, 0.0))
    )


def test_repeated_reports_are_stable():
    g = _game()
    assert g.asset_digest_report() == g.asset_digest_report()


def test_digests_never_touch_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    for _ in range(3):
        g.asset_digest_report()
    assert stable_hash(g.snapshot()) == before
