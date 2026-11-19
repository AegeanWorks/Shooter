"""Contract test: the declared mechanics core stays headless and deterministic.

Cycle 150 declared a mechanics contract in ``.aikit/project.json`` (``core`` and
``test``) so an agent could find the AI-testable core. Nothing enforced that the
declared files *stay* headless: a future import of ``keystone.gpu``, a wall-clock
read, or an unseeded ``random.Random()`` would quietly break the promise while
the declaration kept claiming it.

This reads the contract from the config it lives in and checks the properties an
agent relies on: the core exists, imports no GL/window/web/presentation module,
reads no wall clock, seeds every RNG explicitly, and the declared test command
points at files that exist.
"""

import ast
import re
from pathlib import Path

import pytest

from keystone.input import ActionState
from keystone.replay import stable_hash

from shooter.sim import Sim

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / ".aikit" / "project.json"

BANNED_IMPORT_ROOTS = {"OpenGL", "keystone.gpu", "keystone.app", "keystone.web"}
BANNED_MODULES = {"time", "datetime", "secrets", "multiprocessing"}
BANNED_CORE_IMPORTS = {"shooter.game", "shooter.ui", "shooter.asset_pipeline"}
CLOCK_NAMES = {"perf_counter", "monotonic", "time_ns", "urandom", "SystemRandom"}


def _config():
    import json

    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _core_paths():
    mechanics = _config().get("mechanics")
    assert isinstance(mechanics, dict), "project.json must declare a mechanics contract"
    core = mechanics.get("core")
    assert isinstance(core, list) and core, "the mechanics contract needs a core path list"
    return [ROOT / path for path in core]


def _imports(path: Path):
    """Every module one file imports: (tree, absolute modules, relative names).

    A sibling import such as ``from .sim import Sim`` carries ``module == "sim"``
    and ``level == 1``, so it is neither absolute nor visible through ``module``
    alone. Keeping the two sets apart is what lets the direction check see it.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    absolute: set[str] = set()
    relative: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            absolute.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                relative.add(node.module or "")
            elif node.module:
                absolute.add(node.module)
    return tree, absolute, relative


def test_the_declared_contract_is_well_formed():
    mechanics = _config().get("mechanics")
    assert isinstance(mechanics, dict)
    assert _config().get("mechanics_required") is True
    for path in _core_paths():
        assert path.is_file(), f"declared core path is missing: {path}"

    command = mechanics.get("test")
    assert isinstance(command, str) and command.strip()
    referenced = re.findall(r"\S*\.py\b", command)
    assert referenced, "the mechanics test command must name test files"
    missing = [name for name in referenced if not (ROOT / name).is_file()]
    assert missing == [], f"mechanics test command names missing files: {missing}"


def test_the_core_imports_no_graphics_window_web_or_presentation_module():
    for path in _core_paths():
        _, modules, relative = _imports(path)
        offenders = sorted(
            module
            for module in modules
            if module in BANNED_IMPORT_ROOTS
            or any(module.startswith(root + ".") for root in BANNED_IMPORT_ROOTS)
            or module in BANNED_CORE_IMPORTS
        )
        assert offenders == [], f"{path.name} must stay headless, found {offenders}"


def test_the_core_reads_no_wall_clock_and_no_ambient_entropy():
    for path in _core_paths():
        _, modules, relative = _imports(path)
        banned = modules & BANNED_MODULES
        assert banned == set(), f"{path.name} must not import {banned}"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        used = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        used |= {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        offenders = sorted(used & CLOCK_NAMES)
        assert offenders == [], f"{path.name} must not use {offenders}"


def test_every_rng_in_the_core_is_explicitly_seeded():
    for path in _core_paths():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        unseeded = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = node.func
            label = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", "")
            if label == "Random" and not node.args and not node.keywords:
                unseeded.append(node.lineno)
            if label == "SystemRandom":
                unseeded.append(node.lineno)
        assert unseeded == [], f"{path.name} constructs an unseeded RNG at lines {unseeded}"


def test_the_declared_core_runs_headless_and_repeats_itself():
    """The contract promises an AI-testable core; prove it without an engine."""
    first = Sim(seed=7)
    second = Sim(seed=7)
    actions = ActionState()
    for _ in range(300):
        first.step(1.0 / 60.0, actions)
        second.step(1.0 / 60.0, actions)

    left, right = first.snapshot(), second.snapshot()
    assert left == right
    assert stable_hash(left) == stable_hash(right)
    assert left["tick"] == 300


def test_the_declared_core_reaches_the_game_through_one_direction_only():
    """Presentation may use the core; the core must never reach back."""
    _, absolute, relative = _imports(ROOT / "shooter" / "game.py")
    assert "shooter.sim" in absolute or "sim" in relative, (
        "the presentation layer is expected to consume the declared core"
    )
    for path in _core_paths():
        _, absolute, relative = _imports(path)
        reaches_back = sorted(
            module for module in absolute if module.startswith("shooter.")
        ) + sorted(f".{name}" for name in relative)
        assert reaches_back == [], (
            f"{path.name} must not import another shooter module, found {reaches_back}"
        )
