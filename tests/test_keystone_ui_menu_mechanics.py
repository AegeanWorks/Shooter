"""Keystone mechanics testbed: the pause-menu contract and its closed dispatch.

``ui.menu`` is a pure selection model: items, index, wrap-around and the action
of the selection, with no rendering and no input. The engine's dispatch
(``Engine.apply_ui_action``) knows four actions -- resume, toggle_ui, quit and
pause -- and returns False for anything else.

Both facts matter to a game. The menu validates, so a game cannot ship an empty
or misconfigured pause menu; and dispatch is **closed**: a game cannot add its
own entry (a RESTART item has nowhere to go), which is why the shooter restarts
on Enter during play instead of from the pause menu. This suite pins what the
contract does offer so a future change to either half is visible here.
"""

import dataclasses

import pytest

from keystone.ui.menu import DEFAULT_ITEMS, MenuItem, PauseMenu


def test_the_default_menu_is_resume_hide_hud_and_quit():
    assert [(item.label, item.action) for item in DEFAULT_ITEMS] == [
        ("RESUME", "resume"),
        ("HIDE HUD", "toggle_ui"),
        ("QUIT", "quit"),
    ]
    menu = PauseMenu()
    assert menu.index == 0
    assert menu.action() == "resume"
    assert len(menu.items) == 3


def test_moving_the_selection_wraps_in_both_directions():
    menu = PauseMenu()
    assert [menu.action() for _ in range(1)] == ["resume"]
    menu.move(1)
    assert menu.action() == "toggle_ui"
    menu.move(1)
    assert menu.action() == "quit"
    menu.move(1)
    assert menu.action() == "resume", "down from the last item wraps to the first"
    menu.move(-1)
    assert menu.action() == "quit", "up from the first item wraps to the last"
    # a multi-step move is the same as repeated single steps
    menu.move(3)
    assert menu.action() == "quit"
    menu.move(-6)
    assert menu.action() == "quit"


def test_move_rejects_bools_and_non_integers():
    menu = PauseMenu()
    for bad in (True, False, 1.0, "1", None):
        with pytest.raises(TypeError, match="menu move delta must be an integer"):
            menu.move(bad)
    assert menu.index == 0


def test_a_menu_needs_at_least_one_item():
    with pytest.raises(ValueError, match="pause menu needs at least one item"):
        PauseMenu(items=())
    single = PauseMenu(items=(MenuItem("ONLY", "only"),))
    assert single.action() == "only"
    single.move(1)
    assert single.action() == "only", "a single item wraps onto itself"


def test_items_are_immutable_values():
    item = MenuItem("RESTART", "restart")
    assert item.label == "RESTART" and item.action == "restart"
    with pytest.raises(dataclasses.FrozenInstanceError):
        item.label = "CHANGED"
    assert MenuItem("RESTART", "restart") == MenuItem("RESTART", "restart")
    assert MenuItem("A", "a") != MenuItem("A", "b"), "the action is part of identity"


def test_a_custom_menu_keeps_its_own_order_and_actions():
    """The model accepts any items; only the engine's dispatch is closed."""
    items = (MenuItem("RESUME", "resume"), MenuItem("RESTART", "restart"))
    menu = PauseMenu(items=items)
    assert [menu.action() for _ in range(2)] == ["resume", "resume"]
    assert menu.move(1) == 1 and menu.action() == "restart"


def test_the_menu_carries_no_rendering_state():
    """A pure model: no canvas, no hits, no font metrics."""
    menu = PauseMenu()
    public = {name for name in vars(menu)}
    assert public == {"items", "index"}, f"unexpected menu state: {public}"
