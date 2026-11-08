"""Audio proof: a critical kill gets its own reward cue.

Critical kills roll at 12% and pay double bounty, but the only signals were
the generic kill voice and a larger score pop. A distinct high chime and
CRITICAL caption make the reward legible without changing the reward roll.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import _Enemy


def _kill_game(critical: bool) -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.engagement["reward"] = {
        "standard_p": 0.0 if critical else 1.0,
        "critical_p": 1.0 if critical else 0.0,
        "critical_mult": 2.0,
        "cache_p": 0.0,
        "cache_reserve": 12,
        "cache_expire_s": 8.0,
    }
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = [
        _Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=1, max_hp=30)
    ]
    return g


def test_critical_kill_plays_a_distinct_cue():
    g = _kill_game(True)
    clips: list[str] = []
    g.set_clip_hook(lambda clip, gain: clips.append(clip.name))
    g.update(1.0 / 60.0, ActionState(held=frozenset({"fire"})))
    assert g.sim.kills == 1
    assert "critical" in clips
    assert g.sound_cue == "CRITICAL"


def test_standard_kill_keeps_the_plain_kill_cue():
    g = _kill_game(False)
    clips: list[str] = []
    g.set_clip_hook(lambda clip, gain: clips.append(clip.name))
    g.update(1.0 / 60.0, ActionState(held=frozenset({"fire"})))
    assert g.sim.kills == 1
    assert "critical" not in clips
    assert g.sound_cue != "CRITICAL"


def test_critical_voice_differs_from_the_kill_voice():
    g = ShooterGame()
    g.build_scene()
    critical = g._clips["critical"]
    kill = g._clips["kill"]
    assert critical.samples != kill.samples
    assert critical.duration() != kill.duration()
