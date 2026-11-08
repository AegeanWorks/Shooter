"""Keystone testbed proof: the pickup beacon is a committed .kprefab.

A multi-root prefab (pickup cube + beacon beam + orb) is authored through
Prefab.from_nodes and PrefabLibrary.save, then loaded with the game asset
registry and instantiated at build time. Presentation and layout are
unchanged; the sim and hash never read the prefab.
"""

from pathlib import Path

from keystone.prefab_library import PrefabLibrary

from shooter.game import ShooterGame

DATA = Path(__file__).parent.parent / "shooter" / "data"


def test_pickup_beacon_prefab_loads():
    g = ShooterGame()
    g.build_scene()
    library = PrefabLibrary(DATA, registry=g.assets)
    entry = library.entry("pickup_beacon")
    assert entry.error is None, entry.error
    assert entry.node_count == 3, entry.node_count
    prefab = library.load("pickup_beacon")
    assert prefab.name == "pickup_beacon"
    assert [root.name for root in prefab.roots] == [
        "surge-pickup", "surge-beam", "surge-orb"
    ]


def test_game_instantiates_the_pickup_prefab():
    g = ShooterGame()
    g.build_scene()
    assert g._pickup.id == "pickup:surge-pickup", g._pickup.id
    assert g._pickup_beam.id == "pickup:surge-beam", g._pickup_beam.id
    assert g._pickup_orb.id == "pickup:surge-orb", g._pickup_orb.id
    assert g._pickup.mesh is g.assets.require("mesh.pickup").payload
    assert g._pickup_beam.mesh is g.assets.require("mesh.wall").payload
    assert g._pickup_orb.mesh is g.assets.require("mesh.beacon_orb").payload
    assert g._pickup.material is g.assets.require("material.pickup").payload


def test_pickup_beacon_still_activates():
    g = ShooterGame()
    g.build_scene()
    g.sim.pickup_active = True
    g._sync_scene()
    assert g._pickup.visible is True
    assert g._pickup_beam.visible is True
    assert g._pickup_orb.visible is True
