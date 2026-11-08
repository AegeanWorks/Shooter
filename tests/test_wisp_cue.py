"""Audio proof: a wisp shot gets its own warning cue.

The wisp bolt is visible (cycle 38) but silent until it hits; the only
sound was the generic hurt clip. `wisp_bolt` maps to a distinct warning
without changing the bolt, LOS, damage or snapshot.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import Sim, _Enemy


def _sim() -> Sim:
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.player_pos = Vec3(0.0, 0.9002, 8.0)
    s.body = s.body.__class__(
        position=Vec3(0.0, 0.9002, 8.0), half_extents=s.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    s.enemies = [
        _Enemy(etype="wisp", pos=Vec3(5.0, 0.4, 4.0), hp=20, max_hp=20,
               attack_cd=0.0)
    ]
    return s


def test_wisp_attack_emits_its_own_event():
    s = _sim()
    events = s.step(1.0 / 60.0, ActionState())
    assert int(s.hp) == 94, (s.hp, events)
    assert "wisp_bolt" in events, events
    assert "hurt" in events, events


def test_wisp_bolt_gets_a_voice_and_caption():
    g = ShooterGame()
    g.build_scene()
    g._play_event("wisp_bolt")
    assert g.sound_cue == "WISP BOLT", g.sound_cue
    assert g.mixer.voice_count() >= 1
    assert g._clips["wisp_bolt"].duration() > 0.0
