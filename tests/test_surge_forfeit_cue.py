"""Audio proof: forfeiting surge on a weapon switch is announced.

Switching from the surge pickup to slot 1-3 forfeits the remaining surge
timer and its stranded ammo. The sim emitted `surge_forfeit` but the game
mapped no voice or caption, so the loss was silent; the switch click and
the new weapon name were the only feedback.
"""

from keystone.input import ActionState

from shooter.game import ShooterGame


def _armed_game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    g.sim.weapon = "surge"
    g.sim.surge_t = 5.0
    g.sim.ammo["surge"] = 20
    return g


def test_switching_away_from_surge_plays_a_forfeit_cue():
    g = _armed_game()
    clips: list[str] = []
    g.set_clip_hook(lambda clip, gain: clips.append(clip.name))
    g.update(1.0 / 60.0, ActionState(pressed=frozenset({"slot1"})))
    assert g.sim.weapon == "pulse"
    assert g.sim.surge_t == 0.0
    assert "surge_forfeit" in clips
    assert g.sound_cue == "SURGE FORFEIT"
    assert g.sound_cue_color == (1.0, 0.30, 0.30, 1.0)


def test_forfeit_voice_differs_from_the_switch_click():
    g = ShooterGame()
    g.build_scene()
    forfeit = g._clips["surge_forfeit"]
    click = g._clips["switch_pulse"]
    assert forfeit.samples != click.samples
    assert forfeit.duration() > click.duration()


def test_normal_switch_still_names_the_weapon():
    g = ShooterGame()
    g.build_scene()
    clips: list[str] = []
    g.set_clip_hook(lambda clip, gain: clips.append(clip.name))
    g.update(1.0 / 60.0, ActionState(pressed=frozenset({"slot2"})))
    assert g.sound_cue == "SCATTER"
    assert "surge_forfeit" not in clips
