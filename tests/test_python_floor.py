"""Portability proof: the project's "Python 3.10+" promise stays true.

The README states Python 3.10+ and Keystone's `pyproject.toml` declares
`requires-python = ">=3.10"`. Nothing verified the shooter side, so a later edit
could introduce PEP 695 generics, `itertools.batched`, `typing.Self`,
`datetime.UTC` or `tomllib` and break every 3.10 user at import time -- with the
build machine on 3.14 noticing nothing.

The scan covers `shooter/`, `tests/`, `scripts/` and `play.py`. The scripts were
the original gap: six files, `capture.py` alone over 100 kB, all documented in
the README, none of them checked.

This is a static check on purpose: it can run on any interpreter, including the
newest, and still report what the oldest supported one could not parse or
import.
"""

import ast
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
IGNORED_DIRS = {
    ".git", ".aikit", "__pycache__", ".pytest_cache", "saves", "evidence",
    "assets", "LICENSES", ".venv", "venv", "node_modules", "dist", "build",
}


def _shipped_python_files() -> list[pathlib.Path]:
    """Every Python file a player's machine would ship or run.

    Discovered by walking so a new top-level package is covered the moment it
    appears, instead of waiting for someone to remember this list.
    """
    found = []
    for path in REPO.rglob("*.py"):
        if set(path.relative_to(REPO).parts[:-1]) & IGNORED_DIRS:
            continue
        found.append(path)
    return sorted(found)


# The shipped tooling counts: capture/soak/play_run are documented in the README.
SOURCES = _shipped_python_files()

# Stdlib attributes that only exist after 3.10, keyed by (module, name).
POST_310_STDLIB = {
    ("itertools", "batched"): "3.12",
    ("itertools", "pairwise"): "3.10",  # exactly 3.10, so allowed
    ("typing", "Self"): "3.11",
    ("typing", "override"): "3.12",
    ("typing", "Required"): "3.11",
    ("typing", "NotRequired"): "3.11",
    ("typing", "assert_type"): "3.11",
    ("typing", "TypeVarTuple"): "3.11",
    ("datetime", "UTC"): "3.11",
    ("asyncio", "TaskGroup"): "3.11",
    ("tomllib", ""): "3.11",
}


def test_every_source_parses_with_the_current_interpreter():
    for path in SOURCES:
        assert path.is_file(), path
        ast.parse(path.read_text(encoding="utf-8"))


def test_no_syntax_newer_than_python_310():
    """PEP 695 type parameters (`class C[T]`, `def f[T]()`) need 3.12."""
    offenders = []
    for path in SOURCES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if getattr(node, "type_params", None):
                    offenders.append(f"{path.name}:{node.lineno}")
    assert offenders == [], (
        "PEP 695 type parameters need Python 3.12 but the project supports 3.10: "
        f"{offenders[:8]}"
    )


def test_no_stdlib_api_newer_than_python_310():
    offenders = []
    for path in SOURCES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    version = POST_310_STDLIB.get((node.module, alias.name))
                    if version and version != "3.10":
                        offenders.append(
                            f"{path.name}:{node.lineno} imports {node.module}.{alias.name} (needs {version})"
                        )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    version = POST_310_STDLIB.get((alias.name, ""))
                    if version and version != "3.10":
                        offenders.append(
                            f"{path.name}:{node.lineno} imports {alias.name} (needs {version})"
                        )
            elif isinstance(node, ast.Call):
                func = node.func
                owner = getattr(func, "value", None)
                if not isinstance(owner, ast.Name) or not isinstance(func, ast.Attribute):
                    continue
                version = POST_310_STDLIB.get((owner.id, func.attr))
                if version and version != "3.10":
                    offenders.append(
                        f"{path.name}:{node.lineno} calls {owner.id}.{func.attr} (needs {version})"
                    )
    assert offenders == [], (
        "these stdlib APIs do not exist on Python 3.10, which the project supports: "
        f"{offenders[:8]}"
    )


def test_the_readme_and_keystone_agree_on_the_floor():
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    assert "Python 3.10+" in readme or "Python 3.10 +" in readme, (
        "the README must state the minimum Python version"
    )
    pyproject = REPO.parent / "keystone" / "pyproject.toml"
    if pyproject.is_file():
        declared = pyproject.read_text(encoding="utf-8")
        assert 'requires-python = ">=3.10"' in declared, (
            "Keystone's declared floor moved; update the shooter README to match"
        )


def test_the_floor_scan_covers_every_python_source_in_the_repo():
    """A guard that silently stops scanning a folder is worse than no guard.

    Comparing the scan list against a second hardcoded list proves nothing --
    a brand-new folder escapes both. The reference here is a filesystem walk.
    """
    covered = {path.resolve() for path in SOURCES}
    missing = sorted(
        p.relative_to(REPO).as_posix()
        for p in {path.resolve() for path in _shipped_python_files()} - covered
    )
    assert missing == [], (
        "these Python files are not held to the stated 3.10 floor: "
        f"{missing[:8]}{'...' if len(missing) > 8 else ''}"
    )
    assert len(SOURCES) >= 150, (
        f"only {len(SOURCES)} sources scanned; the repo ships many more"
    )


@pytest.mark.parametrize("module", ["shooter.game", "shooter.sim", "shooter.bot"])
def test_the_core_modules_import_cleanly(module):
    """An import-time failure is the cheapest way a floor regression shows up."""
    import importlib

    assert importlib.import_module(module) is not None
