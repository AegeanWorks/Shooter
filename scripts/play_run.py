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
  pickup   walk the clear side lane into the live surge pickup (ends on pickup)
  death    staged near-death run (profile/debrief proof; ends on death)
  platform run at the rear low platform, jump onto it, stop on the top
  denied   press overdrive with no pulse reserve (audio/caption drill)

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
    if mode == "denied":
        return ActionState(pressed=frozenset({"overdrive"})) if frame == 0 else ActionState()
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
    try:
        game = ShooterGame(profile_path=profile_path)
    except TypeError:  # older checkout without profile support
        game = ShooterGame()
    engine = Engine(game, 960, 540, visible=False, msaa=0, ui=True)
    try:
        if seed != 1:
            game.sim.reseed(seed)
        if mode in ("ambush", "boss", "slam", "death", "platform", "denied"):
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
        if mode == "death":
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
        if mode == "platform":
            sim = game.sim
            sim.player_pos = Vec3(-16.0, 0.9002, 9.5)
            sim.body = sim.body.__class__(
                position=Vec3(-16.0, 0.9002, 9.5), half_extents=sim.body.half_extents,
                velocity=Vec3(), on_ground=True,
            )
            sim.yaw = math.pi
            sim.pitch = 0.0
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

        def step(dt, actions):
            events = original_step(dt, actions)
            current = int(game.sim.tick)
            nonempty = [e for e in events if e]
            if nonempty:
                recorded.append({"frame": int(current), "events": nonempty})
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
            if mode == "platform" and game.sim.player_pos.y > 1.3 and game.sim.body.on_ground:
                break
            if mode == "denied" and frame >= 10:
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
            "profile": {
                "best_score": int(getattr(game, "profile", {}).get("best_score", 0)),
                "runs": int(getattr(game, "profile", {}).get("runs", 0)),
                "last_run": getattr(game, "last_run", None),
                "disabled": bool(getattr(game, "profile_disabled", False)),
                "save_errors": int(getattr(game, "profile_save_errors", 0)),
            },
            "platform": {
                "landed": bool(game.sim.player_pos.y > 1.3 and game.sim.body.on_ground),
                "x": round(float(game.sim.player_pos.x), 3),
                "y": round(float(game.sim.player_pos.y), 3),
                "z": round(float(game.sim.player_pos.z), 3),
            },
            "denied": {
                "cue": getattr(game, "sound_cue", ""),
                "cue_t": round(float(getattr(game, "sound_cue_t", 0.0)), 3),
                "voices": int(game.mixer.voice_count()),
                "reserve": int(game.sim.reserve.get("pulse", 0)),
                "overdrive_t": round(float(game.sim.overdrive_t), 3),
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
