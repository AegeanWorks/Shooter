"""Progress proof: a failed profile save is impossible to miss.

The run debrief already records score and bests, but a failed save only
incremented `profile_save_errors`. The player saw a normal debrief while
the run was lost, and an unwritable profile parent could crash the finish.
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


def test_failed_save_shows_a_debrief_warning(tmp_path):
    (tmp_path / "profile.json.lock").write_text("locked", encoding="utf-8")
    g = _dead_game(tmp_path / "profile.json")
    assert g.profile_save_errors == 1
    assert g.last_run is not None
    assert not (tmp_path / "profile.json").exists()
    assert any("PROFILE NOT SAVED" in label for label in _labels(g)), _labels(g)


def test_unwritable_profile_parent_does_not_crash_and_warns(tmp_path):
    blocked = tmp_path / "blocked"
    blocked.write_text("not a directory", encoding="utf-8")
    g = _dead_game(blocked / "profile.json")
    assert g.sim.alive is False
    assert g.profile_save_errors == 1
    assert g.last_run is not None
    assert any("PROFILE NOT SAVED" in label for label in _labels(g)), _labels(g)


def test_successful_save_keeps_the_debrief_clean(tmp_path):
    g = _dead_game(tmp_path / "profile.json")
    assert g.profile_save_errors == 0
    assert not any("PROFILE NOT SAVED" in label for label in _labels(g)), _labels(g)
