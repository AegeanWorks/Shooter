"""Gameplay-feel proofs: the jump apex and the coyote window are pinned.

A mutation sweep over `shooter/sim.py` found two constants that could change with
the whole suite green: `JUMP_SPEED` (7.2 -> 8.0, a 24% higher apex) and
`COYOTE_S` (0.12 -> 0.24, double the grace period). Both are things a player
feels immediately, and the level design leans on the apex: covers are 1.2 m or
taller while the jumpable platform is 0.7 m, so a taller jump changes which
surfaces are reachable at all.

`test_levels_platform.py` proves the platform *can* be reached; it does not pin
the apex, so a doubled jump still lands there. These tests pin the numbers.
"""

import math

from keystone.input import ActionState
from keystone.math3d import Vec3

import shooter.sim as sim_module
from shooter.sim import Sim

STEP = 1.0 / 60.0


def _jump_rise() -> float:
    """Peak height gained by a standing jump, measured from the ground."""
    sim = Sim(seed=1)
    sim.spawn_queue = []
    sim.spawn_t = 999.0
    base = sim.player_pos.y
    peak = base
    for index in range(120):
        action = ActionState(pressed=frozenset({"jump"})) if index == 0 else ActionState()
        sim.step(STEP, action)
        peak = max(peak, sim.player_pos.y)
    return peak - base


def test_the_standing_jump_rises_about_one_metre():
    """The apex is the level's reachability budget, not an incidental number.

    Measured at the shipped tuning: 1.020 m. Covers start at 1.2 m, so the jump
    must clear the 0.7 m platform and stay under a cover top.
    """
    rise = _jump_rise()
    assert 0.98 <= rise <= 1.06, (
        f"the jump rises {rise:.3f} m, outside the designed ~1.02 m. "
        "A taller jump changes which covers are reachable."
    )


def test_the_jump_clears_the_platform_but_stays_under_the_lowest_cover():
    """The design intent behind the apex, independent of the exact number."""
    rise = _jump_rise()
    covers = [float(c["h"]) for c in Sim(seed=1).levels["arena"]["covers"]]
    lowest_cover = min(h for h in covers if h > 0.7)
    platform = min(covers)

    assert rise > platform, "the 0.7 m platform must be jumpable"
    assert rise < lowest_cover, (
        f"a {rise:.2f} m jump would reach the {lowest_cover} m cover tops, "
        "turning cover into a vantage point"
    )


def _jump_after(frames: int) -> bool:
    """Leave the ground, wait, then try to jump; True when the buffered jump fires."""
    sim = Sim(seed=1)
    sim.spawn_queue = []
    sim.spawn_t = 999.0
    # High enough that the fall cannot land inside the window under test:
    # landing would re-arm the coyote timer and silently invalidate the probe.
    sim.player_pos = Vec3(0.0, 40.0, 0.0)
    sim.body = sim.body.__class__(
        position=sim.player_pos,
        half_extents=sim.body.half_extents,
        velocity=Vec3(),
        on_ground=False,
    )
    sim.coyote = sim_module.COYOTE_S
    for _ in range(frames):
        sim.step(STEP, ActionState())
    before = sim.body.velocity.y
    sim.step(STEP, ActionState(pressed=frozenset({"jump"})))
    return sim.body.velocity.y > before + 1.0


def test_the_coyote_window_is_short_but_not_zero():
    """A jump shortly after leaving the ground must land; a late one must not.

    COYOTE_S 0.12 is ~7 frames. Four frames is comfortably inside the window;
    ten is spent at the shipped tuning (0.12 - 10 frames < 0) but *alive* under a
    doubled 0.24 window, so the boundary pins the real grace period instead of
    restating the constant.
    """
    assert _jump_after(4) is True, "a jump 4 frames after leaving the ground must fire"
    assert _jump_after(10) is False, (
        "a jump 10 frames after leaving the ground must be refused; if this "
        "passes, COYOTE_S has grown toward a second grace period"
    )


def test_the_coyote_window_matches_its_declared_seconds():
    """The constant means what it says: about 0.12 s of grace."""
    frames = sim_module.COYOTE_S / STEP
    assert 6 <= round(frames) <= 9, (
        f"COYOTE_S {sim_module.COYOTE_S}s is {frames:.1f} frames at {math.floor(1/STEP)} Hz"
    )
