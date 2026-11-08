"""Audio proofs: wave spawns get a voice and a direction-less warning.

The spawn marker exists (cycle 26), but the event was silent. The clip and
caption are presentation-only; the sim spawn and marker are unchanged.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    # two queued so one spawn cannot be mistaken for a wave clear
    g.sim.spawn_queue = ["mite", "mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    return g


def test_spawn_event_gets_a_voice_and_caption():
    g = _game()
    g.sim.spawn_pos = Vec3(1.0, 0.5, -2.0)
    g._play_event("spawn")
    assert g.sound_cue == "HOSTILE INBOUND", g.sound_cue
    assert g.sound_cue_t > 0.0
    assert g.mixer.voice_count() >= 1
    assert g._clips["spawn"].duration() > 0.0


def test_real_spawn_sets_the_cue_and_marker():
    g = _game()
    g.sim.spawn_t = 0.0
    g.update(1.0 / 60.0, ActionState())
    assert g.sim.enemies, "spawn did not happen"
    assert g.sound_cue == "HOSTILE INBOUND", g.sound_cue
    assert len(g.spawn_marks) == 1, g.spawn_marks
