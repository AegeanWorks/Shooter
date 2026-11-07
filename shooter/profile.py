"""Versioned, crash-safe run profile: bests, run count and last-run summary.

State contract (project guideline): a loader refuses an unsupported schema
without touching the file; schema 0 migrates to 1. Saves go through the
engine's temp+fsync+atomic-replace writer with a .bak, guarded by a short
advisory lock. Corrupt files are quarantined and the backup is tried.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from keystone.serialization import read_json, write_json_atomic

SCHEMA = 2
DEFAULT_PATH = Path(__file__).resolve().parent.parent / "saves" / "profile.json"
_LOCK_STALE_S = 30.0
_LAST_RUN_KEYS = ("score", "kills", "wave", "best_streak", "time_s", "outcome")


def default_profile() -> dict:
    return {
        "schema": SCHEMA,
        "runs": 0,
        "wins": 0,
        "best_score": 0,
        "best_kills": 0,
        "best_wave": 0,
        "best_streak": 0,
        "last_run": None,
    }


def _normalize(raw: dict) -> dict:
    profile = default_profile()
    for key in ("runs", "wins", "best_score", "best_kills", "best_wave", "best_streak"):
        value = raw.get(key, 0)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            profile[key] = value
    last = raw.get("last_run")
    if isinstance(last, dict):
        cleaned = {}
        for key in _LAST_RUN_KEYS:
            value = last.get(key)
            if key == "outcome":
                if value in ("win", "lose"):
                    cleaned[key] = value
            elif isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                cleaned[key] = value
        if "score" in cleaned:
            profile["last_run"] = cleaned
    return profile


def _migrate_v0(raw: dict) -> dict:
    migrated = default_profile()
    migrated["schema"] = 1
    for key in ("runs", "best_score", "best_kills", "best_wave", "best_streak"):
        if key in raw:
            migrated[key] = raw[key]
    return migrated


def _migrate_v1(raw: dict) -> dict:
    migrated = dict(raw)
    migrated["schema"] = SCHEMA
    migrated.setdefault("wins", 0)
    return migrated


class ProfileStore:
    """One JSON profile with schema checks, quarantine and atomic saves."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else DEFAULT_PATH

    @classmethod
    def default(cls) -> ProfileStore:
        return cls(DEFAULT_PATH)

    def load(self) -> dict:
        try:
            raw = read_json(self.path)
        except FileNotFoundError:
            return default_profile()
        except (OSError, json.JSONDecodeError, ValueError):
            return self._recover()
        if not isinstance(raw, dict):
            return self._recover()
        schema = raw.get("schema", 0)
        if schema == 0:
            raw = _migrate_v0(raw)
            schema = 1
        if schema == 1:
            raw = _migrate_v1(raw)
            schema = SCHEMA
        if schema != SCHEMA:
            raise ValueError(f"unsupported profile schema {schema!r}; expected {SCHEMA}")
        return _normalize(raw)

    def _recover(self) -> dict:
        stamp = int(time.time())
        quarantine = self.path.with_name(f"{self.path.name}.corrupt-{stamp}")
        try:
            os.replace(self.path, quarantine)
        except OSError:  # hygiene: allow best-effort quarantine; read-only dir keeps the bad file
            pass
        backup = self.path.with_name(self.path.name + ".bak")
        try:
            raw = read_json(backup)
        except (OSError, json.JSONDecodeError, ValueError):
            return default_profile()
        if not isinstance(raw, dict):
            return default_profile()
        try:
            return _normalize(raw)
        except (TypeError, ValueError):
            return default_profile()

    def save(self, profile: dict) -> bool:
        lock = self._acquire_lock()
        if lock is None:
            return False
        try:
            write_json_atomic(self.path, dict(profile), backup=True)
            return True
        except OSError:
            return False
        finally:
            try:
                lock.unlink()
            except OSError:  # hygiene: allow best-effort lock cleanup; stale locks expire
                pass

    def _acquire_lock(self) -> Path | None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock = self.path.with_name(self.path.name + ".lock")
        for _ in range(2):
            try:
                descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                try:
                    age = time.time() - lock.stat().st_mtime
                except OSError:
                    return None
                if age <= _LOCK_STALE_S:
                    return None
                try:
                    lock.unlink()
                except OSError:
                    return None
                continue
            os.close(descriptor)
            return lock
        return None
