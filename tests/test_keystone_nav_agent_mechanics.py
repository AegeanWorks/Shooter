"""Keystone testbed: a bot route preview driven by a real NavAgent.

`nav_agent` was one of the Keystone modules the corrected coverage scan still
found unconsumed. `bot_nav_preview()` builds a local NavGrid from the shipped
arena, plans spawn -> pickup with a fresh NavAgent and advances it in a local
CharacterBody. It is an on-demand query: the game's sim and scene never move.
"""

from keystone.replay import stable_hash

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_the_preview_plans_from_spawn_to_the_pickup():
    result = _game().bot_nav_preview()
    assert result["schema"] == 1 and result["planned"] is True
    assert result["goal"] == [20, 14]
    before = result["before"]
    assert before["schema"] == 1 and before["plan_found"] is True
    assert before["waypoints"] > 0
    assert before["position"] == [0.0, 0.9, 8.0]


def test_the_local_agent_advances_toward_its_first_waypoint():
    result = _game().bot_nav_preview(frames=30)
    before, after = result["before"], result["after"]
    assert after["schema"] == 1
    assert after["position"] != before["position"]
    dx = after["position"][0] - before["position"][0]
    dz = after["position"][2] - before["position"][2]
    assert dx > 0.0 and dz > 0.0, (dx, dz)


def test_zero_frames_leave_the_report_at_the_start():
    result = _game().bot_nav_preview(frames=0)
    assert result["before"] == result["after"]


def test_the_preview_is_reproducible():
    g = _game()
    assert g.bot_nav_preview() == g.bot_nav_preview()


def test_previewing_a_route_never_touches_the_sim():
    g = _game()
    before = stable_hash(g.snapshot())
    g.bot_nav_preview(frames=60)
    assert stable_hash(g.snapshot()) == before
