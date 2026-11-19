"""Keystone testbed proof: the ammo-cache material is a .kmaterial.

The file-backed MaterialLibrary document is DATA
(shooter/data/cache_material.kmaterial) and loads into the Material
registered as material.cache. Presentation only: the sim and hash never
read it.
"""

from pathlib import Path

from keystone.material_library import MaterialLibrary
from keystone.math3d import Vec3

from shooter.game import ShooterGame

DATA = Path(__file__).parent.parent / "shooter" / "data"


def test_cache_material_loads_from_library():
    entry = MaterialLibrary(DATA).entry("cache_material")
    assert entry.error is None, entry.error
    material = MaterialLibrary(DATA).load("cache_material")
    assert material.color == Vec3(1.0, 0.68, 0.22)
    assert material.emissive == Vec3(0.82, 0.38, 0.04)
    assert material.specular == 0.5
    assert material.shininess == 48.0
    assert material.texture is None


def test_cache_material_surface_fields_stay_in_their_bands():
    material = MaterialLibrary(DATA).load("cache_material")
    assert 0.0 <= float(material.metallic) <= 0.1, material.metallic
    assert 0.60 <= float(material.roughness) <= 0.80, material.roughness
    assert 0.0 <= float(material.checker_scale) <= 0.1, material.checker_scale


def test_game_registers_the_cache_material():
    g = ShooterGame()
    g.build_scene()
    material = g.assets.require("material.cache").payload
    assert material.color == Vec3(1.0, 0.68, 0.22)
    assert material.emissive == Vec3(0.82, 0.38, 0.04)
    assert material.texture is None


def test_cache_material_is_deterministic():
    first = MaterialLibrary(DATA).load("cache_material")
    second = MaterialLibrary(DATA).load("cache_material")
    assert first == second
