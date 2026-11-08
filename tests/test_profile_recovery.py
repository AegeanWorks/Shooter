"""Progress proof: corrupt-profile recovery is visible on the debrief.

ProfileStore quarantines a corrupt file and silently falls back to .bak or
defaults. The player could lose wins/history with a normal-looking debrief,
or never know a backup restored them.
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


def test_corrupt_without_backup_flags_reset(tmp_path):
    path = tmp_path / "profile.json"
    path.write_text('{"broken":', encoding="utf-8")
    store = ProfileStore(path)
    profile = store.load()
    assert profile["wins"] == 0 and profile["history"] == default_profile()["history"]
    assert store.recovered is True
    assert store.recovered_from_backup is False
    assert not path.exists()
    assert list(tmp_path.glob("profile.json.corrupt-*"))


def test_corrupt_with_backup_flags_recovered(tmp_path):
    path = tmp_path / "profile.json"
    store = ProfileStore(path)
    profile = default_profile()
    profile["best_score"] = 4321
    assert store.save(profile)
    assert store.save(profile)
    path.write_text('not json', encoding="utf-8")
    again = ProfileStore(path)
    recovered = again.load()
    assert recovered["best_score"] == 4321
    assert again.recovered is True
    assert again.recovered_from_backup is True


def test_debrief_names_a_reset_profile(tmp_path):
    path = tmp_path / "profile.json"
    path.write_text('{"broken":', encoding="utf-8")
    g = _dead_game(path)
    assert g.profile_disabled is False
    labels = _labels(g)
    assert any("PROFILE RESET" in label for label in labels), labels
    assert not any("PROFILE RECOVERED" in label for label in labels), labels


def test_debrief_names_a_backup_recovery(tmp_path):
    path = tmp_path / "profile.json"
    store = ProfileStore(path)
    profile = default_profile()
    profile["best_score"] = 4321
    assert store.save(profile)
    assert store.save(profile)
    path.write_text('not json', encoding="utf-8")
    g = _dead_game(path)
    labels = _labels(g)
    assert any("PROFILE RECOVERED" in label for label in labels), labels
    assert not any("PROFILE RESET" in label for label in labels), labels
