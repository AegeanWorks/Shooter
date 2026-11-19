"""Repository hygiene: line-ending rules must agree with the committed blobs.

This repository's committed content is mixed: `.aikit/decisions.md` stores CRLF
while `shooter/sim.py`, `shooter/game.py`, `README.md` and `LICENSE` store LF.
Adding a `.gitattributes` rule of `* text=auto eol=lf` on top of that makes every
CRLF blob report as permanently modified (the clean filter normalises the
worktree to LF while the stored blob stays CRLF), and converting the worktree by
hand instead produces "phantom" modifications where `git status` disagrees with
`git diff`.

Both failure modes cost a long detour, so they are asserted here rather than
rediscovered: a newline rule may only be pinned once the blobs it governs are
consistent, and the status/diff views must agree about what changed.
"""

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


GIT_TIMEOUT = 15


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True, timeout=GIT_TIMEOUT
    )
    return result.stdout


def _head_blobs(names: list[str]) -> dict[str, bytes]:
    """Read many committed blobs in one git process.

    A per-file `git cat-file` costs a process spawn each, which is what made the
    first version of this suite take over a second per test. `cat-file --batch`
    answers every path in a single call.
    """
    if not names:
        return {}
    request = "".join(f"HEAD:{name}\n" for name in names).encode("utf-8")
    out = subprocess.run(
        ["git", "cat-file", "--batch"],
        cwd=REPO,
        input=request,
        capture_output=True,
        timeout=GIT_TIMEOUT * 4,
    ).stdout
    blobs: dict[str, bytes] = {}
    view = memoryview(out)
    offset = 0
    for name in names:
        newline = bytes(view[offset:]).find(b"\n")
        if newline < 0:
            break
        header = bytes(view[offset:offset + newline]).decode("utf-8", "replace")
        offset += newline + 1
        parts = header.split()
        if len(parts) != 3 or parts[1] in ("missing", "ambiguous"):
            continue  # no HEAD entry (a staged addition) or an unreadable path
        size = int(parts[2])
        blobs[name] = bytes(view[offset:offset + size])
        offset += size + 1  # payload plus the trailing newline
    return blobs


def _tracked_blobs_with_cr() -> list[str]:
    """Tracked text files whose committed blob contains a CR byte."""
    names = [n for n in _git("ls-files").splitlines() if n]
    crlf = []
    for name, data in _head_blobs(names).items():
        # Binary content legitimately contains CR; text-ness is what matters.
        if b"\0" not in data[:8000] and b"\r" in data:
            crlf.append(name)
    return sorted(crlf)


def test_an_lf_rule_is_only_pinned_when_the_committed_blobs_agree():
    attributes = REPO / ".gitattributes"
    if not attributes.is_file():
        return
    rules = attributes.read_text(encoding="utf-8", errors="replace")
    if "eol=lf" not in rules:
        return
    offenders = _tracked_blobs_with_cr()
    assert offenders == [], (
        "a .gitattributes rule pins eol=lf but these committed blobs contain CRLF, "
        "so they would report as permanently modified: "
        f"{offenders[:8]}{'...' if len(offenders) > 8 else ''}. "
        "Renormalise them in a dedicated commit before pinning the rule."
    )


def test_status_reports_no_phantom_modifications():
    """Every path git calls modified must really differ from its HEAD blob.

    Comparing `git status` against `git diff` is not enough: both read the same
    stat cache, so a stale entry makes them agree while the tree is unchanged.
    The authoritative check compares the worktree bytes with the committed blob,
    which is what a phantom modification is defined by.
    """
    status = _git("status", "--porcelain").splitlines()
    reported = [
        line[3:].strip() for line in status if line[:2].strip() == "M" and len(line) > 3
    ]
    heads = _head_blobs(reported)
    phantom = []
    for name in reported:
        if name not in heads or not (REPO / name).is_file():
            continue
        # Git compares *filtered* content, so the authoritative question is what
        # hash-object produces for the worktree file: if it equals the committed
        # blob, nothing would ever be committed for this path.
        filtered = subprocess.run(
            ["git", "hash-object", f"--path={name}", "--", name],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
        ).stdout.strip()
        committed = subprocess.run(
            ["git", "rev-parse", f"HEAD:{name}"],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
        ).stdout.strip()
        if filtered and filtered == committed:
            phantom.append(name)
    assert phantom == [], (
        "git status reports these as modified but their bytes match the committed "
        f"blob, so the index stat cache is stale or a line-ending filter disagrees: "
        f"{phantom[:8]}{'...' if len(phantom) > 8 else ''}"
    )
