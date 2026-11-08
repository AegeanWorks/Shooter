"""Graphics proof: arena covers have a deterministic panel texture.

The six covers were flat brown boxes. A grayscale panel texture on the
existing `material.cover` adds seams and bands without new nodes, draw
calls or colliders; the brown color still tints it.
"""

from shooter.game import ShooterGame


def test_cover_material_has_a_panel_texture():
    g = ShooterGame()
    g.build_scene()
    mat = g.assets.require("material.cover").payload
    tex = mat.texture
    assert tex is not None
    assert tex.width == 64 and tex.height == 64
    assert tex.name == "cover-panel"
    center = tex.rgba[(32 * 64 + 32) * 4]
    border = tex.rgba[0]
    assert border < center, (border, center)


def test_cover_texture_is_deterministic():
    first = ShooterGame()
    first.build_scene()
    second = ShooterGame()
    second.build_scene()
    a = first.assets.require("material.cover").payload.texture
    b = second.assets.require("material.cover").payload.texture
    assert a.rgba == b.rgba
