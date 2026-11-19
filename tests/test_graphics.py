"""Graphics proofs: floor grid, lit arena trim, shared batching payloads.

The trim is presentation-only: it shares one mesh/material pair with ten
nodes so the auto-instancer keeps the draw budget flat, and it adds no
colliders or sim state.
"""

from keystone.batch import plan_batches
from keystone.gpu.instancing import plan_instanced
from keystone.input import ActionState

from shooter.game import ShooterGame, _floor_grid_texture


def test_the_shipped_renderer_flags_are_all_enabled():
    """grade.json deliberately adopts all four deterministic renderer features."""
    scene = ShooterGame().build_scene()
    for name in ("shadow", "color", "post", "bloom"):
        settings = getattr(scene, name)
        assert settings.enabled is True, (name, settings)


def test_floor_grid_texture_is_deterministic_and_named():
    first = _floor_grid_texture()
    second = _floor_grid_texture()
    assert first.name == "floor-grid"
    assert (first.width, first.height) == (128, 128)
    assert len(first.rgba) == 128 * 128 * 4
    assert first.sha256() == second.sha256()


def test_arena_has_ten_trim_nodes_sharing_one_material():
    g = ShooterGame()
    scene = g.build_scene()
    trims = [node for node in scene.traverse() if str(node.id).startswith("trim-")]
    assert len(trims) == 10, [node.id for node in trims]
    assert len({id(node.material) for node in trims}) == 1
    assert len({id(node.mesh) for node in trims}) == 1
    # each cover cap sits above its cover, and all are visible
    for node in trims:
        assert node.visible is True
        assert node.transform.position.y > 0.9


def test_floor_material_uses_grid_texture():
    g = ShooterGame()
    g.build_scene()
    floor = g.assets.require("material.floor").payload
    assert floor.texture is not None
    assert floor.texture.name == "floor-grid"


def test_trim_does_not_touch_colliders_or_sim():
    g = ShooterGame()
    g.build_scene()
    colliders = len(g.sim.colliders)
    g.sim.spawn_queue = []
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    g.update(1.0 / 60.0, ActionState())
    assert len(g.sim.colliders) == colliders
    assert g.sim.tick == 1


def test_graphics_budget_with_trim():
    g = ShooterGame()
    g.build_scene()
    plan = plan_batches(g.scene)
    inst = plan_instanced(g.scene)
    assert plan["draw_calls"] <= 40, plan
    assert plan["triangles"] <= 80000, plan
    assert inst["instanced_calls"] <= 40, inst
