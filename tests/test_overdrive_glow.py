"""Graphics proof: the held gun shows the active overdrive state.

Overdrive doubles score for eight seconds, but only the HUD line changed;
the viewmodel kept its normal weapon material. Brighter per-weapon variants
now signal the state and revert when the timer ends.
"""

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    return g


def test_overdrive_swaps_the_viewmodel_material():
    g = _game()
    normal = g.assets.require("material.gun_pulse").payload
    boosted = g.assets.require("material.gun_pulse_od").payload
    assert g._view_body.material is normal
    g.sim.overdrive_t = 3.0
    g._sync_scene()
    assert g._view_body.material is boosted
    assert g._view_barrel.material is boosted
    g.sim.overdrive_t = 0.0
    g._sync_scene()
    assert g._view_body.material is normal
    assert g._view_barrel.material is normal


def test_overdrive_variants_exist_for_every_weapon():
    g = _game()
    for wid in ("pulse", "scatter", "lance", "surge"):
        normal = g.assets.require(f"material.gun_{wid}").payload
        boosted = g.assets.require(f"material.gun_{wid}_od").payload
        assert boosted is not normal
        assert boosted.emissive.length() > normal.emissive.length()
