"""Keystone testbed: profile store contract via VersionedStore.

`persistence` is the last substantive Keystone module the corrected coverage
scan found unconsumed. `profile_store_probe()` runs the shipped profile schema
and its three migrations through a VersionedStore in a throwaway directory:
fresh default, save/reload, old-schema migration and corrupt-file recovery.
The real player profile is never read or written.
"""

from keystone.replay import stable_hash

import shooter.profile as profile_module
from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_the_probe_covers_every_lifecycle_stage():
    report = _game().profile_store_probe()
    assert report["schema"] == 1 and report["store_schema"] == 3
    assert report["fresh"]["source"] == "default"
    assert report["saved"] is True
    assert report["reloaded"]["source"] == "file"
    assert report["reloaded"]["schema"] == 3


def test_an_old_schema_profile_migrates_in_order():
    report = _game().profile_store_probe()["old"]
    assert report["migrated"] is True
    assert report["schema"] == 3
    assert report["runs"] == 4


def test_a_corrupt_profile_is_quarantined_and_recovered():
    report = _game().profile_store_probe()["corrupt"]
    assert report["quarantined"] is True
    assert report["schema"] == 3


def test_the_real_profile_path_is_untouched(tmp_path):
    real = profile_module.DEFAULT_PATH
    before = real.read_bytes() if real.is_file() else None
    _game().profile_store_probe()
    after = real.read_bytes() if real.is_file() else None
    assert before == after


def test_the_probe_is_reproducible_and_never_touches_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    first = g.profile_store_probe()
    assert g.profile_store_probe() == first
    assert stable_hash(g.snapshot()) == before
