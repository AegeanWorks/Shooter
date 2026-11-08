"""Audio proofs: switching weapons gets a voice and a visible caption.

The sim emits `switch:<weapon>`; the game ignored it, so slot changes were
silent. Each slot keeps a distinct short click and the caption names the gun.
"""

from shooter.game import ShooterGame
from shooter.sim import Sim


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    return g


def test_switch_event_gets_a_voice_and_caption():
    g = _game()
    g._play_event("switch:scatter")
    assert g.sound_cue == "SCATTER", g.sound_cue
    assert g.sound_cue_t > 0.0
    assert g.mixer.voice_count() >= 1
    assert g._clips["switch_scatter"].duration() > 0.0


def test_each_slot_has_a_distinct_switch_clip():
    g = _game()
    names = [g._clips[f"switch_{wid}"].name for wid in ("pulse", "scatter", "lance")]
    assert len(set(names)) == 3, names
    for wid in ("pulse", "scatter", "lance"):
        assert g._clips[f"switch_{wid}"].duration() > 0.0, wid


def test_sim_emits_the_switch_event():
    s = Sim(seed=1)
    events: list[str] = []
    s._switch("scatter", events)
    assert "switch:scatter" in events, events
    assert s.weapon == "scatter"
