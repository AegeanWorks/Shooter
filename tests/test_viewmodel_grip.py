"""Combat-feel proof: the viewmodel reads as a held gun, not a floating bar.

The two-cube viewmodel had no grip; the screenshots show a bare gray bar
floating above the bottom edge. A third grip node under the receiver anchors
the silhouette to the lower-right without touching the sim.
"""

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    game = ShooterGame()
    game.build_scene()
    game._sync_scene()
    return game


def _offsets(game: ShooterGame, node) -> tuple[float, float]:
    # The rig root owns the camera pose; parts carry camera-space x/y.
    point = node.transform.position
    return point.x, point.y


def test_viewmodel_has_a_grip_below_the_receiver():
    game = _game()
    assert game._view_grip is not None
    assert game._view_grip.visible is True
    body_x, body_y = _offsets(game, game._view_body)
    grip_x, grip_y = _offsets(game, game._view_grip)
    assert grip_y < body_y - 0.05, (body_y, grip_y)
    assert -1.0 < grip_x < 1.0 and -1.0 < grip_y < 1.0


def test_grip_tints_with_the_active_weapon():
    game = _game()
    for weapon in ("pulse", "scatter", "lance"):
        game.sim.weapon = weapon
        game._sync_scene()
        expected = game.assets.require(f"material.gun_{weapon}").payload
        assert game._view_grip.material is expected, weapon


def test_grip_hides_with_the_gun_on_death():
    game = _game()
    game.sim.alive = False
    game._sync_scene()
    assert game._view_grip.visible is False
