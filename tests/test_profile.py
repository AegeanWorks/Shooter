"""Progress/save proofs: schema, atomic backup, quarantine, run debrief.

The profile is a versioned state file: unsupported versions are refused
without touching the file; schema 0 migrates; corrupt files are quarantined
and the .bak is tried. Death records the run and the HUD shows the debrief.
"""

import json

import pytest
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


def test_profile_round_trip_and_backup(tmp_path):
    store = ProfileStore(tmp_path / "profile.json")
    profile = default_profile()
    profile["best_score"] = 123
    assert store.save(profile)
    assert store.load()["best_score"] == 123
    profile["best_score"] = 456
    assert store.save(profile)
    assert store.load()["best_score"] == 456
    assert (tmp_path / "profile.json.bak").is_file()
    assert not (tmp_path / "profile.json.lock").exists()


def test_unsupported_schema_is_refused_without_touching_the_file(tmp_path):
    path = tmp_path / "profile.json"
    path.write_text('{"schema": 99, "best_score": 1}', encoding="utf-8")
    before = path.read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        ProfileStore(path).load()
    assert path.read_text(encoding="utf-8") == before
    assert not list(tmp_path.glob("*.corrupt-*"))


def test_schema_zero_migrates(tmp_path):
    path = tmp_path / "profile.json"
    path.write_text(
        json.dumps({"best_score": 7, "best_kills": 2, "best_wave": 3,
                    "best_streak": 4, "runs": 5}),
        encoding="utf-8",
    )
    profile = ProfileStore(path).load()
    assert profile["schema"] == 1
    assert profile["best_score"] == 7 and profile["best_kills"] == 2
    assert profile["best_wave"] == 3 and profile["best_streak"] == 4
    assert profile["runs"] == 5


def test_corrupt_profile_is_quarantined_and_backup_used(tmp_path):
    store = ProfileStore(tmp_path / "profile.json")
    first = default_profile()
    first["best_score"] = 11
    store.save(first)
    second = default_profile()
    second["best_score"] = 22
    store.save(second)  # .bak now holds best 11
    (tmp_path / "profile.json").write_text("{not json", encoding="utf-8")
    recovered = store.load()
    assert recovered["best_score"] == 11
    assert not (tmp_path / "profile.json").exists()
    assert list(tmp_path.glob("profile.json.corrupt-*"))


def _dead_game(tmp_path) -> ShooterGame:
    g = ShooterGame(profile_path=tmp_path / "profile.json")
    g.build_scene()
    g.sim.spawn_queue = []
    g.sim.hp = 5
    g.sim.score = 1234
    g.sim.kills = 7
    g.sim.best_streak = 3
    g.sim.enemies = [_Enemy(etype="brute", pos=Vec3(0.0, 0.7, 7.0), hp=120, max_hp=120)]
    for _ in range(240):
        g.update(1.0 / 60.0, ActionState())
        if not g.sim.alive:
            break
    return g


def test_death_records_run_and_new_best(tmp_path):
    g = _dead_game(tmp_path)
    assert g.sim.alive is False
    assert g.last_run is not None
    assert g.profile["runs"] == 1
    assert g.profile["best_score"] == 1234
    assert g.profile["best_kills"] == 7
    assert g.profile["best_streak"] == 3
    assert g.last_run["score"] == 1234 and g.last_run["outcome"] == "lose"
    assert g.run_new_best is True
    saved = ProfileStore(tmp_path / "profile.json").load()
    assert saved["best_score"] == 1234 and saved["last_run"]["kills"] == 7
    # a second death in the same run never double-counts
    g.update(1.0 / 60.0, ActionState())
    assert g.profile["runs"] == 1


def test_wave_progress_saves_bests(tmp_path):
    g = ShooterGame(profile_path=tmp_path / "profile.json")
    g.build_scene()
    g.sim.spawn_queue = []
    g.sim.enemies = []
    g.sim.score = 100
    g.sim.kills = 3
    g.update(1.0 / 60.0, ActionState())
    assert g.sim.wave >= 2
    assert g.profile["best_wave"] >= 2
    assert g.profile["best_score"] >= 100
    saved = ProfileStore(tmp_path / "profile.json").load()
    assert saved["best_wave"] >= 2


def test_best_line_and_death_debrief_draw(tmp_path):
    store = ProfileStore(tmp_path / "profile.json")
    profile = default_profile()
    profile["best_score"] = 4321
    store.save(profile)
    g = ShooterGame(profile_path=tmp_path / "profile.json")
    g.build_scene()
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    assert any("BEST 4321" in str(t[2]) for t in canvas.texts), canvas.texts
    g.sim.alive = False
    g.last_run = {"score": 1500, "kills": 9, "wave": 2, "best_streak": 4,
                  "time_s": 30, "outcome": "lose"}
    g.run_new_best = True
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    labels = [str(t[2]) for t in canvas.texts]
    assert any("RUN OVER" in label for label in labels), labels
    assert any("SCORE 1500" in label for label in labels), labels
    assert any("NEW BEST" in label for label in labels), labels


def test_unsupported_profile_disables_saves_without_overwrite(tmp_path):
    path = tmp_path / "profile.json"
    path.write_text('{"schema": 99, "best_score": 1}', encoding="utf-8")
    g = _dead_game(tmp_path)
    assert g.profile_disabled is True
    assert g.last_run is not None  # the visual debrief still works
    assert path.read_text(encoding="utf-8") == '{"schema": 99, "best_score": 1}'
