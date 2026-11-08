"""Keystone mechanics testbed: perspective camera and CPU frustum culling.

Covers orientation/clamping, projection bounds and aspect handling, frustum
plane/AABB math, and scene culling through nested transforms, invisible
parents and conservative skinned meshes. All math is CPU-only.
"""

import math

import pytest

from keystone.camera import MAX_PITCH, PerspectiveCamera
from keystone.culling import (
    aabb_visible,
    cull_scene,
    culling_enabled,
    extract_planes,
    node_visible,
    world_bounds,
)
from keystone.geometry import MeshData
from keystone.math3d import Mat4, Vec3
from keystone.primitives import cube
from keystone.scene import CullingSettings, Node, Scene, Transform

IDENTITY_16 = (
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0,
)
UNIT_BOX = (
    (1.0, 0.0, 0.0, 1.0),
    (-1.0, 0.0, 0.0, 1.0),
    (0.0, 1.0, 0.0, 1.0),
    (0.0, -1.0, 0.0, 1.0),
    (0.0, 0.0, 1.0, 1.0),
    (0.0, 0.0, -1.0, 1.0),
)


def _skinned_quad():
    positions = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0))
    normals = ((0.0, 0.0, 1.0),) * 4
    return MeshData(
        positions=positions,
        normals=normals,
        indices=(0, 1, 2, 0, 2, 3),
        joints=((0,),) * 4,
        weights=((1.0,),) * 4,
        skin_joints=("j0",),
        skin_inverse_bind=(IDENTITY_16,),
    )


def _cube_scene():
    scene = Scene()
    mesh = cube(1.0)
    scene.add(
        Node("front", transform=Transform(position=Vec3(0.0, 0.0, -5.0)), mesh=mesh)
    )
    scene.add(
        Node("behind", transform=Transform(position=Vec3(0.0, 0.0, 5.0)), mesh=mesh)
    )
    scene.add(
        Node(
            "far-left",
            transform=Transform(position=Vec3(-30.0, 0.0, -5.0)),
            mesh=mesh,
        )
    )
    return scene


def _visible_names(scene, width=960, height=540):
    visible = cull_scene(scene, width, height)
    return {node.name for node in scene.traverse() if id(node) in visible and node.name}


def test_camera_orientation_look_at_and_clamping():
    camera = PerspectiveCamera()
    assert camera.forward() == Vec3(0.0, 0.0, -1.0)
    assert camera.right() == Vec3(1.0, 0.0, 0.0)

    camera.look_at(Vec3(10.0, 0.0, 0.0))
    assert camera.yaw == pytest.approx(math.pi / 2)
    assert camera.pitch == pytest.approx(0.0)
    assert camera.forward().x == pytest.approx(1.0)

    camera.look_at(Vec3(0.0, 100.0, -1.0))
    assert camera.pitch == pytest.approx(MAX_PITCH)
    assert camera.forward().y == pytest.approx(math.sin(MAX_PITCH))
    assert camera.forward().z == pytest.approx(-math.cos(MAX_PITCH))

    with pytest.raises(ValueError, match="own position"):
        camera.look_at(camera.position)

    camera.yaw = 0.0
    camera.rotate(-0.25, 0.0)
    assert camera.yaw == pytest.approx(math.tau - 0.25)
    camera.rotate(0.0, 100.0)
    assert camera.pitch == pytest.approx(MAX_PITCH)
    camera.rotate(0.0, -100.0)
    assert camera.pitch == pytest.approx(-MAX_PITCH)


def test_camera_projection_edges_and_fly_movement():
    aspect = 16 / 9
    camera = PerspectiveCamera()
    centre = camera.view_projection(aspect).project_point(Vec3(0.0, 0.0, -5.0))
    assert centre.x == pytest.approx(0.0)
    assert centre.y == pytest.approx(0.0)
    assert -1.0 < centre.z < 1.0

    half_height = 5.0 * math.tan(math.radians(camera.fov_y) / 2.0)
    right_edge = camera.view_projection(aspect).project_point(
        Vec3(half_height * aspect, 0.0, -5.0)
    )
    top_edge = camera.view_projection(aspect).project_point(
        Vec3(0.0, half_height, -5.0)
    )
    assert right_edge.x == pytest.approx(1.0)
    assert top_edge.y == pytest.approx(1.0)

    near = camera.view_projection(aspect).project_point(
        Vec3(0.0, 0.0, -camera.near)
    )
    far = camera.view_projection(aspect).project_point(
        Vec3(0.0, 0.0, -camera.far)
    )
    assert near.z == pytest.approx(-1.0, abs=1e-6)
    assert far.z == pytest.approx(1.0, abs=1e-6)

    with pytest.raises(ValueError):
        camera.view_projection(0.0)

    camera.rotate(math.pi / 2, 0.0)
    camera.move(2.0, 3.0, 1.0)
    assert camera.position == Vec3(2.0, 1.0, 3.0)


def test_frustum_plane_and_aabb_contract():
    camera = PerspectiveCamera()
    first = extract_planes(camera.view_projection(16 / 9))
    second = extract_planes(camera.view_projection(16 / 9))
    assert len(first) == 6
    assert first == second

    assert aabb_visible(Vec3(1.0, -0.5, -0.5), Vec3(2.0, 0.5, 0.5), UNIT_BOX)
    assert aabb_visible(Vec3(-0.5, -0.5, -0.5), Vec3(0.5, 0.5, 0.5), UNIT_BOX)
    assert not aabb_visible(Vec3(1.5, -0.5, -0.5), Vec3(2.5, 0.5, 0.5), UNIT_BOX)

    with pytest.raises(ValueError, match="degenerate"):
        extract_planes(Mat4((0.0,) * 16))

    mesh = cube(2.0)
    low, high = world_bounds(mesh, Mat4.translation(10.0, 0.0, 0.0))
    assert low.x == pytest.approx(9.0)
    assert high.x == pytest.approx(11.0)
    scaled_low, scaled_high = world_bounds(mesh, Mat4.scale(2.0, 1.0, 1.0))
    assert scaled_low.x == pytest.approx(-2.0)
    assert scaled_high.x == pytest.approx(2.0)


def test_cull_scene_keeps_front_and_respects_aspect():
    scene = _cube_scene()
    planes = extract_planes(scene.camera.view_projection(16 / 9))
    by_name = {node.name: node for node in scene.traverse() if node.name}
    assert node_visible(by_name["front"], planes)
    assert not node_visible(by_name["behind"], planes)
    assert not node_visible(by_name["far-left"], planes)
    assert _visible_names(scene) == {"front"}

    edge = Node(
        "edge",
        transform=Transform(position=Vec3(20.0, 0.0, -5.0)),
        mesh=cube(1.0),
    )
    scene.add(edge)
    assert "edge" not in _visible_names(scene, 100, 100)
    assert "edge" in _visible_names(scene, 1000, 100)

    with pytest.raises(ValueError):
        cull_scene(scene, 0, 540)


def test_nested_hidden_and_skinned_culling():
    parent = Node("parent", transform=Transform(position=Vec3(0.0, 0.0, -5.0)))
    child = Node("child", mesh=cube(1.0))
    parent.add_child(child)
    scene = Scene()
    scene.add(parent)
    planes = extract_planes(scene.camera.view_projection(16 / 9))
    assert node_visible(child, planes)
    low, high = world_bounds(child.mesh, child.world_matrix())
    assert (low.z, high.z) == pytest.approx((-5.5, -4.5))

    parent.transform = Transform(position=Vec3(0.0, 0.0, 5.0))
    assert not node_visible(child, planes)

    parent.transform = Transform(position=Vec3(0.0, 0.0, -5.0))
    parent.visible = False
    assert child.world_visible() is False
    assert not node_visible(child, planes)
    assert "child" not in _visible_names(scene)

    scene = _cube_scene()
    scene.add(Node("hidden", visible=False, mesh=cube(1.0)))
    scene.culling = CullingSettings(enabled=False)
    assert culling_enabled(scene) is False
    names = _visible_names(scene)
    assert {"behind", "far-left"} <= names
    assert "hidden" not in names

    rig = Node(
        "rig",
        transform=Transform(position=Vec3(0.0, 0.0, 50.0)),
        mesh=_skinned_quad(),
    )
    scene = Scene()
    scene.add(rig)
    planes = extract_planes(scene.camera.view_projection(16 / 9))
    assert node_visible(rig, planes)
    assert _visible_names(scene) == {"rig"}
