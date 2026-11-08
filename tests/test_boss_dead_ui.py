"""UI proof: the warden bar yields to the death screen.

The bar was drawn whenever an alive warden existed, so a boss-fight death
showed WARDEN 600/600 over YOU DIED and the debrief.
"""

from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import _Enemy


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


def _game(dead: bool) -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.enemies = [
        _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 2.0), hp=600,
               max_hp=600, summon_cd=999.0)
    ]
    g.sim.hp = 0 if dead else 100
    g.sim.alive = not dead
    if dead:
        g.last_run = {"score": 1500, "kills": 9, "wave": 2,
                      "best_streak": 4, "time_s": 30, "outcome": "lose"}
    return g


def _labels(g: ShooterGame) -> list[str]:
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    return [str(t[2]) for t in canvas.texts]


def test_warden_bar_hides_when_the_player_dies():
    labels = _labels(_game(dead=True))
    assert any("YOU DIED" in label for label in labels), labels
    assert not any("WARDEN" in label for label in labels), labels
    assert not any("600/600" in label for label in labels), labels


def test_warden_bar_still_shows_in_a_live_fight():
    labels = _labels(_game(dead=False))
    assert any("WARDEN" in label for label in labels), labels
    assert any("600/600" in label for label in labels), labels
