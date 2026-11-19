"""Delivery proof: the double-click launchers actually start the game.

`start-shooter.cmd` and `start-shooter.sh` are the first thing a new player
touches, and nothing tested them. A launcher that loses its own-directory `cd`,
stops forwarding arguments, or drops the `Why:`/`Fix:` guidance fails in the one
situation a player cannot debug -- a cold machine with no terminal open.

The README promises both entry points, so both are asserted everywhere: the
`.cmd` is executed for real only on Windows (where `cmd.exe` and `taskkill`
exist), and the `.sh` contract is read statically because a POSIX shell is not
guaranteed on the build machine. On Windows the shell script is not executed; on
POSIX the batch file is not, and each side still gets its static contract.
"""

import os
import pathlib
import subprocess
import sys
import tempfile

import pytest

# A launcher that stops forwarding arguments opens the real game window, which
# never exits. Every subprocess here is therefore bounded and tree-killed, so a
# regression fails in seconds instead of hanging the suite.
RUN_TIMEOUT = 30


WINDOWS = sys.platform == "win32"
needs_cmd = pytest.mark.skipif(
    not WINDOWS, reason="runs the .cmd launcher through cmd.exe, which only exists on Windows"
)


def _run_bounded(args, **kwargs):
    """Run a command, kill its whole tree on timeout, and report that as failure.

    No ``timeout=`` is passed to ``Popen`` because it does not accept one; the
    bound is enforced by ``communicate(timeout=RUN_TIMEOUT)`` below and, on
    expiry, by ``taskkill /F /T``. That is the only reason a bare Popen is
    acceptable here.
    """
    process = subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs
    )
    try:
        out, err = process.communicate(timeout=RUN_TIMEOUT)
        return process.returncode, out or "", err or "", False
    except subprocess.TimeoutExpired:
        # cmd.exe's child survives killing the shell on Windows, so take the tree
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
            capture_output=True,
            timeout=RUN_TIMEOUT,
        )
        try:
            out, err = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            out, err = "", ""
        return None, out or "", err or "", True

REPO = pathlib.Path(__file__).resolve().parent.parent
CMD = REPO / "start-shooter.cmd"
SH = REPO / "start-shooter.sh"


def test_both_launchers_exist_and_stay_in_sync():
    assert CMD.is_file(), "the Windows double-click entry point is missing"
    assert SH.is_file(), "the macOS/Linux entry point is missing"

    sh = SH.read_text(encoding="utf-8")
    cmd = CMD.read_text(encoding="utf-8")
    # both must run the same entry point rather than embedding game logic
    assert "play.py" in sh and "play.py" in cmd
    assert "shooter.game" not in sh and "shooter.game" not in cmd


def test_the_shell_script_uses_a_quoted_self_directory_and_exec():
    sh = SH.read_text(encoding="utf-8")
    assert sh.startswith("#!/bin/sh"), "the script needs a POSIX shebang"
    assert 'cd "$(dirname "$0")"' in sh, "it must run from its own folder"
    assert "exec python3 play.py" in sh, (
        "exec replaces the shell so no orphan process is left behind"
    )
    assert '"$@"' in sh, "arguments must be forwarded and quoted"


@needs_cmd
def test_the_windows_launcher_runs_from_its_own_directory_and_forwards_args():
    code, out, err, timed_out = _run_bounded(
        ["cmd", "/c", str(CMD), "--simulate", "--frames", "30"],
        cwd=str(pathlib.Path(tempfile.gettempdir())),  # deliberately NOT the repo
    )
    assert not timed_out, (
        "the launcher did not exit within "
        f"{RUN_TIMEOUT}s: arguments were probably dropped, so play.py opened the game"
    )
    assert code == 0, out + err
    assert '"tick": 30' in out, (
        "arguments must reach play.py, and the launcher must cd to its own folder"
    )


@needs_cmd
def test_the_windows_launcher_explains_a_missing_python():
    """Run it with a PATH that has neither `python` nor `py`.

    This is the only failure a cold machine hits, and the double-click window
    closes instantly, so the message has to be self-explanatory. stdin is
    DEVNULL so `pause` sees EOF instead of waiting for a key.
    """
    empty = pathlib.Path(tempfile.mkdtemp())
    env = dict(os.environ)
    env["PATH"] = str(empty)
    env["SystemRoot"] = os.environ.get("SystemRoot", r"C:\Windows")
    env["ComSpec"] = os.environ.get("ComSpec", r"C:\Windows\System32\cmd.exe")

    # Bounded by communicate(timeout=RUN_TIMEOUT) and taskkill below.
    process = subprocess.Popen(
        ["cmd", "/c", "call", str(CMD)],
        cwd=str(REPO),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        out, err = process.communicate(timeout=RUN_TIMEOUT)
        timed_out = False
    except subprocess.TimeoutExpired:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
            capture_output=True,
            timeout=RUN_TIMEOUT,
        )
        out, err = "", ""
        timed_out = True

    text = out + err
    assert not timed_out, f"the missing-python path must not hang: {text}"
    assert process.returncode == 1, text
    assert "Why:" in text and "no Python found on PATH" in text
    assert "Fix:" in text and "python.org" in text


def test_the_windows_launcher_falls_back_to_the_py_launcher():
    """`py -3` is the fallback when `python` is absent but Python is installed."""
    lines = CMD.read_text(encoding="utf-8").splitlines()
    # "where python" is a substring of "where py", so compare line positions
    python_line = next(i for i, l in enumerate(lines) if l.strip() == "where python >nul 2>nul")
    py_line = next(i for i, l in enumerate(lines) if l.strip() == "where py >nul 2>nul")
    assert python_line < py_line, (
        "the python branch must come first, or py -3 would shadow a real install"
    )
    assert any("py -3" in line for line in lines)


@pytest.mark.parametrize("launcher", [CMD, SH])
def test_the_launchers_are_documented_in_the_readme(launcher):
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    assert launcher.name in readme, f"{launcher.name} must appear in the README tree"
