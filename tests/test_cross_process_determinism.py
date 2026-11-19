"""Determinism proof across processes, which the in-process gate cannot give.

`--verify-determinism` runs the same factory twice **inside one process**, so it
compares two runs that share a `PYTHONHASHSEED`. Any ordering that derives from
set or dict-of-strings iteration is therefore identical in both passes, and the
gate reports `ok: true` even when the game would diverge between sessions.

That is not hypothetical: replacing the starting weapon with
`next(iter({"pulse", "scatter", "lance", "surge"}))` left `--verify-determinism`
green while two processes produced different hashes
(`3bf71e94…` vs `03b51121…`).

These tests run the same simulation in **separate processes with different hash
seeds**, which is what a player replaying a saved transcript actually does.
"""

import json
import os
import subprocess
import sys
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
TIMEOUT = 180
FRAMES = "120"


def _run_hash(hashseed: str) -> str:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = hashseed
    result = subprocess.run(
        [sys.executable, str(REPO / "play.py"), "--simulate", "--frames", FRAMES],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)["hash"]


def test_the_same_run_hashes_identically_across_processes_and_hash_seeds():
    """A replay recorded in one session must reproduce in the next."""
    hashes = {seed: _run_hash(seed) for seed in ("0", "1", "424242")}
    assert len(set(hashes.values())) == 1, (
        "the simulation depends on string-hash ordering, so a replay would not "
        f"reproduce across sessions: {hashes}"
    )


def test_a_fixed_seed_attribute_is_reproducible_across_processes():
    """The seed passed to the game, not the interpreter's, drives the outcome."""
    def run(seed: str) -> str:
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = "7"
        # --seed belongs to the playtest runner, not to plain --simulate
        result = subprocess.run(
            [sys.executable, str(REPO / "play.py"), "--playtest",
             "--frames", FRAMES, "--seed", seed],
            cwd=str(REPO), capture_output=True, text=True, timeout=TIMEOUT, env=env,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout)["hash"]

    assert run("5") == run("5")
    assert run("5") != run("6"), "different game seeds should differ"


def _report_hash(hashseed: str) -> str:
    """Hash the aggregate testbed report in a fresh interpreter."""
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = hashseed
    env["PYTHONPATH"] = os.pathsep.join((
        str(REPO.parent / "keystone"), str(REPO),
    ))
    code = (
        "from keystone.replay import stable_hash; "
        "from shooter.game import ShooterGame; "
        "g = ShooterGame(); g.build_scene(); "
        "print(stable_hash(g.testbed_report()))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(REPO), capture_output=True, text=True, timeout=TIMEOUT, env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout.strip()


def test_the_testbed_report_is_stable_across_processes_and_hash_seeds():
    """AI/soak evidence must not depend on string-hash iteration order."""
    hashes = {seed: _report_hash(seed) for seed in ("0", "1", "424242")}
    assert len(set(hashes.values())) == 1, (
        "the testbed report depends on hash ordering: "
        f"{hashes}"
    )


def test_the_replay_transcript_reproduces_its_outcome_in_a_fresh_process():
    """bot_campaign.json was recorded earlier; it must still win today."""
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "31337"
    result = subprocess.run(
        [sys.executable, str(REPO / "play.py"), "--replay", "bot_campaign.json"],
        cwd=str(REPO), capture_output=True, text=True, timeout=TIMEOUT, env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["final"]["outcome"] == "win"
    assert payload["final"]["wave"] == 4
