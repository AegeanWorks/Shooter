"""Keystone mechanics testbed: what a frame report's ``hash`` actually covers.

While proving a data-driven camera change was pixel-identical, the before/after
report hashes disagreed even though every field matched. The reason is part of
the contract, not a bug: the hash covers the ``image`` block, which includes the
artifact *path*. Two captures of the same frame therefore hash differently when
written to different filenames, so a consumer comparing evidence must compare
``image.png_sha256`` for pixels and the report hash only for whole artifacts.

This pins both halves so nobody "fixes" the hash by dropping the path (which
would erase artifact identity) or compares hashes across renamed files.
"""

from pathlib import Path

from keystone.analysis import analyze_frame
from keystone.math3d import Vec3
from keystone.png import write_png
from keystone.primitives import cube
from keystone.scene import Node, Scene, Transform


def _frame(tmp_path, name: str) -> dict:
    pixels = bytes((40, 90, 160, 255)) * (8 * 8)
    image = tmp_path / name
    write_png(image, 8, 8, pixels)
    scene = Scene()
    scene.add(
        Node(
            "box",
            id="box",
            transform=Transform(position=Vec3(0.0, 0.0, -4.0)),
            mesh=cube(1.0),
        )
    )
    return analyze_frame(scene, pixels, 8, 8, image_path=image)


def test_identical_pixels_hash_differently_when_the_artifact_is_renamed(tmp_path):
    left = _frame(tmp_path, "left.png")
    right = _frame(tmp_path, "right.png")

    assert left["image"]["path"] != right["image"]["path"]
    assert left["image"]["png_sha256"] == right["image"]["png_sha256"]
    assert left["image"]["rgba_sha256"] == right["image"]["rgba_sha256"]
    assert left["stats"] == right["stats"]
    assert left["scene"]["nodes"] == right["scene"]["nodes"]

    # the report hash identifies the artifact, path included
    assert left["hash"] != right["hash"], "a renamed artifact is a different artifact"


def test_the_same_artifact_path_hashes_identically(tmp_path):
    first = _frame(tmp_path, "same.png")
    second = _frame(tmp_path, "same.png")

    assert first["hash"] == second["hash"]
    assert first["image"]["png_sha256"] == second["image"]["png_sha256"]


def test_the_hash_tracks_real_content_not_only_the_path(tmp_path):
    pixels = bytes((40, 90, 160, 255)) * (8 * 8)
    image = tmp_path / "frame.png"
    write_png(image, 8, 8, pixels)
    scene = Scene()
    scene.add(
        Node(
            "box",
            id="box",
            transform=Transform(position=Vec3(0.0, 0.0, -4.0)),
            mesh=cube(1.0),
        )
    )
    baseline = analyze_frame(scene, pixels, 8, 8, image_path=image)

    moved = Scene()
    moved.add(
        Node(
            "box",
            id="box",
            transform=Transform(position=Vec3(1.0, 0.0, -4.0)),
            mesh=cube(1.0),
        )
    )
    shifted = analyze_frame(moved, pixels, 8, 8, image_path=image)
    assert shifted["hash"] != baseline["hash"], "node placement must affect the hash"

    darker = bytes((10, 20, 40, 255)) * (8 * 8)
    write_png(image, 8, 8, darker)
    dimmed = analyze_frame(scene, darker, 8, 8, image_path=image)
    assert dimmed["hash"] != baseline["hash"], "pixels must affect the hash"
    assert dimmed["stats"] != baseline["stats"]


def test_a_report_without_an_artifact_still_hashes_the_frame(tmp_path):
    pixels = bytes((5, 10, 15, 255)) * (4 * 4)
    scene = Scene()
    plain = analyze_frame(scene, pixels, 4, 4)
    assert plain["image"]["path"] is None
    assert plain["image"]["png_sha256"] is None
    assert plain["hash"] == analyze_frame(Scene(), pixels, 4, 4)["hash"]
