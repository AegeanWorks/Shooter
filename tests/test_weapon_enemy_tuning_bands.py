"""Survivors of the weapons/enemies mutation sweep, pinned by behaviour.

A 12-case full-suite sweep doubled values in weapons.json and enemies.json.
Seven were caught; five survived with all 778 tests green. These tests assert
observable results inside design bands, not the raw literals.
"""

import math

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.sim import Sim, _Enemy


def _aim(s: Sim, enemy: _Enemy) -> None:
    s.yaw = 0.0
    eye_y = s.player_pos.y + 0.72
    distance = abs(enemy.pos.z - s.player_pos.z)
    s.pitch = math.atan2((enemy.pos.y + 0.3) - eye_y, distance)


def _line(enemies: int = 3) -> tuple[Sim, list[_Enemy]]:
    s = Sim(seed=1)
    s.spawn_queue = []
    group = [
        _Enemy(etype="mite", pos=Vec3(0.0, 0.5, z), hp=300, max_hp=300)
        for z in (4.0, 6.0, 8.0)[:enemies]
    ]
    s.enemies = group
    return s, group


def test_every_enemy_has_coherent_shape_and_boss_cadence():
    """A zero speed/radius or a stubby body breaks movement/collision silently."""
    enemies = Sim(seed=1).enemy_defs
    for key, enemy in enemies.items():
        for field in ("hp", "speed", "dmg", "range", "score", "radius", "height"):
            assert float(enemy[field]) > 0.0, f"{key}: {field} must be positive"
        radius = float(enemy["radius"])
        height = float(enemy["height"])
        assert height >= 2.0 * radius, f"{key}: height {height} < diameter {2 * radius}"
    boss = enemies["warden"]
    assert 0.0 < float(boss["summon_first_s"]) < float(boss["summon_cd_s"])
    assert int(boss["summon_count"]) > 0
    assert float(boss["summon_clearance"]) > 0.0
    assert float(boss["attack_cd_s"]) > 0.0 and float(boss["windup_s"]) > 0.0


def test_every_weapon_has_coherent_falloff_and_counts():
    """A falloff that begins past max range is dead data; counts must be positive."""
    for key, weapon in Sim(seed=1).weapons.items():
        falloff = float(weapon["falloff_start"])
        rng = float(weapon["range"])
        assert 0.0 < falloff < rng, f"{key}: falloff_start={falloff} must be inside range={rng}"
        assert int(weapon["pellets"]) >= 1, key
        assert int(weapon["mag"]) > 0, key
        assert int(weapon["pierce"]) >= 1, key
        assert float(weapon["reload_s"]) >= 0.0, key


def test_scatter_fires_the_shipped_pellet_count():
    s, group = _line(1)
    s.weapon = "scatter"
    _aim(s, group[0])
    s._fire(s.weapons["scatter"], [])
    assert 6 <= len(s.tracers) <= 12, len(s.tracers)


def test_lance_deals_the_shipped_damage():
    s, group = _line()
    s.weapon = "lance"
    _aim(s, group[0])
    s._fire(s.weapons["lance"], [])
    damage = max(300 - enemy.hp for enemy in group)
    assert 45 <= damage <= 70, damage


def test_lance_pierces_the_shipped_number_of_enemies():
    s, group = _line()
    s.weapon = "lance"
    _aim(s, group[0])
    s._fire(s.weapons["lance"], [])
    assert s.hits == 2, s.hits


def test_pulse_falloff_applies_past_the_shipped_start_distance():
    s = Sim(seed=1)
    s.spawn_queue = []
    s.hp = 100000
    position = Vec3(15.0, 0.9, 19.0)
    s.player_pos = position
    s.body = s.body.__class__(
        position=position, half_extents=s.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    enemy = _Enemy(etype="mite", pos=Vec3(15.0, 0.5, -19.0), hp=300, max_hp=300)
    s.enemies = [enemy]
    s.weapon = "pulse"
    _aim(s, enemy)
    s._fire(s.weapons["pulse"], [])
    damage = 300 - enemy.hp
    assert 8 <= damage <= 11, damage


def test_the_warden_uses_the_shipped_attack_cooldown():
    s = Sim(seed=1)
    s.spawn_queue = []
    s.spawn_t = 999.0
    warden = _Enemy(
        etype="warden", pos=Vec3(0.0, 1.1, 5.0), hp=600, max_hp=600,
        attack_cd=0.0, summon_cd=999.0,
    )
    s.enemies = [warden]
    s.step(1.0 / 60.0, ActionState())
    assert 2.0 <= float(warden.attack_cd) <= 4.0, warden.attack_cd
