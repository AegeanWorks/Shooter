"""Levels proof: a keystone lifecycle component pulses the launch pad.

The pad used to be driven by a hardcoded sine inside _sync_scene. The
deterministic component runtime now owns it: one PadPulse component on
the pad node, started once and updated by the fixed-step game update.
"""

from keystone.input import ActionState

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_lifecycle_drives_the_pad_pulse():
    g = _game()
    assert g._lifecycle is not None
    assert g._pad_pulse is not None
    base = float(g._approach_pad.transform.scale.x)
    assert abs(base - 1.4) < 1e-6, base
    report = g._lifecycle.describe()
    assert report["active"] is True, report
    assert report["started"] >= 1, report

    for _ in range(32):
        g.update(1.0 / 60.0, ActionState())

    pulsed = float(g._approach_pad.transform.scale.x)
    assert pulsed > base * 1.03, (base, pulsed)
    assert g._lifecycle.describe()["frame"] == 32
    assert g._pad_pulse.ticks == 32


def test_pad_starts_at_base_on_a_fresh_build():
    g = _game()
    assert abs(float(g._approach_pad.transform.scale.x) - 1.4) < 1e-6
