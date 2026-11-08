"""Enemies proof: warden summons leave origin markers.

`boss_summon` had audio and a caption, but the escorts appeared with no
origin cue. The sim records their positions (not in the snapshot); the game
reuses the spawn-marker pool. Summon behavior and damage are unchanged.
"""

import math

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import Sim, _Enemy


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    return g


def test_summon_positions_are_recorded():
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.enemies = [
        _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 5.0), hp=600, max_hp=600,
               summon_cd=0.0)
    ]
    events = s.step(1.0 / 60.0, ActionState())
    assert "boss_summon" in events, events
    assert len(s.summon_positions) == 2, s.summon_positions
    for pos in s.summon_positions:
        distance = math.hypot(pos.x - 0.0, pos.z - 5.0)
        assert 1.0 <= distance <= 2.6, (distance, pos)


def test_boss_summon_adds_spawn_marks():
    g = _game()
    g.sim.summon_positions = [Vec3(1.0, 0.5, 2.0), Vec3(-1.0, 0.5, 2.0)]
    g._play_event("boss_summon")
    assert len(g.spawn_marks) == 2, g.spawn_marks
    assert {round(mark["x"], 1) for mark in g.spawn_marks} == {-1.0, 1.0}
