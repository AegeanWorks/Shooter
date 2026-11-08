"""Levels proof: the launch pad pulses to draw the eye.

The pad is one existing node; a small sine scale pulse makes the launch
spot readable from the approach without new draws or colliders.
"""

from shooter.game import ShooterGame


def test_pad_pulses_with_time():
    g = ShooterGame()
    g.build_scene()
    pad = g._approach_pad
    base = float(pad.transform.scale.x)
    g.sim.time = 0.52
    g._sync_scene()
    pulsed = float(pad.transform.scale.x)
    assert pulsed > base * 1.03, (base, pulsed)
    g.sim.time = 0.0
    g._sync_scene()
    assert abs(float(pad.transform.scale.x) - base) < 1e-6
