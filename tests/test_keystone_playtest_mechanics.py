"""Keystone mechanics testbed: seeded playtests and fairness verdicts.

Covers canonical snapshot hashes/signal readers, scripted/random/greedy
policies, transcript replay/diffs, report envelopes and the fairness
branches using small local contract games plus the real ShooterGame.
"""

import random

import pytest

from keystone.input import ActionState
from keystone.playtest import (
    GreedyPolicy,
    RandomPolicy,
    ScriptedPolicy,
    canon,
    canon_hash,
    diff_transcripts,
    make_report,
    read_outcome,
    read_score,
    run_bot,
    to_command_log,
    validate_fairness,
)
from keystone.replay import CommandLog
from keystone.scene import Scene

from shooter.game import ShooterGame


class _WinGame:
    name = "win"

    def __init__(self):
        self.ticks = 0

    def build_scene(self):
        return Scene()

    def update(self, step, action):
        self.ticks += 1

    def snapshot(self):
        return {
            "outcome": "win" if self.ticks >= 2 else "ongoing",
            "score": float(self.ticks),
        }

    def actions(self):
        return {"axes": ["forward"], "buttons": ["fire"]}


class _NeverWinGame(_WinGame):
    def snapshot(self):
        return {"outcome": "ongoing", "score": 0.0}


class _TerminalGame(_WinGame):
    def snapshot(self):
        return {"outcome": "win", "score": 0.0}


class _NoOutcomeGame:
    name = "nooutcome"

    def __init__(self):
        self.elapsed = 0.0

    def build_scene(self):
        return Scene()

    def update(self, step, action):
        self.elapsed += step

    def snapshot(self):
        return {"score": 0.0}

    def actions(self):
        return {"axes": [], "buttons": []}


def test_canon_signals_and_hash():
    snapshot = {
        "time": 1.23456,
        "z": 2.555,
        "a": [1.23456, {"b": 2.9999}],
        "nested": {"y": True},
    }
    projected = canon(snapshot)
    assert "time" not in projected
    assert projected["z"] == 2.555
    assert projected["a"][0] == 1.235
    assert projected["a"][1]["b"] == 3.0
    assert canon_hash(snapshot) == canon_hash({**snapshot, "time": 999.0})
    with pytest.raises(TypeError):
        canon([])

    assert read_outcome({"outcome": "win"}) == "win"
    assert read_outcome({"outcome": "bogus"}) == "unknown"
    assert read_outcome({}) == "unknown"
    assert read_outcome(None) == "unknown"
    assert read_score({"score": 3}) == 3.0
    assert read_score({"score": 3.5}) == 3.5
    assert read_score({"score": True}) is None
    assert read_score({"score": "3"}) is None
    assert read_score({}) is None


def test_scripted_run_transcript_diff_and_greedy_policy():
    script = [ActionState(forward=1.0), ActionState(right=1.0)]
    first = run_bot(ShooterGame, ScriptedPolicy(script), frames=4, seed=7)
    second = run_bot(ShooterGame, ScriptedPolicy(script), frames=4, seed=7)
    assert first["schema"] == 1
    assert first["game"] == "shooter"
    assert first["steps_used"] == 4
    assert first["actions"][0]["forward"] == 1.0
    assert first["actions"][2]["right"] == 1.0
    assert first["policy"]["name"] == "scripted"
    assert first["hash"] == second["hash"]

    log = to_command_log(first)
    assert isinstance(log, CommandLog)
    assert log.seed == 7
    assert len(log.frames) == 4

    traced = run_bot(
        ShooterGame, ScriptedPolicy(script), frames=4, seed=7, trace=True
    )
    traced_same = run_bot(
        ShooterGame, ScriptedPolicy(script), frames=4, seed=7, trace=True
    )
    same = diff_transcripts(traced, traced_same)
    assert same["same_hash"] is True
    assert same["first_divergent_frame"] is None
    traced_other = run_bot(
        ShooterGame,
        ScriptedPolicy([ActionState(forward=-1.0)]),
        frames=4,
        seed=7,
        trace=True,
    )
    changed = diff_transcripts(traced, traced_other)
    assert changed["same_hash"] is False
    assert changed["first_divergent_frame"] == 0

    policy = GreedyPolicy()
    rng = random.Random(0)
    spec = {"axes": ["forward"], "buttons": []}
    chosen = policy.select({"score": 1.0}, spec, rng)
    assert policy.select({"score": 2.0}, spec, rng) == chosen
    assert policy.params == {"score_guided": True}


def test_policy_and_run_bot_validation():
    with pytest.raises(ValueError):
        RandomPolicy(-0.1)
    with pytest.raises(ValueError):
        RandomPolicy(1.1)
    with pytest.raises(ValueError):
        ScriptedPolicy([])
    with pytest.raises(TypeError):
        ScriptedPolicy([1])

    policy = ScriptedPolicy([ActionState()])
    with pytest.raises(ValueError, match="frames"):
        run_bot(ShooterGame, policy, frames=-1)
    with pytest.raises(TypeError, match="seed"):
        run_bot(ShooterGame, policy, seed=True)
    with pytest.raises(ValueError, match="step"):
        run_bot(ShooterGame, policy, step=0.0)
    with pytest.raises(ValueError, match="max_wall"):
        run_bot(ShooterGame, policy, max_wall_seconds=0.0)

    class Bare:
        pass

    with pytest.raises(TypeError, match="policy"):
        run_bot(ShooterGame, Bare())

    class Blank:
        name = " "

        def reset(self, seed):
            self.seed = seed

        def select(self, snapshot, spec, rng):
            return ActionState()

    with pytest.raises(ValueError, match="name"):
        run_bot(ShooterGame, Blank())

    with pytest.raises(TypeError):
        to_command_log({})
    with pytest.raises(TypeError):
        to_command_log({"command_log": {"seed": "x"}})


def test_make_report_and_transcript_contract():
    transcript = run_bot(
        ShooterGame,
        ScriptedPolicy([ActionState(forward=1.0)]),
        frames=3,
        seed=1,
        trace=True,
    )
    report = make_report(transcript)
    assert report["schema"] == 1
    assert report["game"] == "shooter"
    assert report["policy"]["name"] == "scripted"
    assert report["seed"] == 1
    assert report["frames"] == 3
    assert report["steps_used"] == 3
    assert report["outcome"] in ("ongoing", "win", "lose", "unknown")
    assert report["hash"] == transcript["hash"] == report["transcript_hash"]
    assert report["coverage"]["states_visited"] == 3
    assert report["coverage"]["unique_hashes"] >= 1
    assert report["fairness"] == {
        "verdict": "unknown",
        "reasons": ["no_fairness_check"],
    }
    assert report["web_compatible"] is True

    fair = make_report(
        transcript,
        {"verdict": "fair", "reasons": ["witnessed_win:reference:3"]},
    )
    assert fair["fairness"] == {
        "verdict": "fair",
        "reasons": ["witnessed_win:reference:3"],
    }

    with pytest.raises(ValueError):
        make_report({"schema": 0})
    with pytest.raises(ValueError):
        make_report(transcript, {"verdict": "maybe"})
    with pytest.raises(ValueError):
        make_report(transcript, {"verdict": "fair", "reasons": "ok"})
    with pytest.raises(ValueError):
        diff_transcripts(transcript, {"schema": 0})
    with pytest.raises(TypeError):
        diff_transcripts(None, transcript)


def test_validate_fairness_verdicts():
    fair = validate_fairness(_WinGame, frames=4, seeds=(0,), max_wall_seconds=5)
    assert fair == {
        "verdict": "fair",
        "reasons": ["witnessed_win:random:0:2"],
    }

    budget = validate_fairness(
        _WinGame, frames=4, seeds=(0,), time_limit_frames=1, max_wall_seconds=5
    )
    assert budget == {
        "verdict": "unfair",
        "reasons": ["budget_infeasible:witnessed_win_in_2_frames_exceeds_limit_1"],
    }

    terminal = validate_fairness(_TerminalGame, frames=1, seeds=(0,))
    assert terminal == {"verdict": "unfair", "reasons": ["spawn_terminal:win"]}

    no_outcome = validate_fairness(_NoOutcomeGame, frames=1, seeds=(0,))
    assert no_outcome == {
        "verdict": "unknown",
        "reasons": ["no_outcome_signal"],
    }

    unknown = validate_fairness(
        _NeverWinGame, frames=3, seeds=(0,), max_wall_seconds=5
    )
    assert unknown == {
        "verdict": "unknown",
        "reasons": ["no_reference_solution"],
    }

    reference = validate_fairness(
        _NeverWinGame,
        reference_actions=[ActionState()],
        frames=3,
        seeds=(0,),
        max_wall_seconds=5,
    )
    assert reference == {
        "verdict": "unfair",
        "reasons": ["no_witnessed_win"],
    }

    with pytest.raises(ValueError, match="reference_actions"):
        validate_fairness(
            _WinGame, reference_actions=[], frames=1, seeds=(0,)
        )
