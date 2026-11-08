"""Progress proof: a later successful save clears the stale save warning.

A single locked write left `profile_save_errors` at 1 and the debrief kept
saying PROFILE NOT SAVED even after a later write succeeded.
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


def _labels(g: ShooterGame) -> list[str]:
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    return [str(t[2]) for t in canvas.texts]


def test_successful_retry_clears_the_warning(tmp_path):
    path = tmp_path / "profile.json"
    g = ShooterGame(profile_path=path)
    g.build_scene()
    lock = path.with_name(path.name + ".lock")
    lock.write_text("locked", encoding="utf-8")
    g.sim.spawn_queue = []
    g.sim.enemies = []
    g.sim.spawn_t = 999.0
    g.update(1.0 / 60.0, ActionState())  # wave clear attempts the locked save
    assert g.profile_save_errors == 1
    assert g.profile_save_failed is True
    lock.unlink()
    g.sim.hp = 5
    g.sim.enemies = [
        _Enemy(etype="brute", pos=Vec3(0.0, 0.7, 7.0), hp=120, max_hp=120)
    ]
    for _ in range(120):
        g.update(1.0 / 60.0, ActionState())
        if not g.sim.alive:
            break
    assert g.sim.alive is False
    assert g.profile_save_errors == 1
    assert g.profile_save_failed is False
    assert g.profile["runs"] == 1
    assert g.last_run is not None
    assert not any("PROFILE NOT SAVED" in label for label in _labels(g))
    assert path.is_file()


def test_failed_save_still_warns_until_a_retry(tmp_path):
    path = tmp_path / "profile.json"
    lock = path.with_name(path.name + ".lock")
    lock.write_text("locked", encoding="utf-8")
    g = ShooterGame(profile_path=path)
    g.build_scene()
    g.sim.spawn_queue = []
    g.sim.enemies = []
    g.update(1.0 / 60.0, ActionState())
    assert g.profile_save_failed is True
    g.sim.hp = 5
    g.sim.enemies = [
        _Enemy(etype="brute", pos=Vec3(0.0, 0.7, 7.0), hp=120, max_hp=120)
    ]
    for _ in range(120):
        g.update(1.0 / 60.0, ActionState())
        if not g.sim.alive:
            break
    assert any("PROFILE NOT SAVED" in label for label in _labels(g))
