"""Keystone mechanics testbed: static/skinned batch planning and merging.

Covers static grouping by mesh/material, skinned keying by joints/binds/
world, world-space material merges, exclude-by-id/name, empty summaries and
plan/merge count agreement.
"""

import pytest

from keystone.batch import merge_batches, plan_batches
from keystone.geometry import Material, MeshData
from keystone.math3d import Mat4, Vec3
from keystone.primitives import cube
from keystone.scene import Node, Scene, Transform

IDENTITY_16 = (
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0,
)


def _skinned(bind=IDENTITY_16):
    return MeshData(
        positions=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        normals=((0.0, 0.0, 1.0),) * 3,
        indices=(0, 1, 2),
        joints=((0,),) * 3,
        weights=((1.0,),) * 3,
        skin_joints=("j0",),
        skin_inverse_bind=(bind,),
    )


def test_plan_batches_groups_static_by_mesh_and_material():
    scene = Scene()
    shared = cube(1.0)
    material = Material()
    for index, name in enumerate(("a", "b", "c")):
        scene.add(
            Node(
                name,
                id=name,
                transform=Transform(position=Vec3(index * 2.0 - 2.0, 0.0, 0.0)),
                mesh=shared,
                material=material,
            )
        )
    scene.add(Node("d", id="d", mesh=shared, material=Material()))
    scene.add(Node("hidden", id="hidden", mesh=shared, visible=False))
    scene.add(Node("nom", id="nom"))

    plan = plan_batches(scene)
    assert plan["schema"] == 1
    assert plan["groups"] == 2
    assert plan["draw_calls"] == 4
    assert plan["batched_calls"] == 2
    assert plan["saved_calls"] == 2
    assert plan["triangles"] == 48
    assert plan["batches"] == [
        {"nodes": ["a", "b", "c"], "count": 3, "triangles": 36},
        {"nodes": ["d"], "count": 1, "triangles": 12},
    ]
    assert plan["skin_groups"] == 0
    assert plan["skin_calls"] == 0
    assert plan["skin_triangles"] == 0

    empty = plan_batches(Scene())
    assert empty == {
        "schema": 1,
        "groups": 0,
        "draw_calls": 0,
        "batched_calls": 0,
        "saved_calls": 0,
        "triangles": 0,
        "batches": [],
        "skin_groups": 0,
        "skin_calls": 0,
        "skin_triangles": 0,
    }


def test_plan_batches_skinned_keying():
    scene = Scene()
    mesh = _skinned()
    material = Material()
    scene.add(Node("s1", id="s1", mesh=mesh, material=material))
    scene.add(Node("s2", id="s2", mesh=mesh, material=material))
    scene.add(
        Node(
            "s3",
            id="s3",
            transform=Transform(position=Vec3(1.0, 0.0, 0.0)),
            mesh=mesh,
            material=material,
        )
    )
    other_bind = (2.0, 0.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0,
                  0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 0.0, 1.0)
    scene.add(
        Node("s4", id="s4", mesh=_skinned(other_bind), material=material)
    )
    scene.add(
        Node(
            "hidden",
            id="hidden",
            mesh=mesh,
            material=material,
            visible=False,
        )
    )

    plan = plan_batches(scene)
    assert plan["groups"] == 0
    assert plan["draw_calls"] == 0
    assert plan["skin_groups"] == 3
    assert plan["skin_calls"] == 4
    assert plan["skin_triangles"] == 4


def test_merge_batches_static_world_space_and_exclude():
    scene = Scene()
    material = Material()
    for index, name in enumerate(("a", "b", "c")):
        scene.add(
            Node(
                name,
                id=name,
                transform=Transform(position=Vec3(index * 2.0 - 2.0, 0.0, 0.0)),
                mesh=cube(1.0),
                material=material,
            )
        )
    merged = merge_batches(scene)
    assert merged["schema"] == 1
    assert merged["groups"] == 1
    assert merged["merged_calls"] == 1
    assert merged["saved_calls"] == 2
    assert merged["triangles"] == 36
    assert merged["skin_merged_calls"] == 0
    assert merged["skin_saved_calls"] == 0
    assert len(merged["merged"]) == 1
    group = merged["merged"][0]
    assert group["nodes"] == ["a", "b", "c"]
    assert group["count"] == 3
    assert group["triangles"] == 36
    assert group["mesh"].bounds() == ((-2.5, -0.5, -0.5), (2.5, 0.5, 0.5))
    assert merged["plan"]["groups"] == 3
    assert merged["plan"]["draw_calls"] == 3
    assert merged["plan"]["saved_calls"] == 0
    assert [node.name for node in scene.traverse()] == ["", "a", "b", "c"]
    assert all(node.mesh.triangle_count() == 12 for node in scene.traverse() if node.mesh)

    by_id = merge_batches(scene, exclude={"a"})
    assert by_id["merged"][0]["nodes"] == ["b", "c"]
    assert by_id["saved_calls"] == 1
    by_name = merge_batches(scene, exclude={"b"})
    assert by_name["merged"][0]["nodes"] == ["a", "c"]
    with pytest.raises(TypeError, match="not a string"):
        merge_batches(scene, exclude="a")


def test_merge_batches_skinned_world_and_bind_agreement():
    scene = Scene()
    mesh = _skinned()
    material = Material()
    scene.add(Node("s1", id="s1", mesh=mesh, material=material))
    scene.add(Node("s2", id="s2", mesh=mesh, material=material))
    scene.add(
        Node(
            "s3",
            id="s3",
            transform=Transform(position=Vec3(1.0, 0.0, 0.0)),
            mesh=mesh,
            material=material,
        )
    )
    merged = merge_batches(scene)
    assert merged["groups"] == 2
    assert merged["merged_calls"] == 2
    assert merged["saved_calls"] == 0
    assert merged["triangles"] == 3
    assert merged["skin_merged_calls"] == 2
    assert merged["skin_saved_calls"] == 1
    groups = {tuple(group["nodes"]): group for group in merged["merged"]}
    assert set(groups) == {("s1", "s2"), ("s3",)}
    pair = groups[("s1", "s2")]
    assert pair["count"] == 2
    assert pair["mesh"].skinned is True
    assert pair["triangles"] == 2
    assert len(pair["world"]) == 16
    assert pair["world"] == Mat4.identity().flat()

    other_bind = (2.0, 0.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0,
                  0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 0.0, 1.0)
    scene.add(
        Node("s4", id="s4", mesh=_skinned(other_bind), material=material)
    )
    split = merge_batches(scene)
    assert split["skin_merged_calls"] == 3
    assert split["skin_saved_calls"] == 1


def test_merge_and_plan_summary_invariants():
    scene = Scene()
    material = Material()
    shared = cube(1.0)
    scene.add(Node("a", id="a", mesh=shared, material=material))
    scene.add(Node("b", id="b", mesh=shared, material=material))
    skinned = _skinned()
    scene.add(Node("s1", id="s1", mesh=skinned, material=material))
    scene.add(Node("s2", id="s2", mesh=skinned, material=material))

    plan = plan_batches(scene)
    merged = merge_batches(scene)
    assert merged["plan"] == plan
    assert sum(batch["count"] for batch in plan["batches"]) == plan["draw_calls"]
    assert sum(item["triangles"] for item in merged["merged"]) == merged["triangles"]
    assert merged["groups"] == merged["merged_calls"] == 2
    assert merged["saved_calls"] == 1
    assert merged["triangles"] == 26
    assert merged["skin_merged_calls"] == 1
    assert merged["skin_saved_calls"] == 1
    assert all(
        item["nodes"] == sorted(item["nodes"]) for item in merged["merged"]
    )

    empty = merge_batches(Scene())
    assert empty["groups"] == 0
    assert empty["merged_calls"] == 0
    assert empty["saved_calls"] == 0
    assert empty["triangles"] == 0
    assert empty["merged"] == []
    assert empty["skin_merged_calls"] == 0
    assert empty["skin_saved_calls"] == 0
    assert empty["plan"] == plan_batches(Scene())
