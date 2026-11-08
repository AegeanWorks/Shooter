"""Keystone mechanics testbed: character physics and the fixed-step clock.

Covers the AABB CharacterBody/CharacterController paths the shooter uses
(gravity settle, step-up, tall-step block, cover slide) and the
FixedStepClock release/catch-up behavior the Engine loop relies on.
"""

from keystone.character import CharacterBody, CharacterController
from keystone.clock import FixedStepClock
from keystone.math3d import Vec3
from keystone.physics import AABB, aabb_overlap

STEP = 1.0 / 60.0


def _ground(controller: CharacterController) -> float:
    return 0.5 + 0.9 + controller.skin


def test_character_gravity_settles_on_the_floor():
    controller = CharacterController(gravity=24.0)
    floor = AABB(Vec3(0.0, 0.0, 0.0), Vec3(5.0, 0.5, 5.0))
    body = CharacterBody(Vec3(0.0, 3.0, 0.0), Vec3(0.35, 0.9, 0.35))
    for _ in range(180):
        body = controller.step(body, Vec3(), STEP, [floor])
    assert body.on_ground is True
    assert abs(body.position.y - _ground(controller)) < 1e-3
    assert abs(body.velocity.y) < 1e-9


def test_character_steps_up_a_low_ledge_and_stops_at_a_tall_one():
    controller = CharacterController(gravity=24.0)
    floor = AABB(Vec3(0.0, 0.0, 0.0), Vec3(5.0, 0.5, 5.0))
    low = AABB(Vec3(2.0, 0.65, 0.0), Vec3(0.5, 0.15, 1.0))
    body = CharacterBody(Vec3(0.0, _ground(controller), 0.0), Vec3(0.35, 0.9, 0.35))
    for _ in range(120):
        body = controller.step(body, Vec3(2.0, 0.0, 0.0), STEP, [floor, low])
        if body.position.y > _ground(controller) + 0.2:
            break
    assert body.position.y > _ground(controller) + 0.2, body.position
    assert abs(body.position.y - (0.8 + 0.9)) < 0.05, body.position

    tall = AABB(Vec3(2.0, 1.4, 0.0), Vec3(0.5, 0.9, 1.0))
    blocked = CharacterBody(Vec3(0.0, _ground(controller), 0.0), Vec3(0.35, 0.9, 0.35))
    for _ in range(120):
        blocked = controller.step(blocked, Vec3(2.0, 0.0, 0.0), STEP, [floor, tall])
    assert blocked.position.x < 2.0 - 0.5 - 0.35, blocked.position
    assert blocked.on_ground is True


def test_character_slides_along_cover_without_penetration():
    controller = CharacterController(gravity=24.0)
    floor = AABB(Vec3(0.0, 0.0, 0.0), Vec3(5.0, 0.5, 5.0))
    cover = AABB(Vec3(0.0, 0.9, -3.0), Vec3(5.0, 0.9, 0.5))
    body = CharacterBody(Vec3(0.0, _ground(controller), 0.0), Vec3(0.35, 0.9, 0.35))
    for _ in range(60):
        body = controller.step(body, Vec3(2.0, 0.0, -4.0), STEP, [floor, cover])
    assert body.position.x > 0.5, body.position
    assert body.position.z > -2.5 + 0.35 - 1e-6, body.position
    assert not aabb_overlap(body.box(), cover)
    assert body.on_ground is True


def test_fixed_step_clock_releases_whole_steps():
    clock = FixedStepClock(step=0.1, max_frame=0.2)
    assert clock.advance(0.0) == []
    assert clock.advance(0.05) == []
    released = clock.advance(0.1)
    assert len(released) == 1 and abs(released[0] - 0.1) < 1e-12
    assert clock.advance(0.15) == []
    released = clock.advance(0.25)
    assert len(released) == 1, released
    assert clock.advance(0.2) == []  # backwards time is ignored


def test_fixed_step_clock_caps_catch_up_and_keeps_running():
    clock = FixedStepClock(step=0.1, max_frame=0.2)
    clock.reset(0.0)
    first = clock.advance(100.0)
    second = clock.advance(200.0)
    assert first == [0.1, 0.1], first
    assert second == [0.1, 0.1], second
    assert clock.advance(200.05) == []
    assert len(clock.advance(200.15)) == 1


def test_clock_and_controller_reject_invalid_configuration():
    import pytest

    with pytest.raises(ValueError):
        FixedStepClock(step=0.0)
    with pytest.raises(ValueError):
        FixedStepClock(step=0.1, max_frame=0.05)
    with pytest.raises(ValueError):
        CharacterController(gravity=-1.0)
    with pytest.raises(ValueError):
        CharacterBody(Vec3(), Vec3(-1.0, 1.0, 1.0))
    with pytest.raises(ValueError):
        CharacterController().step(CharacterBody(Vec3()), Vec3(), 0.0, [])
