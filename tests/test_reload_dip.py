"""Combat-feel proof: the viewmodel dips while the magazine reloads.

The reload bar and completion cue exist, but the gun stayed rigidly at hip
through the whole reload. A deterministic sine dip now lowers and pulls the
gun back between reload start and completion, then returns it to rest.
"""

import math

from keystone.math3d import Vec3

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    g.sim.ammo["pulse"] = 0
    g.sim.reserve["pulse"] = 120
    return g


def _offsets(g: ShooterGame) -> tuple[float, float]:
    sim = g.sim
    body = g._view_body.transform.position
    eye = sim.eye()
    forward = sim.forward()
    right = Vec3(math.cos(sim.yaw), 0.0, math.sin(sim.yaw))
    up = right.cross(forward)
    dx, dy, dz = body.x - eye.x, body.y - eye.y, body.z - eye.z
    down = -(dx * up.x + dy * up.y + dz * up.z)
    fwd = dx * forward.x + dy * forward.y + dz * forward.z
    return down, fwd


def test_reload_dips_the_viewmodel_down_and_back():
    g = _game()
    idle_down, idle_fwd = _offsets(g)
    g.sim.reload_t = float(g.sim.weapons["pulse"]["reload_s"]) / 2.0
    g._sync_scene()
    mid_down, mid_fwd = _offsets(g)
    assert mid_down > idle_down + 0.05, (idle_down, mid_down)
    assert mid_fwd < idle_fwd - 0.02, (idle_fwd, mid_fwd)


def test_reload_dip_returns_to_rest():
    g = _game()
    idle_down, idle_fwd = _offsets(g)
    g.sim.reload_t = float(g.sim.weapons["pulse"]["reload_s"]) / 2.0
    g._sync_scene()
    g.sim.reload_t = 0.0
    g._sync_scene()
    rest_down, rest_fwd = _offsets(g)
    assert abs(rest_down - idle_down) < 1e-6
    assert abs(rest_fwd - idle_fwd) < 1e-6


def test_reload_dip_is_data_driven():
    g = ShooterGame()
    g.build_scene()
    cfg = g.sim.juice["viewmodel"]
    assert float(cfg.get("reload_drop", 0.0)) > 0.0
    assert float(cfg.get("reload_back", 0.0)) > 0.0
