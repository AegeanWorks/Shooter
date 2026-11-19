"""Keystone testbed: root motion of the shipped enemy idle clips.

`root_motion` was one of 21 Keystone modules the testbed never imported.
`idle_root_motion_report()` extracts each shipped clip's subject delta over a
short window, proves the pose can be baked in place, and returns JSON for AI or
soak consumers. It is an on-demand query: no scene or sim state is written.
"""

from keystone.replay import stable_hash
from keystone.root_motion import in_place_pose

from shooter.anim import CLIP_NAMES
from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_root_motion_report_covers_the_four_idle_clips():
    report = _game().idle_root_motion_report()
    assert report["schema"] == 1 and report["window"] == 0.3
    assert set(report["clips"]) == set(CLIP_NAMES)
    assert all(item["schema"] == 1 and len(item["position"]) == 3
               for item in report["clips"].values())


def test_the_measured_yaws_band_the_shipped_clips():
    clips = _game().idle_root_motion_report()["clips"]
    assert clips["wisp_idle"]["yaw"] > 1.0, clips["wisp_idle"]
    assert 0.0 < clips["warden_idle"]["yaw"] < 0.1, clips["warden_idle"]
    assert clips["mite_idle"]["yaw"] > clips["warden_idle"]["yaw"]


def test_a_full_loop_closes_to_identity():
    report = _game().idle_root_motion_report(window=2.0)
    assert all(abs(item["yaw"]) < 1e-5 for item in report["clips"].values())


def test_the_in_place_pose_resets_the_subject():
    g = _game()
    assert g.idle_root_motion_report()["in_place"] is True
    pose = g._enemy_anim.clips["wisp_idle"].sample(0.3)
    flat = in_place_pose(pose, "subject")
    subject = flat["subject"]
    assert (subject.position.x, subject.scale.x, subject.rotation.w) == (0.0, 1.0, 1.0)
    assert flat is not pose


def test_repeated_reports_are_stable_and_never_touch_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    first = g.idle_root_motion_report()
    assert g.idle_root_motion_report() == first
    assert stable_hash(g.snapshot()) == before
