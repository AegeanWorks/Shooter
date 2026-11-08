"""Keystone mechanics testbed: real HTTP routes for the web console.

Starts the threaded keystone web server with the shooter GameSession and
drives the public JSON API over loopback: health/describe/scene/inspector,
simulate, editor actions and the 404/405/400 problem paths.
"""

import json
import threading
import urllib.error
import urllib.request

import pytest

from keystone.web.server import create_server

from shooter.game import ShooterGame


@pytest.fixture(scope="module")
def base_url():
    server = create_server(ShooterGame(), host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _request(base: str, path: str, method: str = "GET", payload=None, raw=None):
    data = raw if raw is not None else (
        None if payload is None else json.dumps(payload).encode("utf-8")
    )
    request = urllib.request.Request(base + path, data=data, method=method)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers, exc.read()


def _json(base: str, path: str, method: str = "GET", payload=None, raw=None):
    status, headers, body = _request(base, path, method, payload, raw)
    return status, headers, json.loads(body.decode("utf-8"))


def test_get_health_describe_and_scene(base_url):
    status, headers, health = _json(base_url, "/api/health")
    assert status == 200
    assert headers["Access-Control-Allow-Origin"] == "*"
    assert health["ok"] is True
    assert health["game"] == "shooter"
    assert health["scene_schema"] == 2

    status, _, describe = _json(base_url, "/api/describe")
    assert status == 200
    assert describe["game"] == "shooter"
    assert describe["capabilities"]["web"]["api_version"] == 1
    assert "fire" in describe["actions"]["buttons"]
    assert "overdrive" in describe["actions"]["buttons"]

    status, _, scene = _json(base_url, "/api/scene")
    assert status == 200
    assert scene["schema"] == 2
    assert scene["game"] == "shooter"
    assert scene["node_count"] == 113
    ids = {node["id"] for node in scene["nodes"]}
    assert {"floor", "platform-pad", "pickup:surge-pickup", "warden-core"} <= ids


def test_get_inspector_reports_batches_and_merged(base_url):
    status, _, inspector = _json(base_url, "/api/inspector")
    assert status == 200
    assert inspector["game"] == "shooter"
    assert inspector["node_count"] == 113
    assert inspector["batches"]["groups"] == 8
    assert inspector["batches"]["draw_calls"] == 35
    assert inspector["merged"]["groups"] == 7
    assert inspector["merged"]["saved_calls"] == 28
    assert inspector["scene_schema"] == 2


def test_post_simulate_matches_the_cli_hash(base_url):
    status, _, payload = _json(
        base_url, "/api/simulate", method="POST", payload={"frames": 120}
    )
    assert status == 200
    assert payload["frames"] == 120
    assert payload["hash"] == "7e4b602e029d12d68672790318d119cd"
    assert payload["final"]["outcome"] == "ongoing"
    assert payload["final"]["wave"] == 1
    assert payload["final"]["player"]["hp"] == 100

    status, _, inferred = _json(
        base_url,
        "/api/simulate",
        method="POST",
        payload={"actions": [{"forward": 1.0}, {"right": 1.0}]},
    )
    assert status == 200
    assert inferred["frames"] == 2


def test_editor_actions_and_error_paths(base_url):
    status, _, editor = _json(
        base_url,
        "/api/editor",
        method="POST",
        payload={"action": "select", "id": "platform-pad"},
    )
    assert status == 200
    assert editor["selection"]["id"] == "platform-pad"

    status, _, editor = _json(
        base_url,
        "/api/editor",
        method="POST",
        payload={
            "action": "transform",
            "id": "platform-pad",
            "position": [1.0, 2.0, 3.0],
        },
    )
    assert status == 200
    assert editor["selection"]["transform"]["position"] == [1.0, 2.0, 3.0]

    status, _, _ = _json(
        base_url, "/api/editor", method="POST", payload={"action": "select", "id": "missing"}
    )
    assert status == 404
    status, _, _ = _json(
        base_url, "/api/editor", method="POST", payload={"action": "explode"}
    )
    assert status == 400
    status, _, _ = _json(base_url, "/api/nope")
    assert status == 404
    status, _, _ = _json(base_url, "/api/scene", method="POST")
    assert status == 405
    status, _, _ = _json(base_url, "/api/simulate")
    assert status == 405
    status, _, _ = _json(
        base_url, "/api/simulate", method="POST", payload={"frames": -1}
    )
    assert status == 400
    status, _, _ = _json(
        base_url, "/api/simulate", method="POST", raw=b"not-json"
    )
    assert status == 400
