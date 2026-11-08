"""Progress proof: a disabled profile is visible on the debrief.

An unsupported schema refuses to load, so `_save_profile` returns early and
nothing is written. The run still reaches the debrief, but the panel looked
normal; the player had no way to know persistence was off.
"""

from keystone.input import ActionState
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


def _dead_game(path) -> ShooterGame:
    g = ShooterGame(profile_path=path)
    g.build_scene()
    g.sim.spawn_queue = []
    g.sim.hp = 5
    g.sim.score = 1234
    g.sim.kills = 7
    g.sim.enemies = [_Enemy(etype="brute", pos=Vec3(0.0, 0.7, 7.0), hp=120, max_hp=120)]
    for _ in range(240):
        g.update(1.0 / 60.0, ActionState())
        if not g.sim.alive:
            break
    return g


def _labels(g: ShooterGame) -> list[str]:
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    return [str(t[2]) for t in canvas.texts]


def test_disabled_profile_warns_on_the_debrief(tmp_path):
    path = tmp_path / "profile.json"
    path.write_text('{"schema": 99, "best_score": 1}', encoding="utf-8")
    g = _dead_game(path)
    assert g.profile_disabled is True
    assert g.last_run is not None
    labels = _labels(g)
    assert any("PROFILE DISABLED" in label for label in labels), labels
    assert sum("PROFILE DISABLED" in label for label in labels) == 1
    assert path.read_text(encoding="utf-8") == '{"schema": 99, "best_score": 1}'


def test_supported_profile_has_no_disabled_warning(tmp_path):
    g = _dead_game(tmp_path / "profile.json")
    assert g.profile_disabled is False
    assert not any("PROFILE DISABLED" in label for label in _labels(g))
