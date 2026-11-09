"""Live input proof: the engine's bind_input hook drives the real sim.

Keystone already calls an optional `bind_input` hook; the shooter now uses it
so the buttons its actions() contract advertises have real keys. The fake
context exercises the same InputMap.sample path a GLFW window uses.
"""

from keystone.gpu.context import key_names
from keystone.input import ActionState, InputMap

from shooter.game import ShooterGame


class FakeContext:
    def __init__(self) -> None:
        self.keys: set[str] = set()
        self.pointer = (0.0, 0.0)
        self.mouse = False

    def key_down(self, key: str) -> bool:
        return key in self.keys

    def cursor_position(self) -> tuple[float, float]:
        return self.pointer

    def mouse_down(self, button: str = "left") -> bool:
        return self.mouse


def _game() -> ShooterGame:
    game = ShooterGame()
    game.build_scene()
    game.sim.spawn_queue = ["mite"]
    game.sim.spawn_t = 999.0
    game.sim.enemies = []
    return game


def _mapping(game: ShooterGame) -> InputMap:
    mapping = InputMap()
    game.bind_input(mapping)
    return mapping


def _press(game: ShooterGame, mapping: InputMap, *keys: str):
    context = FakeContext()
    context.keys = set(keys)
    return game, mapping.sample(context, 1.0 / 60.0)


def test_bind_input_covers_every_declared_button_with_real_keys():
    game = _game()
    mapping = _mapping(game)
    assert mapping.unbound_buttons(game.actions()["buttons"]) == []
    assert mapping.unknown_keys(key_names()) == []
    assert mapping.list_actions()["slot2"] == "2"
    assert mapping.list_actions()["reload"] == "r"


def test_number_key_switches_weapon_through_sample():
    game = _game()
    mapping = _mapping(game)
    game, actions = _press(game, mapping, "2")
    assert "slot2" in actions.pressed
    game.update(1.0 / 60.0, actions)
    assert game.sim.weapon == "scatter"


def test_r_key_starts_reload():
    game = _game()
    mapping = _mapping(game)
    game.sim.ammo["pulse"] = 0
    game.sim.reserve["pulse"] = 120
    game, actions = _press(game, mapping, "r")
    game.update(1.0 / 60.0, actions)
    assert game.sim.reload_t > 0.0


def test_j_key_starts_overdrive():
    game = _game()
    mapping = _mapping(game)
    game, actions = _press(game, mapping, "j")
    game.update(1.0 / 60.0, actions)
    assert game.sim.overdrive_t > 0.0


def test_f_and_space_keys_fire_and_jump():
    game = _game()
    mapping = _mapping(game)
    game, actions = _press(game, mapping, "f", "space")
    assert {"fire", "jump"} <= actions.pressed
    shots = game.sim.shots
    height = game.sim.player_pos.y
    game.update(1.0 / 60.0, actions)
    assert game.sim.shots > shots
    # The first update settles the body onto the floor; the buffered jump
    # fires on the next frame, exactly as it does in play.
    game.update(1.0 / 60.0, ActionState())
    assert game.sim.player_pos.y > height
