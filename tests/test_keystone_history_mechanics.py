"""Keystone mechanics testbed: bounded undo/redo history.

Covers push/peek/undo/redo round trips, deep-copy isolation, redo-branch
discard, oldest-entry eviction with index repair, and clear/empty behavior.
"""

import pytest

from keystone.history import History


def test_push_peek_undo_redo_round_trip():
    history = History(capacity=4)
    assert history.peek() is None
    assert history.can_undo is False
    assert history.can_redo is False
    assert history.redo_available is False
    assert history.values() == []
    assert len(history) == 0

    history.push({"n": 1})
    assert history.peek() == {"n": 1}
    assert history.can_undo is False
    history.push({"n": 2})
    history.push({"n": 3})
    assert history.peek() == {"n": 3}
    assert history.can_undo is True
    assert history.can_redo is False
    assert history.undo() == {"n": 2}
    assert history.can_redo is True
    assert history.redo_available is True
    assert history.undo() == {"n": 1}
    assert history.undo() is None
    assert history.redo() == {"n": 2}
    assert history.redo() == {"n": 3}
    assert history.redo() is None


def test_deep_copy_isolation():
    history = History()
    source = {"items": [1, {"deep": [2]}]}
    history.push(source)
    source["items"].append(99)
    assert history.peek() == {"items": [1, {"deep": [2]}]}

    current = history.peek()
    current["items"][1]["deep"].append(3)
    assert history.peek() == {"items": [1, {"deep": [2]}]}

    returned = history.values()
    returned[0]["items"].append(4)
    assert history.peek() == {"items": [1, {"deep": [2]}]}

    history.push([1, 2])
    undone = history.undo()
    assert undone == {"items": [1, {"deep": [2]}]}
    undone["items"].clear()
    assert history.peek() == {"items": [1, {"deep": [2]}]}


def test_push_after_undo_discards_redo_branch():
    history = History()
    history.push(1)
    history.push(2)
    history.push(3)
    assert history.undo() == 2
    assert history.can_redo is True
    history.push(4)
    assert history.values() == [1, 2, 4]
    assert history.peek() == 4
    assert history.can_redo is False
    assert history.redo() is None


def test_capacity_drops_oldest_and_repairs_index():
    history = History(capacity=3)
    for value in range(1, 5):
        history.push(value)
    assert len(history) == 3
    assert history.values() == [2, 3, 4]
    assert history.peek() == 4
    assert history.undo() == 3
    assert history.undo() == 2
    assert history.undo() is None
    assert history.redo() == 3
    assert history.redo() == 4
    assert history.redo() is None

    single = History(capacity=1)
    single.push(1)
    single.push(2)
    assert single.values() == [2]
    assert single.peek() == 2
    assert single.can_undo is False
    assert single.undo() is None

    for bad in (0, -1):
        with pytest.raises(ValueError, match="positive"):
            History(bad)
    for bad in (True, 1.5, "3"):
        with pytest.raises(TypeError, match="positive integer"):
            History(bad)
    assert History(5).capacity == 5


def test_clear_and_empty_behavior():
    history = History()
    assert history.undo() is None
    assert history.redo() is None
    assert history.peek() is None

    history.push(1)
    history.push(2)
    history.clear()
    assert len(history) == 0
    assert history.values() == []
    assert history.peek() is None
    assert history.can_undo is False
    assert history.can_redo is False
    assert history.undo() is None
    assert history.redo() is None
