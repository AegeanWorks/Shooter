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


def _ndc(game: ShooterGame, node) -> object:
    return game.scene.camera.view_projection(960.0 / 540.0).project_point(
        node.transform.position
    )


def test_viewmodel_has_a_grip_below_the_receiver():
    game = _game()
    assert game._view_grip is not None
    assert game._view_grip.visible is True
    body = _ndc(game, game._view_body)
    grip = _ndc(game, game._view_grip)
    assert grip.y < body.y - 0.1, (body.y, grip.y)
    assert -1.0 < grip.x < 1.0 and -1.0 < grip.y < 1.0


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
