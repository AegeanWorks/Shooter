"""One entry point for the testbed's on-demand reports.

Cycles 178-203 added many no-argument report methods without a discovery point.
testbed_report() composes them into one JSON-safe document so an AI or soak run
can inspect the whole plug-in with a single call.
"""

import ast
import inspect
import json
import textwrap

from keystone.replay import stable_hash

import shooter.game as game_module
from shooter.game import ShooterGame

FAMILIES = (
    "engine", "contracts", "nav", "animation", "steering",
    "picking", "assets", "bot", "storage", "presentation", "sources",
)


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_the_aggregate_covers_every_report_family():
    report = _game().testbed_report()
    assert report["schema"] == 1
    assert set(report) == {"schema", *FAMILIES}


def test_every_composed_report_carries_its_schema():
    report = _game().testbed_report()
    for family in FAMILIES:
        if family == "sources":
            continue
        value = report[family]
        assert isinstance(value, dict), family
        if family in ("nav", "animation"):
            for child in value.values():
                assert child["schema"] == 1, (family, child)
        else:
            assert value["schema"] == 1, family


def test_the_aggregate_is_json_safe_and_reproducible():
    g = _game()
    first = g.testbed_report()
    assert json.loads(json.dumps(first)) == first
    assert g.testbed_report() == first


def test_every_no_argument_report_is_composed():
    """The aggregate must name every no-arg report/probe, not a hardcoded subset."""
    discovered = set()
    for name, member in inspect.getmembers(game_module.ShooterGame, callable):
        if name == "testbed_report" or not (name.endswith("_report") or name.endswith("_probe")):
            continue
        if list(inspect.signature(member).parameters) == ["self"]:
            discovered.add(name)
    assert discovered, "no reports found - introspection is broken"
    assert set(_game().testbed_report()["sources"]) == discovered


def test_no_report_method_writes_to_the_sim():
    """Every on-demand report is presentation-only by construction."""
    offenders = []
    for name, member in inspect.getmembers(game_module.ShooterGame, callable):
        if not (name.endswith(("_report", "_probe", "_preview")) or name == "crosshair_pick"):
            continue
        try:
            tree = ast.parse(textwrap.dedent(inspect.getsource(member)))
        except (OSError, TypeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
                targets = [node.target]
            else:
                continue
            for target in targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Attribute)
                    and target.value.attr == "sim"
                    and isinstance(target.value.value, ast.Name)
                    and target.value.value.id == "self"
                ):
                    offenders.append((name, target.attr))
    assert not offenders, offenders


def test_aggregating_never_touches_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    g.testbed_report()
    assert stable_hash(g.snapshot()) == before
