"""Minimal upstream reproducer: manifest assets fail project validation.

`load_project_game` attaches manifest assets to the game registry, then
`validate_project` re-imports the same manifest assets into its own
registry without replace=True. The second registration raises
"asset ... is already registered", so `export_project` rejects any
project whose manifest lists an asset.

Expected: validate_project(...)["ok"] is True.
Actual:   ok is False with an assets error.

Exit 0 when the bug is fixed, 1 while it reproduces.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "keystone"))

from keystone.png import write_png  # noqa: E402
from keystone.project import (  # noqa: E402
    ProjectManifest,
    create_project,
    load_project,
    load_project_game,
    save_project,
    validate_project,
)

PIXELS = bytes(
    (
        10, 20, 30, 255,
        40, 50, 60, 255,
        70, 80, 90, 255,
        100, 110, 120, 255,
    )
)


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "project"
        context = create_project(root, name="manifest_asset_repro")
        (root / "assets").mkdir()
        write_png(root / "assets" / "swatch.png", 2, 2, PIXELS)
        save_project(
            root,
            ProjectManifest(
                name="manifest_asset_repro",
                game=context.manifest.game,
                assets=("assets/swatch.png",),
            ),
        )
        context = load_project(root)
        report = validate_project(context, load_project_game(context))
        errors = report.get("errors", [])
        print(json.dumps({"ok": report["ok"], "errors": errors}, indent=2))
        duplicate = any("already registered" in str(item.get("message", "")) for item in errors)
        if report["ok"] is False and duplicate:
            print(
                "REPRODUCED: validate_project re-imported a manifest asset "
                "already attached by load_project_game."
            )
            return 1
        print("NOT REPRODUCED (keystone may have fixed the duplicate import).")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
