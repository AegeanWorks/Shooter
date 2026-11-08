"""Keystone mechanics testbed: PNG encoding and RGBA textures.

Covers RGBA round trips with the vertical-flip convention, corrupt PNG
rejection, texture immutability/shape hashes, PNG-backed textures and the
deterministic checker pattern.
"""

from dataclasses import FrozenInstanceError

import pytest

from keystone.png import SIGNATURE, png_bytes, read_png, write_png
from keystone.texture import TextureData

PIXELS = bytes(
    (
        255, 0, 0, 255,
        0, 255, 0, 255,
        0, 0, 255, 255,
        255, 255, 0, 255,
    )
)


def test_png_round_trip_flip_and_bytes(tmp_path):
    path = tmp_path / "frame.png"
    write_png(path, 2, 2, PIXELS, flip_vertical=False)
    assert read_png(path) == (2, 2, PIXELS)

    flipped = tmp_path / "flipped.png"
    write_png(flipped, 2, 2, PIXELS)
    assert read_png(flipped) == (2, 2, PIXELS[8:] + PIXELS[:8])

    data = png_bytes(2, 2, PIXELS, flip_vertical=False)
    assert data.startswith(SIGNATURE)
    from_bytes = tmp_path / "bytes.png"
    from_bytes.write_bytes(data)
    assert read_png(from_bytes) == (2, 2, PIXELS)

    with pytest.raises(ValueError, match="positive"):
        png_bytes(0, 2, PIXELS)
    with pytest.raises(ValueError, match="expected"):
        png_bytes(2, 2, PIXELS[:-1])


def test_png_rejects_corrupt_inputs(tmp_path):
    data = png_bytes(2, 2, PIXELS, flip_vertical=False)
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not a png")
    with pytest.raises(ValueError, match="not a PNG"):
        read_png(bad)

    truncated = tmp_path / "truncated.png"
    truncated.write_bytes(data[:-12])
    with pytest.raises(ValueError, match="no IEND"):
        read_png(truncated)

    corrupt = bytearray(data)
    corrupt[45] ^= 0xFF
    bad_crc = tmp_path / "crc.png"
    bad_crc.write_bytes(bytes(corrupt))
    with pytest.raises(ValueError, match="CRC"):
        read_png(bad_crc)


def test_texture_validation_and_sha():
    pixels = bytes(range(8))
    texture = TextureData(2, 1, pixels, "one")
    assert texture.sha256() == TextureData(2, 1, pixels, "two").sha256()
    assert texture.sha256() != TextureData(1, 2, pixels).sha256()
    assert texture.sha256() != TextureData(
        2, 1, bytes((1,)) + pixels[1:]
    ).sha256()

    with pytest.raises(ValueError, match="positive"):
        TextureData(0, 1, b"")
    with pytest.raises(ValueError, match="positive"):
        TextureData(1, 0, b"")
    with pytest.raises(TypeError, match="bytes"):
        TextureData(2, 1, bytearray(pixels))
    with pytest.raises(ValueError, match="expected 8"):
        TextureData(2, 1, pixels[:-1])
    with pytest.raises(FrozenInstanceError):
        texture.width = 3


def test_texture_from_png_and_bytes(tmp_path):
    path = tmp_path / "swatch.png"
    write_png(path, 2, 2, PIXELS, flip_vertical=False)
    texture = TextureData.from_png(path)
    assert (texture.width, texture.height, texture.rgba, texture.name) == (
        2,
        2,
        PIXELS,
        "swatch",
    )
    assert TextureData.from_png(path, name="custom").name == "custom"

    inline = TextureData.from_png_bytes(
        png_bytes(2, 2, PIXELS, flip_vertical=False), name="inline"
    )
    assert (inline.width, inline.height, inline.rgba, inline.name) == (
        2,
        2,
        PIXELS,
        "inline",
    )

    with pytest.raises(ValueError):
        TextureData.from_png_bytes(b"not a png")


def test_texture_checker_pattern_and_validation():
    texture = TextureData.checker(
        size=4, dark=(0.0, 0.0, 0.0), light=(1.0, 1.0, 1.0), cell=2, name="grid"
    )
    assert (texture.width, texture.height, texture.name) == (4, 4, "grid")

    def pixel(x, y):
        offset = (y * texture.width + x) * 4
        return texture.rgba[offset : offset + 4]

    assert pixel(0, 0) == bytes((255, 255, 255, 255))
    assert pixel(2, 0) == bytes((0, 0, 0, 255))
    assert pixel(0, 2) == bytes((0, 0, 0, 255))
    assert pixel(2, 2) == bytes((255, 255, 255, 255))
    assert set(texture.rgba[3::4]) == {255}

    with pytest.raises(ValueError, match="positive"):
        TextureData.checker(size=0)
    with pytest.raises(ValueError, match="positive"):
        TextureData.checker(cell=0)
    with pytest.raises(TypeError, match="three channels"):
        TextureData.checker(dark=(1.0, 2.0))
    with pytest.raises(TypeError, match="three channels"):
        TextureData.checker(light="white")
