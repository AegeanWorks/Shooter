"""Keystone mechanics testbed: input, UI, asset loading and batch merging.

Covers InputMap contexts/rebinding and ActionState pressed/held,
PauseMenu selection and Canvas clipping, PNG/OBJ loading, and
merge_batches on the shooter scene.
"""

import tempfile
from pathlib import Path

import pytest

from keystone.batch import merge_batches, plan_batches
from keystone.input import ActionState, InputMap
from keystone.obj_loader import load_obj, parse_obj
from keystone.png import read_png, write_png
from keystone.ui.canvas import Canvas
from keystone.ui.menu import MenuItem, PauseMenu

from shooter.game import ShooterGame

COLOR = (1.0, 0.5, 0.25, 1.0)


class _InputContext:
    def __init__(self, keys=(), mouse=False, cursor=(0.0, 0.0)) -> None:
        self.keys = set(keys)
        self.mouse = mouse
        self.cursor = cursor

    def key_down(self, key: str) -> bool:
        return key in self.keys

    def mouse_down(self, button: str) -> bool:
        return self.mouse

    def cursor_position(self) -> tuple[float, float]:
        return self.cursor


def test_input_map_contexts_and_pressed_held():
    bindings = InputMap(
        bindings={"jump": "space"},
        contexts={"menu": {"jump": "enter"}},
        context="gameplay",
    )
    context = _InputContext({"space"})
    first = bindings.sample(context, 1.0 / 60.0)
    assert "jump" in first.held
    assert "jump" in first.pressed
    second = bindings.sample(context, 1.0 / 60.0)
    assert "jump" in second.held
    assert "jump" not in second.pressed

    bindings.set_context("menu")
    assert bindings.get_context() == "menu"
    assert bindings.list_contexts() == ["gameplay", "menu"]
    context.keys = {"enter"}
    menu = bindings.sample(context, 1.0 / 60.0)
    assert "jump" in menu.held
    assert "jump" in menu.pressed

    bindings.bind("jump", "j", context="menu")
    assert bindings.list_actions()["jump"] == "j"
    bindings.set_context("gameplay")
    assert bindings.list_actions()["jump"] == "space"
    bindings.set_context("menu")
    assert bindings.unbind("jump") is True
    assert "jump" not in bindings.list_actions()

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "bindings.json"
        bindings.bind("jump", "enter", context="menu")
        bindings.save_bindings(path)
        loaded = InputMap.load_bindings(path)
    assert loaded.get_context() == "menu"
    assert loaded.list_actions()["jump"] == "enter"
    assert loaded.list_contexts() == ["gameplay", "menu"]


def test_action_state_pressed_held_round_trip():
    state = ActionState(
        forward=1.0,
        pressed=frozenset({"fire", "jump"}),
        held=frozenset({"fire", "sprint"}),
    )
    document = state.to_dict()
    restored = ActionState.from_dict(document)
    assert restored.forward == 1.0
    assert restored.pressed == frozenset({"fire", "jump"})
    assert restored.held == frozenset({"fire", "sprint"})
    stripped = state.without_pressed()
    assert stripped.pressed == frozenset()
    assert stripped.held == state.held
    assert stripped.forward == 1.0


def test_pause_menu_and_canvas_clipping():
    menu = PauseMenu()
    assert menu.action() == "resume"
    assert menu.move(1) == 1
    assert menu.action() == "toggle_ui"
    assert menu.move(-1) == 0
    assert menu.move(-1) == 2
    assert menu.action() == "quit"
    with pytest.raises(TypeError):
        menu.move(True)
    custom = PauseMenu((MenuItem("ONE", "one"), MenuItem("TWO", "two")))
    assert custom.move(1) == 1 and custom.action() == "two"

    canvas = Canvas(10, 10)
    canvas.rect(-2.0, -2.0, 5.0, 5.0, COLOR)
    assert canvas.quads == [(0.0, 0.0, 3.0, 3.0, COLOR)]
    canvas.rect(8.0, 8.0, 5.0, 5.0, COLOR)
    assert canvas.quads[-1] == (8.0, 8.0, 2.0, 2.0, COLOR)
    before = len(canvas.quads)
    canvas.rect(20.0, 20.0, 5.0, 5.0, COLOR)
    assert len(canvas.quads) == before
    canvas.text(9.0, 9.0, "a", COLOR, scale=2)
    assert canvas.labels == ["A"]
    for x, y, width, height, _ in canvas.quads:
        assert 0.0 <= x <= 10.0 and 0.0 <= y <= 10.0
        assert 0.0 <= x + width <= 10.0 and 0.0 <= y + height <= 10.0
    canvas.add_button(1.0, 2.0, 3.0, 4.0, "resume", "resume", selected=True)
    assert canvas.buttons[0].label == "RESUME"
    assert canvas.buttons[0].action == "resume"
    assert canvas.buttons[0].selected is True


def test_png_and_obj_loading():
    pixels = bytes(
        (
            1, 2, 3, 255,
            4, 5, 6, 255,
            7, 8, 9, 255,
            10, 11, 12, 255,
        )
    )
    with tempfile.TemporaryDirectory() as directory:
        png = Path(directory) / "roundtrip.png"
        write_png(png, 2, 2, pixels)
        width, height, restored = read_png(png)
        assert (width, height) == (2, 2)
        assert restored == bytes(
            (
                7, 8, 9, 255,
                10, 11, 12, 255,
                1, 2, 3, 255,
                4, 5, 6, 255,
            )
        )
        with pytest.raises(ValueError):
            write_png(Path(directory) / "bad.png", 2, 2, b"\x00" * 8)

        obj = Path(directory) / "quad.obj"
        obj.write_text(
            "v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\nf 1 2 3 4\n",
            encoding="utf-8",
        )
        mesh = load_obj(obj)
        assert mesh.vertex_count() == 4
        assert mesh.triangle_count() == 2
        assert mesh.indices == (0, 1, 2, 0, 2, 3)
        assert mesh.normals[0] == (0.0, 0.0, 1.0)

    parsed = parse_obj("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
    assert parsed.vertex_count() == 3
    assert parsed.indices == (0, 1, 2)


def test_merge_batches_on_the_shooter_scene():
    game = ShooterGame()
    game.build_scene()
    plan = plan_batches(game.scene)
    merged = merge_batches(game.scene)
    assert merged["groups"] == merged["merged_calls"] > 0
    assert merged["saved_calls"] > 0
    assert merged["triangles"] == plan["triangles"]
    assert any(
        "platform-pad" in group["nodes"] for group in merged["merged"]
    )
    excluded = merge_batches(game.scene, exclude={"platform-pad"})
    assert not any(
        "platform-pad" in group["nodes"] for group in excluded["merged"]
    )
    assert excluded["saved_calls"] < merged["saved_calls"]
