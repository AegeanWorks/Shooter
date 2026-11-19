"""Keystone testbed: the authoritative engine version as an AI/soak query.

`_version` is the single source of truth for Keystone's version and was the
last module the corrected coverage scan found unconsumed. `engine_version_report()`
exposes it as JSON so proof summaries need not parse pyproject.toml or trust a
copied literal. It is an on-demand query with no sim or scene writes.
"""

import json

from keystone._version import __version__ as ENGINE_VERSION
from keystone.replay import stable_hash

import shooter.game as game_module
from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_the_report_carries_the_authoritative_version():
    report = _game().engine_version_report()
    assert report["schema"] == 1
    assert report["engine_version"] == ENGINE_VERSION
    assert isinstance(report["engine_version"], str) and report["engine_version"]


def test_the_report_is_wired_to_the_module_constant(monkeypatch):
    monkeypatch.setattr(game_module, "KEYSTONE_VERSION", "9.9.9-test")
    assert _game().engine_version_report()["engine_version"] == "9.9.9-test"


def test_the_report_is_json_safe_and_stable():
    g = _game()
    first = g.engine_version_report()
    assert g.engine_version_report() == first
    assert json.loads(json.dumps(first)) == first


def test_reporting_the_version_never_touches_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    g.engine_version_report()
    assert stable_hash(g.snapshot()) == before
