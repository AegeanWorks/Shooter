"""Keystone mechanics testbed: procedural primitive geometry.

Covers cube face winding/UVs, plane layout, cone and cylinder side/cap
normals, sphere radial normals/UVs and the argument guards on every
primitive.
"""

import pytest

from keystone.math3d import Vec3
from keystone.primitives import cone, cube, cylinder, plane, sphere

CUBE_NORMALS = (
    (1.0, 0.0, 0.0),
    (-1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, -1.0, 0.0),
    (0.0, 0.0, 1.0),
    (0.0, 0.0, -1.0),
)


def test_cube_face_winding_uvs_and_bounds():
    mesh = cube(2.0)
    assert len(mesh.positions) == 24
    assert len(mesh.indices) == 36
    assert mesh.triangle_count() == 12
    assert mesh.bounds() == ((-1.0, -1.0, -1.0), (1.0, 1.0, 1.0))
    assert [mesh.normals[index * 4] for index in range(6)] == list(
        CUBE_NORMALS
    )
    assert mesh.uvs[:4] == ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))

    for face in range(6):
        base = face * 4
        p0, p1, p2 = (
            Vec3(*mesh.positions[base + offset]) for offset in range(3)
        )
        winding = (p1 - p0).cross(p2 - p0).normalized()
        expected = CUBE_NORMALS[face]
        assert (winding.x, winding.y, winding.z) == pytest.approx(
            expected, abs=1e-9
        )

    with pytest.raises(ValueError, match="positive"):
        cube(0.0)


def test_plane_bounds_normals_and_uvs():
    mesh = plane(4.0)
    assert len(mesh.positions) == 4
    assert mesh.indices == (0, 1, 2, 0, 2, 3)
    assert mesh.triangle_count() == 2
    assert mesh.bounds() == ((-2.0, 0.0, -2.0), (2.0, 0.0, 2.0))
    assert mesh.normals == ((0.0, 1.0, 0.0),) * 4
    assert mesh.uvs == ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))

    with pytest.raises(ValueError, match="positive"):
        plane(-1.0)


def test_cone_side_and_base_normals():
    mesh = cone(radius=1.0, height=2.0, segments=8)
    assert len(mesh.positions) == 48
    assert len(mesh.indices) == 48
    assert mesh.triangle_count() == 16
    assert mesh.bounds() == ((-1.0, -1.0, -1.0), (1.0, 1.0, 1.0))

    side_normals = mesh.normals[: 8 * 3]
    for index in range(0, len(side_normals), 3):
        normal = Vec3(*side_normals[index])
        point = Vec3(*mesh.positions[index])
        assert normal.length() == pytest.approx(1.0)
        radial = Vec3(normal.x, 0.0, normal.z).dot(
            Vec3(point.x, 0.0, point.z).normalized()
        )
        assert radial > 0.0
        assert normal.y > 0.0
    assert set(mesh.normals[8 * 3 :]) == {(0.0, -1.0, 0.0)}
    assert any(position[1] == 1.0 for position in mesh.positions)
    assert any(position[1] == -1.0 for position in mesh.positions)

    with pytest.raises(ValueError, match="positive"):
        cone(0.0, 1.0)
    with pytest.raises(ValueError, match="positive"):
        cone(1.0, 0.0)
    with pytest.raises(ValueError, match="at least 3"):
        cone(1.0, 1.0, 2)


def test_cylinder_side_and_cap_normals():
    mesh = cylinder(radius=1.0, height=2.0, segments=8)
    assert len(mesh.positions) == 50
    assert len(mesh.indices) == 96
    assert mesh.triangle_count() == 32
    assert mesh.bounds() == ((-1.0, -1.0, -1.0), (1.0, 1.0, 1.0))

    for index in range(0, 32, 4):
        normal = Vec3(*mesh.normals[index])
        point = Vec3(*mesh.positions[index])
        assert normal.y == 0.0
        assert normal.length() == pytest.approx(1.0)
        assert Vec3(normal.x, 0.0, normal.z).dot(
            Vec3(point.x, 0.0, point.z).normalized()
        ) == pytest.approx(1.0)
    assert set(mesh.normals[32:41]) == {(0.0, 1.0, 0.0)}
    assert set(mesh.normals[41:]) == {(0.0, -1.0, 0.0)}
    assert (0.0, 1.0, 0.0) in mesh.positions
    assert (0.0, -1.0, 0.0) in mesh.positions

    with pytest.raises(ValueError, match="positive"):
        cylinder(0.0, 1.0)
    with pytest.raises(ValueError, match="at least 3"):
        cylinder(1.0, 1.0, 2)


def test_sphere_radial_normals_and_uv_range():
    mesh = sphere(radius=2.0, segments=8, rings=4)
    assert len(mesh.positions) == 45
    assert len(mesh.indices) == 192
    assert mesh.triangle_count() == 64
    assert mesh.bounds() == ((-2.0, -2.0, -2.0), (2.0, 2.0, 2.0))

    for position, normal in zip(mesh.positions, mesh.normals):
        assert Vec3(*normal).length() == pytest.approx(1.0)
        assert Vec3(*normal) == pytest.approx(
            Vec3(*position) / 2.0, abs=1e-9
        )
    assert min(u for u, _ in mesh.uvs) == 0.0
    assert max(u for u, _ in mesh.uvs) == 1.0
    assert min(v for _, v in mesh.uvs) == 0.0
    assert max(v for _, v in mesh.uvs) == 1.0

    with pytest.raises(ValueError, match="positive"):
        sphere(0.0)
    with pytest.raises(ValueError, match="at least 3"):
        sphere(1.0, 2, 4)
    with pytest.raises(ValueError, match="at least 3"):
        sphere(1.0, 8, 1)
