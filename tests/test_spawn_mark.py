"""Level/encounter proof: wave spawns leave a short marker at their origin.

The sim emits a bare `spawn` event; the game ignored it, so an enemy
materialized with no cue. The marker is presentation-only (game state, not
snapshot) and expires; level flow stays readable.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import MAX_SPAWN_MARKS, ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    return g


def test_spawn_event_records_the_spawn_position():
    g = _game()
    g.sim.spawn_pos = Vec3(1.0, 0.5, -2.0)
    g._play_event("spawn")
    assert len(g.spawn_marks) == 1, g.spawn_marks
    mark = g.spawn_marks[0]
    assert (mark["x"], mark["z"]) == (1.0, -2.0), mark
    assert mark["t"] > 0.0, mark


def test_real_spawn_creates_a_marker_at_the_new_enemy():
    g = _game()
    g.sim.spawn_t = 0.0
    g.update(1.0 / 60.0, ActionState())
    assert g.sim.enemies, "spawn did not happen"
    assert len(g.spawn_marks) == 1, g.spawn_marks
    # the marker is the spawn origin; the enemy may already have moved one step
    assert abs(g.spawn_marks[0]["x"] - g.sim.spawn_pos.x) < 1e-6, g.spawn_marks
    assert abs(g.spawn_marks[0]["z"] - g.sim.spawn_pos.z) < 1e-6, g.spawn_marks
    e = g.sim.enemies[-1]
    assert abs(g.spawn_marks[0]["x"] - e.pos.x) < 0.2, g.spawn_marks


def test_spawn_marker_node_stands_and_expires():
    g = _game()
    g.sim.spawn_pos = Vec3(1.0, 0.5, -2.0)
    g._play_event("spawn")
    g._sync_scene()
    visible = [n for n in g._spawn_nodes if n.visible]
    assert len(visible) == 1, [n.visible for n in g._spawn_nodes]
    node = visible[0]
    assert abs(node.transform.position.x - 1.0) < 1e-6
    assert abs(node.transform.position.z + 2.0) < 1e-6
    assert node.transform.scale.y > 0.0
    # no second spawn: let the marker lifetime run out
    for _ in range(60):
        g.update(1.0 / 60.0, ActionState())
    assert not any(n.visible for n in g._spawn_nodes)
    assert g.spawn_marks == []


def test_spawn_mark_config_is_data_owned():
    g = _game()
    for key in ("life_s", "width", "height", "max"):
        assert key in g.sim.juice["spawn_mark"], key


def _with_cap(cap: int) -> ShooterGame:
    g = ShooterGame()
    g.sim.juice["spawn_mark"]["max"] = cap
    g.build_scene()
    return g


def test_the_data_cap_sizes_the_pool_and_bounds_the_spawn_path():
    for cap in (2, 6):
        g = _with_cap(cap)
        assert len(g._spawn_nodes) == cap
        for i in range(cap + 2):
            g.sim.spawn_pos = Vec3(float(i), 0.5, -2.0)
            g._play_event("spawn")
        assert len(g.spawn_marks) == cap
        g._sync_scene()
        assert sum(1 for n in g._spawn_nodes if n.visible) == cap
    g = ShooterGame()
    g.sim.juice["spawn_mark"].pop("max")
    g.build_scene()
    assert len(g._spawn_nodes) == MAX_SPAWN_MARKS


def test_the_summon_path_uses_the_same_data_cap():
    g = _with_cap(2)
    g.sim.summon_positions = [Vec3(float(i), 0.5, 2.0) for i in range(5)]
    g._play_event("boss_summon")
    assert len(g.spawn_marks) == 2, g.spawn_marks
    g._sync_scene()
    assert sum(1 for n in g._spawn_nodes if n.visible) == 2
