"""Combat-feel proofs: reload duration and shot recoil are pinned.

A data mutation sweep over `shooter/data/*.json` caught every *outcome* number
(pulse damage, mite hp, mite damage, mite score) but let two *feel* numbers
through untouched: `kick_deg` 0.6 -> 1.2 and `reload_s` 1.1 -> 2.4, both on the
pulse rifle the player holds from the first frame.

Existing coverage could not catch them because it reads the value back out of
the data it is testing:

* `test_reload_dip.py` computes half the reload as `reload_s / 2.0` -- correct
  for any duration.
* `test_viewmodel_recoil.py` asserts `sim.kick > 0.0` -- true at any magnitude.

These tests assert the *observable* result instead: how long a reload takes in
frames, and how far one shot tilts the camera in radians.
"""

import math

from keystone.input import ActionState
from shooter.sim import Sim

STEP = 1.0 / 60.0


def _quiet_sim() -> Sim:
    sim = Sim(seed=1)
    sim.spawn_queue = []
    sim.spawn_t = 999.0
    return sim


def _reload_frames() -> tuple[int, int]:
    """Empty the pulse magazine, reload, and count the frames until it is full."""
    sim = _quiet_sim()
    sim.ammo["pulse"] = 0
    sim.reload_t = 0.0
    sim.step(STEP, ActionState(pressed=frozenset({"reload"})))
    frames = 0
    while sim.reload_t > 0.0 and frames < 900:
        sim.step(STEP, ActionState())
        frames += 1
    return frames, int(sim.ammo["pulse"])


def _kick_after_one_shot() -> float:
    sim = _quiet_sim()
    sim.step(STEP, ActionState(pressed=frozenset({"fire"})))
    return float(sim.kick)


def test_a_pulse_reload_takes_about_one_second():
    """1.1 s at 60 Hz is 66 frames; the rifle must not become a 2.4 s slog."""
    frames, loaded = _reload_frames()
    assert loaded > 0, "the magazine must come back full"
    assert 58 <= frames <= 74, (
        f"a pulse reload takes {frames} frames ({frames / 60:.2f}s); the designed "
        "value is 1.1s (66 frames)"
    )


def test_one_shot_tilts_the_camera_by_under_a_degree():
    """kick_deg 0.6 is 0.0105 rad; doubling it doubles the climb per shot."""
    kick = _kick_after_one_shot()
    degrees = math.degrees(kick)
    assert kick > 0.0, "firing must produce recoil at all"
    assert 0.45 <= degrees <= 0.75, (
        f"one shot tilts the camera {degrees:.3f} degrees; the designed value is "
        "0.6 degrees, and a doubled kick makes the rifle unmanageable"
    )


def test_recoil_decays_back_to_rest():
    """The kick is a transient, not a permanent aim offset."""
    sim = _quiet_sim()
    sim.step(STEP, ActionState(pressed=frozenset({"fire"})))
    assert sim.kick > 0.0
    for _ in range(120):
        sim.step(STEP, ActionState())
    assert sim.kick == 0.0


def test_the_magazine_refills_to_its_declared_size():
    """Reload restores the magazine the weapon data promises, no more, no less."""
    sim = _quiet_sim()
    declared = int(sim.weapons["pulse"]["mag"])
    sim.ammo["pulse"] = 0
    sim.reload_t = 0.0
    sim.step(STEP, ActionState(pressed=frozenset({"reload"})))
    for _ in range(200):
        if sim.reload_t <= 0.0:
            break
        sim.step(STEP, ActionState())
    assert int(sim.ammo["pulse"]) == declared
