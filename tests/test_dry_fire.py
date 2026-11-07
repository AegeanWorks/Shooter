"""Combat-feel proofs: firing a completely dry gun gives feedback.

The low-ammo panel warns before the fact, but a click on 0/0 was completely
silent: no event, no sound, no caption. `dry_fire` is rate-limited so held
auto-fire does not spam the mixer; gameplay state stays unchanged.
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


def _dry_sim() -> Sim:
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.enemies = []
    s.ammo["pulse"] = 0
    s.reserve["pulse"] = 0
    return s


def test_dry_fire_is_rate_limited():
    s = _dry_sim()
    fire = ActionState(held=frozenset({"fire"}))
    assert "dry_fire" in s.step(1.0 / 60.0, fire)
    for _ in range(10):
        events = s.step(1.0 / 60.0, fire)
        assert "dry_fire" not in events, events
    repeats = sum("dry_fire" in s.step(1.0 / 60.0, fire) for _ in range(8))
    assert repeats == 1, repeats


def test_dry_fire_gets_audio_and_caption():
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    g.sim.ammo["pulse"] = 0
    g.sim.reserve["pulse"] = 0
    g.update(1.0 / 60.0, ActionState(held=frozenset({"fire"})))
    assert g.sound_cue == "NO AMMO", g.sound_cue
    assert g.sound_cue_t > 0.0
    assert g.mixer.voice_count() >= 1
    assert "dry_fire" in g._clips
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    assert any("NO AMMO" in str(t[2]) for t in canvas.texts), canvas.texts


def test_dry_fire_does_not_change_shots_or_score():
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    g.sim.ammo["pulse"] = 0
    g.sim.reserve["pulse"] = 0
    g.update(1.0 / 60.0, ActionState(held=frozenset({"fire"})))
    assert g.sim.shots == 0
    assert g.sim.score == 0
    assert g.sim.hits == 0
