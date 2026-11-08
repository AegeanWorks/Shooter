"""Keystone mechanics testbed: MeshBuilder composition and skin merging.

Covers quad/box counts and bounds, mesh scaling/translation/color merges,
inverse-transpose normals under matrix transforms, skinned concatenation
agreement rules and plain-vs-skin mode isolation.
"""

import math

import pytest

from keystone.geometry import MeshData
from keystone.math3d import Mat4, Vec3
from keystone.mesh_builder import MeshBuilder
from keystone.primitives import cube, plane

IDENTITY_16 = (
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0,
)


def _skinned_quad(offset=0.0, bind=IDENTITY_16, joints=("j0",)):
    positions = (
        (offset, 0.0, 0.0),
        (offset + 1.0, 0.0, 0.0),
        (offset + 1.0, 1.0, 0.0),
        (offset, 1.0, 0.0),
    )
    return MeshData(
        positions=positions,
        normals=((0.0, 0.0, 1.0),) * 4,
        indices=(0, 1, 2, 0, 2, 3),
        joints=((0,),) * 4,
        weights=((1.0,),) * 4,
        skin_joints=joints,
        skin_inverse_bind=(bind,),
    )


def test_quad_and_box_geometry_counts_and_bounds():
    builder = MeshBuilder()
    assert builder.is_empty() is True
    with pytest.raises(ValueError, match="no geometry"):
        builder.build()

    builder.add_quad(
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (1.0, 1.0, 0.0),
        (0.0, 1.0, 0.0),
        color=(0.2, 0.4, 0.6),
    )
    assert builder.is_empty() is False
    quad = builder.build()
    assert len(quad.positions) == 4
    assert len(quad.normals) == 4
    assert len(quad.uvs) == 4
    assert len(quad.colors) == 4
    assert quad.indices == (0, 1, 2, 0, 2, 3)
    assert quad.triangle_count() == 2
    assert quad.normals[0] == (0.0, 0.0, 1.0)
    assert quad.uvs == ((0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0))
    assert quad.colors[0] == (0.2, 0.4, 0.6)

    box_builder = MeshBuilder()
    box_builder.add_box(0.0, 0.0, 0.0, 2.0, 4.0, 6.0)
    box = box_builder.build()
    assert len(box.positions) == 24
    assert len(box.indices) == 36
    assert box.triangle_count() == 12
    assert box.bounds() == ((-1.0, -2.0, -3.0), (1.0, 2.0, 3.0))

    with pytest.raises(ValueError, match="collinear"):
        MeshBuilder().add_quad(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (3.0, 0.0, 0.0),
        )
    with pytest.raises(ValueError, match="positive"):
        MeshBuilder().add_box(0.0, 0.0, 0.0, 0.0, 1.0, 1.0)


def test_add_mesh_scales_translates_and_multiplies_colors():
    builder = MeshBuilder()
    builder.add_mesh(
        cube(2.0),
        offset=(10.0, 0.0, 0.0),
        scale=2.0,
        color=(0.5, 0.25, 1.0),
    )
    mesh = builder.build()
    assert len(mesh.positions) == 24
    assert len(mesh.indices) == 36
    assert mesh.triangle_count() == 12
    assert mesh.bounds() == ((8.0, -2.0, -2.0), (12.0, 2.0, 2.0))
    assert set(mesh.colors) == {(0.5, 0.25, 1.0)}
    assert all(
        abs(Vec3(*normal).length() - 1.0) < 1e-9 for normal in mesh.normals
    )

    with pytest.raises(ValueError, match="scale must be positive"):
        MeshBuilder().add_mesh(cube(1.0), scale=0.0)


def test_add_mesh_matrix_transforms_positions_and_normals():
    matrix = (
        Mat4.translation(3.0, 0.0, 0.0)
        * Mat4.rotation_x(math.pi / 2.0)
        * Mat4.scale(2.0, 1.0, 1.0)
    )
    builder = MeshBuilder()
    builder.add_mesh_matrix(plane(2.0), matrix, color=(1.0, 2.0, 3.0))
    mesh = builder.build()
    low, high = mesh.bounds()
    assert (low[0], low[1], high[0], high[1]) == pytest.approx(
        (1.0, -1.0, 5.0, 1.0)
    )
    assert abs(low[2]) < 1e-9 and abs(high[2]) < 1e-9
    assert len(mesh.positions) == 4
    assert mesh.colors[0] == (1.0, 2.0, 3.0)
    normal = Vec3(*mesh.normals[0])
    assert normal.length() == pytest.approx(1.0)
    assert (normal.x, normal.y, normal.z) == pytest.approx(
        (0.0, 0.0, 1.0), abs=1e-9
    )
    p0 = Vec3(*mesh.positions[0])
    edge_a = (Vec3(*mesh.positions[1]) - p0).normalized()
    edge_b = (Vec3(*mesh.positions[2]) - p0).normalized()
    assert normal.dot(edge_a) == pytest.approx(0.0, abs=1e-9)
    assert normal.dot(edge_b) == pytest.approx(0.0, abs=1e-9)

    with pytest.raises(TypeError, match="Mat4"):
        MeshBuilder().add_mesh_matrix(plane(1.0), matrix.m)


def test_skinned_mesh_concat_and_agreement_rules():
    builder = MeshBuilder()
    builder.add_skinned_mesh(_skinned_quad(0.0))
    builder.add_skinned_mesh(_skinned_quad(2.0))
    mesh = builder.build()
    assert mesh.skinned is True
    assert len(mesh.positions) == 8
    assert len(mesh.joints) == 8
    assert len(mesh.weights) == 8
    assert len(mesh.indices) == 12
    assert mesh.triangle_count() == 4
    assert mesh.skin_joints == ("j0",)
    assert mesh.bounds() == ((0.0, 0.0, 0.0), (3.0, 1.0, 0.0))

    with pytest.raises(ValueError, match="joint-name list"):
        MeshBuilder().add_skinned_mesh(_skinned_quad(joints=("j0",))).add_skinned_mesh(
            _skinned_quad(joints=("j1",))
        )
    other_bind = (2.0, 0.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0,
                  0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 0.0, 1.0)
    with pytest.raises(ValueError, match="inverse bind"):
        MeshBuilder().add_skinned_mesh(_skinned_quad()).add_skinned_mesh(
            _skinned_quad(bind=other_bind)
        )
    with pytest.raises(ValueError, match="needs a skinned"):
        MeshBuilder().add_skinned_mesh(cube(1.0))


def test_plain_and_skin_modes_cannot_mix():
    plain = MeshBuilder()
    plain.add_quad(
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)
    )
    plain.add_box(0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
    plain.add_mesh(cube(1.0))
    mesh = plain.build()
    assert mesh.skinned is False
    assert len(mesh.positions) == 52
    assert len(mesh.indices) == 78
    assert mesh.triangle_count() == 26

    with pytest.raises(ValueError, match="cannot mix plain and skin"):
        MeshBuilder().add_quad(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
        ).add_skinned_mesh(_skinned_quad())
    with pytest.raises(ValueError, match="cannot mix skin and plain"):
        MeshBuilder().add_skinned_mesh(_skinned_quad()).add_box(
            0.0, 0.0, 0.0, 1.0, 1.0, 1.0
        )
