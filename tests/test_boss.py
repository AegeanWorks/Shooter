"""Warden boss proofs: wave-3 placement, telegraph/slam, summons, kill, HUD.

The endless wave-3 slot escalates from more of the same to a designed
threat. Waves 1-2 (the win path) stay untouched, so every existing
fairness/regression pin still measures the same fight.
"""

import json
import math
from pathlib import Path

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import Sim, _Enemy
from shooter.ui import draw_shooter

DATA = Path(__file__).parent.parent / "shooter" / "data"


def _load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _boss_sim(dist: float = 3.0) -> Sim:
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]  # block the wave-clear during the probe
    s.spawn_t = 999.0
    z = s.player_pos.z - dist
    s.enemies = [
        _Enemy(
            etype="warden",
            pos=Vec3(0.0, 1.2, z),
            hp=600,
            max_hp=600,
            summon_cd=999.0,
        )
    ]
    return s


def test_warden_data_and_wave_three():
    enemies = {e["id"]: e for e in _load("enemies.json")["enemies"]}
    assert "warden" in enemies
    w = enemies["warden"]
    assert int(w["hp"]) >= 400 and float(w["speed"]) < 3.0
    assert int(w["score"]) >= 1000
    waves = _load("levels.json")["waves"]
    assert int(waves[2].get("warden", 0)) == 1
    # the win path stays untouched
    assert int(waves[0].get("warden", 0)) == 0
    assert int(waves[1].get("warden", 0)) == 0


def test_warden_windup_then_slam():
    s = _boss_sim(3.0)
    hp0 = int(s.hp)
    events = s.step(1.0 / 60.0, ActionState())
    assert "boss_windup" in events, events
    assert float(s.enemies[0].windup_t) > 0.0
    for _ in range(45):
        events = s.step(1.0 / 60.0, ActionState())
        if "boss_slam" in events:
            break
    assert "boss_slam" in events, events
    assert int(s.hp) == hp0 - 30, (s.hp, events)
    assert "hurt" in events
    assert abs(s.hurt_from.x - s.enemies[0].pos.x) < 1e-6
    assert float(s.hurt_t) > 0.0


def test_warden_summons_mites():
    s = _boss_sim(10.0)
    s.enemies[0].summon_cd = 0.0
    events = s.step(1.0 / 60.0, ActionState())
    assert "boss_summon" in events, events
    mites = [e for e in s.enemies if e.etype == "mite" and e.alive]
    assert len(mites) == 2, [e.etype for e in s.enemies]
    boss = s.enemies[0]
    for m in mites:
        assert math.hypot(m.pos.x - boss.pos.x, m.pos.z - boss.pos.z) < 3.0


def test_warden_kill_scores():
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.enemies = [_Enemy(etype="warden", pos=Vec3(0.0, 1.2, 2.0), hp=12, max_hp=600,
                        summon_cd=999.0)]
    eye_y = s.player_pos.y + 0.72
    s.pitch = math.atan2((1.2 + 0.3) - eye_y, 6.0)
    events: list[str] = []
    for _ in range(12):
        if not any(e.alive for e in s.enemies):
            break
        s._fire(s.weapons["pulse"], events)
    assert s.kills == 1, (s.kills, events)
    assert s.score >= 2000, s.score
    assert "kill" in events


def test_warden_build_wave_is_queued():
    s = Sim(seed=1)
    s.wave = 3
    s.pickup_taken = True
    s._build_wave()
    assert "warden" in s.spawn_queue, s.spawn_queue


class _Canvas:
    def __init__(self) -> None:
        self.rects: list[tuple] = []
        self.texts: list[tuple] = []

    def rect(self, *args) -> None:
        self.rects.append(args)

    def text(self, *args) -> None:
        self.texts.append(args)


class _Hud:
    width = 960
    height = 540


def test_boss_core_follows_warden_and_hides():
    g = ShooterGame()
    g.build_scene()
    g.sim.enemies = [
        _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 3.5), hp=600, max_hp=600)
    ]
    g._sync_scene()
    assert g._boss_core is not None and g._boss_core.visible is True
    core = g._boss_core.transform.position
    # player is at z=8: the core sits on the boss face toward the player
    assert core.z > 3.5
    assert abs(core.x) < 1e-6
    g.sim.enemies = []
    g._sync_scene()
    assert g._boss_core.visible is False


def test_hud_draws_warden_health_bar():
    s = Sim(seed=1)
    s.enemies = [_Enemy(etype="warden", pos=Vec3(0.0, 1.2, 0.0), hp=300, max_hp=600)]
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    assert any("WARDEN" in str(t[2]) for t in canvas.texts), canvas.texts
    bars = [r for r in canvas.rects if r[4][0] >= 0.75 and r[4][1] <= 0.35]
    assert bars, canvas.rects
    assert max(r[2] for r in bars) >= 100, bars
    # half hp -> the filled bar is half the track width
    width = max(r[2] for r in bars)
    assert 120 <= width <= 160, width
