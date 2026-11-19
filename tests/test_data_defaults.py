"""Fallback defaults must match the shipped DATA: deleting a key changes nothing.

juice.json is designer-owned and every reader carries a fallback for a missing
key. A fallback that disagrees with the shipped value is a stealth tuning
change: the game looks healthy while the feel silently moves. Cycle 174 found
four such drifts; this test compares observable behaviour with and without the
keys instead of restating the literals.
"""

import json
import shutil

import shooter.sim as sim_module
from shooter.game import ShooterGame
from shooter.sim import Sim

KEYS = ("tracer_life_s", "flash_life_s", "pickup_fx_scale", "pickup_fx_rise")


def _observables() -> dict:
    s = Sim(seed=1)
    s._fire(s.weapons["pulse"], [])
    result = {
        "tracer_life": float(s.tracers[-1]["life"]),
        "flash_life": float(s.flash_t),
    }
    g = ShooterGame()
    g.build_scene()
    setattr(g, "_pickup_fx_t", 0.15)  # half of the shipped pickup_fx_s, so k == 0.5
    g._sync_scene()
    orb = g._pickup_orb.transform
    result["orb_scale"] = float(orb.scale.x)
    result["orb_y"] = float(orb.position.y)
    return result


def test_deleting_a_tuned_key_changes_no_observable_behaviour(tmp_path, monkeypatch):
    baseline = _observables()
    data = tmp_path / "data"
    data.mkdir()
    for path in sim_module.DATA_DIR.iterdir():
        if path.is_file():
            shutil.copy2(path, data / path.name)
    document = json.loads((data / "juice.json").read_text(encoding="utf-8"))
    for key in KEYS:
        document.pop(key)
    (data / "juice.json").write_text(json.dumps(document), encoding="utf-8")
    monkeypatch.setattr(sim_module, "DATA_DIR", data)
    assert _observables() == baseline
