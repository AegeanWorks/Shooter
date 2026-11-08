"""Graphics proof: the arena boundary walls have vertical depth.

The four walls were flat gray planes with only a top cyan trim. Sixteen
shared-material pilasters add vertical rhythm; they are decoration only,
with no colliders or sim state.
"""

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_wall_pilasters_exist_and_share_one_material():
    g = _game()
    nodes = list(g._wall_pilasters)
    assert len(nodes) == 8, len(nodes)
    mat = g.assets.require("material.pilaster").payload
    assert all(node.visible for node in nodes)
    assert all(node.material is mat for node in nodes)


def test_wall_pilasters_sit_on_all_four_walls():
    g = _game()
    nodes = list(g._wall_pilasters)
    north_south = [n for n in nodes if abs(n.transform.position.z) > 19.0]
    east_west = [n for n in nodes if abs(n.transform.position.x) > 19.0]
    assert len(north_south) == 4, len(north_south)
    assert len(east_west) == 4, len(east_west)
    assert sorted({round(n.transform.position.x, 2) for n in north_south}) == [
        -10.0, 10.0
    ]
    assert sorted({round(n.transform.position.z, 2) for n in east_west}) == [
        -10.0, 10.0
    ]
    assert all(n.transform.scale.y >= 2.9 for n in nodes)
    assert all(abs(n.transform.position.x) < 20.0 for n in nodes)
    assert all(abs(n.transform.position.z) < 20.0 for n in nodes)
