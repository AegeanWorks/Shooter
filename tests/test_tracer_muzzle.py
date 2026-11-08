"""Graphics proof: player tracers start at the gun muzzle.

Tracers began at the camera eye, so beams appeared from the crosshair while
the viewmodel sat lower-right. The hitscan origin stays at the eye; only the
drawn beam start moves to the barrel tip.
"""

from shooter.sim import Sim


def test_player_tracer_starts_at_the_muzzle():
    s = Sim(seed=1)
    s._fire(s.weapons["pulse"], [])
    tracer = s.tracers[-1]
    eye = s.eye()
    assert tracer["x0"] > eye.x + 0.1, tracer
    assert tracer["y0"] < eye.y - 0.1, tracer
    assert tracer["z0"] < eye.z - 0.5, tracer


def test_tracer_still_ends_at_the_hit_distance():
    s = Sim(seed=1)
    s._fire(s.weapons["pulse"], [])
    tracer = s.tracers[-1]
    assert tracer["z1"] < tracer["z0"], tracer
    assert tracer["life"] > 0.0
