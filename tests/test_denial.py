"""Audio/UI proofs: a denied overdrive explains itself.

Before this cycle, pressing overdrive with no pulse reserve emitted
``overdrive_denied:insufficient_ammo`` but the game ignored it: no buzz, no
caption, nothing. The HUD now shows the cost and the mixer gets a low clip.
"""

from keystone.input import ActionState
from keystone.replay import stable_hash

from shooter.game import ShooterGame


def _denied_game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]  # block wave-clear while probing
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    g.sim.reserve["pulse"] = 0
    return g


def test_denied_overdrive_gets_voice_and_caption():
    g = _denied_game()
    g.update(1.0 / 60.0, ActionState(pressed=frozenset({"overdrive"})))
    assert g.sound_cue == "OVERDRIVE: NEED 30 AMMO", g.sound_cue
    assert g.sound_cue_t > 0.0
    assert g.mixer.voice_count() >= 1
    assert "overdrive_denied" in g._clips
    assert g._clips["overdrive_denied"].duration() > 0.05


def test_denied_overdrive_does_not_change_gameplay_state():
    denied = _denied_game()
    idle = _denied_game()
    denied.update(1.0 / 60.0, ActionState(pressed=frozenset({"overdrive"})))
    idle.update(1.0 / 60.0, ActionState())
    assert denied.sim.reserve["pulse"] == 0
    assert denied.sim.overdrive_t == 0.0
    assert stable_hash(denied.snapshot()) == stable_hash(idle.snapshot())
