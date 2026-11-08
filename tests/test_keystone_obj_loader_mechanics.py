"""Keystone mechanics testbed: Wavefront OBJ loading.

Covers explicit/generated normals, UVs, negative indices, quad fan
triangulation, homogeneous vertices, ignored directives, BOM files and
malformed-input errors.
"""

import pytest

from keystone.obj_loader import load_obj, parse_obj


def test_parse_obj_triangle_with_uvs_and_normals():
    mesh = parse_obj(
        """v 0 0 0
v 1 0 0
v 0 1 0
vt 0 0
vt 1 0
vt 0 1
vn 0 0 1
f 1/1/1 2/2/1 3/3/1
"""
    )
    assert len(mesh.positions) == 3
    assert len(mesh.normals) == 3
    assert len(mesh.uvs) == 3
    assert mesh.indices == (0, 1, 2)
    assert mesh.triangle_count() == 1
    assert mesh.bounds() == ((0.0, 0.0, 0.0), (1.0, 1.0, 0.0))
    assert mesh.normals == ((0.0, 0.0, 1.0),) * 3
    assert mesh.uvs == ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0))

    flat = parse_obj(
        """v 0 0 0
v 1 0 0
v 0 1 0
vt 0 0
vt 1 0
vt 0 1
f 1/1 2/2 3/3
"""
    )
    assert flat.normals == ((0.0, 0.0, 1.0),) * 3
    assert flat.uvs == ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0))

    no_uv = parse_obj(
        """v 0 0 0
v 1 0 0
v 0 1 0
vn 0 0 1
f 1//1 2//1 3//1
"""
    )
    assert no_uv.normals == ((0.0, 0.0, 1.0),) * 3
    assert no_uv.uvs == ((0.0, 0.0), (0.0, 0.0), (0.0, 0.0))


def test_parse_obj_negative_indices_and_quad_fan():
    mesh = parse_obj(
        """v 0 0 0
v 1 0 0
v 1 1 0
v 0 1 0
f -4 -3 -2 -1
"""
    )
    assert len(mesh.positions) == 4
    assert mesh.indices == (0, 1, 2, 0, 2, 3)
    assert mesh.triangle_count() == 2
    assert mesh.bounds() == ((0.0, 0.0, 0.0), (1.0, 1.0, 0.0))
    assert mesh.normals == ((0.0, 0.0, 1.0),) * 4
    assert mesh.uvs == ((0.0, 0.0),) * 4


def test_parse_obj_homogeneous_vertices_and_directives():
    mesh = parse_obj(
        """# comment
o object
g group
usemtl material
mtllib library
s off
v 2 4 6 2
v 1 0 0
v 0 1 0
f 1 2 3
"""
    )
    assert mesh.bounds() == ((0.0, 0.0, 0.0), (1.0, 2.0, 3.0))
    assert mesh.triangle_count() == 1

    with pytest.raises(ValueError, match="weight"):
        parse_obj(
            """v 1 2 3 0
v 1 0 0
v 0 1 0
f 1 2 3
"""
        )


def test_load_obj_file_bom_and_missing(tmp_path):
    path = tmp_path / "mesh.obj"
    path.write_bytes(
        b"\xef\xbb\xbfv 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n"
    )
    mesh = load_obj(path)
    assert mesh.triangle_count() == 1
    assert len(mesh.positions) == 3

    with pytest.raises(FileNotFoundError):
        load_obj(tmp_path / "missing.obj")


def test_obj_validation_errors():
    with pytest.raises(ValueError, match="no faces"):
        parse_obj("v 0 0 0\n")
    with pytest.raises(ValueError, match="at least three"):
        parse_obj("v 0 0 0\nv 1 0 0\nf 1 2\n")
    with pytest.raises(ValueError, match="index 0"):
        parse_obj("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 0 1 2\n")
    with pytest.raises(ValueError, match="outside"):
        parse_obj("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 9\n")
    with pytest.raises(ValueError, match="bad face corner"):
        parse_obj("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1/1/1/1 2 3\n")
    with pytest.raises(ValueError, match="could not convert"):
        parse_obj("v x 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
