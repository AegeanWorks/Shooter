"""Progress proof: a missing main profile still restores the backup.

When `.bak` was loaded after a corrupt main, quitting before the next save
left no main file. The next launch treated the missing main as a fresh
profile and ignored the backup, silently losing the recovered progress.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.profile import ProfileStore, default_profile
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


def _profile_with_backup(tmp_path):
    path = tmp_path / "profile.json"
    store = ProfileStore(path)
    profile = default_profile()
    profile["best_score"] = 4321
    profile["wins"] = 2
    assert store.save(profile)
    assert store.save(profile)
    assert path.with_name(path.name + ".bak").is_file()
    path.unlink()
    return path


def _labels(g: ShooterGame) -> list[str]:
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    return [str(t[2]) for t in canvas.texts]


def test_missing_main_restores_the_backup(tmp_path):
    path = _profile_with_backup(tmp_path)
    store = ProfileStore(path)
    profile = store.load()
    assert profile["best_score"] == 4321
    assert profile["wins"] == 2
    assert store.recovered is True
    assert store.recovered_from_backup is True


def test_fresh_profile_ignores_absence_of_backup(tmp_path):
    store = ProfileStore(tmp_path / "profile.json")
    profile = store.load()
    assert profile["best_score"] == 0
    assert store.recovered is False


def test_debrief_shows_backup_recovery_after_restart(tmp_path):
    path = _profile_with_backup(tmp_path)
    g = ShooterGame(profile_path=path)
    g.build_scene()
    g.sim.spawn_queue = []
    g.sim.hp = 5
    g.sim.enemies = [_Enemy(etype="brute", pos=Vec3(0.0, 0.7, 7.0), hp=120, max_hp=120)]
    for _ in range(120):
        g.update(1.0 / 60.0, ActionState())
        if not g.sim.alive:
            break
    labels = _labels(g)
    assert any("PROFILE RECOVERED" in label for label in labels), labels
    assert g.profile["best_score"] >= 4321
