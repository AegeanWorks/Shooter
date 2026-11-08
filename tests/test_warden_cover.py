"""Enemy proof: the warden slam is blocked by cover.

The warden branch applied its 30-damage slam on distance and vertical reach
only; unlike the brute and wisp paths it never checked line of sight. A
cover between the boss and player should stop the slam.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.sim import Sim, _Enemy


def _slam(warden_z: float) -> tuple[Sim, list[str]]:
    s = Sim(seed=1)
    s.wave = 3
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.player_pos = Vec3(0.0, 0.9002, -8.5)
    s.body = s.body.__class__(
        position=Vec3(0.0, 0.9002, -8.5), half_extents=s.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    s.enemies = [
        _Enemy(etype="warden", pos=Vec3(0.0, 1.1, warden_z), hp=600,
               max_hp=600, windup_t=0.01, summon_cd=999.0)
    ]
    events = s.step(1.0 / 60.0, ActionState())
    return s, events


def test_cover_blocks_the_warden_slam():
    s, events = _slam(-10.7)  # north cover sits between z -10.5 and -9.5
    assert "boss_slam" in events, events
    assert s.hp == 100, s.hp
    assert "hurt" not in events, events


def test_open_field_warden_slam_still_hits():
    s, events = _slam(-7.5)
    assert "boss_slam" in events
    assert s.hp == 70, s.hp
    assert "hurt" in events, events
