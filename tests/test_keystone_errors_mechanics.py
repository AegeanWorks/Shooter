"""Keystone testbed: structured Why/Fix errors for broken game data.

`errors` was one of nine Keystone modules a corrected coverage scan found the
testbed never imported. Cycles 167/168 embedded Why:/Fix: prose in ValueError
messages; data failures now carry KeystoneError's structured fields as well,
with the exact same rendered text, and an on-demand JSON report exposes them.
"""

import json
import shutil

import pytest
from keystone.errors import KeystoneError
from keystone.replay import stable_hash

import shooter.sim as sim_module
from shooter.game import ShooterGame


@pytest.fixture()
def data_dir(tmp_path, monkeypatch):
    for path in sim_module.DATA_DIR.iterdir():
        if path.is_file():
            shutil.copy2(path, tmp_path / path.name)
    monkeypatch.setattr(sim_module, "DATA_DIR", tmp_path)
    return tmp_path


def _broken_data_error(data_dir, name="juice.json", payload="{broken"):
    (data_dir / name).write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError) as raised:
        sim_module.Sim(seed=1)
    return raised.value


def test_broken_data_raises_a_structured_keystone_error(data_dir):
    error = _broken_data_error(data_dir)
    assert isinstance(error, KeystoneError)
    assert error.why and error.fix
    assert "juice.json" in error.why
    assert "fresh clone" in error.fix
    assert "Why:" in str(error) and "Fix:" in str(error)


@pytest.mark.parametrize(
    "name, payload",
    [
        ("weapons.json", '{"wrong": []}'),
        ("weapons.json", '{"weapons": [{"name": "x"}]}'),
        ("enemies.json", "[1, 2]"),
        ("juice.json", "{not json"),
    ],
)
def test_every_data_failure_carries_both_fields(data_dir, name, payload):
    error = _broken_data_error(data_dir, name, payload)
    assert isinstance(error, KeystoneError)
    assert error.why.strip() and error.fix.strip()


def test_the_rendered_message_is_unchanged(data_dir):
    (data_dir / "juice.json").unlink()
    error = _broken_data_error(data_dir, "juice.json", "{broken")
    assert str(error).startswith("shooter data file 'juice.json' is not valid JSON.")
    assert "\nWhy: " in str(error) and "\nFix: " in str(error)


def test_the_report_is_a_json_safe_view_of_the_error(data_dir):
    game = ShooterGame()
    game.build_scene()
    report = game.data_error_report(_broken_data_error(data_dir))
    assert report["schema"] == 1
    assert report["why"] == report["why"].strip()
    assert "fresh clone" in report["fix"]
    assert json.loads(json.dumps(report)) == report


def test_reporting_an_error_never_touches_the_sim(data_dir):
    game = ShooterGame()
    game.build_scene()
    before = stable_hash(game.snapshot())
    game.data_error_report(_broken_data_error(data_dir))
    assert stable_hash(game.snapshot()) == before
