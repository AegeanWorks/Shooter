"""UI proof: a sealed campaign stays visibly complete after the banner.

Cycle 68 stopped wave-4 spawns on clear, but the four-second banner then
disappeared and the HUD looked like an ordinary wave-4 lull with no enemies.
A compact persistent line should keep the won state readable.
"""

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


def _labels(g: ShooterGame) -> list[str]:
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    return [str(t[2]) for t in canvas.texts]


def _won_game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.alive = True
    g.sim.victory = True
    g.campaign_cleared = True
    g.campaign_clear_t = 0.0
    return g


def test_campaign_complete_persists_after_the_banner():
    labels = _labels(_won_game())
    assert any("CAMPAIGN COMPLETE" in label for label in labels), labels


def test_banner_still_owns_the_screen_while_it_lasts():
    g = _won_game()
    g.campaign_clear_t = 1.0
    labels = _labels(g)
    assert any("CAMPAIGN CLEAR" in label for label in labels), labels
    assert not any("CAMPAIGN COMPLETE" in label for label in labels), labels


def test_campaign_complete_is_absent_before_the_win():
    g = ShooterGame()
    g.build_scene()
    assert not any("CAMPAIGN COMPLETE" in label for label in _labels(g))
