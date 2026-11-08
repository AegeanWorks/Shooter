"""Played-run evidence harness: drive the shipped game through the Engine loop.

The run uses the real five-operation contract (build_scene -> update ->
snapshot), the real renderer/UI at capture time, and the shipped DATA tables.
No balance changes and no synthetic kills: policies only feed ActionState.

Modes:
  idle     stand still and let the arena come to you (natural hurt events)
  kite     survivor policy from shooter.bot (economy/regression run)
  strafe   strafe_fire drill (minute-one regression run)
  ambush   staged alternating side attackers (damage-direction drill)
  boss     warden-only wave-3 fight with the kite policy (ends on boss death)
  slam     close-range warden windup/slam (audio + caption drill)
  brute    stand in a brute's slam range (brute-slam cue drill)
  brute_gap stand 2.7 m from a brute (dead-zone close drill)
  brute_windup stand in brute range (windup tell, then the delayed slam)
  warden_cover stand behind the north cover during a warden slam (LOS drill)
  west_gap walk the west-wall strip past the platform (gap drill)
  boss_death stand in a warden slam at 5 HP (death-screen UI drill)
  summon   stand on the platform edge while a warden summons by the cover
  summon_overlap  idle at spawn while a centre warden summons (overlap drill)
  campaign stage a wave-3 warden kill, then idle through the clear banner
  pickup   walk the clear side lane into the live surge pickup (ends on pickup)
  death    staged near-death run (profile/debrief proof; ends on death)
  save_fail staged near-death run with the profile lock held (save-error proof)
  save_retry failed wave save, then lock released and a death save (retry proof)
  profile_bad staged near-death run with an unsupported schema (disabled proof)
  profile_corrupt staged near-death run with an unrecoverable corrupt profile (reset proof)
  profile_backup_restart missing main + valid .bak before game start (restart proof)
  platform run at the rear low platform, jump onto it, stop on the top
  highground stand on the platform edge with a mite at its base (reach drill)
  switch   press slot2 -> slot3 -> slot1 (weapon-switch cue drill)
  overdrive press overdrive on an empty arena (state/material drill)
  overdrive_kill  force a kill during overdrive (reward-cue drill)
  clutch   clear a wave at 30 HP (clutch cue drill)
  forfeit  arm surge, then press slot1 (surge-forfeit cue drill)
  denied   press overdrive with no pulse reserve (audio/caption drill)
  dry      hold fire with 0 magazine and 0 reserve (dry-fire drill)
  reload   finish a reload tail (reload-completion cue drill)

Writes a machine-readable report with per-frame health, event frames,
hurt-source telemetry and the final deterministic snapshot hash.
"""

from __future__ import annotations

import json
import math
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "keystone"))

from keystone.app import Engine  # noqa: E402
from keystone.input import ActionState  # noqa: E402
from keystone.math3d import Vec3  # noqa: E402
from keystone.replay import FIXED_STEP, stable_hash  # noqa: E402

from shooter.bot import kite_step, strafe_fire  # noqa: E402
from shooter.game import ShooterGame  # noqa: E402
from shooter.sim import _Enemy  # noqa: E402

CHUNK = 60


def _stage_ambush(game: ShooterGame, frame: int) -> None:
    """Alternate a fresh side attacker every 90 frames (player stands still)."""
    if frame % 90 != 0:
        return
    sim = game.sim
    side = 1.0 if (frame // 90) % 2 == 0 else -1.0
    x = sim.player_pos.x + 5.0 * side
    z = sim.player_pos.z
    sim.enemies = [
        _Enemy(etype="mite", pos=Vec3(x, 0.5, z), hp=30, max_hp=30, attack_cd=0.0)
    ]


def _action(mode: str, game: ShooterGame, frame: int, strafe: list[ActionState]) -> ActionState:
    if mode in ("kite", "boss"):
        return kite_step(game.sim)
    if mode == "strafe":
        return strafe[frame % len(strafe)]
    if mode == "pickup":
        return ActionState(forward=1.0)
    if mode == "platform":
        return (
            ActionState(forward=1.0, up=1.0)
            if frame < 45
            else ActionState(forward=1.0)
        )
    if mode == "switch":
        if frame == 0:
            return ActionState(pressed=frozenset({"slot2"}))
        if frame == 10:
            return ActionState(pressed=frozenset({"slot3"}))
        if frame == 20:
            return ActionState(pressed=frozenset({"slot1"}))
        return ActionState()
    if mode == "forfeit":
        return ActionState(pressed=frozenset({"slot1"})) if frame == 2 else ActionState()
    if mode == "overdrive":
        return ActionState(pressed=frozenset({"overdrive"})) if frame == 0 else ActionState()
    if mode == "overdrive_kill":
        return ActionState(held=frozenset({"fire"})) if frame == 0 else ActionState()
    if mode == "campaign":
        return (
            ActionState(held=frozenset({"fire"}))
            if int(game.sim.wave) < 4
            else ActionState()
        )
    if mode == "west_gap":
        return ActionState(forward=1.0)
    if mode == "denied":
        return ActionState(pressed=frozenset({"overdrive"})) if frame == 0 else ActionState()
    if mode == "dry":
        return ActionState(held=frozenset({"fire"}))
    return ActionState()  # idle / slam


def main(
    mode: str = "kite",
    frames: int = 600,
    seed: int = 1,
    out: str = "",
    png: str = "",
    report: str = "",
) -> dict:
    profile_path = Path(tempfile.mkdtemp(prefix="shooter-play-")) / "profile.json"
    lock_path = profile_path.with_name(profile_path.name + ".lock")
    if mode == "save_fail":
        lock_path.write_text("locked", encoding="utf-8")
    if mode == "save_retry":
        lock_path.write_text("locked", encoding="utf-8")
    if mode == "profile_bad":
        profile_path.write_text('{"schema": 99, "best_score": 1}', encoding="utf-8")
    if mode == "profile_corrupt":
        profile_path.write_text('{"broken":', encoding="utf-8")
    if mode == "profile_backup_restart":
        from shooter.profile import ProfileStore, default_profile

        store = ProfileStore(profile_path)
        seeded = default_profile()
        seeded["best_score"] = 4321
        seeded["wins"] = 2
        store.save(seeded)
        store.save(seeded)
        profile_path.unlink()
    try:
        game = ShooterGame(profile_path=profile_path)
    except TypeError:  # older checkout without profile support
        game = ShooterGame()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    try:
        if seed != 1:
            game.sim.reseed(seed)
        if mode in ("ambush", "boss", "slam", "death", "platform", "denied", "dry", "reload"):
            game.sim.spawn_queue = []
            game.sim.spawn_t = 1e9
        boss = None
        if mode == "boss":
            game.sim.wave = 3
            boss = _Enemy(
                etype="warden", pos=Vec3(0.0, 1.1, 0.0), hp=600, max_hp=600,
                summon_cd=2.5,
            )
            game.sim.enemies = [boss]
        if mode == "slam":
            game.sim.wave = 3
            boss = _Enemy(
                etype="warden", pos=Vec3(0.0, 1.1, 5.0), hp=600, max_hp=600,
                summon_cd=999.0,
            )
            game.sim.enemies = [boss]
        if mode == "brute":
            game.sim.spawn_queue = ["mite"]
            game.sim.spawn_t = 999.0
            game.sim.enemies = [
                _Enemy(etype="brute", pos=Vec3(0.0, 0.7, 6.5), hp=120,
                       max_hp=120, attack_cd=0.0)
            ]
        if mode == "brute_gap":
            sim = game.sim
            sim.wave = 2
            sim.spawn_queue = ["mite"]
            sim.spawn_t = 999.0
            sim.player_pos = Vec3(0.0, 0.9002, 8.0)
            sim.body = sim.body.__class__(
                position=Vec3(0.0, 0.9002, 8.0),
                half_extents=sim.body.half_extents,
                velocity=Vec3(), on_ground=True,
            )
            sim.hvel = Vec3()
            sim.yaw = 0.0
            sim.pitch = 0.0
            sim.enemies = [
                _Enemy(etype="brute", pos=Vec3(0.0, 0.7, 5.3), hp=120,
                       max_hp=120, attack_cd=0.0)
            ]
        if mode == "brute_windup":
            sim = game.sim
            sim.wave = 2
            sim.spawn_queue = ["mite"]
            sim.spawn_t = 999.0
            sim.player_pos = Vec3(0.0, 0.9002, 8.0)
            sim.body = sim.body.__class__(
                position=Vec3(0.0, 0.9002, 8.0),
                half_extents=sim.body.half_extents,
                velocity=Vec3(), on_ground=True,
            )
            sim.hvel = Vec3()
            sim.yaw = 0.0
            sim.pitch = 0.0
            sim.enemies = [
                _Enemy(etype="brute", pos=Vec3(0.0, 0.7, 5.8), hp=120,
                       max_hp=120, attack_cd=0.0)
            ]
        if mode == "warden_cover":
            sim = game.sim
            sim.wave = 3
            sim.spawn_queue = ["mite"]
            sim.spawn_t = 999.0
            sim.player_pos = Vec3(0.0, 0.9002, -8.0)
            sim.body = sim.body.__class__(
                position=Vec3(0.0, 0.9002, -8.0),
                half_extents=sim.body.half_extents,
                velocity=Vec3(), on_ground=True,
            )
            sim.hvel = Vec3()
            sim.yaw = 0.0
            sim.pitch = 0.0
            sim.enemies = [
                _Enemy(etype="warden", pos=Vec3(0.0, 1.1, -11.8), hp=600,
                       max_hp=600, windup_t=0.01, summon_cd=999.0)
            ]
        if mode == "west_gap":
            sim = game.sim
            sim.spawn_queue = ["mite"]
            sim.spawn_t = 999.0
            sim.enemies = []
            sim.player_pos = Vec3(-19.0, 0.9002, 9.5)
            sim.body = sim.body.__class__(
                position=Vec3(-19.0, 0.9002, 9.5),
                half_extents=sim.body.half_extents,
                velocity=Vec3(), on_ground=True,
            )
            sim.hvel = Vec3()
            sim.yaw = math.pi
            sim.pitch = 0.0
        if mode == "boss_death":
            sim = game.sim
            sim.wave = 3
            sim.spawn_queue = ["mite"]
            sim.spawn_t = 999.0
            sim.hp = 5
            sim.enemies = [
                _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 6.0), hp=600,
                       max_hp=600, windup_t=0.01, summon_cd=999.0)
            ]
        if mode in ("death", "save_fail", "profile_bad", "profile_corrupt",
                    "profile_backup_restart"):
            sim = game.sim
            sim.wave = 2
            sim.hp = 10
            sim.score = 1500
            sim.kills = 9
            sim.best_streak = 4
            sim.enemies = [_Enemy(etype="brute", pos=Vec3(0.0, 0.7, 7.0), hp=120, max_hp=120)]
        if mode == "denied":
            game.sim.reserve["pulse"] = 0
            game.sim.enemies = []
            game.sim.spawn_queue = ["mite"]  # block wave-clear from stealing the cue
            game.sim.spawn_t = 999.0
        if mode == "dry":
            game.sim.ammo["pulse"] = 0
            game.sim.reserve["pulse"] = 0
            game.sim.enemies = []
            game.sim.spawn_queue = ["mite"]
            game.sim.spawn_t = 999.0
        if mode == "reload":
            game.sim.ammo["pulse"] = 0
            game.sim.reserve["pulse"] = 120
            game.sim.reload_t = 0.01
            game.sim.enemies = []
            game.sim.spawn_queue = ["mite"]
            game.sim.spawn_t = 999.0
        if mode == "platform":
            sim = game.sim
            sim.player_pos = Vec3(-16.0, 0.9002, 9.5)
            sim.body = sim.body.__class__(
                position=Vec3(-16.0, 0.9002, 9.5), half_extents=sim.body.half_extents,
                velocity=Vec3(), on_ground=True,
            )
            sim.yaw = math.pi
            sim.pitch = 0.0
        if mode == "switch":
            game.sim.spawn_queue = ["mite"]
            game.sim.spawn_t = 999.0
            game.sim.enemies = []
        if mode == "forfeit":
            sim = game.sim
            sim.spawn_queue = ["mite"]
            sim.spawn_t = 999.0
            sim.enemies = []
            sim.weapon = "surge"
            sim.surge_t = 5.0
            sim.ammo["surge"] = 20
        if mode == "overdrive":
            game.sim.spawn_queue = ["mite"]
            game.sim.spawn_t = 999.0
            game.sim.enemies = []
        if mode == "overdrive_kill":
            game.sim.spawn_queue = ["mite"]
            game.sim.spawn_t = 999.0
            game.sim.enemies = [
                _Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=1, max_hp=30)
            ]
            game.sim.overdrive_t = 3.0
        if mode == "clutch":
            game.sim.spawn_queue = []
            game.sim.spawn_t = 999.0
            game.sim.enemies = []
            game.sim.hp = 30
        if mode == "save_retry":
            game.sim.spawn_queue = []
            game.sim.spawn_t = 999.0
            game.sim.enemies = []
        if mode == "highground":
            sim = game.sim
            sim.player_pos = Vec3(-16.0, 1.6002, 17.5)
            sim.body = sim.body.__class__(
                position=Vec3(-16.0, 1.6002, 17.5),
                half_extents=sim.body.half_extents,
                velocity=Vec3(), on_ground=True,
            )
            sim.hvel = Vec3()
            sim.yaw = math.pi
            sim.pitch = -0.9
            sim.kick = 0.0
            sim.enemies = [
                _Enemy(etype="mite", pos=Vec3(-16.0, 0.5, 18.6), hp=30, max_hp=30)
            ]
            sim.spawn_queue = ["mite"]
            sim.spawn_t = 999.0
        if mode == "summon":
            sim = game.sim
            sim.wave = 3
            sim.spawn_queue = ["mite"]
            sim.spawn_t = 999.0
            sim.player_pos = Vec3(-16.0, 0.9002, 18.0)
            sim.body = sim.body.__class__(
                position=Vec3(-16.0, 0.9002, 18.0),
                half_extents=sim.body.half_extents,
                velocity=Vec3(), on_ground=True,
            )
            sim.hvel = Vec3()
            sim.yaw = 0.0
            sim.pitch = -0.35
            sim.enemies = [
                _Enemy(etype="warden", pos=Vec3(-16.0, 1.1, 11.0), hp=600,
                       max_hp=600, summon_cd=0.0)
            ]
        if mode == "summon_overlap":
            sim = game.sim
            sim.wave = 3
            sim.spawn_queue = ["mite"]
            sim.spawn_t = 999.0
            sim.enemies = [
                _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 0.0), hp=600,
                       max_hp=600, summon_cd=0.0)
            ]
        if mode == "campaign":
            sim = game.sim
            sim.wave = 3
            sim.spawn_queue = []
            sim.spawn_t = 999.0
            sim.pickup_taken = True
            sim.score = 5000
            sim.kills = 20
            sim.best_streak = 5
            sim.enemies = [
                _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 2.0), hp=12,
                       max_hp=600, summon_cd=999.0)
            ]
        if mode == "pickup":
            sim = game.sim
            sim.wave = 2
            sim.pickup_active = True
            sim.pickup_taken = False
            sim.enemies = []
            sim.spawn_queue = ["mite"]
            sim.spawn_t = 999.0
            rest_y = float(sim.player_pos.y)  # keeps the 0.0002 floor skin gap
            sim.player_pos = Vec3(3.5, rest_y, 8.0)
            sim.body = sim.body.__class__(
                position=Vec3(3.5, rest_y, 8.0), half_extents=sim.body.half_extents,
                velocity=Vec3(), on_ground=True,
            )
            sim.yaw = math.atan2(0.0 - 3.5, -(-6.0 - 8.0))
            sim.pitch = 0.0
        strafe = strafe_fire(frames)
        recorded: list[dict] = []
        hurts: list[dict] = []
        audio_log: list[dict] = []
        wave_events: list[dict] = []
        last_wave = int(game.sim.wave)
        last_hp = int(game.sim.hp)
        original_step = game.sim.step
        summon_snapshot = None

        def step(dt, actions):
            nonlocal summon_snapshot
            events = original_step(dt, actions)
            current = int(game.sim.tick)
            nonempty = [e for e in events if e]
            if nonempty:
                recorded.append({"frame": int(current), "events": nonempty})
            if "boss_summon" in events and summon_snapshot is None:
                positions = list(getattr(game.sim, "summon_positions", []))
                boss = next(
                    (e for e in game.sim.enemies if e.etype == "warden" and e.alive),
                    None,
                )
                mite_r = float(game.sim.enemy_defs["mite"]["radius"])
                boss_r = float(game.sim.enemy_defs["warden"]["radius"])
                gaps = [
                    math.hypot(p.x - boss.pos.x, p.z - boss.pos.z)
                    for p in positions
                ] if boss is not None else []
                pair_gaps = [
                    math.hypot(p.x - q.x, p.z - q.z)
                    for i, p in enumerate(positions)
                    for q in positions[i + 1:]
                ]
                summon_snapshot = {
                    "count": len(positions),
                    "boss_overlap": sum(1 for gap in gaps if gap < boss_r + mite_r),
                    "pair_overlap": sum(1 for gap in pair_gaps if gap < 2.0 * mite_r),
                    "boss_gaps": [round(gap, 2) for gap in gaps],
                    "pair_gaps": [round(gap, 2) for gap in pair_gaps],
                    "positions": [
                        [round(float(p.x), 2), round(float(p.z), 2)] for p in positions
                    ],
                }
            if "hurt" in events:
                hurt = getattr(game.sim, "hurt_t", None)
                source = getattr(game.sim, "hurt_from", None)
                hurts.append(
                    {
                        "frame": int(current),
                        "hp": int(game.sim.hp),
                        "damage": int(last_hp - game.sim.hp),
                        "source": None if source is None else [round(source.x, 3), round(source.z, 3)],
                        "cue_t": None if hurt is None else round(float(hurt), 3),
                    }
                )
            return events

        game.sim.step = step  # type: ignore[method-assign]
        def play(clip, gain):
            audio_log.append(
                {
                    "frame": int(game.sim.tick),
                    "clip": clip.name,
                    "gain": round(float(gain), 3),
                    "voices_before": int(game.mixer.voice_count()),
                }
            )

        game.set_clip_hook(play)
        peak_voices = 0
        started = time.perf_counter()
        chunk_wall = 0.0
        chunk_max = 0.0
        chunks: list[dict] = []
        slow_frames = 0
        ran = 0
        for frame in range(frames):
            ran = frame + 1
            if mode == "ambush":
                _stage_ambush(game, frame)
            if mode == "save_retry" and frame == 1:
                lock_path.unlink(missing_ok=True)
                game.sim.spawn_queue = []
                game.sim.enemies = [
                    _Enemy(etype="brute", pos=Vec3(0.0, 0.7, 7.0), hp=120,
                           max_hp=120)
                ]
                game.sim.hp = 5
            tick = time.perf_counter()
            game.update(FIXED_STEP, _action(mode, game, frame, strafe))
            elapsed = time.perf_counter() - tick
            chunk_wall += elapsed
            chunk_max = max(chunk_max, elapsed)
            peak_voices = max(peak_voices, int(game.mixer.voice_count()))
            if elapsed > FIXED_STEP:
                slow_frames += 1
            hp = int(game.sim.hp)
            last_hp = hp
            if int(game.sim.wave) != last_wave:
                wave_events.append(
                    {"frame": frame, "wave": int(game.sim.wave), "hp": hp,
                     "kills": int(game.sim.kills), "score": int(game.sim.score)}
                )
                last_wave = int(game.sim.wave)
            if boss is not None and not boss.alive:
                break
            if mode == "slam" and game.sim.hp < 100:
                break
            if mode == "death" and not game.sim.alive:
                break
            if mode in ("save_fail", "profile_bad", "profile_corrupt",
                        "profile_backup_restart") and not game.sim.alive:
                break
            if mode == "save_retry" and not game.sim.alive:
                break
            if mode == "boss_death" and not game.sim.alive:
                break
            if mode == "platform" and game.sim.player_pos.y > 1.3 and game.sim.body.on_ground:
                break
            if mode == "denied" and frame >= 10:
                break
            if mode == "dry" and frame >= 10:
                break
            if mode == "reload" and frame >= 5:
                break
            if mode == "forfeit" and frame >= 5:
                break
            if mode == "summon_overlap" and frame >= 5:
                break
            if mode == "pickup" and game.sim.weapon == "surge":
                break
            if (frame + 1) % CHUNK == 0:
                chunks.append(
                    {
                        "frames": [frame + 1 - CHUNK, frame + 1],
                        "mean_step_ms": round(chunk_wall / CHUNK * 1000.0, 4),
                        "max_step_ms": round(chunk_max * 1000.0, 4),
                    }
                )
                chunk_wall = 0.0
                chunk_max = 0.0
        wall_s = time.perf_counter() - started
        final = game.snapshot()
        if png:
            engine.capture(png, report or None)
        payload = {
            "mode": mode,
            "frames": int(ran),
            "seed": int(seed),
            "viewport": [960, 540],
            "wall_s": round(wall_s, 3),
            "mean_step_ms": round(wall_s / max(1, ran) * 1000.0, 4),
            "chunk_max_step_ms": max((c["max_step_ms"] for c in chunks), default=0.0),
            "slow_frames": int(slow_frames),
            "chunks": chunks,
            "events": recorded,
            "hurt_events": hurts,
            "audio_events": audio_log,
            "peak_voices": int(peak_voices),
            "dropped_sfx": int(game.dropped_sfx),
            "wave_events": wave_events,
            "final": final,
            "pickup": {
                "active": bool(getattr(game.sim, "pickup_active", False)),
                "taken": bool(getattr(game.sim, "pickup_taken", False)),
                "surge_t": round(float(getattr(game.sim, "surge_t", 0.0)), 3),
            },
            "summon": {
                "count": len(getattr(game.sim, "summon_positions", [])),
                "blocked": sum(
                    1
                    for p in getattr(game.sim, "summon_positions", [])
                    if game.sim._enemy_blocked_at(
                        p.x, p.z, float(game.sim.enemy_defs["mite"]["radius"])
                    )
                ),
                "positions": [
                    [round(float(p.x), 2), round(float(p.z), 2)]
                    for p in getattr(game.sim, "summon_positions", [])
                ],
                "spawn": summon_snapshot,
            },
            "campaign": {
                "cleared": bool(getattr(game, "campaign_cleared", False)),
                "victory": bool(getattr(game.sim, "victory", False)),
                "banner_t": round(float(getattr(game, "campaign_clear_t", 0.0)), 2),
                "wave": int(game.sim.wave),
                "alive_enemies": [
                    e.etype for e in game.sim.enemies if e.alive
                ],
            },
            "profile": {
                "best_score": int(getattr(game, "profile", {}).get("best_score", 0)),
                "wins": int(getattr(game, "profile", {}).get("wins", 0)),
                "runs": int(getattr(game, "profile", {}).get("runs", 0)),
                "last_run": getattr(game, "last_run", None),
                "disabled": bool(getattr(game, "profile_disabled", False)),
                "save_errors": int(getattr(game, "profile_save_errors", 0)),
                "save_failed": bool(getattr(game, "profile_save_failed", False)),
                "recovered": bool(getattr(game, "profile_recovered", False)),
                "recovered_from_backup": bool(
                    getattr(game, "profile_recovered_from_backup", False)
                ),
                "history": list(getattr(game, "profile", {}).get("history", [])),
            },
            "platform": {
                "landed": bool(game.sim.player_pos.y > 1.3 and game.sim.body.on_ground),
                "x": round(float(game.sim.player_pos.x), 3),
                "y": round(float(game.sim.player_pos.y), 3),
                "z": round(float(game.sim.player_pos.z), 3),
            },
            "switch": {
                "cue": getattr(game, "sound_cue", ""),
                "cue_t": round(float(getattr(game, "sound_cue_t", 0.0)), 3),
                "voices": int(game.mixer.voice_count()),
                "weapon": str(game.sim.weapon),
            },
            "denied": {
                "cue": getattr(game, "sound_cue", ""),
                "cue_t": round(float(getattr(game, "sound_cue_t", 0.0)), 3),
                "voices": int(game.mixer.voice_count()),
                "reserve": int(game.sim.reserve.get("pulse", 0)),
                "overdrive_t": round(float(game.sim.overdrive_t), 3),
            },
            "overdrive": {
                "cue": getattr(game, "sound_cue", ""),
                "t": round(float(game.sim.overdrive_t), 2),
                "voices": int(game.mixer.voice_count()),
                "reserve": int(game.sim.reserve.get("pulse", 0)),
            },
            "clutch": {
                "cue": getattr(game, "sound_cue", ""),
                "count": int(getattr(game.sim, "clutch", 0)),
                "voices": int(game.mixer.voice_count()),
                "wave": int(game.sim.wave),
            },
            "boss_death": {
                "alive": bool(game.sim.alive),
                "boss_alive": any(
                    e.alive and e.etype == "warden" for e in game.sim.enemies
                ),
                "last_run": getattr(game, "last_run", None) is not None,
            },
            "dry": {
                "cue": getattr(game, "sound_cue", ""),
                "voices": int(game.mixer.voice_count()),
                "shots": int(game.sim.shots),
                "ammo": int(game.sim.ammo.get("pulse", 0)),
                "reserve": int(game.sim.reserve.get("pulse", 0)),
            },
            "reload": {
                "cue": getattr(game, "sound_cue", ""),
                "voices": int(game.mixer.voice_count()),
                "ammo": int(game.sim.ammo.get("pulse", 0)),
                "reserve": int(game.sim.reserve.get("pulse", 0)),
                "reload_t": round(float(game.sim.reload_t), 3),
            },
            "hash": stable_hash(final),
        }
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Path(out).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print(
            "play mode=%s frames=%d wave=%d kills=%d score=%d hp=%d alive=%s "
            "hurts=%d audio=%d peak_vox=%d drops=%d shots=%d hits=%d mean_step_ms=%.4f hash=%s"
            % (
                mode, ran, final["wave"], final["kills"], final["score"],
                final["player"]["hp"], final["player"]["alive"], len(hurts),
                len(audio_log), peak_voices, int(game.dropped_sfx),
                final["shots"], final["hits"], payload["mean_step_ms"], payload["hash"],
            )
        )
        return payload
    finally:
        engine.close()


if __name__ == "__main__":
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    _mode = args[0] if len(args) > 0 else "kite"
    _frames = int(args[1]) if len(args) > 1 else 600
    _out = args[2] if len(args) > 2 else ""
    _png = args[3] if len(args) > 3 else ""
    _report = args[4] if len(args) > 4 else ""
    _seed = 1
    for flag in flags:
        if flag.startswith("--seed="):
            _seed = int(flag.split("=", 1)[1])
    main(_mode, _frames, _seed, _out, _png, _report)
