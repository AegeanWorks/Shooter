"""Keystone mechanics testbed: scene graph queries, IDs and parenting.

Covers name/tag/layer/component queries, find/by-id lookups, deterministic
ID allocation with duplicate rejection, reparenting/cycle guards,
depth-first traversal order and world-visibility chains.
"""

import pytest

from keystone.scene import Node, Scene, Transform
from keystone.math3d import Vec3


class Health:
    def __init__(self, value=10):
        self.value = value


def test_query_filters_find_and_find_by_id():
    scene = Scene()
    enemy = Node("enemy", tags={"hostile"}, layer="gameplay")
    enemy.add_component(Health(7))
    scene.add(enemy)
    pickup = Node("pickup", tags={"loot"}, layer="items")
    scene.add(pickup)
    elite = Node(
        "enemy", id="enemy-2", tags={"hostile", "elite"}, layer="gameplay"
    )
    scene.add(elite)

    assert [node.id for node in scene.query(name="enemy")] == [
        enemy.id,
        "enemy-2",
    ]
    assert [node.id for node in scene.query(tag="hostile")] == [
        enemy.id,
        "enemy-2",
    ]
    assert [node.id for node in scene.query(layer="items")] == [pickup.id]
    assert [node.id for node in scene.query(component=Health)] == [enemy.id]
    assert [
        node.id
        for node in scene.query(name="enemy", layer="gameplay", tag="elite")
    ] == ["enemy-2"]
    assert scene.query(name="missing") == []
    assert {node.name for node in scene.query()} == {"", "enemy", "pickup"}

    assert scene.find(name="pickup") is pickup
    assert scene.find(tag="elite") is elite
    assert scene.find(name="missing") is None
    assert scene.find_by_id("enemy-2") is elite
    assert scene.find_by_id("missing") is None


def test_id_allocation_rejects_duplicates_and_skips_used():
    scene = Scene()
    first = scene.add(Node("first"))
    second = scene.add(Node("second"))
    assert (first.id, second.id) == ("node-1", "node-2")

    with pytest.raises(ValueError, match="duplicate node id"):
        scene.add(Node("duplicate", id=first.id))
    with pytest.raises(ValueError, match="duplicate node id"):
        scene.add(Node("root-copy", id="root"))

    third = scene.add(Node("third"))
    assert third.id == "node-3"

    sub = Node("sub")
    sub.add_child(Node("child", id="shared"))
    scene.add(sub)
    with pytest.raises(ValueError, match="duplicate node id"):
        scene.add(Node("other", children=[Node("child", id="shared")]))

    explicit = Scene()
    explicit.add(Node("explicit", id="node-1"))
    assert explicit.add(Node("auto")).id == "node-2"


def test_parenting_reparenting_and_cycle_guard():
    scene = Scene()
    parent = scene.add(Node("parent"))
    child_a = Node("child-a")
    child_b = Node("child-b")
    parent.add_child(child_a)
    parent.add_child(child_b)
    grandchild = Node("grandchild")
    child_a.add_child(grandchild)
    sibling = scene.add(Node("sibling"))

    assert parent.children == [child_a, child_b]
    assert child_a.parent is parent and grandchild.parent is child_a
    assert child_a.is_ancestor_of(grandchild) is True
    assert grandchild.is_ancestor_of(parent) is False

    child_a.add_child(child_b)
    assert child_b.parent is child_a
    assert child_b not in parent.children
    assert parent.children == [child_a]

    child_b.add_child(grandchild)
    assert grandchild.parent is child_b
    assert grandchild not in child_a.children

    with pytest.raises(ValueError, match="cycle"):
        grandchild.add_child(parent)
    with pytest.raises(ValueError, match="cycle"):
        parent.add_child(parent)
    with pytest.raises(ValueError, match="cycle"):
        child_b.add_child(parent)

    parent.remove_child(child_a)
    assert child_a.parent is None
    with pytest.raises(ValueError, match="not a child"):
        parent.remove_child(child_a)

    attached = Node("attached", parent=parent)
    assert attached in parent.children and attached.parent is parent
    other = Node("other")
    with pytest.raises(ValueError, match="different parent"):
        Node("conflict", children=[attached])
    other.add_child(attached)
    assert attached.parent is other
    assert attached not in parent.children
    assert sibling.parent is scene.root


def test_traversal_order_and_visibility_chain():
    scene = Scene()
    parent = scene.add(Node("parent"))
    child_a = Node("child-a")
    child_b = Node("child-b")
    parent.add_child(child_a)
    parent.add_child(child_b)
    grandchild = Node("grandchild")
    child_a.add_child(grandchild)
    scene.add(Node("sibling"))

    assert [node.name for node in scene.traverse()] == [
        "",
        "parent",
        "child-a",
        "grandchild",
        "child-b",
        "sibling",
    ]

    assert parent.world_visible() is True
    parent.visible = False
    assert parent.world_visible() is False
    assert child_a.world_visible() is False
    assert grandchild.world_visible() is False
    assert scene.find(name="sibling").world_visible() is True
    assert [node.name for node in scene.traverse()][1] == "parent"

    parent.visible = True
    child_a.visible = False
    assert child_a.world_visible() is False
    assert grandchild.world_visible() is False
    assert child_b.world_visible() is True
    child_a.visible = True
    assert grandchild.world_visible() is True


def test_restore_next_id_and_id_preservation():
    scene = Scene()
    scene.restore_next_id(10)
    assert scene.add(Node("ten")).id == "node-10"
    scene.restore_next_id(1)
    assert scene.add(Node("eleven")).id == "node-11"

    for bad in (0, -1, True, "3"):
        with pytest.raises(ValueError, match="positive integer"):
            scene.restore_next_id(bad)

    explicit = Scene()
    explicit.add(Node("explicit", id="node-1"))
    assert explicit.add(Node("auto")).id == "node-2"
    assert explicit.find_by_id("node-1").name == "explicit"
