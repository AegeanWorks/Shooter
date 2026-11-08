"""Keystone mechanics testbed: skinning, glTF import and sprite math.

Covers CPU linear-blend skinning, a skinned glTF import with joint
palettes, a plain triangle glTF with material/registry import, and the
deterministic point-sprite scale/alpha/billboard math.
"""

import base64
import struct

import pytest

from keystone.assets import AssetRegistry
from keystone.geometry import MeshData
from keystone.gltf import load_gltf
from keystone.gpu.sprites import (
    SPRITE_ATTEN,
    SPRITE_COLOR,
    SPRITE_MAX_SIZE,
    SPRITE_MIN_SIZE,
    billboard_corners,
    soft_alpha,
    sprite_alpha,
    sprite_scale,
)
from keystone.math3d import Mat4, Vec3
from keystone.scene import Node, Scene, Transform
from keystone.skin import bone_matrices, skin_mesh, skin_point

IDENTITY_16 = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)


def _quad_mesh(**overrides) -> MeshData:
    kwargs = {
        "positions": ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)),
        "normals": ((0.0, 0.0, 1.0),) * 4,
        "indices": (0, 1, 2, 0, 2, 3),
        "joints": ((0,),) * 4,
        "weights": ((1.0,),) * 4,
        "skin_joints": ("j0",),
        "skin_inverse_bind": (IDENTITY_16,),
    }
    kwargs.update(overrides)
    return MeshData(**kwargs)


def _data_uri(data: bytes) -> str:
    return "data:application/octet-stream;base64," + base64.b64encode(data).decode("ascii")


def _triangle_gltf(color=(0.2, 0.4, 0.6)) -> dict:
    positions = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    data = struct.pack("<" + "f" * len(positions), *positions)
    return {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "tri", "mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "material": 0}]}],
        "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3"}],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(data), "target": 34962}],
        "buffers": [{"uri": _data_uri(data), "byteLength": len(data)}],
        "materials": [{"pbrMetallicRoughness": {"baseColorFactor": [*color, 1.0], "roughnessFactor": 0.25}}],
    }


def _skinned_gltf() -> dict:
    positions = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    joints = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
    weights = [1.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    indices = [0, 1, 2]
    inverse_bind = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0] * 2
    blob = (
        struct.pack("<9f", *positions)
        + bytes(joints)
        + struct.pack("<12f", *weights)
        + struct.pack("<3H", *indices)
        + struct.pack("<32f", *inverse_bind)
    )
    offset = 0

    def view(length: int) -> dict:
        nonlocal offset
        result = {"buffer": 0, "byteOffset": offset, "byteLength": length}
        offset += length
        return result

    views = [view(36), view(12), view(48), view(6), view(128)]
    return {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0, 1, 2]}],
        "nodes": [
            {"name": "mesh-node", "mesh": 0, "skin": 0},
            {"name": "j0"},
            {"name": "j1", "translation": [1.0, 0.0, 0.0]},
        ],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "JOINTS_0": 1, "WEIGHTS_0": 2}, "indices": 3}]}],
        "skins": [{"joints": [1, 2], "inverseBindMatrices": 4}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 1, "componentType": 5121, "count": 3, "type": "VEC4"},
            {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC4"},
            {"bufferView": 3, "componentType": 5123, "count": 3, "type": "SCALAR"},
            {"bufferView": 4, "componentType": 5126, "count": 2, "type": "MAT4"},
        ],
        "bufferViews": views,
        "buffers": [{"uri": _data_uri(blob), "byteLength": len(blob)}],
    }


def test_skin_point_rigid_blend_and_validation():
    identity = (Mat4.identity(),)
    position, normal = skin_point(
        Vec3(1.0, 0.0, 0.0), Vec3(0.0, 0.0, 1.0), (0,), (1.0,), identity
    )
    assert position == Vec3(1.0, 0.0, 0.0)
    assert normal == Vec3(0.0, 0.0, 1.0)

    translated = (Mat4.translation(2.0, 0.0, 0.0),)
    position, _ = skin_point(
        Vec3(1.0, 0.0, 0.0), Vec3(0.0, 0.0, 1.0), (0,), (1.0,), translated
    )
    assert position.x == 3.0

    blended = (
        Mat4.identity(),
        Mat4.translation(2.0, 0.0, 0.0),
    )
    position, _ = skin_point(
        Vec3(0.0, 0.0, 0.0), Vec3(0.0, 0.0, 1.0), (0, 1), (0.5, 0.5), blended
    )
    assert position.x == 1.0

    with pytest.raises(ValueError):
        skin_point(Vec3(), Vec3(0, 0, 1), (0,), (-1.0,), identity)
    with pytest.raises(ValueError):
        skin_point(Vec3(), Vec3(0, 0, 1), (5,), (1.0,), identity)


def test_skin_mesh_and_bone_palette():
    mesh = _quad_mesh()
    deformed = skin_mesh(mesh, (Mat4.translation(1.0, 0.0, 0.0),))
    assert deformed.skinned is True
    assert deformed.indices == mesh.indices
    assert deformed.positions[0][0] == 1.0

    scene = Scene()
    joint = Node("j0", id="j0")
    joint.transform = Transform(position=Vec3(1.0, 2.0, 3.0))
    scene.add(joint)
    first = bone_matrices(scene, mesh)
    second = bone_matrices(scene, mesh)
    assert first[0].flat() == second[0].flat()
    assert first[0][12] == 1.0
    with pytest.raises(ValueError):
        bone_matrices(Scene(), mesh)


def test_skinned_gltf_import_and_deformation():
    imported = load_gltf(_skinned_gltf())
    node = imported.scene.root.children[0]
    mesh = node.mesh
    assert mesh is not None and mesh.skinned is True
    assert mesh.skin_joints == ("node-1", "node-2")
    assert len(mesh.skin_inverse_bind) == 2
    bones = bone_matrices(imported.scene, mesh)
    assert len(bones) == 2
    assert bones[1][12] == 1.0
    deformed = skin_mesh(mesh, bones)
    assert deformed.positions[1][0] == 1.5


def test_triangle_gltf_material_and_registry():
    registry = AssetRegistry()
    imported = load_gltf(_triangle_gltf(), registry=registry)
    assert imported.node_count == 1
    assert imported.meshes[0].triangle_count() == 1
    assert imported.materials[0].color == Vec3(0.2, 0.4, 0.6)
    assert registry.require("gltf.mesh.0").kind == "mesh"
    assert imported.scene.root.children[0].transform.position == Vec3()


def test_sprite_scale_alpha_and_billboard_math():
    assert SPRITE_ATTEN == 180.0
    assert SPRITE_MAX_SIZE == 64.0
    assert SPRITE_MIN_SIZE == 1.0
    assert SPRITE_COLOR == (1.0, 0.9, 0.7)

    assert sprite_scale(180.0, 1.0) == 1.0
    assert sprite_scale(10.0, 1.0) > sprite_scale(100.0, 1.0)
    assert sprite_scale(0.01, 100.0) == SPRITE_MAX_SIZE
    assert sprite_scale(100000.0, 0.001) == SPRITE_MIN_SIZE
    with pytest.raises(ValueError):
        sprite_scale(float("nan"), 1.0)

    assert soft_alpha(0.5, 0.5) == 1.0
    assert soft_alpha(0.0, 0.0) == 0.0
    assert 0.0 < soft_alpha(0.75, 0.5) < 1.0
    with pytest.raises(ValueError):
        soft_alpha(float("inf"), 0.5)

    assert sprite_alpha(0.0, 1.0) == 1.0
    assert sprite_alpha(1.0, 1.0) == 0.0
    assert sprite_alpha(0.5, 1.0) == 0.5
    with pytest.raises(ValueError):
        sprite_alpha(0.0, 0.0)

    corners = billboard_corners(
        Vec3(1.0, 2.0, 3.0), Vec3(1.0, 0.0, 0.0), Vec3(0.0, 1.0, 0.0), 2.0
    )
    assert len(corners) == 4
    center = Vec3(
        sum(point.x for point in corners) / 4.0,
        sum(point.y for point in corners) / 4.0,
        sum(point.z for point in corners) / 4.0,
    )
    assert center == Vec3(1.0, 2.0, 3.0)
    with pytest.raises(ValueError):
        billboard_corners(Vec3(), Vec3(1, 0, 0), Vec3(0, 1, 0), -1.0)
