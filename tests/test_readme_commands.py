"""Documentation proof: the commands the README tells a player to run do work.

The README is the first thing a new player reads, and it makes concrete,
checkable claims -- the launchers start the game, `--describe` describes it,
`--simulate` ticks, and `bot_campaign.json` "clears the wave-3 warden and wins
at wave 4". Documentation drifts silently: nobody notices until a player runs a
command that no longer does what the page says.

Every command here is run through `play.py` exactly as documented, and the
campaign claim is asserted on the replay's own outcome field rather than on the
prose.
"""

import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
README = REPO / "README.md"
TIMEOUT = 120


def _play(*args: str) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(REPO / "play.py"), *args],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )
    return result.returncode, result.stdout + result.stderr


def test_the_readme_documents_describe_and_it_describes_the_game():
    assert "`--describe`" in README.read_text(encoding="utf-8")
    code, out = _play("--describe")
    assert code == 0, out
    payload = json.loads(out)
    assert payload["game"], "a description without a game name is useless"
    assert "capabilities" in payload


def test_the_readme_documents_simulate_and_it_ticks_the_requested_frames():
    text = README.read_text(encoding="utf-8")
    match = re.search(r"--simulate --frames (\d+)", text)
    assert match, "the README advertises a --simulate example"
    frames = int(match.group(1))
    code, out = _play("--simulate", "--frames", str(frames))
    assert code == 0, out
    payload = json.loads(out)
    # the engine reports the requested span twice: as `frames` and on the final
    # snapshot's `tick`; it is not a top-level `tick`.
    assert payload["frames"] == frames, payload.get("frames")
    assert payload["final"]["tick"] == frames, payload["final"].get("tick")
    assert payload["hash"], "a sim run without a hash cannot be compared"


def test_the_documented_campaign_reference_actually_wins():
    """The README says bot_campaign.json clears the warden and wins at wave 4."""
    readme = README.read_text(encoding="utf-8")
    assert "bot_campaign.json" in readme
    assert "wins at wave 4" in readme or "win at wave 4" in readme

    code, out = _play("--replay", "bot_campaign.json")
    assert code == 0, out
    payload = json.loads(out)
    assert payload["ok"] is True
    final = payload["final"]
    assert final["outcome"] == "win", final.get("outcome")
    assert final["wave"] == 4, final.get("wave")
    assert final["kills"] > 0, "a winning run should have kills"


def test_every_documented_play_py_command_parses():
    """A documented command must at least be a command the engine accepts.

    `--help` is not enough to prove behaviour, but it does catch a renamed or
    removed flag, which is the common documentation drift.
    """
    text = README.read_text(encoding="utf-8")
    # the README documents play.py two ways: "python play.py ..." from the
    # project folder and "python projects/shooter/play.py ..." from the repo root
    commands = re.findall(
        r"^python (?:projects/shooter/)?play\.py ([^\n#]+)", text, re.M
    )
    assert commands, "the README no longer documents play.py usage"
    for arguments in commands:
        flags = [part for part in arguments.split() if part.startswith("--")]
        code, out = _play("--help")
        assert code == 0, out
        for flag in flags:
            assert flag.split("=")[0] in out, (
                f"the README documents '{flag}', which the engine no longer accepts"
            )


def test_every_testbed_matrix_reference_points_to_a_real_test():
    """The matrix is AI-facing documentation: a renamed test must not drift."""
    references = set(re.findall(r"`(tests/[A-Za-z0-9_]+\.py)`", README.read_text(encoding="utf-8")))
    assert len(references) > 50, "the README no longer documents the testbed matrix"
    missing = sorted(ref for ref in references if not (REPO / ref).is_file())
    assert not missing, f"README references test files that do not exist: {missing}"
