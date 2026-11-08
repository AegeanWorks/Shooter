"""Audio proof: an overdrive kill is announced as such.

Kills during the eight-second x2 state emitted `overdrive_hit` but the game
only played the normal kill voice; the power payoff was unacknowledged.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import _Enemy


def _kill(overdrive: bool) -> tuple[ShooterGame, list[str]]:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = [
        _Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=1, max_hp=30)
    ]
    g.sim.overdrive_t = 3.0 if overdrive else 0.0
    clips: list[str] = []
    g.set_clip_hook(lambda clip, gain: clips.append(clip.name))
    g.update(1.0 / 60.0, ActionState(held=frozenset({"fire"})))
    return g, clips


def test_overdrive_kill_plays_a_distinct_cue():
    g, clips = _kill(True)
    assert g.sim.kills == 1
    assert "overdrive_hit" in clips, clips
    assert g.sound_cue == "OVERDRIVE KILL"


def test_normal_kill_keeps_the_plain_cue():
    g, clips = _kill(False)
    assert g.sim.kills == 1
    assert "overdrive_hit" not in clips
    assert g.sound_cue != "OVERDRIVE KILL"


def test_overdrive_kill_voice_differs_from_the_kill_voice():
    g = ShooterGame()
    g.build_scene()
    boosted = g._clips["overdrive_hit"]
    kill = g._clips["kill"]
    assert boosted.samples != kill.samples
    assert boosted.duration() != kill.duration()
