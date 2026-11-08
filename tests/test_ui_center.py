"""UI readability proofs: top-center status lines stay centered as values grow.

The HUD drew WAVE/SCORE at `cx - 90` and BEST at `cx - 60` regardless of the
text width. A five-digit score shifts the primary line right by 30 px; these
tests pin every top-center line to `(width - text_width) // 2`.
"""

from keystone.ui.font import text_width

from shooter.game import ShooterGame
from shooter.sim import Sim
from shooter.ui import draw_shooter


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


def _centered_errors(canvas: _Canvas, prefixes: tuple[str, ...]) -> list[tuple]:
    errors = []
    for entry in canvas.texts:
        x, _y, label, _color, scale = entry
        text = str(label)
        if any(text.startswith(prefix) for prefix in prefixes):
            expected = (_Hud.width - text_width(text, scale)) // 2
            errors.append((text, int(x), expected))
    return errors


def test_top_center_status_lines_are_centered():
    s = Sim(seed=1)
    s.wave = 3
    s.score = 12345
    s.streak = 7
    s.overdrive_t = 5.0
    s.near_miss = 3
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    errors = _centered_errors(canvas, ("WAVE ", "STREAK ", "OVERDRIVE ", "NEAR-MISS "))
    assert len(errors) == 4, errors
    assert all(x == expected for _text, x, expected in errors), errors


def test_surge_line_is_centered():
    s = Sim(seed=1)
    s.weapon = "surge"
    s.surge_t = 10.0
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    errors = _centered_errors(canvas, ("SURGE ",))
    assert len(errors) == 1, errors
    assert errors[0][1] == errors[0][2], errors


def test_best_line_is_centered():
    g = ShooterGame()
    g.build_scene()
    g.profile["best_score"] = 9999
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    errors = _centered_errors(canvas, ("BEST ",))
    assert len(errors) == 1, errors
    assert errors[0][1] == errors[0][2], errors
