"""UI readability proofs: a compact kill feed names the kill and its score.

The sim has always emitted only the bare ``kill`` event; the HUD only moved
the distant score number. The feed carries ``kill:<etype>:<score>`` and the
game renders the last few entries for 2.5 s.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import Sim, _Enemy


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


def _kill_sim() -> tuple[Sim, list[str]]:
    s = Sim(seed=1)
    s.spawn_queue = ["mite"]
    s.spawn_t = 999.0
    s.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=12, max_hp=30)]
    events: list[str] = []
    s._fire(s.weapons["pulse"], events)
    return s, events


def test_kill_event_carries_type_and_score():
    s, events = _kill_sim()
    assert s.kills == 1
    typed = [event for event in events if event.startswith("kill:")]
    assert len(typed) == 1, events
    _, etype, amount = typed[0].split(":")
    assert etype == "mite"
    assert int(amount) >= 100
    assert "kill" in events  # the audio/legacy event stays intact


def test_kill_feed_draws_and_expires():
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=12, max_hp=30)]
    g.update(1.0 / 60.0, ActionState(held=frozenset({"fire"})))
    assert g.kill_feed, g.kill_feed
    assert "MITE +" in g.kill_feed[0]["text"]
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    assert any("MITE +" in str(t[2]) for t in canvas.texts), canvas.texts
    for _ in range(180):
        g.update(1.0 / 60.0, ActionState())
    assert g.kill_feed == []
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    assert not any("MITE +" in str(t[2]) for t in canvas.texts), canvas.texts
