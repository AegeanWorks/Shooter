"""Keystone mechanics testbed: CPU instancing grouping and plans.

Covers shared mesh/material grouping, frustum-plane skips, stable group
and node ordering, JSON-safe plan counts/savings and skinned conservatism.
"""

import json

import pytest

from keystone.culling import extract_planes
from keystone.geometry import Material, MeshData
from keystone.gpu.instancing import group_instances, plan_instanced
from keystone.math3d import Vec3
from keystone.primitives import cube
from keystone.scene import Node, Scene, Transform

IDENTITY_16 = (
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0,
)


def _skinned_triangle():
    return MeshData(
        positions=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        normals=((0.0, 0.0, 1.0),) * 3,
        indices=(0, 1, 2),
        joints=((0,),) * 3,
        weights=((1.0,),) * 3,
        skin_joints=("j0",),
        skin_inverse_bind=(IDENTITY_16,),
    )


def _shared_scene():
    mesh = cube(1.0)
    material = Material()
    scene = Scene()
    for name, x in (("a", -1.0), ("b", 0.0), ("c", 1.0)):
        scene.add(
            Node(
                name,
                id=name,
                transform=Transform(position=Vec3(x, 0.0, -5.0)),
                mesh=mesh,
                material=material if name != "c" else Material(color=Vec3(1.0, 0.0, 0.0)),
            )
        )
    scene.add(
        Node(
            "d",
            id="d",
            transform=Transform(position=Vec3(0.0, 0.0, 5.0)),
            mesh=mesh,
            material=material,
        )
    )
    scene.add(
        Node(
            "hidden",
            id="hidden",
            transform=Transform(position=Vec3(0.0, 0.0, -5.0)),
            mesh=mesh,
            visible=False,
        )
    )
    scene.add(Node("nom", id="nom"))
    return scene, mesh, material


def test_group_instances_shared_payloads_and_materials():
    scene, mesh, material = _shared_scene()
    groups = group_instances(scene)
    assert len(groups) == 2
    assert groups[0]["node_keys"] == ["a", "b", "d"]
    assert len(groups[0]["nodes"]) == 3
    assert groups[0]["mesh"] is mesh
    assert groups[0]["material"] is material
    assert groups[0]["triangles"] == 36
    assert groups[1]["node_keys"] == ["c"]
    assert len(groups[1]["nodes"]) == 1
    assert groups[1]["material"] is not material
    assert groups[1]["triangles"] == 12
    assert all(
        [node.id for node in group["nodes"]] == group["node_keys"]
        for group in groups
    )
    assert all(
        len(group["models"]) == len(group["nodes"]) for group in groups
    )
    assert "hidden" not in {key for group in groups for key in group["node_keys"]}
    assert "nom" not in {key for group in groups for key in group["node_keys"]}


def test_group_instances_respects_frustum_planes():
    scene, _, _ = _shared_scene()
    planes = extract_planes(scene.camera.view_projection(960 / 540))
    culled = group_instances(scene, planes)
    assert [group["node_keys"] for group in culled] == [
        ["a", "b"],
        ["c"],
    ]
    assert [group["node_keys"] for group in group_instances(scene)] == [
        ["a", "b", "d"],
        ["c"],
    ]


def test_group_ordering_is_deterministic():
    scene = Scene()
    for name in ("a2", "a1"):
        scene.add(Node(name, id=name, mesh=cube(1.0)))
    for name in ("b3", "b1", "b2"):
        scene.add(Node(name, id=name, mesh=cube(1.0)))
    # A distinct material is what splits a group now that grouping is keyed on
    # content digests rather than object identity: every cube(1.0) is the same
    # mesh content, so only the material can separate the last three nodes.
    accent = Material(color=Vec3(1.0, 0.0, 0.0))
    for name in ("c1", "d1", "e1"):
        scene.add(Node(name, id=name, mesh=cube(1.0), material=accent))
    first = [group["node_keys"] for group in group_instances(scene)]
    second = [group["node_keys"] for group in group_instances(scene)]
    assert first == second
    assert first == [
        ["a1", "a2", "b1", "b2", "b3"],
        ["c1", "d1", "e1"],
    ]


def test_plan_instanced_counts_and_savings():
    scene, _, _ = _shared_scene()
    plan = plan_instanced(scene)
    assert plan["schema"] == 1
    assert plan["groups"] == 2
    assert plan["draw_calls"] == 4
    assert plan["instanced_calls"] == 1
    assert plan["saved_calls"] == 2
    assert plan["instances"] == 3
    assert plan["triangles"] == 48
    assert len(plan["batches"]) == 2
    batch = plan["batches"][0]
    assert batch["nodes"] == ["a", "b", "d"]
    assert batch["count"] == 3
    assert batch["triangles"] == 36
    assert len(batch["matrices"]) == 3
    assert all(len(matrix) == 16 for matrix in batch["matrices"])
    assert json.loads(json.dumps(plan)) == plan

    empty = plan_instanced(Scene())
    assert empty == {
        "schema": 1,
        "groups": 0,
        "draw_calls": 0,
        "instanced_calls": 0,
        "saved_calls": 0,
        "instances": 0,
        "triangles": 0,
        "batches": [],
        "overlay_calls": 0,
    }


def test_skinned_groups_do_not_report_savings():
    skinned = _skinned_triangle()
    scene = Scene()
    scene.add(Node("s1", id="s1", mesh=skinned))
    scene.add(Node("s2", id="s2", mesh=skinned))
    plan = plan_instanced(scene)
    assert plan["groups"] == 1
    assert plan["draw_calls"] == 2
    assert plan["instanced_calls"] == 0
    assert plan["saved_calls"] == 0
    assert plan["instances"] == 0
    assert plan["triangles"] == 2

    plain = cube(1.0)
    scene.add(Node("p1", id="p1", mesh=plain))
    scene.add(Node("p2", id="p2", mesh=plain))
    mixed = plan_instanced(scene)
    assert mixed["groups"] == 2
    assert mixed["draw_calls"] == 4
    assert mixed["instanced_calls"] == 1
    assert mixed["saved_calls"] == 1
    assert mixed["instances"] == 2
    assert mixed["triangles"] == 26
