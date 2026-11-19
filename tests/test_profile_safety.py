"""Player-data safety: the profile's failure modes, exercised for real.

The profile is the one thing in the game that is genuinely the player's data --
bests, wins, run history. `ProfileStore.save` promises a `bool` and the game
relies on that: `_save_profile` catches `OSError` to raise a "PROFILE NOT
SAVED" line in the debrief rather than crashing the finish.

A probe found one place where the promise broke: a path whose parent could not
be created (a *file* where the directory should be) made `_acquire_lock`'s
`mkdir` raise `FileExistsError` out of `save`. That is fixed and pinned here,
alongside the recovery paths a corrupt or locked profile actually hits.
"""

import os
import pathlib
import time

import pytest

from shooter.profile import _LOCK_STALE_S, ProfileStore, default_profile


def _store(tmp_path, name="profile.json"):
    return ProfileStore(tmp_path / name)


def test_save_returns_false_when_the_parent_cannot_be_created(tmp_path):
    """Regression: mkdir used to raise out of save() and break the bool contract."""
    blocker = tmp_path / "notadir"
    blocker.write_text("x", encoding="utf-8")
    store = ProfileStore(blocker / "profile.json")
    assert store.save(default_profile()) is False
    # and loading that impossible path still yields usable defaults
    assert store.load()["best_score"] == 0


def test_save_round_trips_and_keeps_a_backup(tmp_path):
    store = _store(tmp_path)
    first = default_profile()
    first["best_score"] = 100
    assert store.save(first) is True
    second = default_profile()
    second["best_score"] = 200
    assert store.save(second) is True

    assert store.load()["best_score"] == 200
    backup = tmp_path / "profile.json.bak"
    assert backup.is_file(), "a second save must leave the previous version"
    assert ProfileStore(backup).load()["best_score"] == 100


def test_corrupt_profile_without_a_backup_is_quarantined(tmp_path):
    path = tmp_path / "profile.json"
    path.write_text("{not json", encoding="utf-8")
    store = ProfileStore(path)
    loaded = store.load()

    assert loaded["best_score"] == 0
    quarantined = [p.name for p in tmp_path.iterdir() if ".corrupt-" in p.name]
    assert quarantined, "the bad file must be kept, not silently deleted"
    assert path.exists() or store.save(loaded) is True, "a usable profile must return"


def test_corrupt_profile_recovers_from_the_backup(tmp_path):
    path = tmp_path / "profile.json"
    store = ProfileStore(path)
    good = default_profile()
    good["best_score"] = 777
    assert store.save(good) is True
    assert store.save(good) is True  # second save writes the .bak
    path.write_text("{broken", encoding="utf-8")

    recovered = ProfileStore(path).load()
    assert recovered["best_score"] == 777


def test_a_fresh_lock_makes_save_refuse_without_writing(tmp_path):
    path = tmp_path / "profile.json"
    lock = path.with_name(path.name + ".lock")
    lock.write_text("", encoding="utf-8")

    store = ProfileStore(path)
    assert store.save(default_profile()) is False
    assert not path.exists(), "a locked save must not write a partial file"


def test_a_stale_lock_is_taken_over(tmp_path):
    path = tmp_path / "profile.json"
    lock = path.with_name(path.name + ".lock")
    lock.write_text("", encoding="utf-8")
    stale = time.time() - (_LOCK_STALE_S + 5)
    os.utime(lock, (stale, stale))

    store = ProfileStore(path)
    assert store.save(default_profile()) is True
    assert path.is_file()
    assert not lock.exists(), "the lock must be released after a successful save"


def test_save_never_leaves_the_lock_behind(tmp_path):
    path = tmp_path / "profile.json"
    store = ProfileStore(path)
    for _ in range(3):
        assert store.save(default_profile()) is True
    assert not path.with_name(path.name + ".lock").exists()


@pytest.mark.parametrize("junk", ["", "[]", "null", '"text"', "{}"])
def test_load_always_returns_a_usable_profile(tmp_path, junk):
    path = tmp_path / "profile.json"
    path.write_text(junk, encoding="utf-8")
    loaded = ProfileStore(path).load()
    assert isinstance(loaded, dict)
    assert loaded["schema"] >= 1
    assert loaded["best_score"] == 0
    assert isinstance(loaded["history"], list)


def test_the_game_reports_an_unsaveable_profile_instead_of_crashing(tmp_path):
    """The debrief must say PROFILE NOT SAVED rather than dying with the save."""
    from shooter.game import ShooterGame

    blocker = tmp_path / "notadir"
    blocker.write_text("x", encoding="utf-8")
    game = ShooterGame(profile_path=blocker / "profile.json")
    game.build_scene()
    game.sim.score = 1234
    game.sim.alive = False

    game._finish_run()  # must not raise

    assert game.profile_save_failed is True
    assert game.profile_save_errors >= 1
    assert game.last_run is not None, "the run still belongs in the debrief"


def test_a_corrupt_backup_does_not_spoil_a_valid_profile(tmp_path):
    """Only the .bak is broken; the live file must still be used as-is."""
    path = tmp_path / "profile.json"
    store = ProfileStore(path)
    good = default_profile()
    good["best_score"] = 555
    assert store.save(good) is True
    assert store.save(good) is True  # creates the .bak
    (tmp_path / "profile.json.bak").write_text("{broken", encoding="utf-8")

    assert ProfileStore(path).load()["best_score"] == 555
    assert not list(tmp_path.glob("*.corrupt-*")), (
        "a healthy profile must not be quarantined because its backup is bad"
    )


def test_when_both_copies_are_broken_the_live_file_is_quarantined(tmp_path):
    path = tmp_path / "profile.json"
    store = ProfileStore(path)
    good = default_profile()
    good["best_score"] = 555
    store.save(good)
    store.save(good)
    path.write_text("{broken", encoding="utf-8")
    (tmp_path / "profile.json.bak").write_text("{also broken", encoding="utf-8")

    loaded = ProfileStore(path).load()
    assert loaded["best_score"] == 0
    assert list(tmp_path.glob("*.corrupt-*")), "the unreadable live file is kept"


def test_a_profile_from_a_newer_build_is_refused_and_left_intact(tmp_path):
    """Deliberate: a downgrade must not cost the player their newer progress.

    The file is not corrupt, so quarantining it would be wrong, and silently
    resetting it would delete real data. The store refuses it, and the game
    turns saving off for the session so nothing overwrites it.
    """
    path = tmp_path / "profile.json"
    newer = '{"schema": 99, "best_score": 4242, "wins": 7}'
    path.write_text(newer, encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported profile schema"):
        ProfileStore(path).load()
    assert path.read_text(encoding="utf-8") == newer
    assert not list(tmp_path.glob("*.corrupt-*"))
    assert not (tmp_path / "profile.json.bak").exists()


def test_the_game_disables_saving_for_an_unreadable_but_valid_newer_profile(tmp_path):
    from shooter.game import ShooterGame

    path = tmp_path / "profile.json"
    newer = '{"schema": 99, "best_score": 4242}'
    path.write_text(newer, encoding="utf-8")

    game = ShooterGame(profile_path=path)
    game.build_scene()
    assert game.profile_disabled is True
    game.sim.score = 900
    game.sim.alive = False
    game._finish_run()
    assert path.read_text(encoding="utf-8") == newer, "a newer profile must survive the session"
