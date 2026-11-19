"""Game proof: the death cinematic drives the camera through a keystone path.

On death the game used to leave the camera frozen at the last first-person
pose while the debrief drew over it. It now plays a one-shot `CameraPath` that
rises off the shoulder, orbits the body and settles wide. This proves the path
engages, that its poses reach the camera, that it clamps instead of looping,
that it is deterministic, and -- most importantly -- that it is
presentation-only: the sim snapshot and therefore the determinism hash are
untouched.
"""

import pytest

from keystone.camera_path import CameraPathPlayer

from shooter.game import ShooterGame

STEP = 1.0 / 60.0


def _dying_game():
    """A built game whose next tick reports a real death event.

    The sim only emits "died" when an attack lands the killing blow, so the
    test appends that event once after calling the real step. Everything
    downstream -- _finish_run and the cinematic -- runs through update().
    """
    game = ShooterGame()
    game.build_scene()
    original_step = game.sim.step
    pending = ["died"]

    def step(dt, actions):
        events = list(original_step(dt, actions))
        if pending:
            pending.pop()
            game.sim.hp = 0
            game.sim.alive = False
            events.append("died")
        return events

    game.sim.step = step
    return game


def _tick(game, frames):
    from keystone.input import ActionState

    actions = ActionState()
    for _ in range(frames):
        game.update(STEP, actions)


def test_death_starts_a_camera_path_and_reports_it():
    game = ShooterGame()
    game.build_scene()
    assert game._death_camera is None
    assert game.death_camera_report is None

    game = _dying_game()
    _tick(game, 1)

    assert isinstance(game._death_camera, CameraPathPlayer)
    report = game.death_camera_report
    assert report is not None
    assert report["schema"] == 1
    assert report["loop"] is False
    assert report["speed"] == pytest.approx(1.0)
    # the report documents the authored path: four keys over 3.4 s
    path = report["path"]
    assert path["schema"] == 1
    assert path["duration"] == pytest.approx(3.4)
    assert path["loop"] is False
    assert [key["time"] for key in path["keys"]] == [0.0, 0.7, 2.1, 3.4]
    assert [key["fov_y"] for key in path["keys"]] == [75.0, 68.0, 58.0, 52.0]
    # and it records its opening pose, which is the player's eye
    eye = game.sim.eye()
    start = path["keys"][0]["position"]
    assert start == pytest.approx([round(eye.x, 6), round(eye.y, 6), round(eye.z, 6)])
    assert report["time"] == 0.0
    assert report["done"] is False


def test_the_camera_follows_the_pose_not_the_eye():
    game = _dying_game()
    _tick(game, 1)
    eye = game.sim.eye()
    first = game.scene.camera.position
    # the path opens at the eye; one 1/60 s frame of travel later the camera is
    # still within a few centimetres, so the cut reads as continuous
    assert (first - eye).length() < 0.15

    _tick(game, 45)
    later = game.scene.camera.position
    assert (later - eye).length() > 0.5, "the cinematic must leave the shoulder"
    assert later.y > 1.2, "it must rise above the eye line"
    # the pose owns yaw/pitch while the cinematic runs
    assert game.scene.camera.yaw == pytest.approx(game._death_camera.sample().yaw)
    assert game.scene.camera.pitch == pytest.approx(game._death_camera.sample().pitch)


def test_the_path_is_one_shot_and_clamps_on_its_final_pose():
    game = _dying_game()
    _tick(game, 1)
    _tick(game, 400)  # well past the 3.4 s duration
    assert game._death_camera.done is True
    settled = game.scene.camera.position
    assert game._death_camera.time == pytest.approx(3.4)
    _tick(game, 60)
    assert (game.scene.camera.position - settled).length() < 1e-9
    # the report is the authored-path snapshot taken at death, not live state
    assert game.death_camera_report["path"]["keys"][-1]["time"] == 3.4


def test_the_orbit_widens_and_stays_above_the_ground():
    game = _dying_game()
    _tick(game, 1)
    path = game._death_camera.path
    body = None
    radii = []
    for moment in (0.7, 2.1, 3.4):
        pose = path.sample(moment)
        assert pose.position.y >= 0.85, "a key must not dip below the body"
        if body is None:
            body = game.sim.eye()
        radii.append(((pose.position.x - body.x) ** 2 + (pose.position.z - body.z) ** 2) ** 0.5)
    assert radii == sorted(radii), radii
    assert radii[0] < radii[-1]


def test_two_deaths_produce_the_same_camera_trajectory():
    def trajectory():
        game = _dying_game()
        poses = []
        for _ in range(120):
            _tick(game, 1)
            cam = game.scene.camera
            poses.append((round(cam.position.x, 9), round(cam.position.y, 9), round(cam.position.z, 9), round(cam.yaw, 9), round(cam.pitch, 9)))
        return poses

    assert trajectory() == trajectory()


def test_the_cinematic_does_not_touch_the_snapshot_or_the_hash():
    cinematic = _dying_game()
    _tick(cinematic, 180)

    # The record is the sim snapshot plus the SFX drop counter, nothing else:
    # no camera pose, no path time, no cinematic flag can leak into a save.
    snapshot = cinematic.snapshot()
    assert set(snapshot) == set(cinematic.sim.snapshot()) | {"dropped_sfx"}
    assert snapshot["dropped_sfx"] == cinematic.dropped_sfx == 0
    for leaked in ("camera", "death_camera", "cinematic", "camera_path"):
        assert leaked not in snapshot
    # and the authored path is reported separately, not folded into the record
    assert cinematic.death_camera_report is not None
    assert "path" in cinematic.death_camera_report


def test_build_scene_clears_the_cinematic():
    game = _dying_game()
    _tick(game, 1)
    assert game._death_camera is not None
    game.build_scene()
    assert game._death_camera is None
    assert game.death_camera_report is None
    assert game.scene.camera.fov_y == pytest.approx(75.0)


# ---- death cinematic tuning (juice.json) ------------------------------
def test_defaults_are_used_when_the_block_is_missing_or_wrong():
    from shooter.game import _death_cinematic_tuning

    for juice in ({}, None, {"death_cinematic": None}, {"death_cinematic": []}, {"death_cinematic": "nope"}):
        tuning = _death_cinematic_tuning(juice)
        assert tuning["body_height"] == 0.85
        assert tuning["start_forward"] == 4.0
        assert tuning["start_fov"] == 75.0
        assert [key["time"] for key in tuning["keys"]] == [0.7, 2.1, 3.4]
        assert [key["fov"] for key in tuning["keys"]] == [68.0, 58.0, 52.0]
        assert [key["radius"] for key in tuning["keys"]] == [2.0, 3.2, 4.6]


def test_bad_fields_fall_back_individually_not_wholesale():
    from shooter.game import _death_cinematic_tuning

    tuning = _death_cinematic_tuning(
        {
            "death_cinematic": {
                "body_height": "tall",
                "start_forward": -2.0,
                "start_fov": float("nan"),
                "keys": [
                    {"time": "soon", "angle": True, "radius": -1.0,
                     "height_above_eye": float("inf"), "fov": 0.0},
                ],
            }
        }
    )
    # every invalid value is replaced, and an absent key list is padded from defaults
    assert tuning["body_height"] == 0.85
    assert tuning["start_forward"] == 4.0
    assert tuning["start_fov"] == 75.0
    assert len(tuning["keys"]) == 3
    first = tuning["keys"][0]
    assert first["time"] == 0.7
    assert first["angle"] == 0.0
    assert first["radius"] == 2.0
    assert first["height_above_eye"] == 1.15
    assert first["fov"] == 68.0
    assert [key["time"] for key in tuning["keys"][1:]] == [2.1, 3.4]


def test_out_of_range_lenses_fall_back_to_the_authored_default():
    from shooter.game import _death_cinematic_tuning

    for bad in (0.0, 180.0, -12.0, 400.0):
        tuning = _death_cinematic_tuning(
            {"death_cinematic": {"start_fov": bad, "keys": [{"fov": bad}]}}
        )
        assert tuning["start_fov"] == 75.0, bad
        assert tuning["keys"][0]["fov"] == 68.0, bad


def test_a_valid_override_is_honoured():
    from shooter.game import _death_cinematic_tuning

    tuning = _death_cinematic_tuning(
        {
            "death_cinematic": {
                "body_height": 1.1,
                "start_forward": 2.5,
                "start_fov": 60.0,
                "keys": [
                    {"time": 0.5, "angle": 0.3, "radius": 3.0, "height": 2.0, "fov": 64.0},
                    {"time": 1.5, "angle": 1.0, "radius": 4.0, "height_above_eye": 0.8, "fov": 60.0},
                    {"time": 2.5, "angle": 2.0, "radius": 5.0, "height": 2.4, "fov": 55.0},
                ],
            }
        }
    )
    assert tuning["body_height"] == 1.1
    assert tuning["start_forward"] == 2.5
    assert tuning["start_fov"] == 60.0
    assert [key["time"] for key in tuning["keys"]] == [0.5, 1.5, 2.5]
    assert tuning["keys"][0]["height"] == 2.0
    assert tuning["keys"][0]["height_above_eye"] is None
    assert tuning["keys"][1]["height_above_eye"] == 0.8


def test_a_key_with_no_height_of_either_kind_gets_the_default_height():
    from shooter.game import _death_cinematic_tuning

    tuning = _death_cinematic_tuning(
        {"death_cinematic": {"keys": [{"time": 0.9}, {}, {}]}}
    )
    first, second, third = tuning["keys"]
    assert first["time"] == 0.9
    assert (first["height"], first["height_above_eye"]) == (None, 1.15)
    assert (second["height"], second["height_above_eye"]) == (2.15, None)
    assert (third["height"], third["height_above_eye"]) == (2.65, None)


def test_values_that_would_raise_inside_the_builder_fall_back():
    from shooter.game import _death_cinematic_tuning

    # a lens outside 0..180, a zero look-ahead, a zero orbit radius, key times
    # that do not increase, and a first orbit key at the opening key's time
    hostile = (
        {"start_fov": 0.0},
        {"start_fov": 400.0},
        {"start_forward": 0.0},
        {"keys": [{"time": 2.0}, {"time": 1.0}, {"time": 3.0}]},
        {"keys": [{"time": 0.0}]},
        {"keys": [{"time": 3.0}, {"time": 3.0}, {"time": 4.0}]},
        {"keys": [{"radius": 0.0}]},
    )
    for block in hostile:
        tuning = _death_cinematic_tuning({"death_cinematic": block})
        assert 0.0 < tuning["start_fov"] < 180.0, block
        assert tuning["start_forward"] > 0.0, block
        times = [key["time"] for key in tuning["keys"]]
        assert times[0] > 0.0, block
        assert all(later > earlier for earlier, later in zip(times, times[1:])), block
        assert all(key["radius"] > 0.0 for key in tuning["keys"]), block
        assert all(0.0 < key["fov"] < 180.0 for key in tuning["keys"]), block


def test_a_malformed_tuning_block_still_produces_a_playable_cinematic():
    game = _dying_game()
    game.sim.juice["death_cinematic"] = {
        "body_height": "tall",
        "start_fov": float("inf"),
        "keys": "not a list",
    }
    _tick(game, 1)

    assert game._death_camera is not None, "a bad juice edit must not break death"
    assert game.campaign_camera_report is None, "death must not start the victory path"
    assert game.death_camera_report["path"]["duration"] == pytest.approx(3.4)
