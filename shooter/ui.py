"""Shooter HUD: crosshair, HP, ammo, score. Presentation-only, never sim."""

from __future__ import annotations

import math


def draw_shooter(canvas, hud, sim) -> None:
    w, h = int(hud.width), int(hud.height)
    cx, cy = w // 2, h // 2
    white = (0.95, 0.95, 0.97, 1.0)
    dim = (0.55, 0.60, 0.68, 1.0)
    accent = (1.0, 0.62, 0.20, 1.0)
    danger = (1.0, 0.30, 0.30, 1.0)
    panel_c = (0.03, 0.04, 0.06, 0.72)

    # crosshair (expands on hit) with a dark backing so the arms survive a
    # white muzzle flash or a bright floor patch.
    gap = 8 if float(getattr(sim, "hitmark_t", 0.0)) <= 0.0 else 12
    col = accent if float(getattr(sim, "hitmark_t", 0.0)) > 0.0 else white
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
        canvas.rect(bx - 2, by - 2, bw + 4, bh + 4, panel_c)
        canvas.rect(bx, by, max(1, int(bw * frac)), bh, (0.92, 0.20, 0.14, 0.95))
    if boss is None and bool(getattr(sim, "pickup_active", False)):
        # The beacon is the pointer; this label tells a new player what it is.
        spot = getattr(sim, "levels", {}).get("pickup", {"x": 0.0, "z": -6.0})
        dx = float(spot.get("x", 0.0)) - float(sim.player_pos.x)
        dz = float(spot.get("z", -6.0)) - float(sim.player_pos.z)
        if math.hypot(dx, dz) <= 18.0:
            canvas.text(cx - 105, 100, "SURGE PICKUP READY", (0.40, 1.0, 0.52, 1.0), 2)

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
    # top-center wave/score/streak (single source; engine status() omits these)
    canvas.text(cx - 90, 34, f"WAVE {int(getattr(sim, 'wave', 1))}  "
               f"SCORE {int(getattr(sim, 'score', 0))}", white, 2)
    streak = int(getattr(sim, "streak", 0))
    od_t = float(getattr(sim, "overdrive_t", 0.0))
    if streak > 0:
        canvas.text(cx - 90, 52, f"STREAK x{streak}", accent, 2)
    if od_t > 0.0:
        canvas.text(cx - 90, 68, f"OVERDRIVE {od_t:.1f}s x2", accent, 2)
    elif str(getattr(sim, "weapon", "")) == "surge" and float(getattr(sim, "surge_t", 0.0)) > 0.0:
        canvas.text(cx - 90, 68, f"SURGE {float(getattr(sim, 'surge_t', 0.0)):.1f}s - switching drops it", dim, 2)
    if int(getattr(sim, "near_miss", 0)) > 0:
        canvas.text(cx - 90, 84, f"NEAR-MISS {int(getattr(sim, 'near_miss', 0))}", dim, 2)
    if not bool(getattr(sim, "alive", True)):
        canvas.rect(0, 0, w, h, (0.45, 0.02, 0.02, 0.28))
        canvas.text(cx - 70, cy - 60, "YOU DIED", danger, 4)
