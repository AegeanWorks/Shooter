"""Keystone mechanics testbed: glTF source, GLB and accessor decoding.

Covers source variants, GLB container validation, data/file/binary
buffers, accessor normalization/error paths and top-level document checks
with registry side effects.
"""

import base64
import json
import struct
from pathlib import Path

import pytest

from keystone.assets import AssetRegistry
from keystone.gltf import load_gltf
from keystone.gltf.io import (
    _decode_glb,
    decode_data_uri,
    load_buffers,
    read_accessor,
    read_source,
)
from keystone.math3d import Vec3

JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942


def _data_uri(data):
    return "data:application/octet-stream;base64," + base64.b64encode(
        data
    ).decode("ascii")


def _chunk(kind, payload):
    padding = (-len(payload)) % 4
    payload += (b" " if kind == JSON_CHUNK else b"\x00") * padding
    return struct.pack("<II", len(payload), kind) + payload


def _glb(document, binary=None):
    chunks = [_chunk(JSON_CHUNK, json.dumps(document).encode("utf-8"))]
    if binary is not None:
        chunks.append(_chunk(BIN_CHUNK, binary))
    body = b"".join(chunks)
    return struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body


def _triangle_document(uri=True):
    positions = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    data = struct.pack("<9f", *positions)
    document = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "tri", "mesh": 0}],
        "meshes": [
            {"primitives": [{"attributes": {"POSITION": 0}, "material": 0}]}
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": 3,
                "type": "VEC3",
            }
        ],
        "bufferViews": [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": len(data),
                "target": 34962,
            }
        ],
        "buffers": [
            {
                "uri": _data_uri(data) if uri else None,
                "byteLength": len(data),
            }
        ],
        "materials": [
            {
                "pbrMetallicRoughness": {
                    "baseColorFactor": [0.2, 0.4, 0.6, 1.0],
                    "roughnessFactor": 0.25,
                }
            }
        ],
    }
    if not uri:
        del document["buffers"][0]["uri"]
    return document, data


def test_gltf_source_variants(tmp_path):
    document = {"asset": {"version": "2.0"}}
    text, base, binary = read_source(document)
    assert json.loads(text) == document
    assert base == Path.cwd()
    assert binary is None

    assert json.loads(read_source(json.dumps(document))[0]) == document
    assert (
        json.loads(read_source(json.dumps(document).encode("utf-8"))[0])
        == document
    )

    path = tmp_path / "doc.gltf"
    path.write_text(json.dumps(document), encoding="utf-8")
    assert read_source(path)[1] == tmp_path
    assert read_source(str(path))[1] == tmp_path

    glb = _glb(document, b"abcd")
    text, base, binary = read_source(glb)
    assert json.loads(text) == document
    assert base == Path.cwd()
    assert binary[:4] == b"abcd"

    with pytest.raises(TypeError, match="source"):
        read_source(3)
    with pytest.raises(FileNotFoundError):
        read_source(tmp_path / "missing.gltf")


def test_glb_container_validation():
    document = {"asset": {"version": "2.0"}}
    with pytest.raises(ValueError, match="truncated"):
        read_source(b"glTF")
    with pytest.raises(ValueError, match="magic"):
        _decode_glb(struct.pack("<4sII", b"NOPE", 2, 12))
    with pytest.raises(ValueError, match="version"):
        read_source(struct.pack("<4sII", b"glTF", 1, 12))
    with pytest.raises(ValueError, match="declared length"):
        read_source(struct.pack("<4sII", b"glTF", 2, 100))
    with pytest.raises(ValueError, match="chunk header"):
        read_source(struct.pack("<4sII", b"glTF", 2, 16) + b"\x00" * 4)
    with pytest.raises(ValueError, match="past the container"):
        read_source(
            struct.pack("<4sII", b"glTF", 2, 20)
            + struct.pack("<II", 100, JSON_CHUNK)
        )
    bin_chunk = _chunk(BIN_CHUNK, b"abcd")
    with pytest.raises(ValueError, match="missing its JSON"):
        read_source(
            struct.pack("<4sII", b"glTF", 2, 12 + len(bin_chunk))
            + bin_chunk
        )
    duplicate = _chunk(JSON_CHUNK, json.dumps(document).encode("utf-8"))
    body = duplicate + duplicate
    with pytest.raises(ValueError, match="more than one JSON"):
        read_source(
            struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body
        )


def test_load_buffers_data_uri_file_and_glb(tmp_path):
    data = b"\x01\x02\x03"
    assert load_buffers(
        {"buffers": [{"uri": _data_uri(data)}]}, tmp_path
    ) == [data]

    path = tmp_path / "buffer.bin"
    path.write_bytes(data)
    assert load_buffers(
        {"buffers": [{"uri": "buffer.bin"}]}, tmp_path
    ) == [data]
    assert load_buffers(
        {"buffers": [{"byteLength": 2}]}, tmp_path, binary_chunk=b"abcd"
    ) == [b"ab"]

    with pytest.raises(FileNotFoundError):
        load_buffers(
            {"buffers": [{"uri": "missing.bin"}]}, tmp_path
        )
    with pytest.raises(ValueError, match="no uri"):
        load_buffers(
            {"buffers": [{"byteLength": 1}]}, tmp_path
        )
    with pytest.raises(ValueError, match="only the first"):
        load_buffers(
            {"buffers": [{"byteLength": 1}, {"byteLength": 1}]},
            tmp_path,
            binary_chunk=b"abcd",
        )
    with pytest.raises(ValueError, match="exceeds"):
        load_buffers(
            {"buffers": [{"byteLength": 5}]}, tmp_path, binary_chunk=b"abcd"
        )
    with pytest.raises(TypeError, match="buffers"):
        load_buffers({"buffers": {}}, tmp_path)
    with pytest.raises(ValueError, match="base64"):
        decode_data_uri("data:text/plain,abc")


def test_read_accessor_validation_and_normalization():
    floats = struct.pack("<3f", 1.0, 2.0, 3.0)
    views = [{"buffer": 0, "byteOffset": 0, "byteLength": len(floats)}]
    assert read_accessor(
        {"bufferView": 0, "componentType": 5126, "count": 1, "type": "VEC3"},
        views,
        [floats],
    ) == [(1.0, 2.0, 3.0)]
    assert read_accessor(
        {"componentType": 5126, "count": 2, "type": "VEC3"}, [], []
    ) == [0, 0]

    normalized = struct.pack("<3H", 0, 32768, 65535)
    assert read_accessor(
        {
            "bufferView": 0,
            "componentType": 5123,
            "count": 3,
            "type": "SCALAR",
            "normalized": True,
        },
        [{"buffer": 0, "byteOffset": 0, "byteLength": 6}],
        [normalized],
    ) == pytest.approx([0.0, 0.5000076, 1.0])

    with pytest.raises(ValueError, match="sparse"):
        read_accessor({"sparse": {}}, [], [])
    with pytest.raises(ValueError, match="component type"):
        read_accessor(
            {"bufferView": 0, "componentType": 9999, "count": 1},
            views,
            [floats],
        )
    with pytest.raises(ValueError, match="accessor type"):
        read_accessor(
            {"bufferView": 0, "componentType": 5126, "count": 1, "type": "MAT3"},
            views,
            [floats],
        )
    with pytest.raises(ValueError, match="cannot be normalized"):
        read_accessor(
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": 1,
                "normalized": True,
            },
            views,
            [floats],
        )
    with pytest.raises(ValueError, match="unknown bufferView"):
        read_accessor(
            {"bufferView": 5, "componentType": 5126, "count": 1}, views, [floats]
        )
    with pytest.raises(TypeError, match="bufferView"):
        read_accessor(
            {"bufferView": 0, "componentType": 5126, "count": 1}, [1], [floats]
        )
    with pytest.raises(ValueError, match="unknown buffer"):
        read_accessor(
            {"bufferView": 0, "componentType": 5126, "count": 1},
            [{"buffer": 3, "byteLength": 12}],
            [floats],
        )
    with pytest.raises(ValueError, match="stride is too small"):
        read_accessor(
            {"bufferView": 0, "componentType": 5126, "count": 1, "type": "VEC3"},
            [{"buffer": 0, "byteStride": 2, "byteLength": 12}],
            [floats],
        )
    with pytest.raises(ValueError, match="outside"):
        read_accessor(
            {"bufferView": 0, "componentType": 5126, "count": 2, "type": "VEC3"},
            views,
            [floats],
        )


def test_load_gltf_document_validation_and_registry(tmp_path):
    with pytest.raises(ValueError, match="invalid glTF JSON"):
        load_gltf("{")
    with pytest.raises(TypeError, match="JSON object"):
        load_gltf("[]")
    with pytest.raises(ValueError, match="version"):
        load_gltf({"asset": {"version": "1.0"}})
    with pytest.raises(TypeError, match="bufferViews"):
        load_gltf({"asset": {"version": "2.0"}, "bufferViews": {}})
    with pytest.raises(TypeError, match="source"):
        load_gltf(3)
    with pytest.raises(FileNotFoundError):
        load_gltf(tmp_path / "missing.gltf")

    document, data = _triangle_document(uri=True)
    registry = AssetRegistry()
    imported = load_gltf(document, registry=registry)
    assert imported.node_count == 1
    assert imported.meshes[0].triangle_count() == 1
    assert imported.materials[0].color == Vec3(0.2, 0.4, 0.6)
    assert registry.require("gltf.mesh.0").kind == "mesh"
    assert registry.require("gltf.material.0").kind == "material"

    glb = _glb(*_triangle_document(uri=False))
    imported_glb = load_gltf(glb)
    assert imported_glb.node_count == 1
    assert imported_glb.meshes[0].triangle_count() == 1
