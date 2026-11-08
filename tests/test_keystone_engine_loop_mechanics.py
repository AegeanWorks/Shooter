"""Keystone mechanics testbed: Engine loop, pause overlay and CLI gates.

Covers the headless Engine fixed-step loop, pause overlay/engine pause,
and the --expect-hash/--replay no-GL CLI paths against the shooter.
"""

import contextlib
import io
import json
from pathlib import Path

import pytest

from keystone.__main__ import main
from keystone.app import Engine
from keystone.clock import FixedStepClock
from keystone.ui.overlay import HudState, HumanOverlay

from shooter.game import ShooterGame

ROOT = Path(__file__).parent.parent
HASH_120 = "7e4b602e029d12d68672790318d119cd"
CAMPAIGN_HASH = "bb425a57b9839e001906cff227fb618f"


def _cli(args):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        status = main(args)
    return status, json.loads(output.getvalue())


def test_engine_headless_loop_steps_and_clock():
    engine = Engine(ShooterGame(), 320, 180, visible=False, msaa=0, ui=False)
    try:
        assert isinstance(engine.clock, FixedStepClock)
        engine.clock.reset(0.0)
        assert len(engine.clock.advance(1.0 / 30.0)) == 2
        frames = engine.run(max_frames=3)
        assert frames == 3
        assert engine._frames == 3
        assert engine.game.sim.tick == 3
        assert abs(engine._elapsed - 3 * engine.clock.step) < 1e-9
    finally:
        engine.close()


def test_pause_overlay_and_engine_pause():
    overlay = HumanOverlay()
    state = HudState(
        game="SHOOTER", status="WAVE 1", fps=60.0, frame=0, elapsed=0.0,
        width=960, height=540, paused=True,
    )
    canvas = overlay.build(state)
    assert "PAUSED" in canvas.labels
    assert [hit[4] for hit in overlay.hits] == ["resume", "toggle_ui", "quit"]
    left, top, width, height, action = overlay.hits[0]
    assert action == "resume"
    assert overlay.hit_test(left + width / 2, top + height / 2) == "resume"
    overlay.toggle()
    assert overlay.build(state).quads == []
    overlay.toggle()

    engine = Engine(ShooterGame(), 320, 180, visible=False, msaa=0, ui=True)
    try:
        assert engine.overlay is not None
        assert engine.apply_ui_action("pause") is True
        assert engine.paused is True
        before = engine.game.sim.tick
        engine.run(max_frames=2)
        assert engine.game.sim.tick == before
        assert engine.apply_ui_action("resume") is True
        assert engine.paused is False
        engine.run(max_frames=1)
        assert engine.game.sim.tick == before + 1
        assert engine.overlay.visible is True
        assert engine.apply_ui_action("toggle_ui") is True
        assert engine.overlay.visible is False
        assert engine.apply_ui_action("toggle_ui") is True
        assert engine.overlay.visible is True
    finally:
        engine.close()


def test_expect_hash_cli_accepts_the_known_hash():
    status, payload = _cli(
        [
            "--game", "shooter.game:ShooterGame",
            "--simulate", "--frames", "120",
            "--expect-hash", HASH_120,
        ]
    )
    assert status == 0
    assert payload["ok"] is True
    assert payload["hash"] == HASH_120
    assert payload["expected_hash"] == HASH_120

    wrong, mismatch = _cli(
        [
            "--game", "shooter.game:ShooterGame",
            "--simulate", "--frames", "120",
            "--expect-hash", "0" * 32,
        ]
    )
    assert wrong == 1
    assert mismatch["ok"] is False
    assert mismatch["hash"] != mismatch["expected_hash"]


def test_replay_cli_replays_the_campaign_win():
    log = ROOT / "bot_campaign.json"
    status, payload = _cli(
        ["--game", "shooter.game:ShooterGame", "--replay", str(log)]
    )
    assert status == 0
    assert payload["ok"] is True
    assert payload["frames"] == 3000
    assert payload["final"]["outcome"] == "win"
    assert payload["final"]["wave"] == 4
    assert payload["hash"] == CAMPAIGN_HASH
