"""Keystone testbed proof: the warden core is driven by a .kstate machine.

The recent keystone runtime feature (parameter-driven animation state
machines) and its file-backed library are exercised directly: a saved
calm/charge machine pulses the boss core during the existing windup.
Presentation only: sim damage, timing and hash are unchanged.
"""

from pathlib import Path

from keystone.input import ActionState
from keystone.math3d import Vec3
from keystone.state_machine_library import StateMachineLibrary

from shooter.game import ShooterGame
from shooter.sim import _Enemy

DATA = Path(__file__).parent.parent / "shooter" / "data"


def _library() -> StateMachineLibrary:
    return StateMachineLibrary(DATA)


def test_warden_core_machine_loads_from_the_library():
    entry = _library().entry("warden_core")
    assert entry.error is None, entry.error
    assert entry.states == 2, entry.states
    assert entry.transitions == 2, entry.transitions
    assert entry.current == "calm", entry.current


def test_core_clips_target_the_scene_node():
    machine = _library().load("warden_core")
    calm = machine.states["calm"].clip
    charge = machine.states["charge"].clip
    assert calm.node_ids() == ["warden-core"]
    assert charge.node_ids() == ["warden-core"]
    assert charge.duration() < calm.duration()


def test_machine_breathes_calm_then_pulses_charge():
    machine = _library().load("warden_core")
    calm_peak = 0.0
    for _ in range(72):  # one 1.2 s calm loop
        pose = machine.advance(1.0 / 60.0)
        calm_peak = max(calm_peak, float(pose["warden-core"].scale.x))
    assert 1.03 < calm_peak < 1.10, calm_peak

    machine.set_parameter("windup", 1.0)
    charge_peak = 0.0
    for _ in range(30):  # 0.5 s charge loop
        pose = machine.advance(1.0 / 60.0)
        charge_peak = max(charge_peak, float(pose["warden-core"].scale.x))
    assert machine.current == "charge", machine.current
    assert charge_peak > 1.25, charge_peak

    machine.set_parameter("windup", 0.0)
    for _ in range(40):
        machine.advance(1.0 / 60.0)
    assert machine.current == "calm", machine.current


def _game(windup_s: float) -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    sim = g.sim
    sim.wave = 3
    sim.spawn_queue = ["mite"]
    sim.spawn_t = 999.0
    sim.player_pos = Vec3(0.0, 0.9002, 8.0)
    sim.body = sim.body.__class__(
        position=Vec3(0.0, 0.9002, 8.0), half_extents=sim.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    sim.hvel = Vec3()
    sim.yaw = 0.0
    sim.pitch = 0.0
    sim.enemies = [
        _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 4.0), hp=600,
               max_hp=600, windup_t=windup_s, attack_cd=999.0,
               summon_cd=999.0)
    ]
    return g


def test_game_core_pulses_with_the_keystone_machine():
    g = _game(0.7)
    assert g._boss_anim is not None
    peak = 0.0
    for _ in range(24):
        g.update(1.0 / 60.0, ActionState())
        peak = max(peak, float(g._boss_core.transform.scale.x))
    assert g._boss_core.visible
    assert peak > 1.25, peak
    assert g._boss_anim.current == "charge", g._boss_anim.current

    for _ in range(60):
        g.update(1.0 / 60.0, ActionState())
    assert g._boss_anim.current == "calm", g._boss_anim.current
    assert float(g._boss_core.transform.scale.x) <= 1.08


def test_core_is_hidden_without_a_warden():
    g = ShooterGame()
    g.build_scene()
    assert g._boss_anim is not None
    assert g._boss_core.visible is False
