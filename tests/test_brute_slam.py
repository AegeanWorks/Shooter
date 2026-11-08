"""Audio proof: the brute's 20-damage slam gets its own cue.

The warden has windup/slam voices; the brute only produced the generic
`hurt` clip. `brute_slam` maps to a distinct noise and caption without
changing damage, LOS or timing.
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
        _Enemy(etype="brute", pos=Vec3(0.0, 0.7, 6.5), hp=120, max_hp=120,
               attack_cd=0.0)
    ]
    return s


def test_brute_slam_emits_its_own_event():
    s = _sim()
    events = s.step(1.0 / 60.0, ActionState())
    assert "brute_windup" in events, events
    for _ in range(40):
        events += s.step(1.0 / 60.0, ActionState())
        if "brute_slam" in events:
            break
    assert int(s.hp) == 80, (s.hp, events)
    assert "brute_slam" in events, events
    assert "hurt" in events, events


def test_brute_slam_gets_a_voice_and_caption():
    g = ShooterGame()
    g.build_scene()
    g._play_event("brute_slam")
    assert g.sound_cue == "BRUTE SLAM", g.sound_cue
    assert g.mixer.voice_count() >= 1
    assert g._clips["brute_slam"].duration() > 0.0
