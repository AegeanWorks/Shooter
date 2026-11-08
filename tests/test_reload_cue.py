"""Audio/UI proofs: reload completion confirms readiness.

The reload bar disappears when the magazine fills, but the baseline emitted
only the bare `reloaded` event: no voice and no caption. The reload itself
still fills 30/90 exactly.
"""

from keystone.input import ActionState

from shooter.game import ShooterGame
from shooter.sim import Sim


class _Canvas:
    def __init__(self) -> None:
        self.rects: list[tuple] = []
        self.texts: list[tuple] = []

    def rect(self, *args) -> None:
        self.rects.append(args)

    def text(self, *args) -> None:
        self.texts.append(args)


class _Hud:
    width = 960
    height = 540


def _reload_sim() -> Sim:
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.enemies = []
    s.ammo["pulse"] = 0
    s.reserve["pulse"] = 120
    s.reload_t = 0.01
    return s


def test_reload_completion_still_fills_mag():
    s = _reload_sim()
    events = s.step(1.0 / 60.0, ActionState())
    assert "reloaded" in events, events
    assert s.ammo["pulse"] == 30
    assert s.reserve["pulse"] == 90


def test_reload_completion_gets_audio_and_caption():
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    g.sim.ammo["pulse"] = 0
    g.sim.reserve["pulse"] = 120
    g.sim.reload_t = 0.01
    g.update(1.0 / 60.0, ActionState())
    assert g.sim.ammo["pulse"] == 30
    assert g.sound_cue == "RELOADED", g.sound_cue
    assert g.sound_cue_t > 0.0
    assert g.mixer.voice_count() >= 1
    assert "reloaded" in g._clips
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    assert any("RELOADED" in str(t[2]) for t in canvas.texts), canvas.texts
