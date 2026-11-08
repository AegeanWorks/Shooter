"""Keystone mechanics testbed: atomic byte/JSON persistence.

Covers binary atomic replacement, nested directory creation, JSON backup
chaining and opt-out, non-finite/unserializable rejection with the target
intact, BOM-prefixed reads, and temp cleanup when replace fails.
"""

import pytest

from keystone.serialization import (
    read_json,
    write_bytes_atomic,
    write_json_atomic,
)


def test_bytes_atomic_writes_binary_and_replaces(tmp_path):
    target = tmp_path / "nested" / "state.bin"
    payload = bytes(range(256))
    write_bytes_atomic(target, payload)
    assert target.read_bytes() == payload
    write_bytes_atomic(target, b"replacement\x00")
    assert target.read_bytes() == b"replacement\x00"
    assert not list(tmp_path.rglob(".*.tmp"))
    assert not target.with_name("state.bin.bak").exists()


def test_json_atomic_round_trip_and_backup_chain(tmp_path):
    target = tmp_path / "state.json"
    write_json_atomic(target, {"b": 2, "a": 1})
    assert read_json(target) == {"a": 1, "b": 2}
    assert not target.with_name("state.json.bak").exists()

    write_json_atomic(target, {"a": 3})
    assert read_json(target) == {"a": 3}
    backup = target.with_name("state.json.bak")
    assert read_json(backup) == {"a": 1, "b": 2}

    write_json_atomic(target, {"a": 4}, backup=False)
    assert read_json(target) == {"a": 4}
    assert read_json(backup) == {"a": 1, "b": 2}
    assert not list(tmp_path.glob(".*.tmp"))


def test_json_atomic_rejects_non_finite_and_unserializable(tmp_path):
    target = tmp_path / "state.json"
    with pytest.raises(ValueError):
        write_json_atomic(target, {"value": float("nan")})
    assert not target.exists()
    assert not target.with_name("state.json.bak").exists()

    with pytest.raises(TypeError):
        write_json_atomic(target, {"value": object()})
    assert not target.exists()

    write_json_atomic(target, {"ok": 1})
    with pytest.raises(ValueError):
        write_json_atomic(target, {"value": float("inf")})
    assert read_json(target) == {"ok": 1}
    assert not target.with_name("state.json.bak").exists()


def test_read_json_handles_bom_and_errors(tmp_path):
    target = tmp_path / "state.json"
    target.write_bytes(b'\xef\xbb\xbf{"value": 1}')
    assert read_json(target) == {"value": 1}

    with pytest.raises(FileNotFoundError):
        read_json(tmp_path / "missing.json")

    target.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError):
        read_json(target)


def test_atomic_replace_failure_cleans_temp_and_keeps_target(tmp_path):
    target = tmp_path / "state.bin"
    target.mkdir()
    with pytest.raises(OSError):
        write_bytes_atomic(target, b"payload")
    assert target.is_dir()
    assert not list(tmp_path.glob(".*.tmp"))
