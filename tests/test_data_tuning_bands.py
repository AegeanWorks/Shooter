"""Survivors of the engagement/levels mutation sweep, pinned by behaviour.

Cycles 170/174 swept sim constants and juice.json. A 10-case sweep of the two
remaining data documents found three values a designer could double with every
test green: cache_expire_s, overdrive.duration_s and levels.max_alive. These
tests assert the observable result inside a design band, not the raw literal.
"""

import math

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.sim import Sim, _Enemy


def test_a_cache_drop_expires_on_the_shipped_time_window():
    s = Sim(seed=1)
    s.spawn_queue = []
    s.spawn_t = 999.0
    s.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=5, max_hp=30)]
    # Force a cache drop but keep cache_expire_s from the shipped document so
    # a data edit is visible to this test.
    s.engagement["reward"]["standard_p"] = 0.0
    s.engagement["reward"]["critical_p"] = 0.0
    s.engagement["reward"]["cache_p"] = 1.0
    s.yaw = 0.0
    eye_y = s.player_pos.y + 0.72
    s.pitch = math.atan2(0.8 - eye_y, abs(2.0 - s.player_pos.z))
    s._fire(s.weapons["pulse"], [])
    assert len(s.caches) == 1
    assert 6.0 <= float(s.caches[0]["ttl"]) <= 10.0, s.caches
    for _ in range(600):
        s.step(1.0 / 60.0, ActionState())
    assert s.caches == []


def test_overdrive_lasts_the_shipped_duration():
    s = Sim(seed=1)
    assert s.overdrive_preview()["ok"] is True
    s._try_overdrive([])
    assert 6.0 <= float(s.overdrive_t) <= 10.0, s.overdrive_t
    for _ in range(600):
        s.step(1.0 / 60.0, ActionState())
    assert s.overdrive_t == 0.0


def test_the_alive_enemy_cap_is_enforced_during_a_long_wave():
    s = Sim(seed=1)
    s.hp = 100000
    s.spawn_queue = ["mite"] * 60
    s.spawn_t = 0.0
    for _ in range(1600):
        s.step(1.0 / 60.0, ActionState())
    alive = sum(1 for enemy in s.enemies if enemy.alive)
    assert 0 < alive <= 24, alive
