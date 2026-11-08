"""UI readability proof: the death debrief panel fits wide RECENT lines.

Cycle 30's W/L markers made the RECENT line wider; six-digit scores can
outgrow the fixed 380 px panel. The panel width must follow its longest
line while normal scores keep the 380 px layout.
"""

from keystone.ui.font import text_width

from shooter.game import ShooterGame
from shooter.profile import ProfileStore, default_profile


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


def _game(tmp_path, scores: list[tuple[int, str]]) -> ShooterGame:
    path = tmp_path / "profile.json"
    seeded = default_profile()
    seeded["wins"] = sum(1 for _score, outcome in scores if outcome == "win")
    seeded["history"] = [
        {"score": score, "kills": 8, "wave": 3, "best_streak": 5,
         "time_s": 41, "outcome": outcome}
        for score, outcome in scores
    ]
    ProfileStore(path).save(seeded)
    g = ShooterGame(profile_path=path)
    g.build_scene()
    g.last_run = {"score": 999999, "kills": 9, "wave": 2, "best_streak": 4,
                  "time_s": 10, "outcome": "lose"}
    g.sim.alive = False
    return g


def _panel_and_recent(canvas: _Canvas):
    panel = [
        r for r in canvas.rects
        if r[2] >= 380 and r[3] >= 100 and abs(r[0] + r[2] / 2 - 480) <= 2
        and r[4][2] <= 0.10 and r[4][3] >= 0.80
    ]
    recent = [t for t in canvas.texts if str(t[2]).startswith("RECENT ")]
    assert panel, canvas.rects
    assert recent, canvas.texts
    return panel[0], recent[0]


def test_wide_recent_fits_the_panel(tmp_path):
    g = _game(tmp_path, [(999999, "win"), (888888, "lose"), (777777, "win")])
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    panel, recent = _panel_and_recent(canvas)
    x, _y, label, _color, scale = recent
    width = text_width(str(label), scale)
    assert x >= panel[0], (x, panel)
    assert x + width <= panel[0] + panel[2], (x, width, panel)


def test_normal_recent_keeps_the_standard_panel(tmp_path):
    g = _game(tmp_path, [(980, "win"), (740, "lose")])
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    panel, recent = _panel_and_recent(canvas)
    assert panel[2] == 380, panel
    x, _y, label, _color, scale = recent
    assert x + text_width(str(label), scale) <= panel[0] + panel[2]
