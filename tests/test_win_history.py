"""Progression proofs: campaign clears become run-history entries.

`_record_campaign_clear` used to only increment `wins`; `last_run` and
`history` were written by death alone. A win therefore vanished from the
record. The debrief also printed scores without their outcome.
"""

from keystone.input import ActionState

from shooter.game import ShooterGame
from shooter.profile import ProfileStore, default_profile


class _Canvas:
    def __init__(self) -> None:
        self.rects: list[tuple] = []
        self.texts: list[tuple] = []

    def rect(self, *args) -> None:
        self.rects.append(args)

    def text(self, *args) -> None:
        self.texts.append(args)


class _Hud:
    width = 960
    height = 540


def _clear_game(tmp_path) -> ShooterGame:
    g = ShooterGame(profile_path=tmp_path / "profile.json")
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    g.sim.wave = 4
    g.update(1.0 / 60.0, ActionState())
    return g


def test_campaign_clear_records_a_win_run(tmp_path):
    g = _clear_game(tmp_path)
    assert g.campaign_cleared
    assert g.profile["wins"] == 1, g.profile
    assert g.profile["runs"] == 1, g.profile
    assert g.last_run["outcome"] == "win", g.last_run
    assert g.profile["history"][0]["outcome"] == "win", g.profile["history"]
    saved = ProfileStore(tmp_path / "profile.json").load()
    assert saved["history"][0]["outcome"] == "win", saved["history"]


def test_later_death_does_not_duplicate_the_win(tmp_path):
    g = _clear_game(tmp_path)
    g.sim.hp = 0
    g.sim.alive = False
    g._finish_run()
    assert g.profile["runs"] == 1, g.profile
    assert len(g.profile["history"]) == 1, g.profile["history"]
    assert g.last_run["outcome"] == "win", g.last_run


def test_death_still_records_a_loss(tmp_path):
    g = ShooterGame(profile_path=tmp_path / "profile.json")
    g.build_scene()
    g.sim.score = 1500
    g.sim.alive = False
    g._finish_run()
    assert g.profile["history"][0]["outcome"] == "lose", g.profile["history"]
    assert g.profile["runs"] == 1, g.profile


def test_debrief_marks_wins_and_losses(tmp_path):
    path = tmp_path / "profile.json"
    seeded = default_profile()
    seeded["wins"] = 1
    seeded["history"] = [
        {"score": 980, "kills": 8, "wave": 3, "best_streak": 5,
         "time_s": 41, "outcome": "win"},
        {"score": 740, "kills": 6, "wave": 2, "best_streak": 3,
         "time_s": 30, "outcome": "lose"},
    ]
    ProfileStore(path).save(seeded)
    g = ShooterGame(profile_path=path)
    g.build_scene()
    g.last_run = {"score": 1500, "kills": 9, "wave": 2, "best_streak": 4,
                  "time_s": 10, "outcome": "lose"}
    g.sim.alive = False
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    labels = [str(t[2]) for t in canvas.texts]
    assert any("RECENT 980W / 740L" in label for label in labels), labels


def test_the_victory_frame_writes_the_profile_once(tmp_path):
    """A winning wave and the win run land in one atomic save, not two.

    Two fsync-backed writes on the same frame cost ~10 ms of a 16.7 ms budget
    right at the victory moment, so _record_progress defers to the run record
    that follows it in the same update. The real bot run is used because the
    duplicate only happens when a "wave" event and the campaign clear share a
    frame.
    """
    from shooter.bot import kite_step
    from shooter.profile import ProfileStore

    writes = []
    original = ProfileStore.save

    def counting_save(self, profile):
        writes.append({"wins": profile.get("wins"), "best_score": profile.get("best_score")})
        return original(self, profile)

    game = ShooterGame(profile_path=tmp_path / "profile.json")
    game.build_scene()

    ProfileStore.save = counting_save
    try:
        for _ in range(3000):
            before = len(writes)
            game.update(1.0 / 60.0, kite_step(game.sim))
            if game.campaign_cleared:
                on_victory_frame = len(writes) - before
                break
        else:
            raise AssertionError("the bot did not clear the campaign in 3000 frames")
    finally:
        ProfileStore.save = original

    assert on_victory_frame == 1, (
        f"the victory frame performed {on_victory_frame} profile writes, expected 1"
    )
    saved = ProfileStore(tmp_path / "profile.json").load()
    assert saved["wins"] == 1
    assert saved["history"][0]["outcome"] == "win"
    assert saved["best_score"] == game.sim.score
    assert saved["best_wave"] == game.sim.wave


def test_a_non_winning_wave_still_saves_its_bests_immediately(tmp_path):
    from keystone.input import ActionState
    from shooter.profile import ProfileStore

    writes = []
    original = ProfileStore.save

    def counting_save(self, profile):
        writes.append(profile.get("best_wave"))
        return original(self, profile)

    game = ShooterGame(profile_path=tmp_path / "profile.json")
    game.build_scene()
    game.sim.wave = 2
    game.sim.score = 1500
    game.sim.kills = 9
    game.sim.best_streak = 5

    ProfileStore.save = counting_save
    try:
        game._record_progress()
    finally:
        ProfileStore.save = original

    assert len(writes) == 1
    assert ProfileStore(tmp_path / "profile.json").load()["best_wave"] == 2
