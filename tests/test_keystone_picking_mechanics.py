"""Keystone testbed: a presentation-only crosshair probe via scene picking.

`picking` was one of the Keystone modules the shooter had never imported.
The game now casts one eye-forward ray per frame through raycast_scene and
exposes a JSON-safe hit report for AI/soak consumers. It never writes sim
state, and the overlay-layer viewmodel is excluded by the module itself.
"""

from keystone.physics import Ray
from keystone.picking import hit_report, raycast_scene
from keystone.replay import stable_hash

from shooter.game import ShooterGame

OVERLAY = ("viewmodel-body", "viewmodel-barrel", "viewmodel-grip", "muzzle")


def _game(yaw: float = 0.0, pitch: float = 0.0) -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.yaw = yaw
    g.sim.pitch = pitch
    g._sync_scene()
    return g


def test_crosshair_pick_reports_a_world_node():
    report = _game().crosshair_pick()
    assert report["schema"] == 1 and report["hit"] is True
    assert report["node_id"] == "cover-5", report
    assert 0.0 < report["distance"] < 100.0
    assert len(report["point"]) == 3


def test_the_pick_follows_the_aim_direction():
    assert _game().crosshair_pick()["node_id"] == "cover-5"
    assert _game(yaw=0.8).crosshair_pick()["node_id"] == "wall-e"
    assert _game(pitch=-0.4).crosshair_pick()["node_id"] == "floor"


def test_aiming_above_the_arena_is_a_clean_miss():
    report = _game(pitch=1.4).crosshair_pick()
    assert report["hit"] is False
    assert report["node_id"] is None and report["distance"] is None
    assert report["point"] is None


def test_the_overlay_viewmodel_is_never_picked():
    g = _game()
    assert g.crosshair_pick()["node_id"] not in OVERLAY
    hit = raycast_scene(
        g.scene, Ray(g.sim.eye(), g.sim.forward(), 100.0), ignore=OVERLAY
    )
    assert hit_report(hit) == g.crosshair_pick()


def test_picking_never_touches_the_deterministic_state():
    g = _game()
    before = stable_hash(g.snapshot())
    for yaw in (0.0, 0.8, -1.2, 0.0):
        g.sim.yaw = yaw
        g._sync_scene()
    assert stable_hash(g.snapshot()) == before
