"""Startup proof: broken gameplay data names the file, not the game factory.

The engine reports any load failure with a generic hint ("pass a valid
'package.module:Factory'"). That is right for a wrong `--game` argument and
wrong for a corrupt `shooter/data/*.json`: the player would be told to fix the
factory string while the actual problem is a file they can restore.

`shooter.sim._load` now raises a message carrying `Why:` and `Fix:` naming the
file, and the engine prints such a message verbatim when it is present.
"""

import json
import pathlib
import shutil

import pytest

import shooter.sim as sim_module


@pytest.fixture()
def data_dir(tmp_path, monkeypatch):
    """A throwaway copy of the shipped data so a test can break one file."""
    for path in (sim_module.DATA_DIR).iterdir():
        if path.is_file():
            shutil.copy2(path, tmp_path / path.name)
    monkeypatch.setattr(sim_module, "DATA_DIR", tmp_path)
    return tmp_path


def test_a_missing_required_file_names_the_file_and_the_fix(data_dir):
    (data_dir / "weapons.json").unlink()
    with pytest.raises(ValueError) as raised:
        sim_module.Sim(seed=1)

    message = str(raised.value)
    assert "weapons.json" in message
    assert "Why:" in message and "Fix:" in message
    assert "fresh clone" in message, "the fix must say where a good copy comes from"
    assert "package.module:Factory" not in message, (
        "the message must not blame the --game argument"
    )


def test_a_corrupt_file_names_the_json_error(data_dir):
    (data_dir / "juice.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError) as raised:
        sim_module.Sim(seed=1)

    message = str(raised.value)
    assert "juice.json" in message
    assert "not valid JSON" in message
    assert "Why:" in message and "Fix:" in message


def test_every_required_file_is_reported_by_name(data_dir):
    for name in ("weapons.json", "enemies.json", "levels.json", "juice.json"):
        saved = (data_dir / name).read_text(encoding="utf-8")
        (data_dir / name).write_text("{broken", encoding="utf-8")
        with pytest.raises(ValueError) as raised:
            sim_module.Sim(seed=1)
        assert name in str(raised.value), f"{name} must be named in its own failure"
        (data_dir / name).write_text(saved, encoding="utf-8")


def test_a_missing_optional_file_still_falls_back_silently(data_dir):
    """engagement.json is optional: its absence must not stop the game."""
    (data_dir / "engagement.json").unlink()
    sim = sim_module.Sim(seed=1)
    assert sim.engagement == {}
    assert len(sim.weapons) == 4


def test_a_healthy_data_dir_loads_without_incident(data_dir):
    sim = sim_module.Sim(seed=1)
    assert sim.weapons and sim.enemy_defs and sim.levels and sim.juice
    assert json.dumps(sim.levels)  # the levels document is serialisable data


def test_the_message_is_actionable_not_a_traceback(data_dir):
    (data_dir / "enemies.json").write_text("[", encoding="utf-8")
    with pytest.raises(ValueError) as raised:
        sim_module.Sim(seed=1)

    lines = str(raised.value).splitlines()
    kinds = [line.split(":", 1)[0] for line in lines if ":" in line]
    assert "Why" in kinds and "Fix" in kinds
    assert all("Traceback" not in line for line in lines)


@pytest.mark.parametrize(
    "filename, payload, expected",
    [
        ("weapons.json", '{"wrong": []}', "missing its 'weapons' key"),
        ("weapons.json", '{"weapons": 5}', "wrong type for 'weapons'"),
        ("weapons.json", '{"weapons": [{"name": "x"}]}', "malformed entry at index 0"),
        ("enemies.json", '{"enemies": [{"hp": 1}]}', "malformed entry at index 0"),
        ("levels.json", '{"levels": []}', "missing its 'player' key"),
        ("juice.json", '["not", "an", "object"]', "must hold a JSON object"),
        ("weapons.json", '[]', "must hold a JSON object"),
    ],
)
def test_a_wrongly_shaped_file_names_the_file_and_the_shape(data_dir, filename, payload, expected):
    """Valid JSON with the wrong shape used to escape as a bare KeyError/TypeError."""
    (data_dir / filename).write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError) as raised:
        sim_module.Sim(seed=1)

    message = str(raised.value)
    assert filename in message, "the message must name the file"
    assert expected in message, message
    assert "Why:" in message and "Fix:" in message
    assert "package.module:Factory" not in message


def test_the_shipped_weapon_and_enemy_rosters_are_exact():
    sim = sim_module.Sim(seed=1)
    assert set(sim.weapons) == {"pulse", "scatter", "lance", "surge"}
    assert set(sim.enemy_defs) == {"mite", "brute", "wisp", "warden"}
    for key, weapon in sim.weapons.items():
        assert weapon["id"] == key, (key, weapon["id"])
    for key, enemy in sim.enemy_defs.items():
        assert enemy["id"] == key, (key, enemy["id"])


def test_wave_spawn_keys_and_wave_indices_match_the_shipped_roster():
    """A typo in levels.json waves must name itself, not silently spawn nothing."""
    levels = sim_module._load("levels.json")
    roster = set(sim_module.Sim(seed=1).enemy_defs)
    waves = levels["waves"]
    assert waves, "levels must author at least one wave"
    for index, wave in enumerate(waves):
        assert wave, f"wave {index} is empty"
        assert sum(int(count) for count in wave.values()) > 0, f"wave {index} spawns nothing"
        unknown = set(wave) - roster
        assert not unknown, f"wave {index} names unknown enemy types: {sorted(unknown)}"
    for field in ("win_wave", "pickup_wave"):
        index = int(levels[field])
        assert 0 <= index < len(waves), f"{field}={index} is not a wave index"


def test_authored_positions_and_covers_stay_inside_the_arena():
    """An entity edited outside the 40x40 arena would be unreachable, not crashing."""
    levels = sim_module._load("levels.json")
    half = float(levels["arena"]["size"]) / 2.0

    def inside(x, z):
        return -half <= x <= half and -half <= z <= half

    spawn = levels["player"]["spawn"]
    assert inside(float(spawn[0]), float(spawn[2])), spawn
    pickup = levels["pickup"]
    assert inside(float(pickup["x"]), float(pickup["z"])), pickup

    for index, cover in enumerate(levels["arena"]["covers"]):
        x, z = float(cover["x"]), float(cover["z"])
        w, d = float(cover["w"]), float(cover["d"])
        assert inside(x, z), f"cover {index} centre is outside the arena"
        assert w > 0.0 and float(cover["h"]) > 0.0 and d > 0.0, f"cover {index} has a non-positive extent"
        assert abs(x) + w / 2.0 <= half, f"cover {index} pokes through the x wall"
        assert abs(z) + d / 2.0 <= half, f"cover {index} pokes through the z wall"


def test_spawn_capacity_covers_waves_and_pickup_precedes_victory():
    """A cap below wave demand strands enemies; a late pickup is unusable."""
    levels = sim_module._load("levels.json")
    waves = levels["waves"]
    cap = int(levels["max_alive"])
    demand = [sum(int(count) for count in wave.values()) for wave in waves]
    assert cap > 0, cap
    for index, total in enumerate(demand):
        assert total <= cap, f"wave {index} demands {total} alive but cap is {cap}"
    assert int(levels["pickup_wave"]) < int(levels["win_wave"]), (
        "the surge pickup must be available before the campaign can be won"
    )


def test_a_healthy_document_passes_every_shape_check(data_dir):
    sim = sim_module.Sim(seed=1)
    assert len(sim.weapons) == 4
    assert len(sim.enemy_defs) == 4
    assert sim.levels, "levels must load"
    assert sim.juice, "juice must load"
