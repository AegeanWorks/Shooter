"""Keystone mechanics testbed: headless frame analysis and pixel diffs.

Builds small deterministic RGBA frames, checks report stats/hashes and
node/material metadata, compares reports with node/UI/fx changes, and
writes threshold pixel-diff PNGs plus atomic report JSON.
"""

import hashlib

import pytest

from keystone.analysis import (
    REPORT_SCHEMA,
    analyze_frame,
    compare_reports,
    diff_images,
    write_report,
)
from keystone.geometry import Material
from keystone.math3d import Vec3
from keystone.png import read_png, write_png
from keystone.primitives import cube
from keystone.scene import Node, Scene, Transform
from keystone.serialization import read_json
from keystone.texture import TextureData

BG = (26, 26, 26, 255)
RED = (255, 0, 0, 255)


def _flat(width, height, color=BG):
    return bytes(color) * (width * height)


def test_analyze_frame_stats_and_hashes(tmp_path):
    scene = Scene()
    scene.background = Vec3(0.1, 0.1, 0.1)
    pixels = bytes(RED) + _flat(1, 3)
    report = analyze_frame(scene, pixels, 2, 2)
    assert report["schema"] == REPORT_SCHEMA["version"] == 11
    stats = report["stats"]
    assert stats["mean_rgb"] == [83.25, 19.5, 19.5]
    assert stats["mean_luma"] == pytest.approx(33.05)
    assert stats["content_pixels"] == 1
    assert stats["content_ratio"] == 0.25
    assert stats["content_bbox"] == [0, 1, 0, 1]
    assert stats["dominant_colors"][0] == {"rgb": [24, 24, 24], "pixels": 3}
    assert stats["dominant_colors"][1] == {"rgb": [248, 8, 8], "pixels": 1}
    assert len(stats["grid_luma"]) == 8
    assert all(len(row) == 8 for row in stats["grid_luma"])
    assert stats["grid_luma"][4][0] == pytest.approx(54.21)
    assert report["image"] == {
        "path": None,
        "width": 2,
        "height": 2,
        "rgba_sha256": hashlib.sha256(pixels).hexdigest(),
        "png_sha256": None,
    }

    png = tmp_path / "frame.png"
    write_png(png, 2, 2, pixels, flip_vertical=False)
    hashed = analyze_frame(scene, pixels, 2, 2, image_path=png)
    assert hashed["image"]["path"] == png.as_posix()
    assert hashed["image"]["rgba_sha256"] == report["image"]["rgba_sha256"]
    assert hashed["image"]["png_sha256"] == hashlib.sha256(
        png.read_bytes()
    ).hexdigest()

    with pytest.raises(ValueError, match="expected 16 RGBA bytes"):
        analyze_frame(scene, pixels[:-1], 2, 2)


def test_analyze_frame_nodes_material_and_scene_metadata():
    scene = Scene()
    texture = TextureData(2, 2, _flat(2, 2, (40, 50, 60, 255)), name="swatch")
    material = Material(
        color=Vec3(1.0, 0.5, 0.2),
        specular=0.2,
        shininess=16.0,
        metallic=0.4,
        roughness=0.3,
        emissive=Vec3(0.1, 0.2, 0.3),
        texture=texture,
    )
    node = Node(
        "cube",
        transform=Transform(position=Vec3(0.0, 0.0, -5.0)),
        mesh=cube(1.0),
        material=material,
    )
    node.add_tag("enemy")
    node.layer = "gameplay"
    scene.add(node)

    report = analyze_frame(scene, _flat(2, 2), 2, 2, fx={"alive": 3, "drawn": 2})
    assert report["ui"] is None
    assert report["fx"] == {"alive": 3, "drawn": 2, "enabled": True}
    body = report["scene"]
    assert body["node_count"] == 2
    assert body["camera"] == {
        "position": [0.0, 0.0, 0.0],
        "yaw": 0.0,
        "pitch": 0.0,
        "fov_y": 60.0,
        "near": 0.1,
        "far": 1000.0,
    }
    assert body["shadows"] == {"enabled": True, "size": 1024}
    assert body["color"] == {"enabled": True}
    assert body["post"] == {"enabled": True}
    assert body["bloom"] == {"enabled": True}
    assert body["sprites"] == {"enabled": True}
    assert body["culling"] == {"enabled": True}

    nodes = {entry["name"]: entry for entry in body["nodes"]}
    assert nodes[""]["id"] == "root"
    assert nodes[""]["parent"] is None
    assert nodes[""]["screen"] is None
    assert nodes[""]["bbox"] is None
    entry = nodes["cube"]
    assert entry["id"] == "node-1"
    assert entry["parent"] == "" and entry["parent_id"] == "root"
    assert entry["visible"] is True
    assert entry["tags"] == ["enemy"]
    assert entry["layer"] == "gameplay"
    assert entry["components"] == []
    assert entry["world"] == [0.0, 0.0, -5.0]
    assert entry["screen"] == [1.0, 1.0]
    assert entry["bbox"] == [0.81, 0.81, 1.19, 1.19]
    assert entry["triangles"] == 12
    assert entry["material"] == {
        "color": [1.0, 0.5, 0.2],
        "specular": 0.2,
        "shininess": 16.0,
        "checker_scale": 0.0,
        "metallic": 0.4,
        "roughness": 0.3,
        "emissive": [0.1, 0.2, 0.3],
        "texture": {
            "name": "swatch",
            "width": 2,
            "height": 2,
            "sha256": texture.sha256(),
        },
    }


def test_compare_reports_detects_node_and_image_changes():
    pixels = _flat(2, 2)

    def build(x=0.0, extra=False):
        scene = Scene()
        scene.add(
            Node(
                "cube",
                id="cube-1",
                transform=Transform(position=Vec3(x, 0.0, -5.0)),
                mesh=cube(1.0),
            )
        )
        if extra:
            scene.add(Node("extra", id="extra-1"))
        return analyze_frame(scene, pixels, 2, 2)

    base = build()
    same = compare_reports(base, base)
    assert same["same_image"] is True
    assert same["same_report"] is True
    assert same["changed_nodes"] == []
    assert same["added_nodes"] == [] and same["removed_nodes"] == []

    moved = compare_reports(base, build(x=1.0))
    assert moved["same_image"] is True
    assert moved["same_report"] is False
    assert moved["changed_nodes"] == ["cube-1"]
    assert moved["added_nodes"] == [] and moved["removed_nodes"] == []
    assert moved["mean_luma_delta"] == 0.0

    added = compare_reports(base, build(extra=True))
    assert added["added_nodes"] == ["extra-1"]
    removed = compare_reports(build(extra=True), base)
    assert removed["removed_nodes"] == ["extra-1"]

    with pytest.raises(ValueError):
        compare_reports({"schema": 0}, base)


def test_compare_reports_ui_fx_and_legacy_defaults():
    scene = Scene()
    scene.add(
        Node(
            "cube",
            transform=Transform(position=Vec3(0.0, 0.0, -5.0)),
            mesh=cube(1.0),
        )
    )
    pixels = _flat(2, 2)
    label = {"text": "HP 3", "x": 10, "y": 8, "scale": 1, "color": [1, 1, 1]}
    moved = {**label, "x": 12}
    wave = {"text": "WAVE 2", "x": 4, "y": 4, "scale": 1, "color": [1, 1, 1]}
    button = {
        "label": "Resume",
        "action": "resume",
        "rect": [1, 2, 3, 4],
        "selected": False,
        "hovered": False,
    }
    button_on = {**button, "selected": True}
    quit_button = {
        "label": "Quit",
        "action": "quit",
        "rect": [0, 0, 5, 5],
        "selected": False,
        "hovered": False,
    }
    before = analyze_frame(
        scene,
        pixels,
        2,
        2,
        ui={"visible": True, "paused": False, "labels": [label], "buttons": [button]},
        fx={"alive": 1, "drawn": 1, "enabled": True},
    )
    after = analyze_frame(
        scene,
        pixels,
        2,
        2,
        ui={
            "visible": True,
            "paused": True,
            "labels": [moved, wave],
            "buttons": [button_on, quit_button],
        },
        fx={"alive": 3, "drawn": 2, "enabled": False},
    )
    diff = compare_reports(before, after)
    assert diff["same_image"] is True
    assert diff["same_report"] is False
    assert diff["same_ui"] is False
    assert diff["ui"]["paused"] == {"before": False, "after": True}
    assert diff["ui"]["moved_labels"] == ["HP 3"]
    assert diff["ui"]["added_labels"] == ["WAVE 2"]
    assert diff["ui"]["added_buttons"] == ["quit"]
    assert diff["ui"]["changed_buttons"] == ["resume"]
    assert diff["same_fx"] is False
    assert diff["fx"] == {
        "before": {"alive": 1, "drawn": 1, "enabled": True},
        "after": {"alive": 3, "drawn": 2, "enabled": False},
    }

    legacy_before = dict(before)
    legacy_after = dict(after)
    legacy_before.pop("ui")
    legacy_before.pop("fx")
    legacy_after.pop("ui")
    legacy_after.pop("fx")
    legacy = compare_reports(legacy_before, legacy_after)
    assert legacy["same_ui"] is True
    assert legacy["same_fx"] is True


def test_diff_images_writes_threshold_diff_and_report(tmp_path):
    width, height = 3, 2
    base_pixel = (100, 100, 100, 255)
    first = bytes(base_pixel) * (width * height)
    second = bytearray(first)
    second[4:8] = bytes((120, 100, 100, 255))
    second[16:20] = bytes((140, 140, 140, 255))
    second[20:24] = bytes((105, 105, 105, 255))
    before = tmp_path / "before.png"
    after = tmp_path / "after.png"
    output = tmp_path / "diff.png"
    write_png(before, width, height, first, flip_vertical=False)
    write_png(after, width, height, bytes(second), flip_vertical=False)

    diff = diff_images(before, after, output, threshold=8)
    assert diff["width"] == width and diff["height"] == height
    assert diff["changed_pixels"] == 2
    assert diff["changed_ratio"] == pytest.approx(0.3333)
    assert diff["mean_delta"] == pytest.approx(10.833)
    assert diff["max_delta"] == 40
    assert diff["bbox"] == [1, 0, 1, 1]
    assert diff["path"] == output.as_posix()

    diff_width, diff_height, diff_pixels = read_png(output)
    assert (diff_width, diff_height) == (width, height)
    assert diff_pixels[4:8] == bytes((255, 0, 0, 255))
    assert diff_pixels[16:20] == bytes((255, 0, 0, 255))
    assert diff_pixels[20:24] == bytes((33, 33, 33, 255))
    assert diff_pixels[0:4] == bytes((33, 33, 33, 255))

    other = tmp_path / "other.png"
    write_png(other, 2, 2, bytes(base_pixel) * 4, flip_vertical=False)
    with pytest.raises(ValueError, match="same dimensions"):
        diff_images(before, other, output)

    report = analyze_frame(Scene(), first, width, height)
    report_path = tmp_path / "report.json"
    write_report(report_path, report)
    assert read_json(report_path) == report
    write_report(report_path, report)
    assert not report_path.with_name(report_path.name + ".bak").exists()
