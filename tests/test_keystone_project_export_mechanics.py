"""Keystone mechanics testbed: project manifests and export bundles.

Creates a temp shooter-style project through create_project, checks
manifest loading/validation, adds a PNG asset and a broken scene, and
verifies export_project output contents, hashes, refusal paths and the
bundled launcher.
"""

import hashlib
import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

from keystone.export import EXPORT_MANIFEST, export_project
from keystone.png import write_png
from keystone.plugin import load_game
from keystone.project import (
    PROJECT_FILE,
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


def _name() -> str:
    return f"shooter_probe_{uuid.uuid4().hex[:8]}"


def _project_with_png(root: Path, name: str):
    context = create_project(root, name=name)
    assets = root / "assets"
    assets.mkdir()
    write_png(assets / "swatch.png", 2, 2, PIXELS)
    manifest = ProjectManifest(
        name=name,
        game=context.manifest.game,
        description="shooter-style testbed project",
        assets=("assets/swatch.png",),
        startup_scene="main",
    )
    save_project(root, manifest)
    return load_project(root)


def test_create_load_and_manifest_validation():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "project"
        name = _name()
        context = create_project(root, name=name)
        assert context.manifest.name == name
        assert context.manifest.game == f"{name}:Game"
        assert context.manifest.startup_scene == "main"
        assert (root / PROJECT_FILE).is_file()
        assert (root / f"{name}.py").is_file()
        assert (root / "scenes" / "main.kscene").is_file()
        assert (root / "prefabs" / "cube.kprefab").is_file()

        loaded = load_project(root)
        assert loaded.manifest == context.manifest
        assert ProjectManifest.from_dict(loaded.manifest.to_dict()) == loaded.manifest

        with pytest.raises(FileExistsError):
            create_project(root, name=_name())
        with pytest.raises(FileNotFoundError) as missing:
            load_project(root / "absent")
        assert "Why:" in str(missing.value) and "Fix:" in str(missing.value)
        with pytest.raises(ValueError):
            ProjectManifest.from_dict(
                {"schema": 2, "name": "x", "game": "no-colon"}
            )
        with pytest.raises(ValueError):
            ProjectManifest.from_dict(
                {"schema": 2, "name": "x", "game": "x:Y", "unknown": 1}
            )


def _game_without_manifest_assets(context):
    directory = str(context.directory)
    if directory not in sys.path:
        sys.path.insert(0, directory)
    return load_game(context.manifest.game)


def test_validate_project_assets_and_broken_scene():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "project"
        name = _name()
        context = _project_with_png(root, name)
        assert load_project(root).manifest.assets == ("assets/swatch.png",)
        game = _game_without_manifest_assets(context)
        report = validate_project(context, game)
        assert report["ok"] is True, report
        assert report["errors"] == []
        assert report["assets"]["count"] >= 1
        assert all(not item.get("error") for item in report["scenes"])

        (root / "scenes" / "bad.kscene").write_text("{}", encoding="utf-8")
        broken = load_project(root)
        bad = validate_project(broken, _game_without_manifest_assets(broken))
        assert bad["ok"] is False
        assert any(item.get("error") for item in bad["scenes"]), bad


def test_export_bundle_contents_hashes_and_launcher():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "project"
        name = _name()
        context = create_project(root, name=name)
        assets = root / "assets"
        assets.mkdir()
        write_png(assets / "swatch.png", 2, 2, PIXELS)
        target = Path(directory) / "build"
        result = export_project(context.directory, target)
        assert result["schema"] == 1
        assert result["project"]["name"] == name
        assert result["project"]["game"] == f"{name}:Game"
        assert result["entry"] == "run.py"

        for relative in (
            PROJECT_FILE,
            f"{name}.py",
            "run.py",
            "requirements.txt",
            "EXPORT.md",
            "vendor/keystone/__main__.py",
            "scenes/main.kscene",
            "prefabs/cube.kprefab",
            "assets/swatch.png",
        ):
            assert (target / relative).is_file(), relative

        build = json.loads(
            (target / EXPORT_MANIFEST).read_text(encoding="utf-8")
        )
        assert build["schema"] == 1
        assert build["project"]["name"] == name
        assert build["summary"]["scenes"] >= 1
        assert build["summary"]["prefabs"] >= 1
        assert build["summary"]["files"] > 10
        paths = {item["path"] for item in build["files"]}
        assert {"run.py", "vendor/keystone/__main__.py", "assets/swatch.png"} <= paths
        run_entry = next(item for item in build["files"] if item["path"] == "run.py")
        assert run_entry["sha256"] == hashlib.sha256(
            (target / "run.py").read_bytes()
        ).hexdigest()

        with pytest.raises(FileExistsError):
            export_project(context.directory, target)
        reexported = export_project(context.directory, target, force=True)
        assert reexported["project"]["name"] == name

        completed = subprocess.run(
            [
                sys.executable,
                str(target / "run.py"),
                "--simulate",
                "--frames",
                "1",
            ],
            cwd=target,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)
        assert payload["ok"] is True
        assert payload["game"] == name


def test_export_rejects_missing_and_broken_projects():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        with pytest.raises(FileNotFoundError):
            export_project(root / "missing", root / "missing-build")

        broken = create_project(root / "broken", name=_name())
        (broken.directory / "scenes" / "bad.kscene").write_text(
            "{}", encoding="utf-8"
        )
        target = root / "broken-build"
        with pytest.raises(ValueError):
            export_project(broken.directory, target)
        assert not target.exists()


@pytest.mark.xfail(
    strict=True,
    reason=(
        "keystone validate_project re-imports manifest assets after "
        "load_project_game has already attached them"
    ),
)
def test_manifest_asset_validation_after_load_game_duplicates():
    with tempfile.TemporaryDirectory() as directory:
        context = _project_with_png(Path(directory) / "project", _name())
        report = validate_project(context, load_project_game(context))
        assert report["ok"] is True, report["errors"]
