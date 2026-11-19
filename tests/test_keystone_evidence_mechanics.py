"""Keystone testbed: capture routes as reproducible proof artefacts.

`evidence` was one of the Keystone modules the shooter had never imported.
The project's proof driver (`scripts/route_evidence.py`) now owns a named Route
with checkpoints; this module exercises the capture and diff contract with a
tiny engine double so the testbed stays headless and fast.
"""

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from keystone.evidence import capture_route, diff_evidence, write_evidence
from keystone.png import write_png
from keystone.scene import Scene

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import route_evidence  # noqa: E402


class _Engine:
    """Only run(), capture() and scene are needed by capture_route."""

    def __init__(self, luma: float = 30.0) -> None:
        self.scene = Scene()
        self.renderer = SimpleNamespace(
            last_stats={"draw_calls": 7, "triangles": 810, "overlay_calls": 3}
        )
        self._tick = 0
        self._luma = luma

    def run(self, frames: int) -> int:
        self._tick += frames
        return frames if self._tick <= 12 else 0

    def capture(self, png: Path, report_path: Path) -> None:
        write_png(png, 4, 4, bytes([40, 90, 30, 255]) * 16)
        digest = hashlib.sha256(Path(png).read_bytes()).hexdigest()
        Path(report_path).write_text(
            json.dumps({
                "image": {"png_sha256": digest},
                "stats": {
                    "mean_luma": self._luma + self._tick * 0.1,
                    "content_ratio": 0.1,
                    "content_pixels": 16,
                },
            }),
            encoding="utf-8",
        )


def _capture(tmp_path: Path, name: str, luma: float = 30.0) -> dict:
    return capture_route(_Engine(luma), route_evidence.build_route(), tmp_path / name)


def test_the_shipped_route_has_named_checkpoints():
    route = route_evidence.build_route()
    assert route.name == "shooter-spawn"
    assert route.frames == 12
    assert route.frame_numbers() == (1, 6, 12)
    assert [point.label for point in route.checkpoints] == ["frame-1", "frame-6", "frame-12"]


def test_capture_route_is_byte_reproducible(tmp_path):
    one = _capture(tmp_path, "one")
    two = _capture(tmp_path, "two")
    assert one == two
    assert len(one["checkpoints"]) == 3
    assert one["frames_run"] == 12
    assert len(one["route_hash"]) == 32


def test_diff_reports_a_changed_checkpoint(tmp_path):
    before = _capture(tmp_path, "before")
    after = _capture(tmp_path, "after", luma=40.0)
    diff = diff_evidence(before, after)
    assert diff["changed"] is True
    assert diff["route"] == "shooter-spawn"
    assert any(point["mean_luma_delta"] == 10.0 for point in diff["checkpoints"])


def test_diff_reports_a_missing_and_an_added_label(tmp_path):
    route = route_evidence.build_route(checkpoints=(1,))
    before = capture_route(_Engine(), route, tmp_path / "short")
    after = _capture(tmp_path, "full")
    diff = diff_evidence(before, after)
    assert diff["missing"] == [] and diff["added"] == ["frame-12", "frame-6"]
    assert diff["changed"] is True


def test_diff_summaries_reads_a_written_baseline(tmp_path):
    before = _capture(tmp_path, "base")
    baseline = tmp_path / "base" / "route-summary.json"
    write_evidence(baseline, before)
    after = _capture(tmp_path, "new", luma=35.0)
    assert route_evidence.diff_summaries(baseline, after) == diff_evidence(before, after)
