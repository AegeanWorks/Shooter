"""Keystone mechanics testbed: the shipped victory path through the editor API.

The game ships ``shooter/data/campaign_clear.kpath`` and loads it through
``CameraPathLibrary`` at runtime. This suite proves the *same document* is a
first-class editor asset: it can be saved into a live camera-path library over
HTTP, listed, previewed, deleted to trash and restored -- and that the preview
pose agrees exactly with the sampler the game drives its camera from.

Keystone's own editor test uses a synthetic path, so agreeing with the game's
shipped document is the consumer property only this testbed can assert.
"""

import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

# Loopback calls are fast, but a loaded machine can be an order of
# magnitude slower; a tight 5s bound turns contention into false failures.
REQUEST_TIMEOUT = 60
# A server thread that will not stop is a real hang, so keep this tight.
JOIN_TIMEOUT = 10

from keystone.camera_path import CameraPath, camera_path_from_dict
from keystone.serialization import read_json
from keystone.web.server import create_server

from shooter.game import ShooterGame

DATA_DIR = Path(__file__).resolve().parent.parent / "shooter" / "data"


@pytest.fixture()
def library_server(tmp_path):
    server = create_server(
        ShooterGame(),
        host="127.0.0.1",
        port=0,
        camera_path_dir=tmp_path / "paths",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=JOIN_TIMEOUT)


def _editor(base, action, **payload):
    body = json.dumps({"action": action, **payload}).encode("utf-8")
    request = urllib.request.Request(base + "/api/editor", data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _shipped_path() -> CameraPath:
    return camera_path_from_dict(read_json(DATA_DIR / "campaign_clear.kpath"))


def test_the_shipped_document_saves_lists_and_previews_over_http(library_server):
    document = read_json(DATA_DIR / "campaign_clear.kpath")

    status, saved = _editor(library_server, "save_camera_path", name="victory", path=document)
    assert status == 200
    entry = next(item for item in saved["camera_paths"] if item["name"] == "victory")
    assert entry["keys"] == 4
    assert entry["duration"] == pytest.approx(3.5)
    assert entry["loop"] is False
    assert entry["error"] is None

    status, previewed = _editor(
        library_server, "preview_camera_path", name="victory", time=1.2
    )
    assert status == 200
    preview = previewed["camera_path_preview"]
    assert preview["source"] == "library"
    assert preview["time"] == pytest.approx(1.2)

    # the editor preview must agree with the sampler the game drives its camera
    # from, or an author would tune a fly-around the game never plays
    expected = _shipped_path().sample(1.2)
    assert preview["pose"]["position"] == pytest.approx(
        [expected.position.x, expected.position.y, expected.position.z], abs=1e-6
    )
    assert preview["pose"]["fov_y"] == pytest.approx(expected.fov_y, abs=1e-6)
    assert preview["pose"]["yaw"] == pytest.approx(expected.yaw, abs=1e-6)
    assert preview["pose"]["pitch"] == pytest.approx(expected.pitch, abs=1e-6)


def test_preview_at_every_key_matches_the_document_key_poses(library_server):
    document = read_json(DATA_DIR / "campaign_clear.kpath")
    _editor(library_server, "save_camera_path", name="victory", path=document)
    path = _shipped_path()

    for key in path.keys:
        status, previewed = _editor(
            library_server, "preview_camera_path", name="victory", time=key.time
        )
        assert status == 200
        pose = previewed["camera_path_preview"]["pose"]
        assert pose["position"] == pytest.approx(
            [key.position.x, key.position.y, key.position.z], abs=1e-6
        )
        assert pose["fov_y"] == pytest.approx(key.fov_y, abs=1e-6)


def test_the_shipped_document_survives_delete_and_restore(library_server):
    document = read_json(DATA_DIR / "campaign_clear.kpath")
    _editor(library_server, "save_camera_path", name="victory", path=document)

    status, deleted = _editor(library_server, "delete_camera_path", name="victory")
    assert status == 200
    assert deleted["camera_paths"] == []
    trash = deleted["trash"]["camera_paths"]
    assert len(trash) == 1

    status, restored = _editor(
        library_server, "restore_camera_path", trash=trash[0]["trash"]
    )
    assert status == 200
    entry = next(item for item in restored["camera_paths"] if item["name"] == "victory")
    assert entry["keys"] == 4
    assert entry["error"] is None

    # the restored file still parses as the path the game expects
    assert _shipped_path().duration == pytest.approx(entry["duration"])


def test_a_malformed_document_is_rejected_without_corrupting_the_library(library_server):
    status, _ = _editor(
        library_server,
        "save_camera_path",
        name="broken",
        path={"schema": 1, "loop": False, "keys": []},
    )
    assert status >= 400

    document = read_json(DATA_DIR / "campaign_clear.kpath")
    status, listed = _editor(library_server, "save_camera_path", name="victory", path=document)
    assert status == 200
    assert all(item["name"] != "broken" for item in listed["camera_paths"])
    assert any(item["name"] == "victory" for item in listed["camera_paths"])


def test_preview_needs_exactly_one_source(library_server):
    document = read_json(DATA_DIR / "campaign_clear.kpath")
    status, problem = _editor(
        library_server, "preview_camera_path", name="victory", path=document, time=0.0
    )
    assert status >= 400
    assert "name or path" in json.dumps(problem)

    status, problem = _editor(library_server, "preview_camera_path", time=0.0)
    assert status >= 400
