"""Audio proof: a low-health wave clear announces CLUTCH CLEAR.

The sim increments `clutch` when a wave is cleared at 30 HP or less, but the
game ignored the event; only the generic wave voice/caption played.
"""

from keystone.input import ActionState

from shooter.game import ShooterGame


def _clear(hp: int) -> tuple[ShooterGame, list[str]]:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = []
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    g.sim.hp = hp
    clips: list[str] = []
    g.set_clip_hook(lambda clip, gain: clips.append(clip.name))
    g.update(1.0 / 60.0, ActionState())
    return g, clips


def test_low_health_clear_plays_the_clutch_cue():
    g, clips = _clear(30)
    assert g.sim.clutch == 1
    assert "clutch" in clips, clips
    assert "wave" in clips, clips
    assert g.sound_cue == "CLUTCH CLEAR"


def test_normal_clear_keeps_the_wave_cue():
    g, clips = _clear(100)
    assert g.sim.clutch == 0
    assert "clutch" not in clips
    assert g.sound_cue == "WAVE CLEAR"


def test_clutch_voice_differs_from_the_wave_voice():
    g = ShooterGame()
    g.build_scene()
    clutch = g._clips["clutch"]
    wave = g._clips["wave"]
    assert clutch.samples != wave.samples
    assert clutch.duration() != wave.duration()
