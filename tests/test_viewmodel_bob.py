"""Combat-feel proof: the viewmodel sways with horizontal movement.

The gun was rigidly camera-locked while walking or sprinting; only recoil
and reload moved it. A small deterministic bob now follows horizontal speed
and settles back to rest when the player stops.
"""

from keystone.math3d import Vec3

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    g.sim.body = g.sim.body.__class__(
        position=g.sim.body.position, half_extents=g.sim.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    return g


def _offsets(g: ShooterGame) -> tuple[float, float]:
    # The rig owns the camera pose, so the part's local x/y ARE right/up.
    body = g._view_body.transform.position
    return body.x, body.y


def test_moving_viewmodel_sways_off_the_rest_pose():
    g = _game()
    g.sim.hvel = Vec3()
    g.sim.time = 0.2
    g._sync_scene()
    rest_right, _rest_up = _offsets(g)
    g.sim.hvel = Vec3(4.0, 0.0, 0.0)
    g._sync_scene()
    moving_right, _moving_up = _offsets(g)
    assert abs(moving_right - rest_right) > 0.01, (rest_right, moving_right)
    g.sim.time = 0.0
    g._sync_scene()
    _phase_right, phase_up = _offsets(g)
    g.sim.hvel = Vec3()
    g._sync_scene()
    _rest_right, rest_up = _offsets(g)
    assert abs(phase_up - rest_up) > 0.008, (rest_up, phase_up)


def test_viewmodel_bob_returns_to_rest_when_stopped():
    g = _game()
    g.sim.hvel = Vec3()
    g.sim.time = 0.3
    g._sync_scene()
    rest = _offsets(g)
    g.sim.hvel = Vec3(4.0, 0.0, 0.0)
    g._sync_scene()
    assert _offsets(g) != rest
    g.sim.hvel = Vec3()
    g._sync_scene()
    assert _offsets(g) == rest


def test_viewmodel_bob_is_data_driven():
    g = ShooterGame()
    g.build_scene()
    cfg = g.sim.juice["viewmodel"]
    assert float(cfg.get("bob_right", 0.0)) > 0.0
    assert float(cfg.get("bob_up", 0.0)) > 0.0
    assert float(cfg.get("bob_hz", 0.0)) > 0.0
