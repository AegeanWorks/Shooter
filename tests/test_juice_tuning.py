"""Presentation tuning bounds: the juice.json numbers a designer edits are wired.

A mutation sweep over juice.json doubled twelve feel constants and the suite
stayed green for nine of them. These tests pin the observable result of each
survivor inside a design band, so a mistyped number fails a test instead of
silently changing what the player sees. They assert behaviour, not the raw
literal from the file they are protecting.
"""

import math

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import Sim, _Enemy
from shooter.ui import draw_shooter, reticle_gap


def _warden_winding_up() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = [
        _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 5.0), hp=600, max_hp=600,
               summon_cd=999.0, windup_t=0.5),
    ]
    g._sync_scene()
    return g


def _aimed(hp: int) -> Sim:
    s = Sim(seed=1)
    s.spawn_queue = []
    s.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=hp, max_hp=30)]
    s.yaw = 0.0
    eye_y = s.player_pos.y + 0.72
    s.pitch = math.atan2(0.8 - eye_y, abs(2.0 - s.player_pos.z))
    return s


def test_slam_ring_bars_stay_a_thin_ground_ring():
    g = _warden_winding_up()
    visible = [n for n in g._slam_ring if n.visible]
    assert visible
    for node in visible:
        scale = node.transform.scale
        assert 0.15 <= scale.x <= 0.25, scale
        assert 0.015 <= scale.y <= 0.04, scale


def test_spawn_marker_stays_a_tall_thin_pillar():
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_pos = Vec3(1.0, 0.5, -2.0)
    g._play_event("spawn")
    g._sync_scene()
    visible = [n for n in g._spawn_nodes if n.visible]
    assert visible
    for node in visible:
        scale = node.transform.scale
        assert 0.12 <= scale.x <= 0.25, scale
        assert 2.0 <= scale.y <= 3.0, scale


def test_shipped_spawn_mark_cap_stays_in_the_budget_band():
    g = ShooterGame()
    g.build_scene()
    cap = int(g.sim.juice["spawn_mark"]["max"])
    assert 2 <= cap <= 6, cap
    assert len(g._spawn_nodes) == cap, len(g._spawn_nodes)


def test_pad_pulse_amplitude_stays_in_the_design_band():
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = []
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    base = float(g._approach_pad.transform.scale.x)
    peak = base
    for _ in range(64):
        g.update(1.0 / 60.0, ActionState())
        peak = max(peak, float(g._approach_pad.transform.scale.x))
    assert base * 1.05 <= peak <= base * 1.15, (base, peak)


def test_death_fx_caps_cover_every_shipped_enemy():
    """A missing cap falls back to 1.0 (full-size burst) - pin the lookup keys."""
    caps = dict(Sim(seed=1).juice.get("death_fx_scale", {}))
    roster = set(Sim(seed=1).enemy_defs)
    assert set(caps) == roster, f"death_fx_scale keys {set(caps)} != roster {roster}"
    for key, cap in caps.items():
        assert 0.0 < float(cap) <= 1.0, f"{key}: death FX cap {cap} out of band"
    # The boss uses the smallest cap so a 2.2 m white cube cannot fill the frame.
    assert float(caps["warden"]) == min(float(value) for value in caps.values())


def test_impact_burst_stays_in_the_design_band():
    s = _aimed(30)
    s.particles.clear()
    s._fire(s.weapons["pulse"], [])
    assert 8 <= s.particles.alive_count() <= 20, s.particles.alive_count()


def test_kill_burst_stays_in_the_design_band():
    s = _aimed(5)
    s.particles.clear()
    s._fire(s.weapons["pulse"], [])
    # one impact burst plus one kill burst (12 + 20 by the shipped tuning)
    assert 24 <= s.particles.alive_count() <= 44, s.particles.alive_count()


def test_muzzle_flash_lifetime_stays_in_the_design_band():
    s = Sim(seed=1)
    s._fire(s.weapons["pulse"], [])
    assert 0.08 <= s.flash_t <= 0.15, s.flash_t
    for _ in range(6):
        s.step(1.0 / 60.0, ActionState())
    assert s.flash_t < 0.01, s.flash_t


class _Canvas:
    width = 960
    height = 540

    def __init__(self) -> None:
        self.rects: list[tuple] = []
        self.texts: list[tuple] = []

    def rect(self, *args) -> None:
        self.rects.append(args)

    def text(self, *args) -> None:
        self.texts.append(args)


def test_hitmark_expands_the_reticle_by_the_design_gap():
    s = Sim(seed=1)
    s.weapon = "pulse"
    base = reticle_gap(s)
    s.hitmark_t = 0.1
    assert 2 <= reticle_gap(s) - base <= 6


def test_a_wide_spread_is_capped_by_the_reticle_budget():
    s = Sim(seed=1)
    s.weapons["wide"] = dict(s.weapons["pulse"], id="wide", spread_hip_deg=20.0)
    s.weapon = "wide"
    assert 30 <= reticle_gap(s) <= 50, reticle_gap(s)


def test_low_health_edge_alpha_stays_in_the_design_band():
    s = Sim(seed=1)
    s.hp = 30
    s.time = math.pi / 12.0  # sin(6t) = 1 at the shipped 6 Hz
    canvas = _Canvas()
    draw_shooter(canvas, canvas, s)
    peaks = [rect[4][3] for rect in canvas.rects
             if (rect[2] == 960 and rect[3] == 6) or (rect[2] == 6 and rect[3] == 540)]
    assert peaks and 0.35 <= max(peaks) <= 0.55, peaks


def test_death_fx_window_stays_in_the_design_band():
    s = _aimed(5)
    s._fire(s.weapons["pulse"], [])
    assert 0.10 <= float(s.enemies[0].death_t) <= 0.22, s.enemies[0].death_t


def test_pickup_burst_window_stays_in_the_design_band():
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    g.sim.wave = 2
    g.sim.pickup_active = True
    g.sim.pickup_taken = False
    rest_y = float(g.sim.player_pos.y)
    g.sim.player_pos = Vec3(0.0, rest_y, -6.0)
    g.sim.body = g.sim.body.__class__(
        position=g.sim.player_pos, half_extents=g.sim.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    g.update(1.0 / 60.0, ActionState())
    assert 0.2 <= float(g._pickup_fx_t) <= 0.35, g._pickup_fx_t


def test_killmark_and_hitmark_windows_stay_in_their_bands():
    killed = _aimed(5)
    killed._fire(killed.weapons["pulse"], [])
    assert 0.12 <= float(killed.killmark_t) <= 0.25, killed.killmark_t
    assert 0.08 <= float(killed.hitmark_t) <= 0.18, killed.hitmark_t


def test_hit_flinch_window_stays_in_the_design_band():
    s = _aimed(30)
    s._fire(s.weapons["pulse"], [])
    assert 0.18 <= float(s.enemies[0].hit_t) <= 0.32, s.enemies[0].hit_t
