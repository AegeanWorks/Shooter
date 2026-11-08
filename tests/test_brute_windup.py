"""Combat-feel proof: the brute slam has a readable windup.

The brute dealt its 20-damage slam on the first in-range frame. A 0.35 s
windup with a BRUTE WINDUP event now separates the tell from the hit.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.sim import Sim, _Enemy


def _sim() -> Sim:
    s = Sim(seed=1)
    s.wave = 2
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.player_pos = Vec3(0.0, 0.9002, 8.0)
    s.body = s.body.__class__(
        position=Vec3(0.0, 0.9002, 8.0), half_extents=s.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    s.enemies = [
        _Enemy(etype="brute", pos=Vec3(0.0, 0.7, 5.8), hp=120,
               max_hp=120, attack_cd=0.0)
    ]
    return s


def test_brute_first_frame_is_a_windup_not_a_hit():
    s = _sim()
    events = s.step(1.0 / 60.0, ActionState())
    assert "brute_windup" in events, events
    assert "brute_slam" not in events
    assert "hurt" not in events
    assert s.hp == 100
    assert s.enemies[0].windup_t > 0.0


def test_brute_windup_still_lands_after_the_delay():
    s = _sim()
    events = s.step(1.0 / 60.0, ActionState())
    assert "brute_windup" in events
    for _ in range(40):
        events += s.step(1.0 / 60.0, ActionState())
        if "brute_slam" in events:
            break
    assert "brute_slam" in events, events
    assert "hurt" in events, events
    assert s.hp == 80
