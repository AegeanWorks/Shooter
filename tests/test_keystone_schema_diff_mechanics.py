"""Keystone testbed: live contract versions as an AI/soak query.

`schema_diff` was one of nine Keystone modules a corrected coverage scan found
the testbed never imported. `keystone_contract_report()` exposes the versions
Keystone currently exports so an agent can tell what this build is pinned
against, without re-reading schema.py or trusting a copied literal.
"""

from keystone.replay import stable_hash
from keystone.schema_diff import current_versions

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_the_report_has_the_four_live_contract_versions():
    report = _game().keystone_contract_report()
    assert report["schema"] == 1
    assert set(report["versions"]) == {"web_api", "scene", "editor", "prefab"}
    assert all(isinstance(value, int) for value in report["versions"].values())


def test_versions_match_the_module_not_a_copied_literal():
    assert _game().keystone_contract_report()["versions"] == current_versions()


def test_the_report_is_wired_to_the_module_function(monkeypatch):
    import shooter.game as game_module

    monkeypatch.setattr(
        game_module, "current_versions", lambda: {"web_api": 99, "scene": 98}
    )
    assert _game().keystone_contract_report()["versions"] == {
        "web_api": 99, "scene": 98
    }


def test_repeated_reports_are_stable_and_json_serialisable():
    import json

    g = _game()
    first = g.keystone_contract_report()
    assert g.keystone_contract_report() == first
    assert json.loads(json.dumps(first)) == first


def test_reporting_versions_never_touches_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    g.keystone_contract_report()
    assert stable_hash(g.snapshot()) == before
