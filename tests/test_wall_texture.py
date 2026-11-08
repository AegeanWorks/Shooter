"""Graphics proof: arena walls have a deterministic panel texture.

The four boundary walls were flat gray boxes. A grayscale panel texture
on the existing `material.wall` adds seams, bands and rivets without new
nodes, draw calls or colliders; the gray-blue color still tints it.
"""

from shooter.game import ShooterGame


def _wall_texture(game: ShooterGame):
    return game.assets.require("material.wall").payload.texture


def test_wall_material_has_a_panel_texture():
    g = ShooterGame()
    g.build_scene()
    tex = _wall_texture(g)
    assert tex is not None
    assert tex.width == 64 and tex.height == 64
    assert tex.name == "wall-panel"
    face = tex.rgba[(8 * 64 + 4) * 4]
    border = tex.rgba[0]
    assert border < face, (border, face)


def test_wall_texture_is_deterministic_and_distinct_from_covers():
    first = ShooterGame()
    first.build_scene()
    second = ShooterGame()
    second.build_scene()
    a = _wall_texture(first)
    b = _wall_texture(second)
    assert a.rgba == b.rgba
    cover = first.assets.require("material.cover").payload.texture
    assert a.rgba != cover.rgba
