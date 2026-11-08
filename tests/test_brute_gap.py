"""Enemy proof: a brute must close its 2.5-3.0 m no-man's-land.

Brutes moved only while farther than 3 m but slammed only within 2.5 m. At
2.7 m from a stationary player the brute stood still forever.
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
        _Enemy(etype="brute", pos=Vec3(0.0, 0.7, 5.3), hp=120,
               max_hp=120, attack_cd=0.0)
    ]
    return s


def test_brute_closes_the_three_meter_dead_zone():
    s = _sim()
    start = abs(s.enemies[0].pos.z - s.player_pos.z)
    assert 2.6 < start < 2.8, start
    events: list[str] = []
    for _ in range(240):
        events += s.step(1.0 / 60.0, ActionState())
    assert "brute_slam" in events, events
    assert s.hp < 100, s.hp
