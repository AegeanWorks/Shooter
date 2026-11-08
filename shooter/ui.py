"""Shooter HUD: crosshair, HP, ammo, score. Presentation-only, never sim."""

from __future__ import annotations

import math

from keystone.ui.font import text_width


def _center(canvas, cx: int, y: int, text: str, color, scale: int = 2) -> None:
    """Draw one top-center HUD line centered on the viewport."""
    canvas.text(cx - text_width(text, scale) // 2, y, text, color, scale)


def reticle_gap(sim) -> int:
    """Crosshair half-gap in px for the equipped weapon's hip-fire cone.

    The pulse rifle's 8 px is the reference; every other gun scales by the
    tangent of its spread, so the 4.5-degree scatter reads much wider than
    the 0.1-degree lance. Tuning lives in juice.json:reticle and the hit
    expansion is added on top.
    """
    weapon = str(getattr(sim, "weapon", "pulse"))
    wdef = getattr(sim, "weapons", {}).get(weapon, {})
    ret = dict((getattr(sim, "juice", {}) or {}).get("reticle", {}))
    ref_gap = float(ret.get("ref_gap_px", 8.0))
    ref_spread = math.radians(float(ret.get("ref_spread_deg", 1.2)))
    spread = math.radians(float(wdef.get("spread_hip_deg", math.degrees(ref_spread))))
    low = float(ret.get("min_gap_px", 3.0))
    high = float(ret.get("max_gap_px", 40.0))
    if math.tan(ref_spread) > 1e-9:
        ratio = math.tan(spread) / math.tan(ref_spread)
    else:
        ratio = 1.0
    gap = int(round(max(low, min(high, ref_gap * ratio))))
    if float(getattr(sim, "hitmark_t", 0.0)) > 0.0:
        gap += int(round(float(ret.get("hit_gap_px", 4.0))))
    return gap


def draw_shooter(canvas, hud, sim) -> None:
    w, h = int(hud.width), int(hud.height)
    cx, cy = w // 2, h // 2
    white = (0.95, 0.95, 0.97, 1.0)
    dim = (0.55, 0.60, 0.68, 1.0)
    accent = (1.0, 0.62, 0.20, 1.0)
    danger = (1.0, 0.30, 0.30, 1.0)
    panel_c = (0.03, 0.04, 0.06, 0.72)

    # crosshair (spread-aware, expands on hit) with a dark backing so the
    # arms survive a white muzzle flash or a bright floor patch.
    hitmark = float(getattr(sim, "hitmark_t", 0.0)) > 0.0
    gap = reticle_gap(sim)
    col = accent if hitmark else white
    ink = (0.02, 0.02, 0.03, 0.90)
    for x, y, rw, rh in (
        (cx - gap - 8, cy - 1, 8, 2),
        (cx + gap, cy - 1, 8, 2),
        (cx - 1, cy - gap - 8, 2, 8),
        (cx - 1, cy + gap, 2, 8),
        (cx - 1, cy - 1, 2, 2),
    ):
        canvas.rect(x - 2, y - 2, rw + 4, rh + 4, ink)
        canvas.rect(x, y, rw, rh, col)
    if float(getattr(sim, "killmark_t", 0.0)) > 0.0:
        # Kill-only corner ticks: the final hit at the aim point.
        kr = gap + 6
        for dx, dy in ((-kr, -kr), (kr, -kr), (-kr, kr), (kr, kr)):
            canvas.rect(cx + dx - 2, cy + dy - 2, 5, 5, (1.0, 0.22, 0.18, 0.95))

    # Ammo feedback: reload progress near the crosshair, then a low-magazine
    # warning. Exact counts stay in the engine status panel; this is the
    # glanceable layer.
    weapon = str(getattr(sim, "weapon", "pulse"))
    wdef = getattr(sim, "weapons", {}).get(weapon, {})
    mag = int(getattr(sim, "ammo", {}).get(weapon, 0))
    mag_size = max(1, int(wdef.get("mag", 1)))
    reload_t = float(getattr(sim, "reload_t", 0.0))
    if bool(getattr(sim, "alive", True)):
        if reload_t > 0.0:
            duration = max(1e-6, float(wdef.get("reload_s", 1.0)))
            progress = max(0.0, min(1.0, 1.0 - reload_t / duration))
            bx, by, bw, bh = cx - 60, cy + 34, 120, 6
            canvas.rect(bx - 2, by - 2, bw + 4, bh + 4, panel_c)
            canvas.rect(bx, by, max(1, int(bw * progress)), bh, accent)
            canvas.text(cx - 50, by + 10, "RELOADING", dim, 2)
        elif mag <= mag_size // 4:
            canvas.rect(cx - 55, cy + 30, 110, 22, panel_c)
            canvas.text(cx - 45, cy + 35, "LOW AMMO", danger, 2)

    # Directional damage cue: point at the last attacker for a short window.
    # World-space source + camera yaw -> bearing around the crosshair; the
    # sim's damage/RNG state is never touched by this presentation code.
    hurt_t = float(getattr(sim, "hurt_t", 0.0))
    if hurt_t > 0.0 and bool(getattr(sim, "alive", True)):
        src = getattr(sim, "hurt_from", None)
        if src is not None:
            dx = float(src.x) - float(sim.player_pos.x)
            dz = float(src.z) - float(sim.player_pos.z)
            if abs(dx) + abs(dz) > 1e-6:
                yaw = float(getattr(sim, "yaw", 0.0))
                dot = dx * math.sin(yaw) + dz * -math.cos(yaw)
                side = dx * math.cos(yaw) + dz * math.sin(yaw)
                bearing = math.atan2(side, dot)
                ux, uy = math.sin(bearing), -math.cos(bearing)
                pulse = min(1.0, hurt_t / 0.8)
                # Ring cue around the crosshair: never occluded by the engine
                # panels (top-left/top-right/bottom help), readable at any yaw.
                for step in range(5):
                    radius = 40.0 + step * 12.0
                    alpha = 0.30 + 0.12 * step + 0.30 * pulse
                    canvas.rect(
                        cx + ux * radius - 2.0,
                        cy + uy * radius - 2.0,
                        4.0, 4.0, (1.0, 0.25, 0.20, alpha),
                    )
                mx, my = cx + ux * 98.0, cy + uy * 98.0
                cue = (1.0, 0.28, 0.22, 0.55 + 0.40 * pulse)
                canvas.rect(mx - 3, my - 10, 6, 20, cue)
                canvas.rect(mx - 10, my - 3, 20, 6, cue)
                canvas.rect(mx - 5, my - 5, 10, 10, cue)

    # Boss health bar: the warden is the only enemy with a named bar. Kept
    # below the wave/score/streak lines and above the bottom panels.
    boss = next(
        (e for e in getattr(sim, "enemies", ()) if getattr(e, "alive", False) and e.etype == "warden"),
        None,
    )
    if boss is not None:
        frac = max(0.0, min(1.0, float(boss.hp) / max(1.0, float(boss.max_hp))))
        bx, by, bw, bh = cx - 140, 116, 280, 10
        canvas.text(bx, by - 18, "WARDEN", danger, 2)
        hp_label = f"{int(boss.hp)}/{int(boss.max_hp)}"
        canvas.text(bx + bw - text_width(hp_label, 2), by - 18, hp_label, white, 2)
        canvas.rect(bx - 2, by - 2, bw + 4, bh + 4, panel_c)
        canvas.rect(bx, by, max(1, int(bw * frac)), bh, (0.92, 0.20, 0.14, 0.95))
    if boss is None and bool(getattr(sim, "pickup_active", False)):
        # The beacon is the pointer; this label tells a new player what it is.
        spot = getattr(sim, "levels", {}).get("pickup", {"x": 0.0, "z": -6.0})
        dx = float(spot.get("x", 0.0)) - float(sim.player_pos.x)
        dz = float(spot.get("z", -6.0)) - float(sim.player_pos.z)
        if math.hypot(dx, dz) <= 18.0:
            _center(canvas, cx, 100, "SURGE PICKUP READY", (0.40, 1.0, 0.52, 1.0))
            # Directional edge tag when the beacon is outside the forward
            # view: a green SURGE chip at the bearing.
            yaw = float(getattr(sim, "yaw", 0.0))
            dot = dx * math.sin(yaw) + dz * -math.cos(yaw)
            side = dx * math.cos(yaw) + dz * math.sin(yaw)
            bearing = math.atan2(side, dot)
            if abs(bearing) > 1.35:
                ux, uy = math.sin(bearing), -math.cos(bearing)
                px = max(48.0, min(w - 48.0, cx + ux * (w * 0.40)))
                py = max(140.0, min(h - 150.0, cy + uy * (h * 0.28)))
                canvas.rect(px - 34, py - 13, 68, 26, (0.40, 1.0, 0.52, 0.35))
                canvas.rect(px - 32, py - 11, 64, 22, panel_c)
                canvas.text(px - 30, py - 6, "SURGE", (0.40, 1.0, 0.52, 1.0), 2)

    # HP/ammo is owned by the engine status panel (top-left); the old
    # bottom-left copy was removed so the HUD shows each fact once.
    hp = int(getattr(sim, "hp", 100))
    # low-hp edge warning (translucent, presentation-only)
    if hp <= 30 and bool(getattr(sim, "alive", True)):
        edge = (1.0, 0.15, 0.15, 0.28)
        canvas.rect(0, 0, w, 6, edge)
        canvas.rect(0, h - 6, w, 6, edge)
        canvas.rect(0, 0, 6, h, edge)
        canvas.rect(w - 6, 0, 6, h, edge)
    # top-center wave/score/streak (single source; engine status() omits these).
    # Every line is centered from its actual text width, so five-digit scores
    # and long status labels no longer drift right.
    _center(canvas, cx, 34, f"WAVE {int(getattr(sim, 'wave', 1))}  "
            f"SCORE {int(getattr(sim, 'score', 0))}", white)
    streak = int(getattr(sim, "streak", 0))
    od_t = float(getattr(sim, "overdrive_t", 0.0))
    if streak > 0:
        _center(canvas, cx, 52, f"STREAK x{streak}", accent)
    if od_t > 0.0:
        _center(canvas, cx, 68, f"OVERDRIVE {od_t:.1f}s x2", accent)
    elif str(getattr(sim, "weapon", "")) == "surge" and float(getattr(sim, "surge_t", 0.0)) > 0.0:
        # Keep this inside the top-right stats panel (<=30 chars at scale 2).
        _center(canvas, cx, 68, f"SURGE {float(getattr(sim, 'surge_t', 0.0)):.1f}s - SWITCH DROPS IT", dim)
    if int(getattr(sim, "near_miss", 0)) > 0:
        _center(canvas, cx, 84, f"NEAR-MISS {int(getattr(sim, 'near_miss', 0))}", dim)
    if not bool(getattr(sim, "alive", True)):
        canvas.rect(0, 0, w, h, (0.45, 0.02, 0.02, 0.28))
        canvas.text(cx - 70, cy - 60, "YOU DIED", danger, 4)
