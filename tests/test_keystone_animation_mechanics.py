"""Keystone mechanics testbed: animation clips, controller and poses.

Covers the `.kanim` library, keyframe sampling/interpolation, controller
crossfades, loop event wrap and scene pose application used by the boss
core state machine.
"""

import tempfile

from keystone.animation import (
    AnimationClip,
    AnimationController,
    Track,
    animation_report,
    apply_pose,
)
from keystone.animation_library import AnimationLibrary
from keystone.math3d import Vec3
from keystone.scene import Node, Scene, Transform


def _bob_clip() -> AnimationClip:
    return AnimationClip(
        name="bob",
        position_tracks=(
            (
                "hero",
                Track(
                    times=(0.0, 0.5, 1.0),
                    values=(Vec3(0.0, 0.0, 0.0),
                            Vec3(0.0, 1.0, 0.0),
                            Vec3(0.0, 0.0, 0.0)),
                ),
            ),
        ),
        scale_tracks=(
            (
                "hero",
                Track(
                    times=(0.0, 0.5, 1.0),
                    values=(Vec3(1.0, 1.0, 1.0),
                            Vec3(1.2, 1.2, 1.2),
                            Vec3(1.0, 1.0, 1.0)),
                ),
            ),
        ),
        events=((0.5, "peak"),),
    )


def _low_clip() -> AnimationClip:
    return AnimationClip(
        name="low",
        position_tracks=(
            (
                "hero",
                Track(
                    times=(0.0, 1.0),
                    values=(Vec3(0.0, 2.0, 0.0), Vec3(0.0, 2.0, 0.0)),
                    interpolation="step",
                ),
            ),
        ),
    )


def test_animation_library_round_trips_and_samples():
    with tempfile.TemporaryDirectory() as directory:
        library = AnimationLibrary(directory)
        entry = library.save("bob", _bob_clip())
        assert entry.name == "bob"
        assert entry.error is None
        assert entry.duration == 1.0
        assert entry.track_count == 2
        loaded = library.load("bob")

    pose = loaded.sample(0.25)
    assert abs(pose["hero"].position.y - 0.5) < 1e-9
    assert abs(pose["hero"].scale.x - 1.1) < 1e-9
    assert loaded.events_in_range(0.0, 0.5) == ["peak"]
    assert loaded.events_in_range(0.0, 0.49) == []
    assert abs(loaded.sample(0.9)["hero"].position.y - 0.2) < 1e-9
    step = _low_clip().sample(0.9)
    assert step["hero"].position.y == 2.0


def test_controller_crossfades_and_reports_events():
    controller = AnimationController()
    controller.add(_bob_clip())
    controller.add(_low_clip())
    controller.play("bob")

    pose, events = controller.advance_with_events(0.5)
    assert "peak" in events, events
    assert abs(pose["hero"].position.y - 1.0) < 1e-9

    controller.crossfade("low", 0.4)
    assert controller.blending is True
    mid, _ = controller.advance_with_events(0.2)
    assert controller.blending is True
    assert 1.0 < mid["hero"].position.y < 2.0
    end, _ = controller.advance_with_events(0.3)
    assert controller.blending is False
    assert abs(end["hero"].position.y - 2.0) < 1e-9
    report = animation_report(controller)
    assert report["current"] == "low"
    assert report["clips"] == ["bob", "low"]


def test_controller_loops_and_refires_events():
    controller = AnimationController()
    controller.add(_bob_clip())
    controller.play("bob")
    controller.loop = True
    pose, events = controller.advance_with_events(1.2)
    assert "peak" in events, events
    assert abs(controller.time - 1.2) < 1e-9
    assert abs(pose["hero"].position.y - 0.4) < 1e-9


def test_apply_pose_writes_scene_nodes():
    scene = Scene()
    node = Node("hero", id="hero")
    scene.add(node)
    pose = _bob_clip().sample(0.5)
    updated = apply_pose(
        scene, {**pose, "missing": Transform(position=Vec3(9.0, 9.0, 9.0))}
    )
    assert updated == ["hero"], updated
    assert node.transform.position == Vec3(0.0, 1.0, 0.0)
    assert node.transform.scale == Vec3(1.2, 1.2, 1.2)
