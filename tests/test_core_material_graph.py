"""Keystone testbed proof: the boss core material is a material graph.

The declarative graph document is DATA (shooter/data/core_material.json)
and evaluates through keystone.material_graph into the Material used by
the warden core sphere. Presentation only: the sim and hash never read it.
"""

import json
from pathlib import Path

from keystone.material_graph import MaterialGraph

from shooter.game import ShooterGame

DATA = Path(__file__).parent.parent / "shooter" / "data"


def _graph() -> MaterialGraph:
    return MaterialGraph.from_dict(
        json.loads((DATA / "core_material.json").read_text(encoding="utf-8"))
    )


def test_core_graph_evaluates_to_a_checker_material():
    graph = _graph()
    graph.validate()
    material = graph.evaluate()
    assert material.texture is not None
    assert material.texture.name == "core-checker"
    assert (material.texture.width, material.texture.height) == (16, 16)
    assert abs(material.emissive.x - 1.0) < 1e-9
    assert abs(material.emissive.y - 0.48) < 1e-9
    assert material.specular == 0.8
    assert material.shininess == 64.0


def test_core_graph_is_deterministic():
    first = _graph().evaluate().texture
    second = _graph().evaluate().texture
    assert first is not None and second is not None
    assert first.sha256() == second.sha256()


def test_game_registers_the_graph_material():
    g = ShooterGame()
    g.build_scene()
    material = g.assets.require("material.boss_core").payload
    assert material.texture is not None
    assert material.texture.name == "core-checker"
    assert g._boss_core.material is material
