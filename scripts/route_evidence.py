"""Deterministic capture proofs for the shooter via keystone.evidence.

The project already writes before/after screenshots by hand. This driver uses
Keystone's Route/Checkpoint plan so a proof has a named route, a stable hash
and a machine-readable diff instead of an ad-hoc pair of filenames.

Usage:
    python scripts/route_evidence.py --out shots/route-a
    python scripts/route_evidence.py --out shots/route-b --compare shots/route-a/route-summary.json
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "keystone"))

from keystone.app import Engine  # noqa: E402
from keystone.evidence import (  # noqa: E402
    Checkpoint,
    Route,
    capture_route,
    diff_evidence,
    write_evidence,
)

from shooter.game import ShooterGame  # noqa: E402

ROUTE_NAME = "shooter-spawn"
DEFAULT_FRAMES = 12
DEFAULT_CHECKPOINTS = (1, 6, 12)


def build_route(frames: int = DEFAULT_FRAMES, checkpoints=DEFAULT_CHECKPOINTS) -> Route:
    """The shipped idle-spawn route: three named frames, no staging callback."""
    points = tuple(Checkpoint(frame=frame, label=f"frame-{frame}") for frame in checkpoints)
    return Route(name=ROUTE_NAME, frames=frames, checkpoints=points)


def diff_summaries(before_path: str | Path, after: dict) -> dict:
    """Compare a written baseline route summary with a freshly captured one."""
    before = json.loads(Path(before_path).read_text(encoding="utf-8"))
    return diff_evidence(before, after)


def run_route(out: Path, frames: int = DEFAULT_FRAMES) -> dict:
    """Capture the route headlessly and write its summary atomically."""
    game = ShooterGame(
        profile_path=Path(tempfile.mkdtemp(prefix="shooter-route-")) / "profile.json"
    )
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    try:
        summary = capture_route(engine, build_route(frames), out)
    finally:
        engine.close()
    write_evidence(out / "route-summary.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="directory for PNG, report and summary")
    parser.add_argument("--compare", help="baseline route-summary.json to diff against")
    args = parser.parse_args(argv)

    summary = run_route(Path(args.out))
    print(f"route {ROUTE_NAME}: {summary['frames_run']} frames, "
          f"hash {summary['route_hash']}")
    if args.compare:
        print(json.dumps(diff_summaries(args.compare, summary), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
