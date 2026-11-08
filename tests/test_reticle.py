"""Combat-feel proofs: the crosshair gap tracks each weapon's hip-fire cone.

A fixed 8 px gap claims the same accuracy for the 0.1-degree lance and the
4.5-degree scatter. These tests measure the drawn arms and pin the reticle
to the JSON spread values; the pulse rifle's 8 px remains the reference.
"""

import math

from shooter.sim import Sim, _load
from shooter.ui import draw_shooter, reticle_gap


class _Canvas:
    def __init__(self) -> None:
        self.rects: list[tuple] = []
        self.texts: list[tuple] = []

    def rect(self, *args) -> None:
        self.rects.append(args)

    def text(self, *args) -> None:
        self.texts.append(args)


class _Hud:
    width = 960
    height = 540


def _drawn_gap(weapon: str, hitmark: bool = False) -> int:
    s = Sim(seed=1)
    s.weapon = weapon
    s.hitmark_t = 0.12 if hitmark else 0.0
    canvas = _Canvas()
    draw_shooter(canvas, _Hud(), s)
    cx, cy = _Hud.width // 2, _Hud.height // 2
    right_arm = [
        r for r in canvas.rects
        if r[2] == 8 and r[3] == 2 and int(r[1]) == cy - 1 and r[0] >= cx
    ]
    assert right_arm, canvas.rects
    return int(min(r[0] for r in right_arm) - cx)


def _spreads() -> dict[str, float]:
    return {
        w["id"]: float(w["spread_hip_deg"])
        for w in _load("weapons.json")["weapons"]
    }


def _expected_gap(spread_deg: float, config: dict) -> int:
    ref_gap = float(config["ref_gap_px"])
    ref_spread = math.radians(float(config["ref_spread_deg"]))
    spread = math.radians(spread_deg)
    ratio = math.tan(spread) / math.tan(ref_spread)
    gap = ref_gap * ratio
    return int(round(max(float(config["min_gap_px"]),
                         min(float(config["max_gap_px"]), gap))))


def test_reticle_gap_follows_weapon_spread():
    spreads = _spreads()
    gaps = {wid: _drawn_gap(wid) for wid in spreads}
    assert gaps["scatter"] > gaps["surge"] > gaps["pulse"] > gaps["lance"], gaps
    # the pulse rifle is the 8 px reference; the scatter cone is much wider
    assert gaps["pulse"] == 8, gaps
    assert gaps["scatter"] >= 26, gaps
    assert gaps["lance"] <= 3, gaps


def test_drawn_gap_matches_data_derived_expectation():
    s = Sim(seed=1)
    config = dict(s.juice["reticle"])
    for wid, spread in _spreads().items():
        expected = _expected_gap(spread, config)
        assert _drawn_gap(wid) == expected, (wid, spread, expected)
        s.weapon = wid
        assert reticle_gap(s) == expected, (wid, reticle_gap(s), expected)


def test_hitmark_expands_the_spread_gap():
    config = dict(Sim(seed=1).juice["reticle"])
    for wid in ("pulse", "scatter", "lance", "surge"):
        base = _drawn_gap(wid)
        assert _drawn_gap(wid, hitmark=True) == base + int(config["hit_gap_px"])


def test_reticle_config_is_data_owned():
    s = Sim(seed=1)
    for key in ("ref_gap_px", "ref_spread_deg", "min_gap_px", "max_gap_px",
                "hit_gap_px"):
        assert key in s.juice["reticle"], key
    assert float(s.juice["reticle"]["ref_spread_deg"]) == 1.2
    assert float(s.juice["reticle"]["ref_gap_px"]) == 8.0
