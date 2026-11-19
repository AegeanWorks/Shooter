"""Keystone testbed: root-motion presentation on a local container rig.

`root_motion_presenter` was one of five Keystone modules the corrected coverage
scan still found unconsumed. `idle_presenter_preview()` builds a tiny local
scene, steps a RootMotionBody through its presenter and reports the container
pose plus the child nodes the in-place pose actually updated. Nothing in the
game's scene or sim is touched.
"""

from keystone.replay import stable_hash

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_the_preview_reports_a_container_and_its_applied_child():
    result = _game().idle_presenter_preview()
    assert result["schema"] == 1
    assert result["before"]["schema"] == 1 and result["after"]["schema"] == 1
    assert result["container"] == "preview-container"
    assert "subject" in result["updated"]
    assert result["pose_nodes"] == ["subject"]


def test_the_container_follows_the_body_and_turns():
    result = _game().idle_presenter_preview(frames=12)
    before, after = result["before"], result["after"]
    assert before["position"] == [0.0, 0.9, 0.0]
    assert after["position"] != before["position"]
    assert after["yaw"] != before["yaw"]
    assert after["motion"]["yaw"] != 0.0


def test_zero_frames_leave_the_report_at_the_start():
    result = _game().idle_presenter_preview(frames=0)
    assert result["before"] == result["after"]


def test_the_preview_is_reproducible():
    g = _game()
    assert g.idle_presenter_preview() == g.idle_presenter_preview()


def test_presenting_a_rig_never_touches_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    g.idle_presenter_preview(frames=30)
    assert stable_hash(g.snapshot()) == before
