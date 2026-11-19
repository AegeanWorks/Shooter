"""Game proof: the victory cinematic is a shipped .kpath document.

The campaign-clear fly-around is authored data, not code: it lives in
``shooter/data/campaign_clear.kpath`` and is loaded through Keystone's
``CameraPathLibrary`` when the last wave is sealed. This proves the document
loads, that the game drives its camera from it, that it is presentation only,
and that a missing document degrades to first person instead of breaking the
victory screen.
"""

from pathlib import Path

import pytest

from keystone.camera_path import CAMERA_PATH_SCHEMA
from keystone.camera_path_library import CameraPathLibrary
from keystone.input import ActionState
from keystone.serialization import read_json

from shooter.game import ShooterGame

STEP = 1.0 / 60.0
DATA_DIR = Path(__file__).resolve().parent.parent / "shooter" / "data"


def _sealing_game():
    """A built game whose next update seals the campaign."""
    game = ShooterGame()
    game.build_scene()
    game.sim.wave = int(game.sim.levels.get("win_wave", 4))
    return game


def _tick(game, frames):
    actions = ActionState()
    for _ in range(frames):
        game.update(STEP, actions)


def test_the_authored_lens_and_height_stay_inside_their_bands():
    document = read_json(DATA_DIR / "campaign_clear.kpath")
    fovs = []
    for key in document["keys"]:
        fov = float(key["fov_y"])
        height = float(key["position"][1])
        assert 50.0 <= fov <= 65.0, fov
        assert 1.5 <= height <= 4.0, height
        fovs.append(fov)
    assert fovs == sorted(fovs, reverse=True), fovs
    assert fovs[0] - fovs[-1] >= 5.0, fovs


def test_the_shipped_document_loads_as_a_one_shot_path():
    document = read_json(DATA_DIR / "campaign_clear.kpath")
    assert document["schema"] == CAMERA_PATH_SCHEMA == 1
    assert document["loop"] is False
    assert len(document["keys"]) == 4

    library = CameraPathLibrary(DATA_DIR)
    entry = library.entry("campaign_clear")
    assert entry.error is None
    assert entry.name == "campaign_clear"
    assert entry.loop is False
    assert entry.keys == 4
    assert entry.duration == pytest.approx(3.5)

    path = library.load("campaign_clear")
    assert path.duration == pytest.approx(3.5)
    assert [key.time for key in path.keys] == [0.0, 1.2, 2.4, 3.5]


def test_sealing_the_campaign_starts_the_document_camera():
    game = _sealing_game()
    assert game._clear_camera is None

    _tick(game, 1)

    assert game.campaign_cleared is True
    assert game._clear_camera is not None
    report = game.campaign_camera_report
    assert report is not None and "error" not in report
    assert report["path"]["duration"] == pytest.approx(3.5)
    assert len(report["path"]["keys"]) == 4


def test_the_camera_follows_the_document_pose():
    game = _sealing_game()
    _tick(game, 1)
    _tick(game, 30)

    pose = game._clear_camera.sample()
    cam = game.scene.camera
    assert cam.position.x == pytest.approx(pose.position.x)
    assert cam.position.y == pytest.approx(pose.position.y)
    assert cam.position.z == pytest.approx(pose.position.z)
    assert cam.yaw == pytest.approx(pose.yaw)
    assert cam.fov_y == pytest.approx(pose.fov_y)
    # it is a real fly-around: away from the player's eye
    eye = game.sim.eye()
    assert (cam.position - eye).length() > 1.0


def test_the_victory_camera_clamps_and_leaves_the_record_alone():
    game = _sealing_game()
    _tick(game, 1)
    _tick(game, 400)
    assert game._clear_camera.done is True
    settled = game.scene.camera.position
    _tick(game, 30)
    assert (game.scene.camera.position - settled).length() < 1e-9

    snapshot = game.snapshot()
    assert set(snapshot) == set(game.sim.snapshot()) | {"dropped_sfx"}
    for leaked in ("camera", "campaign_camera", "cinematic", "camera_path"):
        assert leaked not in snapshot


class _RedirectedLibrary(CameraPathLibrary):
    """Point the game's library at a temporary directory of real files."""

    def __init__(self, directory):
        super().__init__(_RedirectedLibrary.target)

    target = None


def _victory_game_over(directory, monkeypatch):
    """A game whose campaign_clear.kpath is read from a temp directory."""
    import shooter.game as game_module

    _RedirectedLibrary.target = directory
    monkeypatch.setattr(game_module, "CameraPathLibrary", _RedirectedLibrary)
    game = ShooterGame()
    game.build_scene()
    game.sim.wave = int(game.sim.levels.get("win_wave", 4))
    return game


@pytest.mark.parametrize(
    "raw",
    [
        '{"schema": 1, "keys": [{"time": 0.0',
        "",
        "[1, 2, 3]",
        '{"schema": 9, "loop": false, "keys": []}',
        '{"schema": 1, "loop": false, "keys": []}',
    ],
    ids=["truncated", "empty-file", "not-an-object", "wrong-schema", "no-keys"],
)
def test_a_really_corrupt_document_degrades_to_first_person(tmp_path, monkeypatch, raw):
    """A hand-broken .kpath must never crash the victory screen."""
    paths = tmp_path / "paths"
    paths.mkdir()
    (paths / "campaign_clear.kpath").write_text(raw, encoding="utf-8")

    game = _victory_game_over(paths, monkeypatch)
    _tick(game, 1)

    assert game.campaign_cleared is True
    assert game._clear_camera is None, "a corrupt document must not drive the camera"
    report = game.campaign_camera_report
    assert report is not None and "error" in report
    # and the victory screen still renders from the player's eye
    eye = game.sim.eye()
    cam = game.scene.camera
    assert cam.position.x == pytest.approx(eye.x)
    assert cam.position.z == pytest.approx(eye.z)


def test_a_completely_missing_library_directory_also_degrades(tmp_path, monkeypatch):
    game = _victory_game_over(tmp_path / "does-not-exist", monkeypatch)
    _tick(game, 1)

    assert game._clear_camera is None
    assert "error" in game.campaign_camera_report


def test_a_missing_document_falls_back_to_first_person(monkeypatch):
    def broken_load(self, name):
        raise ValueError("could not load camera path 'campaign_clear': corrupt")

    monkeypatch.setattr(CameraPathLibrary, "load", broken_load)
    game = _sealing_game()
    _tick(game, 1)

    assert game.campaign_cleared is True
    assert game._clear_camera is None
    assert "corrupt" in game.campaign_camera_report["error"]
    # the victory screen still renders from the player's eye
    eye = game.sim.eye()
    cam = game.scene.camera
    assert cam.position.x == pytest.approx(eye.x)
    assert cam.position.z == pytest.approx(eye.z)


def test_rebuilding_clears_the_victory_camera():
    game = _sealing_game()
    _tick(game, 1)
    assert game._clear_camera is not None
    game.build_scene()
    assert game._clear_camera is None
    assert game.campaign_camera_report is None
    assert game.scene.camera.fov_y == pytest.approx(75.0)
