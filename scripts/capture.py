"""Seeded capture driver: step ShooterGame with a bot script, then headless Engine capture.

Routes (seed 1, FIXED_STEP):
  spawn   : 1 idle frame (empty arena baseline)
  combat  : kite 300 frames (aimed fight, tracers/particles live)
  pickup  : kite until wave>=2 and pickup visible, or 1200 frames max
  death   : hp=10 + brute at 1 m, 180 idle frames (YOU DIED)

Writes PNG + JSON report pairs for before/after comparison.
No balance changes; driver only.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "keystone"))

from keystone.input import ActionState  # noqa: E402
from keystone.math3d import Vec3  # noqa: E402
from keystone.replay import FIXED_STEP  # noqa: E402

from shooter.bot import fire_hold, kite_step  # noqa: E402
from shooter.game import ShooterGame  # noqa: E402
from shooter.sim import _Enemy  # noqa: E402

try:  # older checkouts used for before/after worktrees have no profile module
    from shooter.profile import ProfileStore, default_profile  # noqa: E402
except ImportError:  # pragma: no cover - only for cross-commit evidence worktrees
    ProfileStore = None  # type: ignore[assignment]
    default_profile = None  # type: ignore[assignment]


def _new_game() -> ShooterGame:
    """Evidence runs use a throwaway profile, never the player's save."""
    import tempfile

    return ShooterGame(profile_path=Path(tempfile.mkdtemp(prefix="shooter-capture-")) / "profile.json")


def _capture_stepped(game: ShooterGame, out_png: str, out_json: str, w: int = 960, h: int = 540) -> None:
    """Capture the already-stepped game without resetting it.

    Engine.__init__ calls game.build_scene(), so the game must be stepped
    AFTER the Engine exists (engine.game is the same object).
    """
    from keystone.app import Engine

    engine = Engine(game, w, h, visible=False, msaa=0, ui=True)
    try:
        engine.capture(out_png, out_json)
        print(f"wrote {out_png} + {out_json}")
    finally:
        engine.close()


def _capture(game: ShooterGame, out_png: str, out_json: str, w: int = 960, h: int = 540) -> None:
    _capture_stepped(game, out_png, out_json, w, h)


def _engine_with(game: ShooterGame, w: int = 960, h: int = 540):
    from keystone.app import Engine

    return Engine(game, w, h, visible=False, msaa=0, ui=True)


def _tune(engine, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Apply renderer toggles to an already-built Engine scene (before stepping)."""
    from keystone.scene import BloomSettings, ColorSettings, PostSettings, ShadowSettings

    engine.scene.shadow = ShadowSettings(enabled=bool(shadows))
    engine.scene.color = ColorSettings(enabled=bool(srgb))
    engine.scene.post = PostSettings(enabled=bool(post))
    engine.scene.bloom = BloomSettings(enabled=bool(bloom))


def _profiler(engine) -> dict:
    stats = dict(getattr(engine.renderer, "last_stats", {}))
    print(f"profiler draws={stats.get('draw_calls')} tris={stats.get('triangles')} inst={stats.get('instanced_calls')} shadow_calls={stats.get('shadow_calls')} shadow_map={stats.get('shadow_map_size')} flags=S{stats.get('shadows_enabled')}C{stats.get('srgb_enabled')}P{stats.get('post_enabled')}B{stats.get('bloom_enabled')}")
    return stats


def route_spawn(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        engine.game.update(FIXED_STEP, ActionState())
        engine.capture(f"{prefix}_spawn.png", f"{prefix}_spawn.json")
        _profiler(engine)
        print(f"wrote {prefix}_spawn.png + {prefix}_spawn.json")
    finally:
        engine.close()


def route_combat(prefix: str, frames: int = 277, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    # 277 = 2 enemies alive + a shot fired this frame (kite scan);
    # frame 300 lands between waves with nothing alive.
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        for _ in range(frames):
            engine.game.update(FIXED_STEP, kite_step(engine.game.sim))
        g = engine.game
        print(f"combat shots={g.sim.shots} hits={g.sim.hits} kills={g.sim.kills} wave={g.sim.wave} hp={g.sim.hp}")
        engine.capture(f"{prefix}_combat.png", f"{prefix}_combat.json")
        _profiler(engine)
        print(f"wrote {prefix}_combat.png + {prefix}_combat.json")
    finally:
        engine.close()


def route_fireburst(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Aimed burst at a static target: guarantees visible tracer + flash + hitmark."""
    from keystone.app import Engine
    from keystone.input import ActionState as AS

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = []
        g.sim.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=30, max_hp=30)]
        # step until a shot fires, then capture on that exact frame
        fired = False
        for a in fire_hold(60):
            before = g.sim.shots
            g.update(FIXED_STEP, a)
            if g.sim.shots > before:
                fired = True
                break
        # keep stepping idle (no fire) at most 1 frame so flash/tracer stay alive
        print(f"burst shots={g.sim.shots} hits={g.sim.hits} flash={g.sim.flash_t:.3f} tracers={len(g.sim.tracers)} fired={fired}")
        engine.capture(f"{prefix}_burst.png", f"{prefix}_burst.json")
        _profiler(engine)
        print(f"wrote {prefix}_burst.png + {prefix}_burst.json")
    finally:
        engine.close()


def route_pickup(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        for i in range(1200):
            g.update(FIXED_STEP, kite_step(g.sim))
            if g.sim.pickup_active:
                break
        # Re-stage for the proof frame: the wave-2 surge spot (0, -6) sits
        # behind center cover from spawn, so stage the viewer at (3.5, 8)
        # facing it. Gameplay DATA is untouched; only the camera moves.
        import math
        from dataclasses import replace

        from keystone.math3d import Vec3 as _V

        rest_y = float(g.sim.player_pos.y)  # keeps the 0.0002 floor skin gap
        g.sim.player_pos = _V(3.5, rest_y, 8.0)
        # physics body overwrites player_pos each step: re-stage it too
        g.sim.body = replace(g.sim.body, position=_V(3.5, rest_y, 8.0), on_ground=True)
        g.sim.hvel = _V(0.0, 0.0, 0.0)
        g.sim.yaw = math.atan2(0.0 - 3.5, -(-6.0 - 8.0))
        g.sim.pitch = 0.0
        g.sim.kick = 0.0
        g.update(FIXED_STEP, ActionState())
        print(f"pickup wave={g.sim.wave} active={g.sim.pickup_active} frame={g.sim.tick}")
        engine.capture(f"{prefix}_pickup.png", f"{prefix}_pickup.json")
        _profiler(engine)
        print(f"wrote {prefix}_pickup.png + {prefix}_pickup.json")
    finally:
        engine.close()


def route_boss(prefix: str, with_boss: bool = True, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Fixed wave-3 roster at one frame; same staging on every build.

    The roster is identical before and after the warden lands; the after build
    adds exactly one warden at the centre. This is the boss-content pair.
    """
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = []
        g.sim.spawn_t = 999.0
        g.sim.wave = 3
        g.sim.pickup_taken = True
        roster = [
            ("mite", -3.0, 0.5, 2.0), ("mite", 3.0, 0.5, 2.0),
            ("mite", -6.0, 0.5, -3.0), ("mite", 6.0, 0.5, -3.0),
            ("brute", -5.0, 0.7, 4.0), ("brute", 5.0, 0.7, 4.0),
            ("wisp", -8.0, 0.4, 0.0), ("wisp", 8.0, 0.4, 0.0),
        ]
        if with_boss and "warden" in g.sim.enemy_defs:
            # Front-and-centre showcase clear of every cover from the spawn eye.
            roster.append(("warden", 0.0, 1.1, 3.5))
        enemies = []
        for etype, x, y, z in roster:
            enemies.append(
                _Enemy(
                    etype=etype, pos=Vec3(x, y, z),
                    hp=int(g.sim.enemy_defs[etype]["hp"]),
                    max_hp=int(g.sim.enemy_defs[etype]["hp"]),
                    attack_cd=10.0,  # one clean staging frame: no immediate hit
                )
            )
        g.sim.enemies = enemies
        if g.sim.enemies and "warden" in g.sim.enemy_defs:
            for enemy in g.sim.enemies:
                if enemy.etype == "warden":
                    enemy.summon_cd = 999.0  # keep the proof frame free of escorts
        g.update(FIXED_STEP, ActionState())
        print(
            f"boss wave={g.sim.wave} roster={[e.etype for e in g.sim.enemies]} "
            f"alive={sum(1 for e in g.sim.enemies if e.alive)} hp={g.sim.hp}"
        )
        engine.capture(f"{prefix}_boss.png", f"{prefix}_boss.json")
        _profiler(engine)
        print(f"wrote {prefix}_boss.png + {prefix}_boss.json")
    finally:
        engine.close()


def route_hurt(prefix: str, side: str = "right", shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """First-hit frame with the attacker just outside the centre view.

    Same seeded state for every side, so before/after screenshots differ only
    by the game's own damage feedback. The attacker is placed at 2.2 m and the
    player stands still; the first mite hit lands in ~10 frames.
    """
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.enemies = []
        x, z = g.sim.player_pos.x, g.sim.player_pos.z
        if side == "right":
            x += 2.2
        elif side == "left":
            x -= 2.2
        else:  # behind
            z += 2.2
        g.sim.enemies = [_Enemy(etype="mite", pos=Vec3(x, 0.5, z), hp=30, max_hp=30)]
        for _ in range(90):
            before = int(g.sim.hp)
            g.update(FIXED_STEP, ActionState())
            if int(g.sim.hp) < before:
                break
        hurt_t = getattr(g.sim, "hurt_t", None)
        print(
            f"hurt side={side} frame={g.sim.tick} hp={g.sim.hp} "
            f"cue_t={hurt_t} source=({g.sim.enemies[0].pos.x:.2f},{g.sim.enemies[0].pos.z:.2f})"
        )
        engine.capture(f"{prefix}_hurt_{side}.png", f"{prefix}_hurt_{side}.json")
        _profiler(engine)
        print(f"wrote {prefix}_hurt_{side}.png + {prefix}_hurt_{side}.json")
    finally:
        engine.close()


def route_pickup_spawn(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Wave-2 pickup active, clean arena, player staged back at spawn.

    Shows what a player sees when the surge pickup is ready: the centre cover
    hides the cube from the spawn eye. Same staging before/after the beacon.
    """
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        for _ in range(1200):
            g.update(FIXED_STEP, kite_step(g.sim))
            if g.sim.pickup_active:
                break
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.enemies = []
        rest_y = float(g.sim.player_pos.y)  # keeps the 0.0002 floor skin gap
        g.sim.player_pos = Vec3(0.0, rest_y, 8.0)
        g.sim.body = g.sim.body.__class__(
            position=Vec3(0.0, rest_y, 8.0), half_extents=g.sim.body.half_extents,
            velocity=Vec3(), on_ground=True,
        )
        g.sim.hvel = Vec3()
        g.sim.yaw = 0.0
        g.sim.pitch = 0.0
        g.sim.kick = 0.0
        g.update(FIXED_STEP, ActionState())
        print(
            f"pickup-spawn frame={g.sim.tick} active={g.sim.pickup_active} "
            f"hp={g.sim.hp} dist={abs(g.sim.player_pos.z + 6.0):.1f}"
        )
        engine.capture(f"{prefix}_pickup_spawn.png", f"{prefix}_pickup_spawn.json")
        _profiler(engine)
        print(f"wrote {prefix}_pickup_spawn.png + {prefix}_pickup_spawn.json")
    finally:
        engine.close()


def route_slam(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Close-range warden windup + slam frames; the audio-caption proof pair."""
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = []
        g.sim.spawn_t = 999.0
        g.sim.wave = 3
        g.sim.enemies = [
            _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 5.0), hp=600, max_hp=600,
                   summon_cd=999.0)
        ]
        captured = False
        for _ in range(120):
            g.update(FIXED_STEP, ActionState())
            boss = g.sim.enemies[0]
            if not captured and 0.0 < boss.windup_t < 0.45:
                engine.capture(f"{prefix}_slam_windup.png", f"{prefix}_slam_windup.json")
                print(f"slam-windup frame={g.sim.tick} hp={g.sim.hp} windup={boss.windup_t:.2f}")
                captured = True
            if g.sim.hp < 100:
                engine.capture(f"{prefix}_slam_hit.png", f"{prefix}_slam_hit.json")
                print(f"slam-hit frame={g.sim.tick} hp={g.sim.hp} cue_t={getattr(g, 'sound_cue_t', 0.0)}")
                break
        _profiler(engine)
    finally:
        engine.close()


def route_reload(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Frame where the reload tail completes; the reload-cue pair."""
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.enemies = []
        g.sim.ammo["pulse"] = 0
        g.sim.reserve["pulse"] = 120
        g.sim.reload_t = 0.01
        g.update(FIXED_STEP, ActionState())
        print(
            f"reload frame={g.sim.tick} ammo={g.sim.ammo['pulse']} "
            f"reserve={g.sim.reserve['pulse']} cue={getattr(g, 'sound_cue', '-')!r} "
            f"voices={g.mixer.voice_count()}"
        )
        engine.capture(f"{prefix}_reload.png", f"{prefix}_reload.json")
        _profiler(engine)
    finally:
        engine.close()


def route_reticle(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """One clean frame per weapon: the hip-fire reticle-spread pair.

    Same seed, frame count, target, camera and renderer flags in both builds;
    only the HUD gap may differ. The pulse frame is the unchanged control.
    """
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=30, max_hp=30)]
        for wid in ("scatter", "lance", "surge", "pulse"):
            g.sim.weapon = wid
            if wid == "surge":
                g.sim.surge_t = float(g.sim.weapons["surge"].get("duration_s", 10.0))
                g.sim.ammo["surge"] = int(g.sim.weapons["surge"]["mag"])
            else:
                g.sim.surge_t = 0.0
            g.update(FIXED_STEP, ActionState())
            wdef = g.sim.weapons[wid]
            print(
                f"reticle {wid} frame={g.sim.tick} spread={float(wdef['spread_hip_deg']):.2f}deg "
                f"mag={g.sim.ammo[wid]}/{g.sim.reserve[wid]} hp={g.sim.hp}"
            )
            engine.capture(f"{prefix}_{wid}.png", f"{prefix}_{wid}.json")
        _profiler(engine)
    finally:
        engine.close()


def route_slam_ring(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Staged warden windup with the player outside the slam: the ring pair."""
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.wave = 3
        g.sim.enemies = [_Enemy(etype="warden", pos=Vec3(0.0, 1.1, 2.0),
                                hp=600, max_hp=600, summon_cd=999.0,
                                windup_t=0.5)]
        g.update(FIXED_STEP, ActionState())
        boss = g.sim.enemies[0]
        print(
            f"slam-ring frame={g.sim.tick} windup={boss.windup_t:.3f} "
            f"ring={sum(1 for n in getattr(g, '_slam_ring', []) if n.visible)} "
            f"radius={float(g.sim.enemy_defs['warden']['range']):.1f}"
        )
        engine.capture(f"{prefix}_slam_ring.png", f"{prefix}_slam_ring.json")
        _profiler(engine)
    finally:
        engine.close()


def route_killmark(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """First-kill frame after the flash clears: the kill-marker pair."""
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0),
                                hp=12, max_hp=30)]
        fire = ActionState(held=frozenset({"fire"}))
        for _ in range(20):
            before = int(g.sim.kills)
            g.update(FIXED_STEP, fire)
            if int(g.sim.kills) > before:
                for _ in range(7):
                    g.update(FIXED_STEP, ActionState())
                print(
                    f"killmark frame={g.sim.tick} kills={g.sim.kills} "
                    f"killmark_t={float(getattr(g.sim, 'killmark_t', 0.0)):.3f} "
                    f"hitmark_t={float(getattr(g.sim, 'hitmark_t', 0.0)):.3f}"
                )
                engine.capture(f"{prefix}_killmark.png", f"{prefix}_killmark.json")
                break
        _profiler(engine)
    finally:
        engine.close()


def route_switch_cue(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """One clean frame after pressing slot 2: the weapon-switch cue pair."""
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.enemies = []
        g.update(FIXED_STEP, ActionState(pressed=frozenset({"slot2"})))
        print(
            f"switch-cue frame={g.sim.tick} weapon={g.sim.weapon} "
            f"cue={getattr(g, 'sound_cue', '')!r} "
            f"voices={g.mixer.voice_count()}"
        )
        engine.capture(f"{prefix}_switch_cue.png", f"{prefix}_switch_cue.json")
        _profiler(engine)
    finally:
        engine.close()


def route_tracer_tint(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """One first-shot frame per weapon: the tracer/flash tint pair.

    The target is a 600 hp brute at 6 m, so no shot kills and every frame
    keeps its live tracer and flash. Same staging in both builds.
    """
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        for wid in ("pulse", "scatter", "lance", "surge"):
            g.sim.enemies = [_Enemy(etype="brute", pos=Vec3(0.0, 0.7, 2.0),
                                    hp=600, max_hp=600, attack_cd=10.0)]
            g.sim.weapon = wid
            g.sim.ammo[wid] = int(g.sim.weapons[wid]["mag"])
            g.sim.cooldown = 0.0
            g.sim.reload_t = 0.0
            g.sim.surge_t = 10.0 if wid == "surge" else 0.0
            g.sim.flash_t = 0.0
            g.sim.tracers = []
            g.update(FIXED_STEP, ActionState(mouse_clicked=True))
            print(
                f"tracer {wid} frame={g.sim.tick} flash={g.sim.flash_t:.3f} "
                f"tracers={len(g.sim.tracers)} hp={g.sim.enemies[0].hp}"
            )
            engine.capture(f"{prefix}_{wid}.png", f"{prefix}_{wid}.json")
        _profiler(engine)
    finally:
        engine.close()


def route_score_center(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """High-score HUD with every top-center status line live: centering pair."""
    from keystone.app import Engine

    game = _new_game()
    game.profile["best_score"] = 9999
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.enemies = []
        g.sim.wave = 3
        g.sim.score = 12345
        g.sim.streak = 7
        g.sim.best_streak = 9
        g.sim.overdrive_t = 5.0
        g.sim.near_miss = 3
        g.update(FIXED_STEP, ActionState())
        print(
            f"score-center frame={g.sim.tick} wave={g.sim.wave} "
            f"score={g.sim.score} best={g.profile.get('best_score')} "
            f"streak={g.sim.streak} near={g.sim.near_miss}"
        )
        engine.capture(f"{prefix}_score_center.png", f"{prefix}_score_center.json")
        _profiler(engine)
    finally:
        engine.close()


def route_spawn_mark(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """A staged wave spawn at the pickup line: the spawn-marker pair.

    The enemy and spawn position are fixed; only the game's marker may
    differ, so the before frame has no beam and the after frame does.
    """
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, -6.0),
                                hp=30, max_hp=30)]
        g.sim.spawn_pos = Vec3(0.0, 0.5, -6.0)
        g._play_event("spawn")
        g.update(FIXED_STEP, ActionState())
        print(
            f"spawn-mark frame={g.sim.tick} enemies={len(g.sim.enemies)} "
            f"marks={len(getattr(g, 'spawn_marks', []))} hp={g.sim.hp}"
        )
        engine.capture(f"{prefix}_spawn_mark.png", f"{prefix}_spawn_mark.json")
        _profiler(engine)
    finally:
        engine.close()


def route_highground(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Player on the low platform edge with a mite at its base.

    The mite is below the platform; the first frame is the vertical-reach
    proof (hp 100 after the fix, 92 before). Same staging in both builds.
    """
    import math

    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.player_pos = Vec3(-16.0, 1.6002, 17.5)
        g.sim.body = g.sim.body.__class__(
            position=Vec3(-16.0, 1.6002, 17.5), half_extents=g.sim.body.half_extents,
            velocity=Vec3(), on_ground=True,
        )
        g.sim.hvel = Vec3()
        g.sim.yaw = math.pi
        g.sim.pitch = -0.9
        g.sim.kick = 0.0
        g.sim.enemies = [
            _Enemy(etype="mite", pos=Vec3(-16.0, 0.5, 18.6), hp=30, max_hp=30)
        ]
        g.update(FIXED_STEP, ActionState())
        e = g.sim.enemies[0]
        print(
            f"highground frame={g.sim.tick} hp={g.sim.hp} "
            f"mite=({e.pos.x:.2f},{e.pos.y:.2f},{e.pos.z:.2f}) "
            f"cue_t={float(getattr(g.sim, 'hurt_t', 0.0)):.2f}"
        )
        engine.capture(f"{prefix}_highground.png", f"{prefix}_highground.json")
        _profiler(engine)
    finally:
        engine.close()


def route_boss_hp(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Half-health warden bar: the numeric-HP HUD pair."""
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = []
        g.sim.spawn_t = 999.0
        g.sim.wave = 3
        g.sim.pickup_taken = True
        g.sim.enemies = [
            _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 3.5), hp=300, max_hp=600,
                   attack_cd=10.0, summon_cd=999.0)
        ]
        g.update(FIXED_STEP, ActionState())
        print(f"boss-hp frame={g.sim.tick} hp={g.sim.enemies[0].hp}/{g.sim.enemies[0].max_hp}")
        engine.capture(f"{prefix}_boss_hp.png", f"{prefix}_boss_hp.json")
        _profiler(engine)
    finally:
        engine.close()


def route_los(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Brute adjacent to a thin cover with the player on the other side."""
    import math

    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.player_pos = Vec3(-6.0, 0.9002, 3.8)
        g.sim.body = g.sim.body.__class__(
            position=Vec3(-6.0, 0.9002, 3.8), half_extents=g.sim.body.half_extents,
            velocity=Vec3(), on_ground=True,
        )
        g.sim.hvel = Vec3()
        g.sim.yaw = math.pi
        g.sim.pitch = 0.0
        g.sim.enemies = [
            _Enemy(etype="brute", pos=Vec3(-6.0, 0.7, 6.2), hp=120, max_hp=120)
        ]
        g.update(FIXED_STEP, ActionState())
        print(
            f"los frame={g.sim.tick} hp={g.sim.hp} "
            f"brute=({g.sim.enemies[0].pos.x:.2f},{g.sim.enemies[0].pos.z:.2f})"
        )
        engine.capture(f"{prefix}_los.png", f"{prefix}_los.json")
        _profiler(engine)
    finally:
        engine.close()


def route_dry(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Fire with no magazine and no reserve: the dry-fire cue pair."""
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.enemies = []
        g.sim.ammo["pulse"] = 0
        g.sim.reserve["pulse"] = 0
        g.update(FIXED_STEP, ActionState(held=frozenset({"fire"})))
        print(
            f"dry frame={g.sim.tick} cue={getattr(g, 'sound_cue', '-')!r} "
            f"voices={g.mixer.voice_count()} shots={g.sim.shots}"
        )
        engine.capture(f"{prefix}_dry.png", f"{prefix}_dry.json")
        _profiler(engine)
    finally:
        engine.close()


def route_denied(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Overdrive pressed with no pulse reserve: the denial cue pair."""
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.enemies = []
        g.sim.reserve["pulse"] = 0
        g.update(FIXED_STEP, ActionState(pressed=frozenset({"overdrive"})))
        print(
            f"denied frame={g.sim.tick} cue={getattr(g, 'sound_cue', '-')!r} "
            f"cue_t={getattr(g, 'sound_cue_t', 0.0):.2f} voices={g.mixer.voice_count()} "
            f"reserve={g.sim.reserve['pulse']}"
        )
        engine.capture(f"{prefix}_denied.png", f"{prefix}_denied.json")
        _profiler(engine)
    finally:
        engine.close()


def route_muzzle(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Exact first-shot frame: the muzzle-flash occlusion pair."""
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=30, max_hp=30)]
        fire = ActionState(held=frozenset({"fire"}))
        for _ in range(20):
            before = int(g.sim.shots)
            g.update(FIXED_STEP, fire)
            if int(g.sim.shots) > before:
                print(
                    f"muzzle frame={g.sim.tick} shots={g.sim.shots} hits={g.sim.hits} "
                    f"flash=({g.sim.flash_pos.x:.2f},{g.sim.flash_pos.y:.2f},{g.sim.flash_pos.z:.2f}) "
                    f"t={g.sim.flash_t:.2f}"
                )
                engine.capture(f"{prefix}_muzzle.png", f"{prefix}_muzzle.json")
                break
        _profiler(engine)
    finally:
        engine.close()


def route_killfeed(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """First-kill frame after the flash clears: the kill-feed pair."""
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=12, max_hp=30)]
        fire = ActionState(held=frozenset({"fire"}))
        for _ in range(20):
            before = int(g.sim.kills)
            g.update(FIXED_STEP, fire)
            if int(g.sim.kills) > before:
                for _ in range(7):
                    g.update(FIXED_STEP, ActionState())
                print(
                    f"killfeed frame={g.sim.tick} kills={g.sim.kills} score={g.sim.score} "
                    f"feed={getattr(g, 'kill_feed', None)}"
                )
                engine.capture(f"{prefix}_killfeed.png", f"{prefix}_killfeed.json")
                break
        _profiler(engine)
    finally:
        engine.close()


def route_platform(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Spawn view turned toward the rear low platform (before/after pair)."""
    import math

    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.player_pos = Vec3(-16.0, 0.9002, 9.5)
        g.sim.body = g.sim.body.__class__(
            position=Vec3(-16.0, 0.9002, 9.5), half_extents=g.sim.body.half_extents,
            velocity=Vec3(), on_ground=True,
        )
        g.sim.hvel = Vec3()
        g.sim.yaw = math.pi
        g.sim.pitch = 0.0
        g.sim.kick = 0.0
        g.update(FIXED_STEP, ActionState())
        print(f"platform view z={g.sim.player_pos.z:.2f} covers={len(g.sim.cover_boxes)}")
        engine.capture(f"{prefix}_platform.png", f"{prefix}_platform.json")
        _profiler(engine)
    finally:
        engine.close()


def route_cover(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """A mite walks from behind the centre cover toward the spawn eye."""
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, -2.0), hp=30, max_hp=30)]
        for _ in range(40):
            g.update(FIXED_STEP, ActionState())
        e = g.sim.enemies[0]
        inside = any(
            abs(e.pos.x - float(c["x"])) < float(c["w"]) / 2.0 + 0.5
            and abs(e.pos.z - float(c["z"])) < float(c["d"]) / 2.0 + 0.5
            for c in g.sim.levels["arena"]["covers"]
        )
        print(f"cover frame={g.sim.tick} mite=({e.pos.x:.2f},{e.pos.z:.2f}) inside={inside}")
        engine.capture(f"{prefix}_cover.png", f"{prefix}_cover.json")
        _profiler(engine)
    finally:
        engine.close()


def route_flinch(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Exact first-hit frame on a live mite: the combat hit-reaction pair."""
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.enemies = [_Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=30, max_hp=30)]
        fire = ActionState(held=frozenset({"fire"}))
        for _ in range(20):
            before = int(g.sim.hits)
            g.update(FIXED_STEP, fire)
            if int(g.sim.hits) > before:
                enemy = g.sim.enemies[0]
                # Let the muzzle flash expire but keep the flinch visible.
                for _ in range(7):
                    g.update(FIXED_STEP, ActionState())
                print(
                    f"flinch hit frame={g.sim.tick} hp={enemy.hp} "
                    f"hit_t={getattr(enemy, 'hit_t', None)} "
                    f"pos=({enemy.pos.x:.2f},{enemy.pos.z:.2f})"
                )
                engine.capture(f"{prefix}_flinch.png", f"{prefix}_flinch.json")
                break
        _profiler(engine)
    finally:
        engine.close()


def route_hud_ammo(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Low-magazine and mid-reload HUD frames on a clean arena."""
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = ["mite"]
        g.sim.spawn_t = 999.0
        g.sim.enemies = []
        g.sim.weapon = "pulse"
        g.sim.ammo["pulse"] = 3
        g.update(FIXED_STEP, ActionState())
        engine.capture(f"{prefix}_low_ammo.png", f"{prefix}_low_ammo.json")
        g.sim.ammo["pulse"] = 0
        g.sim.reload_t = 0.55
        g.update(FIXED_STEP, ActionState())
        engine.capture(f"{prefix}_reload.png", f"{prefix}_reload.json")
        print(f"hud-ammo mag={g.sim.ammo['pulse']} reload_t={g.sim.reload_t:.2f}")
        _profiler(engine)
    finally:
        engine.close()


def route_win(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    """Kill the wave-3 warden and capture the wave-4 clear frame."""
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = []
        g.sim.spawn_t = 999.0
        g.sim.pickup_taken = True
        g.sim.wave = 3
        g.sim.score = 5000
        g.sim.kills = 20
        g.sim.best_streak = 5
        g.sim.enemies = [
            _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 2.0), hp=12, max_hp=600,
                   summon_cd=999.0)
        ]
        fire = ActionState(held=frozenset({"fire"}))
        for _ in range(60):
            g.update(FIXED_STEP, fire)
            if int(g.sim.wave) >= 4:
                break
        print(
            f"win wave={g.sim.wave} score={g.sim.score} alive={g.sim.alive} "
            f"cleared={bool(getattr(g, 'campaign_cleared', False))} "
            f"banner_t={getattr(g, 'campaign_clear_t', 0.0)}"
        )
        engine.capture(f"{prefix}_win.png", f"{prefix}_win.json")
        _profiler(engine)
    finally:
        engine.close()


def route_death_profile(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True,
                        bloom: bool = True, win_history: bool = False) -> None:
    """Staged run-over frame with a seeded best, against the no-profile build."""
    from keystone.app import Engine

    profile_path = Path(tempfile.mkdtemp(prefix="shooter-death-")) / "profile.json"
    if ProfileStore is not None and default_profile is not None:
        seeded = default_profile()
        seeded.update({"runs": 3, "best_score": 1000, "best_kills": 12,
                       "best_wave": 4, "best_streak": 6})
        seeded["history"] = [
            {"score": 980, "kills": 8, "wave": 3, "best_streak": 5,
             "time_s": 41, "outcome": "win" if win_history else "lose"},
            {"score": 740, "kills": 6, "wave": 2, "best_streak": 3,
             "time_s": 30, "outcome": "lose"},
        ]
        if win_history:
            seeded["wins"] = 1
        ProfileStore(profile_path).save(seeded)
    try:
        game = ShooterGame(profile_path=profile_path)
    except TypeError:  # pre-profile build
        game = ShooterGame()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = []
        g.sim.spawn_t = 999.0
        g.sim.wave = 2
        g.sim.hp = 10
        g.sim.score = 1500
        g.sim.kills = 9
        g.sim.best_streak = 4
        g.sim.enemies = [_Enemy(etype="brute", pos=Vec3(0.0, 0.7, 7.0), hp=120, max_hp=120)]
        for _ in range(180):
            g.update(FIXED_STEP, ActionState())
            if not g.sim.alive:
                break
        profile = getattr(g, "profile", {})
        print(
            f"death-profile alive={g.sim.alive} score={g.sim.score} "
            f"best={profile.get('best_score')} runs={profile.get('runs')} "
            f"wins={profile.get('wins')} "
            f"history={[r.get('outcome') for r in profile.get('history', [])]} "
            f"last={getattr(g, 'last_run', None)}"
        )
        engine.capture(f"{prefix}_death_profile.png", f"{prefix}_death_profile.json")
        _profiler(engine)
    finally:
        engine.close()


def route_win_history(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True,
                      bloom: bool = True) -> None:
    """Debrief with a seeded win + loss: the outcome-marker pair."""
    route_death_profile(prefix, shadows, srgb, post, bloom, win_history=True)


def route_death(prefix: str, shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    from keystone.app import Engine

    game = _new_game()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    _tune(engine, shadows, srgb, post, bloom)
    try:
        g = engine.game
        g.sim.spawn_queue = []
        g.sim.hp = 10
        g.sim.enemies = [_Enemy(etype="brute", pos=Vec3(0.0, 0.7, 7.0), hp=120, max_hp=120)]
        for _ in range(180):
            g.update(FIXED_STEP, ActionState())
        print(f"death hp={g.sim.hp} alive={g.sim.alive}")
        engine.capture(f"{prefix}_death.png", f"{prefix}_death.json")
        _profiler(engine)
        print(f"wrote {prefix}_death.png + {prefix}_death.json")
    finally:
        engine.close()


def main(which: str = "all", prefix: str = "shot_fix", shadows: bool = True, srgb: bool = True, post: bool = True, bloom: bool = True) -> None:
    if which in ("all", "spawn"):
        route_spawn(prefix, shadows, srgb, post, bloom)
    if which in ("all", "combat"):
        route_combat(prefix, 277, shadows, srgb, post, bloom)
    if which in ("all", "burst"):
        route_fireburst(prefix, shadows, srgb, post, bloom)
    if which in ("all", "pickup"):
        route_pickup(prefix, shadows, srgb, post, bloom)
    if which == "hurt":
        for side in ("left", "right", "behind"):
            route_hurt(prefix, side, shadows, srgb, post, bloom)
    if which == "boss":
        route_boss(prefix, "--no-boss" not in _flags, shadows, srgb, post, bloom)
    if which == "pickup_spawn":
        route_pickup_spawn(prefix, shadows, srgb, post, bloom)
    if which == "slam":
        route_slam(prefix, shadows, srgb, post, bloom)
    if which == "death_profile":
        route_death_profile(prefix, shadows, srgb, post, bloom)
    if which == "win_history":
        route_win_history(prefix, shadows, srgb, post, bloom)
    if which == "win":
        route_win(prefix, shadows, srgb, post, bloom)
    if which == "hud_ammo":
        route_hud_ammo(prefix, shadows, srgb, post, bloom)
    if which == "flinch":
        route_flinch(prefix, shadows, srgb, post, bloom)
    if which == "cover":
        route_cover(prefix, shadows, srgb, post, bloom)
    if which == "platform":
        route_platform(prefix, shadows, srgb, post, bloom)
    if which == "killfeed":
        route_killfeed(prefix, shadows, srgb, post, bloom)
    if which == "muzzle":
        route_muzzle(prefix, shadows, srgb, post, bloom)
    if which == "denied":
        route_denied(prefix, shadows, srgb, post, bloom)
    if which == "dry":
        route_dry(prefix, shadows, srgb, post, bloom)
    if which == "los":
        route_los(prefix, shadows, srgb, post, bloom)
    if which == "boss_hp":
        route_boss_hp(prefix, shadows, srgb, post, bloom)
    if which == "reticle":
        route_reticle(prefix, shadows, srgb, post, bloom)
    if which == "highground":
        route_highground(prefix, shadows, srgb, post, bloom)
    if which == "spawn_mark":
        route_spawn_mark(prefix, shadows, srgb, post, bloom)
    if which == "score_center":
        route_score_center(prefix, shadows, srgb, post, bloom)
    if which == "tracer_tint":
        route_tracer_tint(prefix, shadows, srgb, post, bloom)
    if which == "switch_cue":
        route_switch_cue(prefix, shadows, srgb, post, bloom)
    if which == "killmark":
        route_killmark(prefix, shadows, srgb, post, bloom)
    if which == "slam_ring":
        route_slam_ring(prefix, shadows, srgb, post, bloom)
    if which == "reload":
        route_reload(prefix, shadows, srgb, post, bloom)
    if which in ("all", "death"):
        route_death(prefix, shadows, srgb, post, bloom)


if __name__ == "__main__":
    _args = [a for a in sys.argv[1:] if not a.startswith("--")]
    _flags = {a for a in sys.argv[1:] if a.startswith("--")}
    _which = _args[0] if len(_args) > 0 else "all"
    _prefix = _args[1] if len(_args) > 1 else "shot_fix"
    main(
        _which,
        _prefix,
        shadows="--no-shadows" not in _flags,
        srgb="--no-srgb" not in _flags,
        post="--no-post" not in _flags,
        bloom="--no-bloom" not in _flags,
    )
