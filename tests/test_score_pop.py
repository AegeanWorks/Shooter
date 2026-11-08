"""Combat-feel proof: the kill bounty pops at the crosshair.

The top-left kill feed carried the reward, far from the aim point; the
crosshair killmark confirmed the kill but not its value. A short +N pop
puts the bounty at the aim point. Presentation only.
"""

from keystone.input import ActionState

from shooter.game import ShooterGame


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


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    return g


def test_kill_event_sets_score_pop():
    g = _game()
    g._play_event("kill:mite:110")
    assert g.score_pop is not None
    assert g.score_pop["text"] == "+110"
    assert g.score_pop["t"] > 0.0


def test_score_pop_draws_near_the_crosshair():
    g = _game()
    g.score_pop = {"text": "+110", "t": 0.5}
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    hits = [t for t in canvas.texts if str(t[2]) == "+110"]
    assert hits, canvas.texts
    x, y = int(hits[0][0]), int(hits[0][1])
    assert 480 <= x <= 600 and 270 <= y <= 340, (x, y)


def test_score_pop_expires():
    g = _game()
    g._play_event("kill:mite:110")
    for _ in range(45):
        g.update(1.0 / 60.0, ActionState())
    assert g.score_pop is None
