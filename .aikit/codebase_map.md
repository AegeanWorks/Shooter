# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document catalogues Python modules, classes, and exported functions. See Map Coverage for any stack it does not index.

---

## 📊 Codebase Metrics
- **Total Python Modules**: `201`
- **Total Classes**: `99`
- **Total Top-Level Functions**: `1176`
- **Total Class Methods**: `247`
- **Total Source Lines**: `26770`

## 🧭 Map Coverage
- **Indexed**: python (`201` module(s))
- **Not indexed by this map**: none (no non-Python source files were found)

---

## 📦 Modules & Exported Symbols

### [`play.py`](play.py)
> *One-click shooter launcher.*

**Size**: `88` lines

**Functions:**
- `def build_argv(extra)` - *Return the Keystone argv, defaulting ``--game`` to the shooter.*
- `def ensure_paths()`
- `def check_prerequisites()`
- `def main(argv)`

---

### [`scripts/audio_probe.py`](scripts/audio_probe.py)
> *Audio-cue evidence: render the new voices to WAV + a spectrogram PNG.*

**Size**: `162` lines

**Functions:**
- `def _join(clips, gap)`
- `def _spectrogram(clip, path, marks)`
- `def main(out_dir)`

---

### [`scripts/capture.py`](scripts/capture.py)
> *Seeded capture driver: step ShooterGame with a bot script, then headless Engine capture.*

**Size**: `2716` lines

**Functions:**
- `def _new_game()` - *Evidence runs use a throwaway profile, never the player's save.*
- `def _capture_stepped(game, out_png, out_json, w, h)` - *Capture the already-stepped game without resetting it.*
- `def _capture(game, out_png, out_json, w, h)`
- `def _engine_with(game, w, h)`
- `def _tune(engine, shadows, srgb, post, bloom)` - *Apply renderer toggles to an already-built Engine scene (before stepping).*
- `def _profiler(engine)`
- `def route_spawn(prefix, shadows, srgb, post, bloom)`
- `def route_combat(prefix, frames, shadows, srgb, post, bloom)`
- `def route_fireburst(prefix, shadows, srgb, post, bloom)` - *Aimed burst at a static target: guarantees visible tracer + flash + hitmark.*
- `def route_viewmodel_bob(prefix, shadows, srgb, post, bloom)` - *Twelve sprint frames: the moving viewmodel-sway pair.*
- `def route_recoil(prefix, shadows, srgb, post, bloom)` - *One scatter shot frame: the viewmodel recoil pair.*
- `def route_summon_overlap(prefix, shadows, srgb, post, bloom)` - *Forced warden summon at centre: the boss/escort overlap pair.*
- `def route_summon_cover(prefix, shadows, srgb, post, bloom)` - *Forced warden summon next to the centre cover: the summon-placement pair.*
- `def route_overdrive_kill(prefix, shadows, srgb, post, bloom)` - *Forced overdrive kill: the reward-cue pair.*
- `def route_overdrive_glow(prefix, shadows, srgb, post, bloom)` - *Three seconds of overdrive left: the held-gun state pair.*
- `def route_pickup_pop(prefix, shadows, srgb, post, bloom)` - *Six frames after the surge pickup is taken: the orb-pop pair.*
- `def route_pickup(prefix, shadows, srgb, post, bloom)`
- `def route_boss(prefix, with_boss, shadows, srgb, post, bloom)` - *Fixed wave-3 roster at one frame; same staging on every build.*
- `def route_hurt(prefix, side, shadows, srgb, post, bloom)` - *First-hit frame with the attacker just outside the centre view.*
- `def route_pickup_spawn(prefix, shadows, srgb, post, bloom)` - *Wave-2 pickup active, clean arena, player staged back at spawn.*
- `def route_slam(prefix, shadows, srgb, post, bloom)` - *Close-range warden windup + slam frames; the audio-caption proof pair.*
- `def route_reload_dip(prefix, shadows, srgb, post, bloom)` - *Mid-reload frame with the viewmodel dipped: the reload-dip pair.*
- `def route_reload(prefix, shadows, srgb, post, bloom)` - *Frame where the reload tail completes; the reload-cue pair.*
- `def route_reticle(prefix, shadows, srgb, post, bloom)` - *One clean frame per weapon: the hip-fire reticle-spread pair.*
- `def route_platform_pulse(prefix, shadows, srgb, post, bloom)` - *Approach view at a pulse peak: the launch-pad pulse pair.*
- `def route_cover_texture(prefix, shadows, srgb, post, bloom)` - *Spawn view of the near covers: the cover-panel pair.*
- `def route_boss_pickup(prefix, shadows, srgb, post, bloom)` - *Live warden + active pickup, player facing away: the boss-pickup pair.*
- `def route_target_hp(prefix, shadows, srgb, post, bloom)` - *A damaged mite under the crosshair: the target-health pair.*
- `def route_score_pop(prefix, shadows, srgb, post, bloom)` - *Two frames after the first kill: the bounty-pop pair.*
- `def route_brute_gap(prefix, shadows, srgb, post, bloom)` - *Idle frame where a 2.7 m brute either stalls or slams: the gap pair.*
- `def route_warden_charge(prefix, shadows, srgb, post, bloom)` - *Warden core at the keystone state-machine charge peak.*
- `def route_brute_windup(prefix, shadows, srgb, post, bloom)` - *First brute tell at close range: windup swell + BRUTE WINDUP caption.*
- `def route_enemy_spacing(prefix, shadows, srgb, post, bloom)` - *Four mites staged on one point: the crowd-spacing pair.*
- `def route_brute_slam(prefix, shadows, srgb, post, bloom)` - *First brute hit at close range: the brute-slam cue pair.*
- `def route_death_fx(prefix, shadows, srgb, post, bloom)` - *Two frames after a kill: the shrinking death-silhouette pair.*
- `def route_streak_bonus(prefix, shadows, srgb, post, bloom)` - *Streak 7 at wave 3: the bonus-percentage pair.*
- `def route_platform_base(prefix, shadows, srgb, post, bloom)` - *Farther approach to the platform: the base/top frame pair.*
- `def route_platform_rim(prefix, shadows, srgb, post, bloom)` - *Approach view of the jump platform: the lit-rim pair.*
- `def route_summon_mark(prefix, shadows, srgb, post, bloom)` - *One warden summon at center: the escort-origin marker pair.*
- `def route_wisp_bolt(prefix, shadows, srgb, post, bloom)` - *First wisp hit from the right: the enemy-bolt pair.*
- `def route_spawn_cue(prefix, shadows, srgb, post, bloom)` - *A staged wave spawn at the pickup line: the spawn-voice pair.*
- `def route_wall_depth(prefix, shadows, srgb, post, bloom)` - *Spawn view of the north wall: the pilaster/depth pair.*
- `def route_wall_texture(prefix, shadows, srgb, post, bloom)` - *Spawn view of the north wall: the wall-panel pair.*
- `def route_pickup_arrow(prefix, shadows, srgb, post, bloom)` - *Pickup active behind the player at spawn: the edge-tag pair.*
- `def route_slam_ring(prefix, shadows, srgb, post, bloom)` - *Staged warden windup with the player outside the slam: the ring pair.*
- `def route_killmark(prefix, shadows, srgb, post, bloom)` - *First-kill frame after the flash clears: the kill-marker pair.*
- `def route_switch_cue(prefix, shadows, srgb, post, bloom)` - *One clean frame after pressing slot 2: the weapon-switch cue pair.*
- `def route_surge_forfeit(prefix, shadows, srgb, post, bloom)` - *One frame after switching away from surge: the forfeit-cue pair.*
- `def route_save_retry(prefix, shadows, srgb, post, bloom)` - *Failed wave save, then a successful death save: the stale-warning pair.*
- `def route_profile_backup(prefix, shadows, srgb, post, bloom)` - *Restart with a missing main and valid .bak: the recovery pair.*
- `def route_profile_reset(prefix, shadows, srgb, post, bloom)` - *Death debrief after an unrecoverable corrupt profile: the reset pair.*
- `def route_profile_disabled(prefix, shadows, srgb, post, bloom)` - *Death debrief with an unsupported schema: the disabled-profile pair.*
- `def route_save_error(prefix, shadows, srgb, post, bloom)` - *Death debrief with the profile write locked: the save-error pair.*
- `def route_tracer_tint(prefix, shadows, srgb, post, bloom)` - *One first-shot frame per weapon: the tracer/flash tint pair.*
- `def route_score_center(prefix, shadows, srgb, post, bloom)` - *High-score HUD with every top-center status line live: centering pair.*
- `def route_spawn_mark(prefix, shadows, srgb, post, bloom)` - *A staged wave spawn at the pickup line: the spawn-marker pair.*
- `def route_highground(prefix, shadows, srgb, post, bloom)` - *Player on the low platform edge with a mite at its base.*
- `def route_boss_hp(prefix, shadows, srgb, post, bloom)` - *Half-health warden bar: the numeric-HP HUD pair.*
- `def route_los(prefix, shadows, srgb, post, bloom)` - *Brute adjacent to a thin cover with the player on the other side.*
- `def route_dry(prefix, shadows, srgb, post, bloom)` - *Fire with no magazine and no reserve: the dry-fire cue pair.*
- `def route_denied(prefix, shadows, srgb, post, bloom)` - *Overdrive pressed with no pulse reserve: the denial cue pair.*
- `def route_cache_drop_cue(prefix, shadows, srgb, post, bloom)` - *Forced cache drop frame: the drop-cue pair.*
- `def route_cache_visual(prefix, shadows, srgb, post, bloom)` - *One live ammo cache ahead of spawn: the cache-visibility pair.*
- `def route_critical(prefix, shadows, srgb, post, bloom)` - *Forced critical kill frame: the critical-cue pair.*
- `def route_muzzle(prefix, shadows, srgb, post, bloom)` - *Exact first-shot frame: the muzzle-flash occlusion pair.*
- `def route_killfeed(prefix, shadows, srgb, post, bloom)` - *First-kill frame after the flash clears: the kill-feed pair.*
- `def route_pad_lifecycle(prefix, shadows, srgb, post, bloom)` - *Launch pad at the pulse peak: hardcoded sine vs lifecycle component.*
- `def route_platform(prefix, shadows, srgb, post, bloom)` - *Spawn view turned toward the rear low platform (before/after pair).*
- `def route_cover(prefix, shadows, srgb, post, bloom)` - *A mite walks from behind the centre cover toward the spawn eye.*
- `def route_flinch(prefix, shadows, srgb, post, bloom)` - *Exact first-hit frame on a live mite: the combat hit-reaction pair.*
- `def route_hud_ammo(prefix, shadows, srgb, post, bloom)` - *Low-magazine and mid-reload HUD frames on a clean arena.*
- `def route_campaign_seal(prefix, shadows, srgb, post, bloom)` - *Three seconds after the campaign clear: the wave-4 seal pair.*
- `def route_lowhp_pulse(prefix, shadows, srgb, post, bloom)` - *A 30 HP frame at the pulse peak: the low-health edge pair.*
- `def route_tracer_muzzle(prefix, shadows, srgb, post, bloom)` - *One clean shot at the north wall: the tracer-origin pair.*
- `def route_boss_dead(prefix, shadows, srgb, post, bloom)` - *Death frame with a live warden: the boss-bar death pair.*
- `def route_west_gap(prefix, shadows, srgb, post, bloom)` - *Approach along the west wall: the platform-gap pair.*
- `def route_warden_cover(prefix, shadows, srgb, post, bloom)` - *One slam frame with the north cover between: the warden-LOS pair.*
- `def route_clutch(prefix, shadows, srgb, post, bloom)` - *A wave clear at 30 HP: the clutch-cue pair.*
- `def route_campaign_complete(prefix, shadows, srgb, post, bloom)` - *Five seconds after the clear, banner gone: the completion-line pair.*
- `def route_win(prefix, shadows, srgb, post, bloom)` - *Kill the wave-3 warden and capture the wave-4 clear frame.*
- `def route_death_profile(prefix, shadows, srgb, post, bloom, win_history, wide_history, full_history)` - *Staged run-over frame with a seeded best, against the no-profile build.*
- `def route_win_history(prefix, shadows, srgb, post, bloom)` - *Debrief with a seeded win + loss: the outcome-marker pair.*
- `def route_debrief_width(prefix, shadows, srgb, post, bloom)` - *Debrief with six-digit recent scores: the panel-width pair.*
- `def route_history5(prefix, shadows, srgb, post, bloom)` - *Debrief with four prior runs plus the current one: the full-history pair.*
- `def route_death(prefix, shadows, srgb, post, bloom)`
- `def main(which, prefix, shadows, srgb, post, bloom)`

---

### [`scripts/keystone_manifest_asset_repro.py`](scripts/keystone_manifest_asset_repro.py)
> *Minimal upstream reproducer: manifest assets fail project validation.*

**Size**: `76` lines

**Functions:**
- `def main()`

---

### [`scripts/play_run.py`](scripts/play_run.py)
> *Played-run evidence harness: drive the shipped game through the Engine loop.*

**Size**: `739` lines

**Functions:**
- `def _stage_ambush(game, frame)` - *Alternate a fresh side attacker every 90 frames (player stands still).*
- `def _action(mode, game, frame, strafe)`
- `def main(mode, frames, seed, out, png, report)`

---

### [`scripts/record_bot.py`](scripts/record_bot.py)
> *Emit a CommandLog for --replay determinism audits.*

**Size**: `28` lines

**Functions:**
- `def main(out, frames)`

---

### [`scripts/route_evidence.py`](scripts/route_evidence.py)
> *Deterministic capture proofs for the shooter via keystone.evidence.*

**Size**: `81` lines

**Functions:**
- `def build_route(frames, checkpoints)` - *The shipped idle-spawn route: three named frames, no staging callback.*
- `def diff_summaries(before_path, after)` - *Compare a written baseline route summary with a freshly captured one.*
- `def run_route(out, frames)` - *Capture the route headlessly and write its summary atomically.*
- `def main(argv)`

---

### [`scripts/soak.py`](scripts/soak.py)
> *Full-length sustain soak: feedback bot, chunk timings, peak budget samples.*

**Size**: `177` lines

**Functions:**
- `def _peak24_budget()` - *Synthetic max-load budget: 24 pooled enemies + full tracer ring, one sync.*
- `def main(frames, out_log, out_report)`

---

### [`shooter/__init__.py`](shooter/__init__.py)
> *Boltshooter plug-in package.*

**Size**: `5` lines

---

### [`shooter/anim.py`](shooter/anim.py)
> *Enemy presentation animation: file-backed .kanim idle clips.*

**Size**: `57` lines

**Classes:**
- `class EnemyAnimations` - *One deterministic idle controller per enemy node slot.*
  - Method `.__init__(directory)`
  - Method `._controller(slot, name)`
  - Method `.offset(slot, etype, dt)` - *Advance one slot's idle clip and return its sampled Transform.*

---

### [`shooter/asset_pipeline.py`](shooter/asset_pipeline.py)
> *File-backed gameplay assets registered through Keystone's asset pipeline.*

**Size**: `29` lines

**Functions:**
- `def register_cache_crate(assets, directory, fallback)` - *Register the cache crate from disk, or the fallback mesh when absent.*

---

### [`shooter/bot.py`](shooter/bot.py)
> *Headless bot scripts: move, shoot, kill. No window, deterministic.*

**Size**: `134` lines

**Functions:**
- `def idle(n)`
- `def move_forward(n, sprint)`
- `def look_spin(n, yaw_per_frame)`
- `def fire_hold(n)` - *Hold fire (keyboard path) so auto weapons keep firing headless.*
- `def fire_clicks(n)`
- `def assault(n_move, n_fire)` - *Walk forward then hold fire: movement + determinism proof (see ADR-006).*
- `def _ammo_total(sim, wid)`
- `def _face(sim, tx, tz, turn)`
- `def kite_step(sim)` - *One feedback tick: face the nearest live enemy, hold 6-12 m, fire when aimed.*
- `def strafe_fire(n)`
- `def overdrive_step(sim)` - *Measurement policy: kite + voluntary overdrive when it is a real choice.*

---

### [`shooter/game.py`](shooter/game.py)
> *Boltshooter: Keystone plug-in shooter. Engine owns loop/render/input.*

**Size**: `2342` lines

**Classes:**
- `class PadPulseComponent` - *Keystone lifecycle component: pulse the launch pad deterministically.*
  - Method `.update(context)`
- `class ShooterGame`
  - Method `.__init__(profile_path)`
  - Method `._clear_shake_reports()` - *One reset for trauma and both camera-shake reports.*
  - Method `._reset_presentation_reports()` - *Clear every presentation report when a new scene is built.*
  - Method `.build_scene()`
  - Method `.set_clip_hook(hook)` - *Attach an optional (clip, gain) observer for evidence tooling.*
  - Method `.reload_assets()` - *Re-read changed file-backed assets and rebind scene nodes; expose report.*
  - Method `._start_death_camera()` - *Build the death cinematic around where the run ended.*
  - Method `._start_campaign_clear_camera()` - *Play the authored victory fly-around from a shipped .kpath document.*
  - Method `._play_clip(clip, gain)` - *Play one SFX clip, counting (never hiding) a mixer refusal.*
  - Method `._presentation_gain(gain)` - *Bounded per-event gain variation from the presentation-only stream.*
  - Method `.presentation_rng_report()` - *JSON-safe state of the presentation stream for reproducible AI runs.*
  - Method `._run_ended()` - *True when the current run is over: the player is down or the campaign sealed.*
  - Method `._restart_ready()` - *True when Enter should start a new run.*
  - Method `.new_run()` - *Start a fresh run after a death or a sealed campaign.*
  - Method `.update(dt, actions)`
  - Method `._cue(text, danger)`
  - Method `._save_profile()`
  - Method `._record_campaign_clear()`
  - Method `._campaign_win_reached()` - *True when this frame seals the campaign.*
  - Method `._record_progress()` - *Persist a new best at wave clear, even if the player later quits.*
  - Method `._record_run(outcome)` - *Append one finished run (death or campaign clear) to the profile.*
  - Method `._finish_run()`
  - Method `._spawn_mark_cap()` - *The DATA-owned marker cap; MAX_SPAWN_MARKS only when the key is absent.*
  - Method `._play_event(event)` - *Map one sim event to its audio voice and on-screen caption.*
  - Method `._sync_scene(dt)`
  - Method `.crosshair_pick()` - *JSON-safe answer to 'what world node is under the crosshair'.*
  - Method `.asset_digest_report()` - *Stable content digests for the registered render assets.*
  - Method `.testbed_report()` - *One JSON-safe view of every no-argument on-demand report.*
  - Method `.engine_version_report()` - *The authoritative Keystone version, as a JSON-safe AI/soak query.*
  - Method `.profile_store_probe()` - *Exercise the shipped profile contract in a throwaway directory.*
  - Method `.nav_authoring_report(clearance)` - *NavGrid authored from the same collider authority as the route plan.*
  - Method `.idle_presenter_preview(frames)` - *Step a local root-motion rig and report its container pose.*
  - Method `.bot_nav_preview(frames)` - *Plan spawn -> pickup with a local NavAgent and advance it in isolation.*
  - Method `.data_error_report(error)` - *JSON-safe view of a structured data failure, on demand.*
  - Method `.keystone_contract_report()` - *The Keystone contract versions this build is running against.*
  - Method `.enemy_steering_report()` - *AI-visible steering vectors for the first alive enemy, on demand.*
  - Method `.enemy_state_preview(threat, frames)` - *Parameter-driven enemy animation states, as a JSON preview.*
  - Method `.idle_root_motion_report(window)` - *Subject root deltas of the shipped idle clips, as a JSON report.*
  - Method `.enemy_blend_report(parameter, time)` - *Shipped enemy idle clips as a 1D blend space keyed by enemy HP.*
  - Method `.arena_tile_report()` - *The shipped arena as a Keystone TileMap document, on demand.*
  - Method `._arena_layout()` - *The one grid layout shared by every arena-shaped report.*
  - Method `._to_cell(x, z)` - *Clamp a world XZ point to the shared arena grid cell.*
  - Method `._nav_grid(clearance)` - *The authoritative arena nav grid, rasterized from collision boxes.*
  - Method `.nav_plan_report()` - *Arena route from spawn to the surge pickup as Keystone nav data.*
  - Method `.snapshot()`
  - Method `.bind_input(mapping)` - *Bind every live button the actions() contract advertises.*
  - Method `.actions()`
  - Method `.status()`
  - Method `.draw_ui(canvas, state)`

**Functions:**
- `def _pose_json(pose)` - *One JSON-safe, six-decimal view of a sampled pose for AI reports.*
- `def _number(value, label, fallback, *, minimum)` - *Read one finite tuning number at or above ``minimum``, or fall back.*
- `def _lens(value, label, fallback)` - *Read one finite field of view strictly between 0 and 180 degrees.*
- `def _death_cinematic_tuning(juice)` - *Read the death-cinematic block from juice.json, falling back per field.*
- `def _floor_grid_texture(size, cell)` - *Deterministic dark floor with brighter 2-px grid lines (no image file).*
- `def _cover_panel_texture(size)` - *Deterministic grayscale panel detail for the arena covers.*
- `def _wall_panel_texture(size)` - *Deterministic grayscale panel detail for the boundary walls.*
- `def _warden_armor_texture(size)` - *Deterministic grayscale armor plates for the campaign boss body.*
- `def _platform_frame_mesh(width, depth, thickness, height, bottom_y)` - *Four thin top-edge strips, plus a matching base frame when requested.*

---

### [`shooter/profile.py`](shooter/profile.py)
> *Versioned, crash-safe run profile: bests, run count and last-run summary.*

**Size**: `202` lines

**Classes:**
- `class ProfileStore` - *One JSON profile with schema checks, quarantine and atomic saves.*
  - Method `.__init__(path)`
  - Method `.default()`
  - Method `.load()`
  - Method `._recover()`
  - Method `._backup_profile()`
  - Method `.save(profile)`
  - Method `._acquire_lock()`

**Functions:**
- `def default_profile()`
- `def _clean_run(value)`
- `def _normalize(raw)`
- `def _migrate_v0(raw)`
- `def _migrate_v1(raw)`
- `def _migrate_v2(raw)`

---

### [`shooter/sim.py`](shooter/sim.py)
> *Deterministic shooter simulation: movement, hitscan weapons, enemies, waves.*

**Size**: `1204` lines

**Classes:**
- `class ShooterDataError` - *A data failure with structured why/fix and the rendered player message.*
  - Method `.__init__(message, why, fix)`
  - Method `.__str__()`
- `class _Enemy`
- `class Sim` - *Owns all deterministic shooter state. Game.py mirrors it into a Scene.*
  - Method `.__init__(seed)`
  - Method `.reseed(seed)`
  - Method `._eng()`
  - Method `.streak_bonus()` - *Current per-kill score bonus: 10% each, capped at 50%.*
  - Method `.overdrive_preview()`
  - Method `._colliders()`
  - Method `.reset()`
  - Method `._build_wave()`
  - Method `.seal_campaign()` - *Stop future wave construction after the campaign is won.*
  - Method `._spawn_enemy(etype)`
  - Method `._summon_mites(boss, count, events)` - *Spawn a bounded escort around the warden; never exceeds max_alive.*
  - Method `._enemy_blocked_at(x, z, radius)`
  - Method `._colliders_along(start, end)` - *Wall/cover boxes whose bounds meet the segment's box, in build order.*
  - Method `._enemy_has_los(enemy)` - *True when no wall/cover intersects enemy chest -> player eye.*
  - Method `._in_melee_reach(enemy)` - *Vertical melee gate: a short enemy cannot bite through a platform.*
  - Method `._move_enemy(enemy, dx, dz)` - *Move with cover collision; slide along a blocked face or tangent.*
  - Method `.eye()`
  - Method `.forward()`
  - Method `.muzzle_position()` - *World point at the viewmodel barrel tip (presentation only).*
  - Method `._enemy_box(e)`
  - Method `.aim_target()` - *Nearest live enemy under the forward crosshair, behind no wall.*
  - Method `.step(dt, actions)`
  - Method `._on_hurt(events, source)`
  - Method `._try_overdrive(events)`
  - Method `._switch(wid, events)`
  - Method `._fire(w, events)`
  - Method `._step_enemies(dt, events)`
  - Method `._separate_enemies()` - *Deterministic soft spacing so melee crowds never stack.*
  - Method `._nudge_enemy(enemy, dx, dz)` - *Move by a spacing nudge unless a cover or the arena edge blocks it.*
  - Method `.snapshot()`

**Functions:**
- `def _data_error(name, headline, why, fix)` - *Build the exact legacy text while keeping the structured fields.*
- `def _load(name)` - *Read one data file, naming the file and the fix when it cannot be used.*

---

### [`shooter/ui.py`](shooter/ui.py)
> *Shooter HUD: crosshair, HP, ammo, score. Presentation-only, never sim.*

**Size**: `212` lines

**Functions:**
- `def _center(canvas, cx, y, text, color, scale)` - *Draw one top-center HUD line centered on the viewport.*
- `def reticle_gap(sim)` - *Crosshair half-gap in px for the equipped weapon's hip-fire cone.*
- `def draw_shooter(canvas, hud, sim)`

---

### [`tests/conftest.py`](tests/conftest.py)
**Size**: `18` lines

**Functions:**
- `def _isolate_default_profile(tmp_path, monkeypatch)` - *Never let the suite read or write the player's real save file.*

---

### [`tests/test_approach_pad.py`](tests/test_approach_pad.py)
> *Levels proof: the jump-platform launch spot is marked on the floor.*

**Size**: `34` lines

**Functions:**
- `def _game()`
- `def test_approach_pad_exists_and_uses_trim()`
- `def test_approach_pad_sits_before_the_platform()`

---

### [`tests/test_audio.py`](tests/test_audio.py)
> *Audio-cue proofs: boss/engagement events own a voice and a caption.*

**Size**: `140` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _close_boss_game()`
- `def test_boss_windup_and_slam_get_audio_and_caption()`
- `def test_pickup_gets_audio_and_caption()`
- `def test_the_shipped_audio_cue_manifest_is_complete()` - *Every voice the event layer can request must exist and be non-empty.*
- `def test_clip_hook_observes_play_without_owning_mixer()`
- `def test_boss_down_event_and_clip()`
- `def test_caption_draws_and_expires()`

---

### [`tests/test_audio_resilience.py`](tests/test_audio_resilience.py)
> *Game proof: an audio refusal is counted, never fatal.*

**Size**: `75` lines

**Functions:**
- `def _game(tmp_path)`
- `def test_a_mixer_refusal_is_counted_and_the_frame_survives(tmp_path, monkeypatch, failure)`
- `def test_the_drop_counter_does_not_touch_the_deterministic_sim(tmp_path, monkeypatch)`
- `def test_a_healthy_mixer_counts_nothing(tmp_path)`
- `def test_the_counter_appears_in_the_snapshot_for_soak_reports(tmp_path)`

---

### [`tests/test_audit.py`](tests/test_audit.py)
> *Wave-2 audit regression pins: cache pickup, surge forfeit, mixer cap,*

**Size**: `171` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _parked_sim(seed)`
- `def test_overlapping_caches_all_collected_same_frame()`
- `def test_surge_forfeit_relinquishes_ammo()`
- `def test_voice_cap_stays_bounded()`
- `def test_overdrive_step_presses_only_when_ready()`
- `def test_draw_shooter_smoke()`
- `def test_live_input_limits_documented()`
- `def test_dropped_sfx_resets_on_rebuild_and_surfaces_in_snapshot()`
- `def test_surge_pickup_breaks_overdrive()`
- `def test_kite_dodges_when_completely_dry()`

---

### [`tests/test_best_row.py`](tests/test_best_row.py)
> *Progression proof: the debrief shows career bests, not only the run.*

**Size**: `61` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _game(tmp_path, kills, wave, streak)`
- `def test_debrief_shows_career_bests(tmp_path)`
- `def test_debrief_omits_bests_at_zero(tmp_path)`

---

### [`tests/test_boss.py`](tests/test_boss.py)
> *Warden boss proofs: wave-3 placement, telegraph/slam, summons, kill, HUD.*

**Size**: `156` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _load(name)`
- `def _boss_sim(dist)`
- `def test_warden_data_and_wave_three()`
- `def test_warden_windup_then_slam()`
- `def test_warden_summons_mites()`
- `def test_warden_kill_scores()`
- `def test_warden_build_wave_is_queued()`
- `def test_boss_core_follows_warden_and_hides()`
- `def test_hud_draws_warden_health_bar()`

---

### [`tests/test_boss_anim_state.py`](tests/test_boss_anim_state.py)
> *Keystone testbed proof: the warden core is driven by a .kstate machine.*

**Size**: `124` lines

**Functions:**
- `def _library()`
- `def test_warden_core_machine_loads_from_the_library()`
- `def test_the_windup_transition_contract_stays_inside_its_bands()`
- `def test_core_clips_target_the_scene_node()`
- `def test_machine_breathes_calm_then_pulses_charge()`
- `def _game(windup_s)`
- `def test_game_core_pulses_with_the_keystone_machine()`
- `def test_core_is_hidden_without_a_warden()`

---

### [`tests/test_boss_dead_ui.py`](tests/test_boss_dead_ui.py)
> *UI proof: the warden bar yields to the death screen.*

**Size**: `61` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _game(dead)`
- `def _labels(g)`
- `def test_warden_bar_hides_when_the_player_dies()`
- `def test_warden_bar_still_shows_in_a_live_fight()`

---

### [`tests/test_boss_death_fx.py`](tests/test_boss_death_fx.py)
> *Effects proof: the warden dies as an ember collapse, not a white block.*

**Size**: `53` lines

**Functions:**
- `def _game()`
- `def test_warden_death_uses_ember_material_and_a_scale_cap()`
- `def test_small_enemy_death_keeps_the_white_shrink()`
- `def test_boss_death_material_is_warm()`

---

### [`tests/test_boss_hp.py`](tests/test_boss_hp.py)
> *UI readability proofs: the warden bar has a numeric HP readout.*

**Size**: `46` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def test_warden_bar_shows_numeric_hp()`
- `def test_warden_bar_numbers_update()`

---

### [`tests/test_brute_gap.py`](tests/test_brute_gap.py)
> *Enemy proof: a brute must close its 2.5-3.0 m no-man's-land.*

**Size**: `38` lines

**Functions:**
- `def _sim()`
- `def test_brute_closes_the_three_meter_dead_zone()`

---

### [`tests/test_brute_slam.py`](tests/test_brute_slam.py)
> *Audio proof: the brute's 20-damage slam gets its own cue.*

**Size**: `50` lines

**Functions:**
- `def _sim()`
- `def test_brute_slam_emits_its_own_event()`
- `def test_brute_slam_gets_a_voice_and_caption()`

---

### [`tests/test_brute_windup.py`](tests/test_brute_windup.py)
> *Combat-feel proof: the brute slam has a readable windup.*

**Size**: `50` lines

**Functions:**
- `def _sim()`
- `def test_brute_first_frame_is_a_windup_not_a_hit()`
- `def test_brute_windup_still_lands_after_the_delay()`

---

### [`tests/test_cache_asset.py`](tests/test_cache_asset.py)
> *Gameplay proof: the ammo cache is a file-backed OBJ asset.*

**Size**: `95` lines

**Functions:**
- `def test_cache_crate_registers_from_obj_with_faces()`
- `def test_the_shipped_crate_keeps_its_mesh_shape_and_bounds()`
- `def test_missing_obj_falls_back_to_the_old_cube(tmp_path)`
- `def test_game_cache_nodes_render_the_file_backed_crate()`
- `def test_reload_assets_reports_unchanged_and_keeps_a_json_safe_report()`
- `def test_reload_assets_rebinds_live_cache_nodes_on_obj_modification(tmp_path)`

---

### [`tests/test_cache_drop_cue.py`](tests/test_cache_drop_cue.py)
> *Audio proof: an ammo cache announces its drop, not just its pickup.*

**Size**: `62` lines

**Functions:**
- `def _kill_game(cache)`
- `def test_cache_drop_plays_a_distinct_cue_and_caption()`
- `def test_standard_kill_does_not_play_the_drop_cue()`
- `def test_drop_voice_differs_from_collection_and_kill()`

---

### [`tests/test_cache_material_library.py`](tests/test_cache_material_library.py)
> *Keystone testbed proof: the ammo-cache material is a .kmaterial.*

**Size**: `49` lines

**Functions:**
- `def test_cache_material_loads_from_library()`
- `def test_cache_material_surface_fields_stay_in_their_bands()`
- `def test_game_registers_the_cache_material()`
- `def test_cache_material_is_deterministic()`

---

### [`tests/test_cache_visual.py`](tests/test_cache_visual.py)
> *Graphics proof: dropped ammo caches are visible in the arena.*

**Size**: `57` lines

**Functions:**
- `def _game()`
- `def test_cache_pool_renders_the_active_drop()`
- `def test_cache_nodes_share_the_glowing_material()`
- `def test_cache_pool_hides_after_collection()`

---

### [`tests/test_campaign_camera_path.py`](tests/test_campaign_camera_path.py)
> *Game proof: the victory cinematic is a shipped .kpath document.*

**Size**: `203` lines

**Classes:**
- `class _RedirectedLibrary` - *Point the game's library at a temporary directory of real files.*
  - Method `.__init__(directory)`

**Functions:**
- `def _sealing_game()` - *A built game whose next update seals the campaign.*
- `def _tick(game, frames)`
- `def test_the_authored_lens_and_height_stay_inside_their_bands()`
- `def test_the_shipped_document_loads_as_a_one_shot_path()`
- `def test_sealing_the_campaign_starts_the_document_camera()`
- `def test_the_camera_follows_the_document_pose()`
- `def test_the_victory_camera_clamps_and_leaves_the_record_alone()`
- `def _victory_game_over(directory, monkeypatch)` - *A game whose campaign_clear.kpath is read from a temp directory.*
- `def test_a_really_corrupt_document_degrades_to_first_person(tmp_path, monkeypatch, raw)` - *A hand-broken .kpath must never crash the victory screen.*
- `def test_a_completely_missing_library_directory_also_degrades(tmp_path, monkeypatch)`
- `def test_a_missing_document_falls_back_to_first_person(monkeypatch)`
- `def test_rebuilding_clears_the_victory_camera()`

---

### [`tests/test_campaign_complete.py`](tests/test_campaign_complete.py)
> *UI proof: a sealed campaign stays visibly complete after the banner.*

**Size**: `60` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _labels(g)`
- `def _won_game()`
- `def test_campaign_complete_persists_after_the_banner()`
- `def test_banner_still_owns_the_screen_while_it_lasts()`
- `def test_campaign_complete_is_absent_before_the_win()`

---

### [`tests/test_campaign_seal.py`](tests/test_campaign_seal.py)
> *Level proof: a cleared campaign does not start wave 4 combat.*

**Size**: `47` lines

**Functions:**
- `def _win_game()`
- `def test_campaign_clear_seals_future_waves()`

---

### [`tests/test_career_debrief.py`](tests/test_career_debrief.py)
> *Progression proof: the death debrief shows career runs and wins.*

**Size**: `55` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _game(tmp_path, runs, wins)`
- `def test_debrief_shows_career_runs_and_wins(tmp_path)`
- `def test_debrief_omits_career_row_without_runs(tmp_path)`

---

### [`tests/test_clutch_cue.py`](tests/test_clutch_cue.py)
> *Audio proof: a low-health wave clear announces CLUTCH CLEAR.*

**Size**: `46` lines

**Functions:**
- `def _clear(hp)`
- `def test_low_health_clear_plays_the_clutch_cue()`
- `def test_normal_clear_keeps_the_wave_cue()`
- `def test_clutch_voice_differs_from_the_wave_voice()`

---

### [`tests/test_combat_feel.py`](tests/test_combat_feel.py)
> *Combat-feel proofs: non-lethal hits visibly flinch the enemy.*

**Size**: `58` lines

**Functions:**
- `def _hit_sim(hp)`
- `def test_nonlethal_hit_sets_flinch_timer()`
- `def test_flinch_expires_without_changing_damage()`
- `def test_sync_scene_squashes_and_pushes_flinching_enemy()`

---

### [`tests/test_core_material_graph.py`](tests/test_core_material_graph.py)
> *Keystone testbed proof: the boss core material is a material graph.*

**Size**: `61` lines

**Functions:**
- `def _graph()`
- `def test_core_graph_evaluates_to_a_checker_material()`
- `def test_core_material_fields_stay_inside_their_design_bands()` - *The shipped graph's colour and surface fields are designer-owned DATA.*
- `def test_core_graph_is_deterministic()`
- `def test_game_registers_the_graph_material()`

---

### [`tests/test_cover_texture.py`](tests/test_cover_texture.py)
> *Graphics proof: arena covers have a deterministic panel texture.*

**Size**: `31` lines

**Functions:**
- `def test_cover_material_has_a_panel_texture()`
- `def test_cover_texture_is_deterministic()`

---

### [`tests/test_critical_cue.py`](tests/test_critical_cue.py)
> *Audio proof: a critical kill gets its own reward cue.*

**Size**: `60` lines

**Functions:**
- `def _kill_game(critical)`
- `def test_critical_kill_plays_a_distinct_cue()`
- `def test_standard_kill_keeps_the_plain_kill_cue()`
- `def test_critical_voice_differs_from_the_kill_voice()`

---

### [`tests/test_critical_killfeed.py`](tests/test_critical_killfeed.py)
> *UI proof: critical kills stay marked in the persistent kill feed.*

**Size**: `72` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _kill_game(critical)`
- `def test_critical_kill_is_tagged_and_accented_in_the_feed()`
- `def test_normal_kill_keeps_the_plain_feed_entry()`

---

### [`tests/test_cross_process_determinism.py`](tests/test_cross_process_determinism.py)
> *Determinism proof across processes, which the in-process gate cannot give.*

**Size**: `114` lines

**Functions:**
- `def _run_hash(hashseed)`
- `def test_the_same_run_hashes_identically_across_processes_and_hash_seeds()` - *A replay recorded in one session must reproduce in the next.*
- `def test_a_fixed_seed_attribute_is_reproducible_across_processes()` - *The seed passed to the game, not the interpreter's, drives the outcome.*
- `def _report_hash(hashseed)` - *Hash the aggregate testbed report in a fresh interpreter.*
- `def test_the_testbed_report_is_stable_across_processes_and_hash_seeds()` - *AI/soak evidence must not depend on string-hash iteration order.*
- `def test_the_replay_transcript_reproduces_its_outcome_in_a_fresh_process()` - *bot_campaign.json was recorded earlier; it must still win today.*

---

### [`tests/test_data_defaults.py`](tests/test_data_defaults.py)
> *Fallback defaults must match the shipped DATA: deleting a key changes nothing.*

**Size**: `49` lines

**Functions:**
- `def _observables()`
- `def test_deleting_a_tuned_key_changes_no_observable_behaviour(tmp_path, monkeypatch)`

---

### [`tests/test_data_integrity.py`](tests/test_data_integrity.py)
> *Startup proof: broken gameplay data names the file, not the game factory.*

**Size**: `183` lines

**Functions:**
- `def data_dir(tmp_path, monkeypatch)` - *A throwaway copy of the shipped data so a test can break one file.*
- `def test_a_missing_required_file_names_the_file_and_the_fix(data_dir)`
- `def test_a_corrupt_file_names_the_json_error(data_dir)`
- `def test_every_required_file_is_reported_by_name(data_dir)`
- `def test_a_missing_optional_file_still_falls_back_silently(data_dir)` - *engagement.json is optional: its absence must not stop the game.*
- `def test_a_healthy_data_dir_loads_without_incident(data_dir)`
- `def test_the_message_is_actionable_not_a_traceback(data_dir)`
- `def test_a_wrongly_shaped_file_names_the_file_and_the_shape(data_dir, filename, payload, expected)` - *Valid JSON with the wrong shape used to escape as a bare KeyError/TypeError.*
- `def test_the_shipped_weapon_and_enemy_rosters_are_exact()`
- `def test_wave_spawn_keys_and_wave_indices_match_the_shipped_roster()` - *A typo in levels.json waves must name itself, not silently spawn nothing.*
- `def test_authored_positions_and_covers_stay_inside_the_arena()` - *An entity edited outside the 40x40 arena would be unreachable, not crashing.*
- `def test_spawn_capacity_covers_waves_and_pickup_precedes_victory()` - *A cap below wave demand strands enemies; a late pickup is unusable.*
- `def test_a_healthy_document_passes_every_shape_check(data_dir)`

---

### [`tests/test_data_tuning_bands.py`](tests/test_data_tuning_bands.py)
> *Survivors of the engagement/levels mutation sweep, pinned by behaviour.*

**Size**: `56` lines

**Functions:**
- `def test_a_cache_drop_expires_on_the_shipped_time_window()`
- `def test_overdrive_lasts_the_shipped_duration()`
- `def test_the_alive_enemy_cap_is_enforced_during_a_long_wave()`

---

### [`tests/test_death_camera_path.py`](tests/test_death_camera_path.py)
> *Game proof: the death cinematic drives the camera through a keystone path.*

**Size**: `300` lines

**Functions:**
- `def _dying_game()` - *A built game whose next tick reports a real death event.*
- `def _tick(game, frames)`
- `def test_death_starts_a_camera_path_and_reports_it()`
- `def test_the_camera_follows_the_pose_not_the_eye()`
- `def test_the_path_is_one_shot_and_clamps_on_its_final_pose()`
- `def test_the_orbit_widens_and_stays_above_the_ground()`
- `def test_two_deaths_produce_the_same_camera_trajectory()`
- `def test_the_cinematic_does_not_touch_the_snapshot_or_the_hash()`
- `def test_build_scene_clears_the_cinematic()`
- `def test_defaults_are_used_when_the_block_is_missing_or_wrong()`
- `def test_bad_fields_fall_back_individually_not_wholesale()`
- `def test_out_of_range_lenses_fall_back_to_the_authored_default()`
- `def test_a_valid_override_is_honoured()`
- `def test_a_key_with_no_height_of_either_kind_gets_the_default_height()`
- `def test_values_that_would_raise_inside_the_builder_fall_back()`
- `def test_a_malformed_tuning_block_still_produces_a_playable_cinematic()`

---

### [`tests/test_death_fx.py`](tests/test_death_fx.py)
> *Graphics proof: a kill leaves a brief shrinking death silhouette.*

**Size**: `53` lines

**Functions:**
- `def _kill_sim()`
- `def test_kill_sets_death_timer()`
- `def test_death_timer_expires()`
- `def test_scene_shows_a_shrinking_death()`

---

### [`tests/test_debrief_width.py`](tests/test_debrief_width.py)
> *UI readability proof: the death debrief panel fits wide RECENT lines.*

**Size**: `79` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _game(tmp_path, scores)`
- `def _panel_and_recent(canvas)`
- `def test_wide_recent_fits_the_panel(tmp_path)`
- `def test_normal_recent_keeps_the_standard_panel(tmp_path)`

---

### [`tests/test_denial.py`](tests/test_denial.py)
> *Audio/UI proofs: a denied overdrive explains itself.*

**Size**: `41` lines

**Functions:**
- `def _denied_game()`
- `def test_denied_overdrive_gets_voice_and_caption()`
- `def test_denied_overdrive_does_not_change_gameplay_state()`

---

### [`tests/test_dry_fire.py`](tests/test_dry_fire.py)
> *Combat-feel proofs: firing a completely dry gun gives feedback.*

**Size**: `81` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _dry_sim()`
- `def test_dry_fire_is_rate_limited()`
- `def test_dry_fire_gets_audio_and_caption()`
- `def test_dry_fire_does_not_change_shots_or_score()`

---

### [`tests/test_enemy_animation.py`](tests/test_enemy_animation.py)
> *Gameplay proof: enemies animate from Keystone .kanim clips.*

**Size**: `93` lines

**Functions:**
- `def _game()`
- `def test_library_loads_every_enemy_idle_clip()`
- `def test_idle_sampling_is_deterministic_and_uniform()`
- `def test_shipped_idle_clips_stay_inside_their_presentation_bands()` - *A mistyped keyframe must fail a test, not silently change enemy feel.*
- `def test_sync_scene_rotates_a_live_enemy_without_moving_it()`
- `def test_idle_scale_keeps_the_flinch_squash_invariant()`
- `def test_animation_never_changes_the_sim_snapshot()`

---

### [`tests/test_enemy_cover.py`](tests/test_enemy_cover.py)
> *Enemy/cover proofs: melee enemies cannot walk through arena cover.*

**Size**: `60` lines

**Functions:**
- `def _inside_any_cover(sim, x, z, radius)`
- `def _crossing_sim()`
- `def test_enemy_never_enters_cover()`
- `def test_enemy_gets_around_cover_toward_player()`
- `def test_spawn_guard_keeps_enemies_out_of_covers()`

---

### [`tests/test_enemy_los.py`](tests/test_enemy_los.py)
> *Enemy proofs: brute slams respect line of sight.*

**Size**: `48` lines

**Functions:**
- `def _sim(player_z, brute_z, x)`
- `def test_brute_cannot_slam_through_cover()`
- `def test_brute_still_slams_in_the_open()`

---

### [`tests/test_enemy_spacing.py`](tests/test_enemy_spacing.py)
> *Enemy proof: melee crowds keep their footprint instead of stacking.*

**Size**: `55` lines

**Functions:**
- `def _sim(count)`
- `def test_melee_crowd_keeps_its_footprint()`
- `def test_separation_is_data_owned()`

---

### [`tests/test_engagement.py`](tests/test_engagement.py)
> *Engagement mechanics: stated-vs-coded odds, honesty, overdrive, lock, determinism.*

**Size**: `269` lines

**Functions:**
- `def _load_eng()`
- `def _aimed_sim(enemy_hp, etype)`
- `def test_engagement_data_valid()`
- `def test_reward_stream_separate_and_reseedable()`
- `def test_reseed_restores_a_played_sim_to_a_fresh_one()` - *reseed(seed) must be a full reset, not just an rng rewind.*
- `def test_stated_odds_match_coded_partition()`
- `def test_kill_counts_rewards_and_streak_bonus()`
- `def test_streak_cap_and_hurt_break()`
- `def test_near_miss_honest_once_per_wave()`
- `def test_clutch_is_flavor_only()`
- `def test_overdrive_preview_refusals_cost_and_break()`
- `def test_overdrive_doubles_score_while_active()`
- `def test_cache_drop_pickup_and_expiry()`
- `def test_surge_lock_forfeits_on_switch()`
- `def test_engagement_deterministic()`

---

### [`tests/test_feedback.py`](tests/test_feedback.py)
> *Combat-feedback proofs: damage source tracking and HUD direction cue.*

**Size**: `125` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _parked_with_mite(x, z)`
- `def test_hurt_records_source_and_timer()`
- `def test_hurt_cue_expires()`
- `def _red_rects(canvas)`
- `def _draw_with_source(side)`
- `def test_hud_draws_directional_damage_cue()`
- `def test_hud_hides_damage_cue_when_quiet()`
- `def test_hurt_cue_does_not_change_sim_hash_path()`

---

### [`tests/test_graphics.py`](tests/test_graphics.py)
> *Graphics proofs: floor grid, lit arena trim, shared batching payloads.*

**Size**: `72` lines

**Functions:**
- `def test_the_shipped_renderer_flags_are_all_enabled()` - *grade.json deliberately adopts all four deterministic renderer features.*
- `def test_floor_grid_texture_is_deterministic_and_named()`
- `def test_arena_has_ten_trim_nodes_sharing_one_material()`
- `def test_floor_material_uses_grid_texture()`
- `def test_trim_does_not_touch_colliders_or_sim()`
- `def test_graphics_budget_with_trim()`

---

### [`tests/test_history.py`](tests/test_history.py)
> *Progression proofs: bounded run history survives saves.*

**Size**: `77` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def test_schema_two_migrates_with_empty_history(tmp_path)`
- `def test_death_history_appends_newest_first_and_caps(tmp_path)`
- `def test_debrief_shows_recent_scores(tmp_path)`

---

### [`tests/test_hurt_shake.py`](tests/test_hurt_shake.py)
> *Combat-feel proof: taking damage jolts the camera through Keystone shake.*

**Size**: `158` lines

**Functions:**
- `def _cam(game)`
- `def _hurt_once(game)` - *Make the next update() report one real "hurt" event.*
- `def _death_once(game)` - *Make the next update() report one real "died" event.*
- `def _quiet(game)` - *Remove attackers so decay is measured without a second hit.*
- `def test_camera_jolts_after_taking_damage_and_settles_when_trauma_decays()`
- `def test_the_jolt_composes_onto_the_sim_pose_without_replacing_it()`
- `def test_camera_jolt_does_not_change_sim()`
- `def test_build_scene_clears_trauma()`
- `def test_a_cinematic_owns_the_camera_and_clears_live_trauma()` - *A hit on the killing blow must not freeze mid-decay behind a path.*
- `def test_the_victory_cinematic_also_clears_trauma()`

---

### [`tests/test_juice_tuning.py`](tests/test_juice_tuning.py)
> *Presentation tuning bounds: the juice.json numbers a designer edits are wired.*

**Size**: `200` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`

**Functions:**
- `def _warden_winding_up()`
- `def _aimed(hp)`
- `def test_slam_ring_bars_stay_a_thin_ground_ring()`
- `def test_spawn_marker_stays_a_tall_thin_pillar()`
- `def test_shipped_spawn_mark_cap_stays_in_the_budget_band()`
- `def test_pad_pulse_amplitude_stays_in_the_design_band()`
- `def test_death_fx_caps_cover_every_shipped_enemy()` - *A missing cap falls back to 1.0 (full-size burst) - pin the lookup keys.*
- `def test_impact_burst_stays_in_the_design_band()`
- `def test_kill_burst_stays_in_the_design_band()`
- `def test_muzzle_flash_lifetime_stays_in_the_design_band()`
- `def test_hitmark_expands_the_reticle_by_the_design_gap()`
- `def test_a_wide_spread_is_capped_by_the_reticle_budget()`
- `def test_low_health_edge_alpha_stays_in_the_design_band()`
- `def test_death_fx_window_stays_in_the_design_band()`
- `def test_pickup_burst_window_stays_in_the_design_band()`
- `def test_killmark_and_hitmark_windows_stay_in_their_bands()`
- `def test_hit_flinch_window_stays_in_the_design_band()`

---

### [`tests/test_jump_feel.py`](tests/test_jump_feel.py)
> *Gameplay-feel proofs: the jump apex and the coyote window are pinned.*

**Size**: `108` lines

**Functions:**
- `def _jump_rise()` - *Peak height gained by a standing jump, measured from the ground.*
- `def test_the_standing_jump_rises_about_one_metre()` - *The apex is the level's reachability budget, not an incidental number.*
- `def test_the_jump_clears_the_platform_but_stays_under_the_lowest_cover()` - *The design intent behind the apex, independent of the exact number.*
- `def _jump_after(frames)` - *Leave the ground, wait, then try to jump; True when the buffered jump fires.*
- `def test_the_coyote_window_is_short_but_not_zero()` - *A jump shortly after leaving the ground must land; a late one must not.*
- `def test_the_coyote_window_matches_its_declared_seconds()` - *The constant means what it says: about 0.12 s of grace.*

---

### [`tests/test_keystone_agent_mechanics.py`](tests/test_keystone_agent_mechanics.py)
> *Keystone mechanics testbed: AI actions, observations and audit trails.*

**Size**: `207` lines

**Functions:**
- `def test_parse_actions_clamps_axes_and_accepts_wrappers()`
- `def test_observe_is_deterministic_and_auditable()`
- `def test_summarize_report_truncates_and_keeps_material()`
- `def test_audit_trail_chains_and_detects_tampering()`
- `def test_audit_trail_persists_reloads_and_rejects_bad_documents(tmp_path)`

---

### [`tests/test_keystone_analysis_mechanics.py`](tests/test_keystone_analysis_mechanics.py)
> *Keystone mechanics testbed: headless frame analysis and pixel diffs.*

**Size**: `303` lines

**Functions:**
- `def _flat(width, height, color)`
- `def test_analyze_frame_stats_and_hashes(tmp_path)`
- `def test_analyze_frame_nodes_material_and_scene_metadata()`
- `def test_compare_reports_detects_node_and_image_changes()`
- `def test_compare_reports_ui_fx_and_legacy_defaults()`
- `def test_diff_images_writes_threshold_diff_and_report(tmp_path)`

---

### [`tests/test_keystone_animation_blend_mechanics.py`](tests/test_keystone_animation_blend_mechanics.py)
> *Keystone testbed: enemy idle clips as a real 1D blend space.*

**Size**: `74` lines

**Functions:**
- `def _game()`
- `def _pose(sample)`
- `def test_blend_report_uses_shipped_clips_and_hp_thresholds()`
- `def test_low_and_high_parameters_pick_exact_clips()`
- `def test_a_mid_parameter_blends_the_neighbouring_poses()`
- `def test_the_alive_threat_drives_the_default_parameter()`
- `def test_reporting_a_blend_never_touches_the_sim()`

---

### [`tests/test_keystone_animation_mechanics.py`](tests/test_keystone_animation_mechanics.py)
> *Keystone mechanics testbed: animation clips, controller and poses.*

**Size**: `145` lines

**Functions:**
- `def _bob_clip()`
- `def _low_clip()`
- `def test_animation_library_round_trips_and_samples()`
- `def test_controller_crossfades_and_reports_events()`
- `def test_controller_loops_and_refires_events()`
- `def test_apply_pose_writes_scene_nodes()`
- `def test_apply_pose_with_channel_mask_preserves_unmasked_position()`

---

### [`tests/test_keystone_animation_state_mechanics.py`](tests/test_keystone_animation_state_mechanics.py)
> *Keystone testbed: a parameter-driven enemy animation state preview.*

**Size**: `62` lines

**Functions:**
- `def _game()`
- `def test_the_preview_reports_the_authored_states_and_transitions()`
- `def test_threat_drives_the_active_state()`
- `def test_the_sampled_pose_is_json_safe()`
- `def test_the_default_parameter_comes_from_the_alive_threat()`
- `def test_previewing_a_state_never_touches_the_sim()`

---

### [`tests/test_keystone_api_contract_mechanics.py`](tests/test_keystone_api_contract_mechanics.py)
> *Keystone mechanics testbed: public API and schema contracts.*

**Size**: `148` lines

**Functions:**
- `def test_public_exports_resolve_and_engine_lazy_load()`
- `def test_schema_versions_and_editor_actions()`
- `def test_describe_game_matches_schema_actions()`
- `def test_cube_demo_contract_and_determinism()`
- `def test_module_all_exports_and_reexports()`

---

### [`tests/test_keystone_arena_layout_mechanics.py`](tests/test_keystone_arena_layout_mechanics.py)
> *Testbed consistency: one arena layout for every grid-shaped report.*

**Size**: `51` lines

**Functions:**
- `def _game()`
- `def test_the_shared_layout_matches_the_shipped_arena()`
- `def test_the_shared_cell_conversion_matches_spawn_and_pickup()`
- `def test_a_resized_arena_propagates_to_every_report()`
- `def test_the_layout_helpers_never_touch_the_sim()`

---

### [`tests/test_keystone_asset_io_mechanics.py`](tests/test_keystone_asset_io_mechanics.py)
> *Keystone mechanics testbed: disk-backed asset sources and reload reports.*

**Size**: `164` lines

**Functions:**
- `def test_default_loader_and_suffix_kinds()`
- `def test_fingerprint_and_load_asset_sources(tmp_path)`
- `def test_asset_kind_accepts_only_supported_payloads()`
- `def test_asset_source_validates_fields(tmp_path)`
- `def test_reload_report_ok_and_describe()`

---

### [`tests/test_keystone_audio_assets.py`](tests/test_keystone_audio_assets.py)
> *Keystone mechanics testbed: audio buses/mixdown and asset hot reload.*

**Size**: `136` lines

**Functions:**
- `def _clip()`
- `def test_mixer_bus_gain_scales_the_render()`
- `def test_mixer_validates_buses_and_gains()`
- `def test_shooter_mixer_routes_sfx_and_caps_voices()`
- `def test_registry_tracks_dependencies_and_duplicates()`
- `def test_registry_replace_guard_and_digest()`
- `def test_registry_register_file_hot_reloads_and_reports_missing()`

---

### [`tests/test_keystone_audio_spatial_mechanics.py`](tests/test_keystone_audio_spatial_mechanics.py)
> *Keystone testbed: the spawn warning voice consumes audio_spatial.*

**Size**: `90` lines

**Functions:**
- `def _game()`
- `def _played_gain(g, position)`
- `def _at(eye, dx)`
- `def test_spawn_voice_gain_falls_off_with_distance()`
- `def test_spatial_report_describes_the_same_geometry()`
- `def test_a_bad_position_falls_back_without_crashing_the_frame()`
- `def test_a_rebuild_clears_the_spatial_report()`
- `def test_spatial_audio_does_not_touch_the_deterministic_state()`

---

### [`tests/test_keystone_authoring_mechanics.py`](tests/test_keystone_authoring_mechanics.py)
> *Keystone mechanics testbed: editor authoring workflows.*

**Size**: `207` lines

**Classes:**
- `class _SceneGame` - *Minimal editable game: one pad/child scene on the shooter assets.*
  - Method `.__init__(assets, scene)`
  - Method `.build_scene()`
  - Method `.update(dt, actions)`
  - Method `.snapshot()`
  - Method `.actions()`

**Functions:**
- `def _game()`
- `def _node(doc, node_id)`
- `def test_undo_and_redo_a_node_edit()`
- `def test_play_mode_steps_and_restores_the_scene()`
- `def test_material_save_assign_delete_and_restore()`
- `def test_animation_key_authoring()`
- `def test_scene_diff_and_validation()`

---

### [`tests/test_keystone_batch_mechanics.py`](tests/test_keystone_batch_mechanics.py)
> *Keystone mechanics testbed: static/skinned batch planning and merging.*

**Size**: `243` lines

**Functions:**
- `def _skinned(bind)`
- `def test_plan_batches_groups_static_by_mesh_and_material()`
- `def test_plan_batches_skinned_keying()`
- `def test_merge_batches_static_world_space_and_exclude()`
- `def test_merge_batches_skinned_world_and_bind_agreement()`
- `def test_merge_and_plan_summary_invariants()`

---

### [`tests/test_keystone_bot_nav_grid_mechanics.py`](tests/test_keystone_bot_nav_grid_mechanics.py)
> *Testbed consistency: the bot preview plans on the authoritative nav grid.*

**Size**: `43` lines

**Functions:**
- `def _game()`
- `def test_bot_preview_uses_the_authoritative_blocked_set()`
- `def test_bot_preview_goal_matches_the_route_plan()`
- `def test_bot_preview_follows_a_resized_arena()`
- `def test_bot_preview_never_touches_the_sim()`

---

### [`tests/test_keystone_broadphase_mechanics.py`](tests/test_keystone_broadphase_mechanics.py)
> *Keystone mechanics testbed: the spatial-grid broadphase contract.*

**Size**: `195` lines

**Functions:**
- `def _box(x, y, z, half)`
- `def _populated()` - *A scene whose cells overlap in every interesting way.*
- `def test_cell_size_changes_no_answer()`
- `def test_a_large_proxy_is_found_from_an_edge_cell()`
- `def test_results_follow_insertion_order_not_spatial_order()`
- `def test_reinserting_a_key_keeps_its_original_rank()`
- `def test_insert_replaces_bounds_and_drops_stale_cells()`
- `def test_remove_clear_and_membership()`
- `def test_empty_and_degenerate_inputs()`
- `def test_cell_size_validation()`
- `def test_proxy_cell_budget_is_inclusive_and_names_the_limit()`
- `def test_an_oversized_query_degrades_to_a_linear_scan()`
- `def test_non_finite_bounds_never_reach_the_grid()`
- `def test_two_grids_agree_and_repeat_calls_are_stable()`

---

### [`tests/test_keystone_camera_culling_mechanics.py`](tests/test_keystone_camera_culling_mechanics.py)
> *Keystone mechanics testbed: perspective camera and CPU frustum culling.*

**Size**: `224` lines

**Functions:**
- `def _skinned_quad()`
- `def _cube_scene()`
- `def _visible_names(scene, width, height)`
- `def test_camera_orientation_look_at_and_clamping()`
- `def test_camera_projection_edges_and_fly_movement()`
- `def test_frustum_plane_and_aabb_contract()`
- `def test_cull_scene_keeps_front_and_respects_aspect()`
- `def test_nested_hidden_and_skinned_culling()`

---

### [`tests/test_keystone_camera_path_editor_mechanics.py`](tests/test_keystone_camera_path_editor_mechanics.py)
> *Keystone mechanics testbed: the shipped victory path through the editor API.*

**Size**: `163` lines

**Functions:**
- `def library_server(tmp_path)`
- `def _editor(base, action, **payload)`
- `def _shipped_path()`
- `def test_the_shipped_document_saves_lists_and_previews_over_http(library_server)`
- `def test_preview_at_every_key_matches_the_document_key_poses(library_server)`
- `def test_the_shipped_document_survives_delete_and_restore(library_server)`
- `def test_a_malformed_document_is_rejected_without_corrupting_the_library(library_server)`
- `def test_preview_needs_exactly_one_source(library_server)`

---

### [`tests/test_keystone_camera_rig_mechanics.py`](tests/test_keystone_camera_rig_mechanics.py)
> *Keystone testbed: the viewmodel is a CameraRig, not hand-composed world nodes.*

**Size**: `56` lines

**Functions:**
- `def _game()`
- `def test_the_rig_and_its_parts_live_on_the_overlay_layer()`
- `def test_the_root_follows_the_camera_and_a_missing_sync_is_visible()`
- `def test_parts_declare_camera_space_offsets()`
- `def test_syncing_the_rig_never_reaches_the_sim()`

---

### [`tests/test_keystone_camera_shaker_mechanics.py`](tests/test_keystone_camera_shaker_mechanics.py)
> *Keystone testbed: camera_shaker composes the damage jolt onto the base pose.*

**Size**: `95` lines

**Functions:**
- `def _shaking_game()`
- `def test_the_rendered_camera_is_the_shaker_pose()`
- `def test_the_base_pose_stays_on_the_sim_eye_across_frames()`
- `def test_the_report_distinguishes_the_base_from_the_shaken_pose()`
- `def test_the_shaker_reports_keep_the_sim_out_of_the_picture()`
- `def test_build_scene_and_a_cinematic_clear_the_shaker_report()`

---

### [`tests/test_keystone_component_codec_mechanics.py`](tests/test_keystone_component_codec_mechanics.py)
> *Keystone mechanics testbed: typed component codecs and lifecycle.*

**Size**: `162` lines

**Classes:**
- `class Health`
- `class Counter`
  - Method `.__init__(value)`
  - Method `.to_dict()`
  - Method `.from_dict(data)`
  - Method `.__eq__(other)`
- `class Ticker`
  - Method `.start(context)`
  - Method `.update(context)`
  - Method `.stop(context)`

**Functions:**
- `def test_component_codec_round_trips_dataclass_and_custom()`
- `def test_node_component_attach_require_remove()`
- `def test_scene_snapshot_components_round_trip()`
- `def test_prefab_components_round_trip()`
- `def test_component_runtime_runs_a_codec_component()`

---

### [`tests/test_keystone_content_mechanics.py`](tests/test_keystone_content_mechanics.py)
> *Keystone testbed: content digests for the shooter's registered assets.*

**Size**: `58` lines

**Functions:**
- `def _game()`
- `def test_digest_report_covers_the_shipped_render_assets()`
- `def test_equal_payloads_share_a_digest_without_object_identity()`
- `def test_different_content_produces_a_different_digest()`
- `def test_repeated_reports_are_stable()`
- `def test_digests_never_touch_the_sim()`

---

### [`tests/test_keystone_engine_loop_mechanics.py`](tests/test_keystone_engine_loop_mechanics.py)
> *Keystone mechanics testbed: Engine loop, pause overlay and CLI gates.*

**Size**: `120` lines

**Functions:**
- `def _cli(args)`
- `def test_engine_headless_loop_steps_and_clock()`
- `def test_pause_overlay_and_engine_pause()`
- `def test_expect_hash_cli_accepts_the_known_hash()`
- `def test_replay_cli_replays_the_campaign_win()`

---

### [`tests/test_keystone_errors_mechanics.py`](tests/test_keystone_errors_mechanics.py)
> *Keystone testbed: structured Why/Fix errors for broken game data.*

**Size**: `82` lines

**Functions:**
- `def data_dir(tmp_path, monkeypatch)`
- `def _broken_data_error(data_dir, name, payload)`
- `def test_broken_data_raises_a_structured_keystone_error(data_dir)`
- `def test_every_data_failure_carries_both_fields(data_dir, name, payload)`
- `def test_the_rendered_message_is_unchanged(data_dir)`
- `def test_the_report_is_a_json_safe_view_of_the_error(data_dir)`
- `def test_reporting_an_error_never_touches_the_sim(data_dir)`

---

### [`tests/test_keystone_evidence_mechanics.py`](tests/test_keystone_evidence_mechanics.py)
> *Keystone testbed: capture routes as reproducible proof artefacts.*

**Size**: `100` lines

**Classes:**
- `class _Engine` - *Only run(), capture() and scene are needed by capture_route.*
  - Method `.__init__(luma)`
  - Method `.run(frames)`
  - Method `.capture(png, report_path)`

**Functions:**
- `def _capture(tmp_path, name, luma)`
- `def test_the_shipped_route_has_named_checkpoints()`
- `def test_capture_route_is_byte_reproducible(tmp_path)`
- `def test_diff_reports_a_changed_checkpoint(tmp_path)`
- `def test_diff_reports_a_missing_and_an_added_label(tmp_path)`
- `def test_diff_summaries_reads_a_written_baseline(tmp_path)`

---

### [`tests/test_keystone_frame_report_hash_mechanics.py`](tests/test_keystone_frame_report_hash_mechanics.py)
> *Keystone mechanics testbed: what a frame report's ``hash`` actually covers.*

**Size**: `101` lines

**Functions:**
- `def _frame(tmp_path, name)`
- `def test_identical_pixels_hash_differently_when_the_artifact_is_renamed(tmp_path)`
- `def test_the_same_artifact_path_hashes_identically(tmp_path)`
- `def test_the_hash_tracks_real_content_not_only_the_path(tmp_path)`
- `def test_a_report_without_an_artifact_still_hashes_the_frame(tmp_path)`

---

### [`tests/test_keystone_gltf_import_mechanics.py`](tests/test_keystone_gltf_import_mechanics.py)
> *Keystone mechanics testbed: glTF scene import adapter.*

**Size**: `190` lines

**Functions:**
- `def _data_uri(data)`
- `def _image_uri(data)`
- `def _triangle(texture, color)`
- `def _write_gltf(root, name, document)`
- `def test_is_gltf_asset_suffixes_and_types()`
- `def test_import_gltf_prefab_registers_and_saves(tmp_path)`
- `def test_import_gltf_texture_registration(tmp_path)`
- `def test_import_gltf_name_override_reimport_and_errors(tmp_path)`
- `def test_import_gltf_prefab_scene_and_library_contents(tmp_path)`

---

### [`tests/test_keystone_gltf_loader_mechanics.py`](tests/test_keystone_gltf_loader_mechanics.py)
> *Keystone mechanics testbed: glTF source, GLB and accessor decoding.*

**Size**: `301` lines

**Functions:**
- `def _data_uri(data)`
- `def _chunk(kind, payload)`
- `def _glb(document, binary)`
- `def _triangle_document(uri)`
- `def test_gltf_source_variants(tmp_path)`
- `def test_glb_container_validation()`
- `def test_load_buffers_data_uri_file_and_glb(tmp_path)`
- `def test_read_accessor_validation_and_normalization()`
- `def test_load_gltf_document_validation_and_registry(tmp_path)`

---

### [`tests/test_keystone_history_mechanics.py`](tests/test_keystone_history_mechanics.py)
> *Keystone mechanics testbed: bounded undo/redo history.*

**Size**: `121` lines

**Functions:**
- `def test_push_peek_undo_redo_round_trip()`
- `def test_deep_copy_isolation()`
- `def test_push_after_undo_discards_redo_branch()`
- `def test_capacity_drops_oldest_and_repairs_index()`
- `def test_clear_and_empty_behavior()`

---

### [`tests/test_keystone_http_server_mechanics.py`](tests/test_keystone_http_server_mechanics.py)
> *Keystone mechanics testbed: real HTTP routes for the web console.*

**Size**: `161` lines

**Functions:**
- `def base_url()`
- `def _request(base, path, method, payload, raw)`
- `def _json(base, path, method, payload, raw)`
- `def test_get_health_describe_and_scene(base_url)`
- `def test_get_inspector_reports_batches_and_merged(base_url)`
- `def test_post_simulate_matches_the_cli_hash(base_url)`
- `def test_editor_actions_and_error_paths(base_url)`

---

### [`tests/test_keystone_input_ui_asset_mechanics.py`](tests/test_keystone_input_ui_asset_mechanics.py)
> *Keystone mechanics testbed: input, UI, asset loading and batch merging.*

**Size**: `186` lines

**Classes:**
- `class _InputContext`
  - Method `.__init__(keys, mouse, cursor)`
  - Method `.key_down(key)`
  - Method `.mouse_down(button)`
  - Method `.cursor_position()`

**Functions:**
- `def test_input_map_contexts_and_pressed_held()`
- `def test_action_state_pressed_held_round_trip()`
- `def test_pause_menu_and_canvas_clipping()`
- `def test_png_and_obj_loading()`
- `def test_merge_batches_on_the_shooter_scene()`

---

### [`tests/test_keystone_instancing_mechanics.py`](tests/test_keystone_instancing_mechanics.py)
> *Keystone mechanics testbed: CPU instancing grouping and plans.*

**Size**: `188` lines

**Functions:**
- `def _skinned_triangle()`
- `def _shared_scene()`
- `def test_group_instances_shared_payloads_and_materials()`
- `def test_group_instances_respects_frustum_planes()`
- `def test_group_ordering_is_deterministic()`
- `def test_plan_instanced_counts_and_savings()`
- `def test_skinned_groups_do_not_report_savings()`

---

### [`tests/test_keystone_library_trash_mechanics.py`](tests/test_keystone_library_trash_mechanics.py)
> *Keystone mechanics testbed: library soft delete and restore.*

**Size**: `134` lines

**Functions:**
- `def _scene(*names)`
- `def test_scene_library_delete_trash_and_restore(tmp_path)`
- `def test_prefab_library_delete_trash_and_restore(tmp_path)`
- `def test_trash_entries_are_unique_sorted_and_keep_dotted_names(tmp_path)`
- `def test_restore_rejects_paths_wrong_suffix_and_collisions(tmp_path)`
- `def test_scene_and_prefab_trash_are_isolated_by_suffix(tmp_path)`

---

### [`tests/test_keystone_mechanics.py`](tests/test_keystone_mechanics.py)
> *Keystone mechanics testbed: replay, triggers, particles, batching, grid.*

**Size**: `152` lines

**Functions:**
- `def test_replay_runner_verifies_the_campaign_win()`
- `def test_trigger_tracker_enters_once_and_exits()`
- `def test_pickup_trigger_fires_once()`
- `def test_particle_burst_is_deterministic()`
- `def test_scene_batches_plan_shared_static_groups()`
- `def test_scene_budget_invariants_pass_with_presentation_node()`
- `def test_spatial_grid_broadphase_matches_colliders()`

---

### [`tests/test_keystone_mesh_builder_mechanics.py`](tests/test_keystone_mesh_builder_mechanics.py)
> *Keystone mechanics testbed: MeshBuilder composition and skin merging.*

**Size**: `191` lines

**Functions:**
- `def _skinned_quad(offset, bind, joints)`
- `def test_quad_and_box_geometry_counts_and_bounds()`
- `def test_add_mesh_scales_translates_and_multiplies_colors()`
- `def test_add_mesh_matrix_transforms_positions_and_normals()`
- `def test_skinned_mesh_concat_and_agreement_rules()`
- `def test_plain_and_skin_modes_cannot_mix()`

---

### [`tests/test_keystone_nav_agent_mechanics.py`](tests/test_keystone_nav_agent_mechanics.py)
> *Keystone testbed: a bot route preview driven by a real NavAgent.*

**Size**: `54` lines

**Functions:**
- `def _game()`
- `def test_the_preview_plans_from_spawn_to_the_pickup()`
- `def test_the_local_agent_advances_toward_its_first_waypoint()`
- `def test_zero_frames_leave_the_report_at_the_start()`
- `def test_the_preview_is_reproducible()`
- `def test_previewing_a_route_never_touches_the_sim()`

---

### [`tests/test_keystone_nav_authoring_mechanics.py`](tests/test_keystone_nav_authoring_mechanics.py)
> *Keystone testbed: nav grid authored from the live collision boxes.*

**Size**: `53` lines

**Functions:**
- `def _game()`
- `def test_the_authored_grid_has_open_endpoints_and_a_route()`
- `def test_the_arena_floor_is_explicitly_excluded()`
- `def test_more_clearance_blocks_more_cells()`
- `def test_the_report_is_reproducible()`
- `def test_authoring_a_grid_never_touches_the_sim()`

---

### [`tests/test_keystone_nav_unification_mechanics.py`](tests/test_keystone_nav_unification_mechanics.py)
> *Testbed consistency: one authoritative nav grid for every report.*

**Size**: `50` lines

**Functions:**
- `def _game()`
- `def test_the_two_nav_reports_agree_on_the_blocked_set()`
- `def test_both_routes_still_exist_and_agree()`
- `def test_the_shared_helper_is_the_authority_for_both()`
- `def test_unifying_the_grid_never_touches_the_sim()`

---

### [`tests/test_keystone_navigation_mechanics.py`](tests/test_keystone_navigation_mechanics.py)
> *Keystone testbed: the arena's nav plan comes from pathfinding + navigation.*

**Size**: `63` lines

**Functions:**
- `def _game()`
- `def test_nav_plan_reports_a_route_from_spawn_to_pickup()`
- `def test_the_grid_marks_the_shipped_covers_as_blocked()`
- `def test_waypoints_are_world_points_near_the_endpoints()`
- `def test_a_blocked_goal_reports_no_route()`
- `def test_building_a_nav_plan_never_touches_the_sim()`

---

### [`tests/test_keystone_obj_loader_mechanics.py`](tests/test_keystone_obj_loader_mechanics.py)
> *Keystone mechanics testbed: Wavefront OBJ loading.*

**Size**: `128` lines

**Functions:**
- `def test_parse_obj_triangle_with_uvs_and_normals()`
- `def test_parse_obj_negative_indices_and_quad_fan()`
- `def test_parse_obj_homogeneous_vertices_and_directives()`
- `def test_load_obj_file_bom_and_missing(tmp_path)`
- `def test_obj_validation_errors()`

---

### [`tests/test_keystone_persistence_mechanics.py`](tests/test_keystone_persistence_mechanics.py)
> *Keystone testbed: profile store contract via VersionedStore.*

**Size**: `57` lines

**Functions:**
- `def _game()`
- `def test_the_probe_covers_every_lifecycle_stage()`
- `def test_an_old_schema_profile_migrates_in_order()`
- `def test_a_corrupt_profile_is_quarantined_and_recovered()`
- `def test_the_real_profile_path_is_untouched(tmp_path)`
- `def test_the_probe_is_reproducible_and_never_touches_the_sim()`

---

### [`tests/test_keystone_physics_mechanics.py`](tests/test_keystone_physics_mechanics.py)
> *Keystone mechanics testbed: character physics and the fixed-step clock.*

**Size**: `99` lines

**Functions:**
- `def _ground(controller)`
- `def test_character_gravity_settles_on_the_floor()`
- `def test_character_steps_up_a_low_ledge_and_stops_at_a_tall_one()`
- `def test_character_slides_along_cover_without_penetration()`
- `def test_fixed_step_clock_releases_whole_steps()`
- `def test_fixed_step_clock_caps_catch_up_and_keeps_running()`
- `def test_clock_and_controller_reject_invalid_configuration()`

---

### [`tests/test_keystone_picking_mechanics.py`](tests/test_keystone_picking_mechanics.py)
> *Keystone testbed: a presentation-only crosshair probe via scene picking.*

**Size**: `63` lines

**Functions:**
- `def _game(yaw, pitch)`
- `def test_crosshair_pick_reports_a_world_node()`
- `def test_the_pick_follows_the_aim_direction()`
- `def test_aiming_above_the_arena_is_a_clean_miss()`
- `def test_the_overlay_viewmodel_is_never_picked()`
- `def test_picking_never_touches_the_deterministic_state()`

---

### [`tests/test_keystone_playtest_mechanics.py`](tests/test_keystone_playtest_mechanics.py)
> *Keystone mechanics testbed: seeded playtests and fairness verdicts.*

**Size**: `293` lines

**Classes:**
- `class _WinGame`
  - Method `.__init__()`
  - Method `.build_scene()`
  - Method `.update(step, action)`
  - Method `.snapshot()`
  - Method `.actions()`
- `class _NeverWinGame`
  - Method `.snapshot()`
- `class _TerminalGame`
  - Method `.snapshot()`
- `class _NoOutcomeGame`
  - Method `.__init__()`
  - Method `.build_scene()`
  - Method `.update(step, action)`
  - Method `.snapshot()`
  - Method `.actions()`

**Functions:**
- `def test_canon_signals_and_hash()`
- `def test_scripted_run_transcript_diff_and_greedy_policy()`
- `def test_policy_and_run_bot_validation()`
- `def test_make_report_and_transcript_contract()`
- `def test_validate_fairness_verdicts()`

---

### [`tests/test_keystone_png_texture_mechanics.py`](tests/test_keystone_png_texture_mechanics.py)
> *Keystone mechanics testbed: PNG encoding and RGBA textures.*

**Size**: `136` lines

**Functions:**
- `def test_png_round_trip_flip_and_bytes(tmp_path)`
- `def test_png_rejects_corrupt_inputs(tmp_path)`
- `def test_texture_validation_and_sha()`
- `def test_texture_from_png_and_bytes(tmp_path)`
- `def test_texture_checker_pattern_and_validation()`

---

### [`tests/test_keystone_pose_json_mechanics.py`](tests/test_keystone_pose_json_mechanics.py)
> *Testbed consistency: one JSON-safe serializer for sampled poses.*

**Size**: `60` lines

**Functions:**
- `def _game()`
- `def test_the_serializer_keeps_all_three_channels_with_stable_rounding()`
- `def test_both_animation_reports_use_the_shared_serializer(monkeypatch)`
- `def test_both_reports_still_produce_json_safe_poses()`
- `def test_serializing_poses_never_touches_the_sim()`

---

### [`tests/test_keystone_presentation_resets_mechanics.py`](tests/test_keystone_presentation_resets_mechanics.py)
> *Testbed consistency: one rebuild reset for presentation state.*

**Size**: `73` lines

**Functions:**
- `def _game()`
- `def _dirty(g)`
- `def _assert_clean(g)`
- `def test_the_helper_clears_every_presentation_field()`
- `def test_build_scene_uses_the_shared_helper(monkeypatch)`
- `def test_a_rebuild_after_a_cinematic_clears_everything()`
- `def test_resetting_presentation_never_touches_the_sim()`

---

### [`tests/test_keystone_primitives_mechanics.py`](tests/test_keystone_primitives_mechanics.py)
> *Keystone mechanics testbed: procedural primitive geometry.*

**Size**: `139` lines

**Functions:**
- `def test_cube_face_winding_uvs_and_bounds()`
- `def test_plane_bounds_normals_and_uvs()`
- `def test_cone_side_and_base_normals()`
- `def test_cylinder_side_and_cap_normals()`
- `def test_sphere_radial_normals_and_uv_range()`

---

### [`tests/test_keystone_project_export_mechanics.py`](tests/test_keystone_project_export_mechanics.py)
> *Keystone mechanics testbed: project manifests and export bundles.*

**Size**: `305` lines

**Functions:**
- `def _name()`
- `def _project_with_png(root, name)`
- `def test_create_load_and_manifest_validation()`
- `def _game_without_manifest_assets(context)`
- `def test_validate_project_assets_and_broken_scene()`
- `def test_export_bundle_contents_hashes_and_launcher()`
- `def test_export_rejects_missing_and_broken_projects()`
- `def _main(argv)`
- `def test_cli_validate_project_reports_clean_and_broken_content()`
- `def test_cli_export_builds_bundle_and_refuses_non_empty_target()`
- `def test_manifest_asset_validation_after_load_game_duplicates()`
- `def test_cli_export_with_manifest_asset_self_clears()`

---

### [`tests/test_keystone_raycast_scene_mechanics.py`](tests/test_keystone_raycast_scene_mechanics.py)
> *Keystone mechanics testbed: rays, sphere collision and scene serialization.*

**Size**: `125` lines

**Functions:**
- `def _cover_box()`
- `def test_ray_aabb_distances_misses_and_t_max()`
- `def test_filtered_raycast_nearest_and_skip()`
- `def test_sphere_pushout_and_aabb_overlap_pairs()`
- `def test_scene_library_round_trip_with_shooter_assets()`

---

### [`tests/test_keystone_report_resets_mechanics.py`](tests/test_keystone_report_resets_mechanics.py)
> *Testbed consistency: one reset path for camera-shake presentation state.*

**Size**: `79` lines

**Functions:**
- `def _game()`
- `def _shaking(g)`
- `def _assert_clean(g)`
- `def test_the_helper_clears_trauma_and_both_reports()`
- `def test_build_scene_uses_the_shared_reset()`
- `def test_the_death_cinematic_uses_the_shared_reset()`
- `def test_the_victory_cinematic_uses_the_shared_reset()`
- `def test_repeated_resets_are_idempotent_and_never_touch_the_sim()`

---

### [`tests/test_keystone_rng_mechanics.py`](tests/test_keystone_rng_mechanics.py)
> *Keystone testbed: an isolated RandomStream for presentation-only variety.*

**Size**: `62` lines

**Functions:**
- `def _game(seed)`
- `def test_presentation_draws_are_reproducible_and_seed_dependent()`
- `def test_presentation_draws_cannot_touch_the_sim_hash()`
- `def test_the_json_state_restores_the_exact_next_draw()`
- `def test_a_rebuild_reseeds_the_stream()`
- `def test_the_shoot_voice_actually_draws_from_the_stream()`

---

### [`tests/test_keystone_root_motion_mechanics.py`](tests/test_keystone_root_motion_mechanics.py)
> *Keystone testbed: root motion of the shipped enemy idle clips.*

**Size**: `57` lines

**Functions:**
- `def _game()`
- `def test_root_motion_report_covers_the_four_idle_clips()`
- `def test_the_measured_yaws_band_the_shipped_clips()`
- `def test_a_full_loop_closes_to_identity()`
- `def test_the_in_place_pose_resets_the_subject()`
- `def test_repeated_reports_are_stable_and_never_touch_the_sim()`

---

### [`tests/test_keystone_root_motion_presenter_mechanics.py`](tests/test_keystone_root_motion_presenter_mechanics.py)
> *Keystone testbed: root-motion presentation on a local container rig.*

**Size**: `53` lines

**Functions:**
- `def _game()`
- `def test_the_preview_reports_a_container_and_its_applied_child()`
- `def test_the_container_follows_the_body_and_turns()`
- `def test_zero_frames_leave_the_report_at_the_start()`
- `def test_the_preview_is_reproducible()`
- `def test_presenting_a_rig_never_touches_the_sim()`

---

### [`tests/test_keystone_scene_diff_mechanics.py`](tests/test_keystone_scene_diff_mechanics.py)
> *Keystone mechanics testbed: structured scene-document diffs.*

**Size**: `173` lines

**Functions:**
- `def _scene()`
- `def test_identical_documents_produce_empty_diff()`
- `def test_node_added_removed_and_changed_fields()`
- `def test_section_diffs_camera_environment_root()`
- `def test_diff_validation_errors()`
- `def test_diff_is_deterministic_json_safe_and_uses_snapshots()`

---

### [`tests/test_keystone_scene_editor_mechanics.py`](tests/test_keystone_scene_editor_mechanics.py)
> *Keystone mechanics testbed: editor scene operations and prefab instances.*

**Size**: `175` lines

**Functions:**
- `def _shooter_scene(g)`
- `def test_scene_group_add_save_and_unload()`
- `def test_layer_visibility_lock_and_hide()`
- `def test_prefab_override_and_revert()`
- `def test_nested_prefab_instance_links_rebase()`

---

### [`tests/test_keystone_scene_graph_mechanics.py`](tests/test_keystone_scene_graph_mechanics.py)
> *Keystone mechanics testbed: scene graph queries, IDs and parenting.*

**Size**: `179` lines

**Classes:**
- `class Health`
  - Method `.__init__(value)`

**Functions:**
- `def test_query_filters_find_and_find_by_id()`
- `def test_id_allocation_rejects_duplicates_and_skips_used()`
- `def test_parenting_reparenting_and_cycle_guard()`
- `def test_traversal_order_and_visibility_chain()`
- `def test_restore_next_id_and_id_preservation()`

---

### [`tests/test_keystone_scene_snapshot_mechanics.py`](tests/test_keystone_scene_snapshot_mechanics.py)
> *Keystone mechanics testbed: versioned scene snapshots.*

**Size**: `289` lines

**Functions:**
- `def _source_scene()`
- `def test_scene_snapshot_round_trip_nodes_and_transforms()`
- `def test_scene_snapshot_camera_environment_and_settings()`
- `def test_scene_snapshot_assets_round_trip()`
- `def test_scene_snapshot_validation_errors()`
- `def test_restore_scene_replaces_contents_in_place()`

---

### [`tests/test_keystone_schema_diff_mechanics.py`](tests/test_keystone_schema_diff_mechanics.py)
> *Keystone testbed: live contract versions as an AI/soak query.*

**Size**: `56` lines

**Functions:**
- `def _game()`
- `def test_the_report_has_the_four_live_contract_versions()`
- `def test_versions_match_the_module_not_a_copied_literal()`
- `def test_the_report_is_wired_to_the_module_function(monkeypatch)`
- `def test_repeated_reports_are_stable_and_json_serialisable()`
- `def test_reporting_versions_never_touches_the_sim()`

---

### [`tests/test_keystone_serialization_mechanics.py`](tests/test_keystone_serialization_mechanics.py)
> *Keystone mechanics testbed: atomic byte/JSON persistence.*

**Size**: `82` lines

**Functions:**
- `def test_bytes_atomic_writes_binary_and_replaces(tmp_path)`
- `def test_json_atomic_round_trip_and_backup_chain(tmp_path)`
- `def test_json_atomic_rejects_non_finite_and_unserializable(tmp_path)`
- `def test_read_json_handles_bom_and_errors(tmp_path)`
- `def test_atomic_replace_failure_cleans_temp_and_keeps_target(tmp_path)`

---

### [`tests/test_keystone_skinning_gltf_sprite_mechanics.py`](tests/test_keystone_skinning_gltf_sprite_mechanics.py)
> *Keystone mechanics testbed: skinning, glTF import and sprite math.*

**Size**: `220` lines

**Functions:**
- `def _quad_mesh(**overrides)`
- `def _data_uri(data)`
- `def _triangle_gltf(color)`
- `def _skinned_gltf()`
- `def test_skin_point_rigid_blend_and_validation()`
- `def test_skin_mesh_and_bone_palette()`
- `def test_skinned_gltf_import_and_deformation()`
- `def test_triangle_gltf_material_and_registry()`
- `def test_sprite_scale_alpha_and_billboard_math()`

---

### [`tests/test_keystone_steering_mechanics.py`](tests/test_keystone_steering_mechanics.py)
> *Keystone testbed: enemy steering built from live sim state.*

**Size**: `71` lines

**Functions:**
- `def _game(enemies)`
- `def _mite(x, z)`
- `def test_no_enemies_reports_no_subject()`
- `def test_seek_points_at_the_player_and_stays_within_the_data_speed()`
- `def test_arrive_slows_down_near_the_target()`
- `def test_a_close_neighbour_contributes_separation()`
- `def test_reporting_steering_never_touches_the_sim()`

---

### [`tests/test_keystone_tilemap_mechanics.py`](tests/test_keystone_tilemap_mechanics.py)
> *Keystone testbed: the shipped arena authored as a TileMap document.*

**Size**: `59` lines

**Functions:**
- `def _game()`
- `def test_arena_tile_report_has_the_shipped_shape()`
- `def test_cover_cells_are_marked_solid()`
- `def test_the_document_round_trips_to_an_equal_tile_map()`
- `def test_colliders_and_merged_mesh_are_reported()`
- `def test_repeated_reports_are_stable_and_never_touch_the_sim()`

---

### [`tests/test_keystone_ui_menu_mechanics.py`](tests/test_keystone_ui_menu_mechanics.py)
> *Keystone mechanics testbed: the pause-menu contract and its closed dispatch.*

**Size**: `90` lines

**Functions:**
- `def test_the_default_menu_is_resume_hide_hud_and_quit()`
- `def test_moving_the_selection_wraps_in_both_directions()`
- `def test_move_rejects_bools_and_non_integers()`
- `def test_a_menu_needs_at_least_one_item()`
- `def test_items_are_immutable_values()`
- `def test_a_custom_menu_keeps_its_own_order_and_actions()` - *The model accepts any items; only the engine's dispatch is closed.*
- `def test_the_menu_carries_no_rendering_state()` - *A pure model: no canvas, no hits, no font metrics.*

---

### [`tests/test_keystone_version_mechanics.py`](tests/test_keystone_version_mechanics.py)
> *Keystone testbed: the authoritative engine version as an AI/soak query.*

**Size**: `47` lines

**Functions:**
- `def _game()`
- `def test_the_report_carries_the_authoritative_version()`
- `def test_the_report_is_wired_to_the_module_constant(monkeypatch)`
- `def test_the_report_is_json_safe_and_stable()`
- `def test_reporting_the_version_never_touches_the_sim()`

---

### [`tests/test_keystone_web_api.py`](tests/test_keystone_web_api.py)
> *Keystone testbed proof: the shooter is served by the web session API.*

**Size**: `52` lines

**Functions:**
- `def _session()`
- `def test_describe_exposes_the_shooter_contract()`
- `def test_scene_document_contains_the_arena_and_prefab_nodes()`
- `def test_editor_selects_a_shooter_node()`
- `def test_simulate_matches_the_cli_transcript()`

---

### [`tests/test_kill_feed.py`](tests/test_kill_feed.py)
> *UI readability proofs: a compact kill feed names the kill and its score.*

**Size**: `70` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _kill_sim()`
- `def test_kill_event_carries_type_and_score()`
- `def test_kill_feed_draws_and_expires()`

---

### [`tests/test_killmark.py`](tests/test_killmark.py)
> *Combat-feel proofs: a kill gets its own crosshair marker.*

**Size**: `71` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _hit(hp)`
- `def test_kill_sets_killmark_timer()`
- `def test_nonlethal_hit_does_not_set_killmark()`
- `def test_killmark_draws_red_corner_ticks()`
- `def test_killmark_expires()`

---

### [`tests/test_launchers.py`](tests/test_launchers.py)
> *Delivery proof: the double-click launchers actually start the game.*

**Size**: `163` lines

**Functions:**
- `def _run_bounded(args, **kwargs)` - *Run a command, kill its whole tree on timeout, and report that as failure.*
- `def test_both_launchers_exist_and_stay_in_sync()`
- `def test_the_shell_script_uses_a_quoted_self_directory_and_exec()`
- `def test_the_windows_launcher_runs_from_its_own_directory_and_forwards_args()`
- `def test_the_windows_launcher_explains_a_missing_python()` - *Run it with a PATH that has neither `python` nor `py`.*
- `def test_the_windows_launcher_falls_back_to_the_py_launcher()` - *`py -3` is the fallback when `python` is absent but Python is installed.*
- `def test_the_launchers_are_documented_in_the_readme(launcher)`

---

### [`tests/test_levels.py`](tests/test_levels.py)
> *Level affordance proofs: the surge pickup beacon is visible over cover.*

**Size**: `96` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def test_pickup_beacon_hidden_at_wave_one_spawn()`
- `def test_pickup_beacon_visible_only_while_active()`
- `def test_hud_pickup_label_only_when_close_and_active()`
- `def test_beacon_does_not_touch_the_pickup_trigger()`

---

### [`tests/test_levels_platform.py`](tests/test_levels_platform.py)
> *Level proofs: the arena has a low platform the jump can actually reach.*

**Size**: `52` lines

**Functions:**
- `def _covers()`
- `def test_level_has_a_jumpable_platform()`
- `def test_player_can_jump_onto_the_low_platform()`

---

### [`tests/test_live_bindings.py`](tests/test_live_bindings.py)
> *Live input proof: the engine's bind_input hook drives the real sim.*

**Size**: `99` lines

**Classes:**
- `class FakeContext`
  - Method `.__init__()`
  - Method `.key_down(key)`
  - Method `.cursor_position()`
  - Method `.mouse_down(button)`

**Functions:**
- `def _game()`
- `def _mapping(game)`
- `def _press(game, mapping, *keys)`
- `def test_bind_input_covers_every_declared_button_with_real_keys()`
- `def test_number_key_switches_weapon_through_sample()`
- `def test_r_key_starts_reload()`
- `def test_j_key_starts_overdrive()`
- `def test_f_and_space_keys_fire_and_jump()`

---

### [`tests/test_los_broadphase.py`](tests/test_los_broadphase.py)
> *Game proof: the enemy line-of-sight check uses the wave broadphase.*

**Size**: `96` lines

**Classes:**
- `class _FakeEnemy` - *Only the attributes _enemy_has_los reads.*
  - Method `.__init__(pos)`

**Functions:**
- `def _full_scan(sim, src, target)` - *The previous implementation, kept here as the reference verdict.*
- `def test_prefilter_returns_every_box_the_full_scan_can_block_on()`
- `def test_los_verdict_matches_the_full_scan_across_the_arena()`
- `def test_collider_boxes_keep_build_order_through_the_grid()`
- `def test_every_wall_is_reachable_through_the_grid()`

---

### [`tests/test_lowammo_count.py`](tests/test_lowammo_count.py)
> *UI proof: the low-ammo panel shows the exact magazine count.*

**Size**: `52` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _draw(mag)`
- `def test_low_ammo_panel_shows_mag_count()`
- `def test_low_ammo_count_tracks_the_magazine()`
- `def test_no_low_panel_above_threshold()`

---

### [`tests/test_lowhp_pulse.py`](tests/test_lowhp_pulse.py)
> *Combat-feel proof: the low-health edge warning pulses.*

**Size**: `51` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _edge_alphas(hp, t)`
- `def test_low_health_edges_pulse_with_time()`
- `def test_healthy_player_has_no_edge_warning()`

---

### [`tests/test_mechanics_contract.py`](tests/test_mechanics_contract.py)
> *Contract test: the declared mechanics core stays headless and deterministic.*

**Size**: `154` lines

**Functions:**
- `def _config()`
- `def _core_paths()`
- `def _imports(path)` - *Every module one file imports: (tree, absolute modules, relative names).*
- `def test_the_declared_contract_is_well_formed()`
- `def test_the_core_imports_no_graphics_window_web_or_presentation_module()`
- `def test_the_core_reads_no_wall_clock_and_no_ambient_entropy()`
- `def test_every_rng_in_the_core_is_explicitly_seeded()`
- `def test_the_declared_core_runs_headless_and_repeats_itself()` - *The contract promises an AI-testable core; prove it without an engine.*
- `def test_the_declared_core_reaches_the_game_through_one_direction_only()` - *Presentation may use the core; the core must never reach back.*

---

### [`tests/test_melee_reach.py`](tests/test_melee_reach.py)
> *Enemy proofs: short melee enemies cannot bite through a raised platform.*

**Size**: `69` lines

**Functions:**
- `def _sim(player_y, player_z, etype, enemy_z, enemy_y, hp)`
- `def test_mite_cannot_bite_a_player_on_the_platform()`
- `def test_mite_still_bites_at_ground_level()`
- `def test_brute_still_reaches_the_platform_edge()`
- `def test_melee_vertical_reach_is_data_owned()`

---

### [`tests/test_muzzle.py`](tests/test_muzzle.py)
> *Graphics proofs: the muzzle flash is small and off the aim line.*

**Size**: `44` lines

**Functions:**
- `def _flash_state()`
- `def test_muzzle_flash_is_small_and_off_the_aim_line()`
- `def test_muzzle_flash_node_uses_small_scale()`

---

### [`tests/test_new_run.py`](tests/test_new_run.py)
> *Game proof: a finished run can be restarted without relaunching.*

**Size**: `191` lines

**Functions:**
- `def _finish_death_cinematic(game, limit)` - *Advance until the death cinematic has clapped out on its final pose.*
- `def _tick(game, actions, frames)`
- `def _step_with(game, events_once)` - *Wrap sim.step so the next update also reports the given events.*
- `def _dying_game(tmp_path)` - *A game that dies during its first update, the way a real hit does.*
- `def _winning_game(tmp_path)`
- `def test_enter_after_death_starts_a_new_run_and_keeps_the_record(tmp_path)`
- `def test_enter_after_victory_starts_a_new_run(tmp_path)`
- `def test_enter_during_the_victory_banner_is_ignored(tmp_path)`
- `def test_enter_mid_run_does_nothing(tmp_path)`
- `def test_enter_on_the_death_frame_does_not_skip_the_debrief(tmp_path)`
- `def test_enter_during_the_death_cinematic_is_ignored(tmp_path)` - *A player mashing confirm while dying must still see the debrief.*
- `def test_a_death_without_a_cinematic_is_restartable_at_once(tmp_path, monkeypatch)` - *A failed cinematic build must not leave the player stuck on the debrief.*
- `def test_restart_resets_transient_presentation_state(tmp_path)`

---

### [`tests/test_new_run_integration.py`](tests/test_new_run_integration.py)
> *Integration proof: a real run, a real end, and a real restart.*

**Size**: `140` lines

**Functions:**
- `def _finish_death_cinematic(game, limit)` - *Advance until the death cinematic has clapped out on its final pose.*
- `def _game(tmp_path)`
- `def _play_until_campaign_seal(game, limit)`
- `def _run_out_the_banner(game, limit)`
- `def test_win_then_restart_then_play_a_second_run(tmp_path)`
- `def test_a_real_death_restarts_into_a_live_second_run(tmp_path)`
- `def test_restarting_twice_keeps_a_single_history_entry_per_finished_run(tmp_path)`

---

### [`tests/test_no_reserve.py`](tests/test_no_reserve.py)
> *UI proof: the low-ammo panel names an empty reserve.*

**Size**: `51` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _draw(mag, reserve)`
- `def test_empty_reserve_is_named_at_the_crosshair()`
- `def test_reserve_rounds_keep_the_short_warning()`

---

### [`tests/test_overdrive_glow.py`](tests/test_overdrive_glow.py)
> *Graphics proof: the held gun shows the active overdrive state.*

**Size**: `38` lines

**Functions:**
- `def _game()`
- `def test_overdrive_swaps_the_viewmodel_material()`
- `def test_overdrive_variants_exist_for_every_weapon()`

---

### [`tests/test_overdrive_kill_cue.py`](tests/test_overdrive_kill_cue.py)
> *Audio proof: an overdrive kill is announced as such.*

**Size**: `49` lines

**Functions:**
- `def _kill(overdrive)`
- `def test_overdrive_kill_plays_a_distinct_cue()`
- `def test_normal_kill_keeps_the_plain_cue()`
- `def test_overdrive_kill_voice_differs_from_the_kill_voice()`

---

### [`tests/test_pad_pulse.py`](tests/test_pad_pulse.py)
> *Levels proof: a keystone lifecycle component pulses the launch pad.*

**Size**: `40` lines

**Functions:**
- `def _game()`
- `def test_lifecycle_drives_the_pad_pulse()`
- `def test_pad_starts_at_base_on_a_fresh_build()`

---

### [`tests/test_pickup_arrow.py`](tests/test_pickup_arrow.py)
> *Levels proof: an off-screen surge pickup gets a directional edge tag.*

**Size**: `67` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _sim(yaw, active)`
- `def _tags(canvas)`
- `def test_offscreen_pickup_gets_an_edge_tag()`
- `def test_pickup_ahead_has_no_edge_tag()`
- `def test_inactive_pickup_has_no_edge_tag()`

---

### [`tests/test_pickup_boss_tag.py`](tests/test_pickup_boss_tag.py)
> *UI proof: the pickup edge tag survives a boss fight.*

**Size**: `65` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _sim(boss, active)`
- `def _labels(sim)`
- `def test_boss_suppresses_top_label_but_keeps_edge_tag()`
- `def test_no_boss_keeps_both_cues()`
- `def test_inactive_pickup_has_no_tag()`

---

### [`tests/test_pickup_pop.py`](tests/test_pickup_pop.py)
> *Graphics proof: the surge pickup pops when it is collected.*

**Size**: `54` lines

**Functions:**
- `def _collect()`
- `def test_pickup_collection_starts_an_orb_burst()`
- `def test_orb_burst_expands_then_clears()`

---

### [`tests/test_pickup_prefab.py`](tests/test_pickup_prefab.py)
> *Keystone testbed proof: the pickup beacon is a committed .kprefab.*

**Size**: `69` lines

**Functions:**
- `def test_pickup_beacon_prefab_loads()`
- `def test_the_prefab_document_matches_the_sim_pickup_spot()`
- `def test_game_instantiates_the_pickup_prefab()`
- `def test_pickup_beacon_still_activates()`

---

### [`tests/test_platform_base.py`](tests/test_platform_base.py)
> *Levels proof: the jump platform is framed at its base as well as its top.*

**Size**: `34` lines

**Functions:**
- `def _frame()`
- `def test_platform_frame_includes_base_strips()`
- `def test_platform_frame_keeps_the_top_edge()`

---

### [`tests/test_platform_rim.py`](tests/test_platform_rim.py)
> *Levels proof: the jumpable platform has a readable lit rim.*

**Size**: `45` lines

**Functions:**
- `def _game()`
- `def test_platform_rim_is_one_four_strip_frame()`
- `def test_platform_rim_frame_reaches_all_four_edges()`

---

### [`tests/test_profile.py`](tests/test_profile.py)
> *Progress/save proofs: schema, atomic backup, quarantine, run debrief.*

**Size**: `208` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def test_profile_round_trip_and_backup(tmp_path)`
- `def test_intermediate_schemas_migrate_without_losing_progress(tmp_path, raw, expected_wins)`
- `def test_unsupported_schema_is_refused_without_touching_the_file(tmp_path)`
- `def test_schema_zero_migrates(tmp_path)`
- `def test_corrupt_profile_is_quarantined_and_backup_used(tmp_path)`
- `def _dead_game(tmp_path)`
- `def test_death_records_run_and_new_best(tmp_path)`
- `def test_wave_progress_saves_bests(tmp_path)`
- `def test_best_line_and_death_debrief_draw(tmp_path)`
- `def test_boss_wave_clear_shows_campaign_clear(tmp_path)`
- `def test_unsupported_profile_disables_saves_without_overwrite(tmp_path)`

---

### [`tests/test_profile_backup_restart.py`](tests/test_profile_backup_restart.py)
> *Progress proof: a missing main profile still restores the backup.*

**Size**: `82` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _profile_with_backup(tmp_path)`
- `def _labels(g)`
- `def test_missing_main_restores_the_backup(tmp_path)`
- `def test_fresh_profile_ignores_absence_of_backup(tmp_path)`
- `def test_debrief_shows_backup_recovery_after_restart(tmp_path)`

---

### [`tests/test_profile_disabled.py`](tests/test_profile_disabled.py)
> *Progress proof: a disabled profile is visible on the debrief.*

**Size**: `68` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _dead_game(path)`
- `def _labels(g)`
- `def test_disabled_profile_warns_on_the_debrief(tmp_path)`
- `def test_supported_profile_has_no_disabled_warning(tmp_path)`

---

### [`tests/test_profile_recovery.py`](tests/test_profile_recovery.py)
> *Progress proof: corrupt-profile recovery is visible on the debrief.*

**Size**: `102` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _dead_game(path)`
- `def _labels(g)`
- `def test_corrupt_without_backup_flags_reset(tmp_path)`
- `def test_corrupt_with_backup_flags_recovered(tmp_path)`
- `def test_debrief_names_a_reset_profile(tmp_path)`
- `def test_debrief_names_a_backup_recovery(tmp_path)`

---

### [`tests/test_profile_safety.py`](tests/test_profile_safety.py)
> *Player-data safety: the profile's failure modes, exercised for real.*

**Size**: `199` lines

**Functions:**
- `def _store(tmp_path, name)`
- `def test_save_returns_false_when_the_parent_cannot_be_created(tmp_path)` - *Regression: mkdir used to raise out of save() and break the bool contract.*
- `def test_save_round_trips_and_keeps_a_backup(tmp_path)`
- `def test_corrupt_profile_without_a_backup_is_quarantined(tmp_path)`
- `def test_corrupt_profile_recovers_from_the_backup(tmp_path)`
- `def test_a_fresh_lock_makes_save_refuse_without_writing(tmp_path)`
- `def test_a_stale_lock_is_taken_over(tmp_path)`
- `def test_save_never_leaves_the_lock_behind(tmp_path)`
- `def test_load_always_returns_a_usable_profile(tmp_path, junk)`
- `def test_the_game_reports_an_unsaveable_profile_instead_of_crashing(tmp_path)` - *The debrief must say PROFILE NOT SAVED rather than dying with the save.*
- `def test_a_corrupt_backup_does_not_spoil_a_valid_profile(tmp_path)` - *Only the .bak is broken; the live file must still be used as-is.*
- `def test_when_both_copies_are_broken_the_live_file_is_quarantined(tmp_path)`
- `def test_a_profile_from_a_newer_build_is_refused_and_left_intact(tmp_path)` - *Deliberate: a downgrade must not cost the player their newer progress.*
- `def test_the_game_disables_saving_for_an_unreadable_but_valid_newer_profile(tmp_path)`

---

### [`tests/test_python_floor.py`](tests/test_python_floor.py)
> *Portability proof: the project's "Python 3.10+" promise stays true.*

**Size**: `157` lines

**Functions:**
- `def _shipped_python_files()` - *Every Python file a player's machine would ship or run.*
- `def test_every_source_parses_with_the_current_interpreter()`
- `def test_no_syntax_newer_than_python_310()` - *PEP 695 type parameters (`class C[T]`, `def f[T]()`) need 3.12.*
- `def test_no_stdlib_api_newer_than_python_310()`
- `def test_the_readme_and_keystone_agree_on_the_floor()`
- `def test_the_floor_scan_covers_every_python_source_in_the_repo()` - *A guard that silently stops scanning a folder is worse than no guard.*
- `def test_the_core_modules_import_cleanly(module)` - *An import-time failure is the cheapest way a floor regression shows up.*

---

### [`tests/test_readme_commands.py`](tests/test_readme_commands.py)
> *Documentation proof: the commands the README tells a player to run do work.*

**Size**: `104` lines

**Functions:**
- `def _play(*args)`
- `def test_the_readme_documents_describe_and_it_describes_the_game()`
- `def test_the_readme_documents_simulate_and_it_ticks_the_requested_frames()`
- `def test_the_documented_campaign_reference_actually_wins()` - *The README says bot_campaign.json clears the warden and wins at wave 4.*
- `def test_every_documented_play_py_command_parses()` - *A documented command must at least be a command the engine accepts.*
- `def test_every_testbed_matrix_reference_points_to_a_real_test()` - *The matrix is AI-facing documentation: a renamed test must not drift.*

---

### [`tests/test_rebuild_isolation.py`](tests/test_rebuild_isolation.py)
> *Architecture safety net: a rebuild fully resets scene-scoped state.*

**Size**: `224` lines

**Functions:**
- `def _game(tmp_path)`
- `def _scene_scoped_attributes()` - *Attributes assigned inside build_scene, discovered from its own source.*
- `def _committed_scene_attributes()` - *The attribute surface of build_scene as committed at HEAD.*
- `def _attributes_of(source)` - *Attributes assigned inside build_scene in one source text.*
- `def test_build_scene_reassigns_a_large_scene_surface()` - *Sanity: the discovery works and reports the real size of the surface.*
- `def test_no_committed_scene_attribute_has_been_dropped()` - *A deleted build_scene assignment must fail, not quietly leave the list.*
- `def test_every_scene_scoped_attribute_is_reassignable_on_a_rebuild(tmp_path)` - *Each attribute build_scene owns must exist after a build and survive one.*
- `def test_a_restart_does_not_inherit_transient_scene_state(tmp_path)` - *The real path a player takes: die, press Enter, play again.*
- `def test_a_rebuild_does_not_keep_the_previous_scene_object(tmp_path)` - *A stale Scene would keep dead nodes alive in the renderer.*
- `def test_a_rebuild_produces_an_equivalent_scene(tmp_path)` - *The scene must come back the same, not merely different.*

---

### [`tests/test_recent_five.py`](tests/test_recent_five.py)
> *Progression proof: the debrief shows all five stored runs.*

**Size**: `49` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def test_debrief_shows_all_five_history_entries(tmp_path)`

---

### [`tests/test_reload_cue.py`](tests/test_reload_cue.py)
> *Audio/UI proofs: reload completion confirms readiness.*

**Size**: `67` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _reload_sim()`
- `def test_reload_completion_still_fills_mag()`
- `def test_reload_completion_gets_audio_and_caption()`

---

### [`tests/test_reload_dip.py`](tests/test_reload_dip.py)
> *Combat-feel proof: the viewmodel dips while the magazine reloads.*

**Size**: `55` lines

**Functions:**
- `def _game()`
- `def _offsets(g)`
- `def test_reload_dips_the_viewmodel_down_and_back()`
- `def test_reload_dip_returns_to_rest()`
- `def test_reload_dip_is_data_driven()`

---

### [`tests/test_repo_line_endings.py`](tests/test_repo_line_endings.py)
> *Repository hygiene: line-ending rules must agree with the committed blobs.*

**Size**: `134` lines

**Functions:**
- `def _git(*args)`
- `def _head_blobs(names)` - *Read many committed blobs in one git process.*
- `def _tracked_blobs_with_cr()` - *Tracked text files whose committed blob contains a CR byte.*
- `def test_an_lf_rule_is_only_pinned_when_the_committed_blobs_agree()`
- `def test_status_reports_no_phantom_modifications()` - *Every path git calls modified must really differ from its HEAD blob.*

---

### [`tests/test_reticle.py`](tests/test_reticle.py)
> *Combat-feel proofs: the crosshair gap tracks each weapon's hip-fire cone.*

**Size**: `112` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _drawn_gap(weapon, hitmark)`
- `def _spreads()`
- `def _expected_gap(spread_deg, config)`
- `def test_reticle_gap_follows_weapon_spread()`
- `def test_drawn_gap_matches_data_derived_expectation()`
- `def test_hitmark_expands_the_spread_gap()`
- `def test_hud_drawing_is_presentation_only()` - *draw_shooter/reticle_gap must never mutate sim state (no hash drift).*
- `def test_reticle_config_is_data_owned()`

---

### [`tests/test_save_error.py`](tests/test_save_error.py)
> *Progress proof: a failed profile save is impossible to miss.*

**Size**: `75` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _dead_game(path)`
- `def _labels(g)`
- `def test_failed_save_shows_a_debrief_warning(tmp_path)`
- `def test_unwritable_profile_parent_does_not_crash_and_warns(tmp_path)`
- `def test_successful_save_keeps_the_debrief_clean(tmp_path)`

---

### [`tests/test_save_retry.py`](tests/test_save_retry.py)
> *Progress proof: a later successful save clears the stale save warning.*

**Size**: `85` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _labels(g)`
- `def test_successful_retry_clears_the_warning(tmp_path)`
- `def test_failed_save_still_warns_until_a_retry(tmp_path)`

---

### [`tests/test_score_pop.py`](tests/test_score_pop.py)
> *Combat-feel proof: the kill bounty pops at the crosshair.*

**Size**: `63` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _game()`
- `def test_kill_event_sets_score_pop()`
- `def test_score_pop_draws_near_the_crosshair()`
- `def test_score_pop_expires()`

---

### [`tests/test_shooter.py`](tests/test_shooter.py)
> *Shooter headless proofs: move, shoot, hit, kill, die, score, determinism.*

**Size**: `295` lines

**Functions:**
- `def test_the_headless_bot_is_pure_and_its_scripts_are_exactly_n_actions()` - *kite_step claims purity; a stray RNG/sim write would break replay.*
- `def _aimed_game()`
- `def _run_manual(g, actions, dt)`
- `def test_contract()`
- `def test_data_tables()`
- `def test_movement()`
- `def test_sprint_faster()`
- `def test_first_gun_fires_hits()`
- `def test_kill_scores()`
- `def _run_kite(g, frames)`
- `def test_kite_bot_clears_wave_one()`
- `def test_kite_holds_distance_600()`
- `def test_strafe_baseline_locked()`
- `def test_player_can_die()`
- `def test_determinism()`
- `def test_frame_budget()`
- `def test_fixed_step()`
- `def test_outcome_signal()`
- `def _kite_reference_actions()`
- `def test_playtest_random_deterministic()`
- `def test_playtest_fair_with_kite_reference()`
- `def test_mixer_refusal_is_counted_not_hidden()`

---

### [`tests/test_slam_ring.py`](tests/test_slam_ring.py)
> *Enemies/bosses proofs: the warden slam radius is visible during windup.*

**Size**: `67` lines

**Classes:**
- `class _Hud`

**Functions:**
- `def _game()`
- `def _warden(windup)`
- `def test_windup_shows_a_ground_ring_at_the_slam_radius()`
- `def test_ring_is_hidden_without_a_windup()`
- `def test_ring_is_hidden_without_a_warden()`
- `def test_slam_ring_is_data_owned()`

---

### [`tests/test_spawn_cue.py`](tests/test_spawn_cue.py)
> *Audio proofs: wave spawns get a voice and a direction-less warning.*

**Size**: `39` lines

**Functions:**
- `def _game()`
- `def test_spawn_event_gets_a_voice_and_caption()`
- `def test_real_spawn_sets_the_cue_and_marker()`

---

### [`tests/test_spawn_lane.py`](tests/test_spawn_lane.py)
> *Level proofs: the spawn lane to the pickup is not blocked by the centre cover.*

**Size**: `32` lines

**Functions:**
- `def test_spawn_forward_lane_is_clear()`
- `def test_spawn_to_pickup_lane_is_clear()`

---

### [`tests/test_spawn_mark.py`](tests/test_spawn_mark.py)
> *Level/encounter proof: wave spawns leave a short marker at their origin.*

**Size**: `99` lines

**Functions:**
- `def _game()`
- `def test_spawn_event_records_the_spawn_position()`
- `def test_real_spawn_creates_a_marker_at_the_new_enemy()`
- `def test_spawn_marker_node_stands_and_expires()`
- `def test_spawn_mark_config_is_data_owned()`
- `def _with_cap(cap)`
- `def test_the_data_cap_sizes_the_pool_and_bounds_the_spawn_path()`
- `def test_the_summon_path_uses_the_same_data_cap()`

---

### [`tests/test_streak_bonus.py`](tests/test_streak_bonus.py)
> *UI proof: the streak line shows the score bonus, not just the count.*

**Size**: `44` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def test_streak_bonus_scales_and_caps()`
- `def test_streak_line_shows_the_bonus()`

---

### [`tests/test_summon_cover.py`](tests/test_summon_cover.py)
> *Enemy proof: warden escorts never materialize inside arena covers.*

**Size**: `40` lines

**Functions:**
- `def _seed_with_summon(seed)`
- `def test_summons_never_land_inside_cover()`

---

### [`tests/test_summon_mark.py`](tests/test_summon_mark.py)
> *Enemies proof: warden summons leave origin markers.*

**Size**: `47` lines

**Functions:**
- `def _game()`
- `def test_summon_positions_are_recorded()`
- `def test_boss_summon_adds_spawn_marks()`

---

### [`tests/test_summon_overlap.py`](tests/test_summon_overlap.py)
> *Enemy proof: warden escorts keep clear of the boss and each other.*

**Size**: `45` lines

**Functions:**
- `def _summon(seed)`
- `def test_summons_keep_clear_of_boss_and_each_other()`

---

### [`tests/test_surge_forfeit_cue.py`](tests/test_surge_forfeit_cue.py)
> *Audio proof: forfeiting surge on a weapon switch is announced.*

**Size**: `54` lines

**Functions:**
- `def _armed_game()`
- `def test_switching_away_from_surge_plays_a_forfeit_cue()`
- `def test_forfeit_voice_differs_from_the_switch_click()`
- `def test_normal_switch_still_names_the_weapon()`

---

### [`tests/test_switch_cue.py`](tests/test_switch_cue.py)
> *Audio proofs: switching weapons gets a voice and a visible caption.*

**Size**: `42` lines

**Functions:**
- `def _game()`
- `def test_switch_event_gets_a_voice_and_caption()`
- `def test_each_slot_has_a_distinct_switch_clip()`
- `def test_sim_emits_the_switch_event()`

---

### [`tests/test_target_dead.py`](tests/test_target_dead.py)
> *Enemies proof: the target-health bar yields to the death screen.*

**Size**: `55` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _sim(alive)`
- `def _labels(sim)`
- `def test_dead_player_has_no_target_health_bar()`
- `def test_alive_player_still_sees_the_target_bar()`

---

### [`tests/test_target_hp.py`](tests/test_target_hp.py)
> *Enemies proof: the enemy under the crosshair shows its health.*

**Size**: `70` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _sim(etype, hp, yaw)`
- `def test_aim_target_is_the_enemy_under_the_crosshair()`
- `def test_target_bar_shows_type_and_hp()`
- `def test_no_target_bar_when_facing_away()`
- `def test_warden_keeps_its_own_bar()`

---

### [`tests/test_testbed_report_mechanics.py`](tests/test_testbed_report_mechanics.py)
> *One entry point for the testbed's on-demand reports.*

**Size**: `102` lines

**Functions:**
- `def _game()`
- `def test_the_aggregate_covers_every_report_family()`
- `def test_every_composed_report_carries_its_schema()`
- `def test_the_aggregate_is_json_safe_and_reproducible()`
- `def test_every_no_argument_report_is_composed()` - *The aggregate must name every no-arg report/probe, not a hardcoded subset.*
- `def test_no_report_method_writes_to_the_sim()` - *Every on-demand report is presentation-only by construction.*
- `def test_aggregating_never_touches_the_sim()`

---

### [`tests/test_tracer_muzzle.py`](tests/test_tracer_muzzle.py)
> *Graphics proof: player tracers start at the gun muzzle.*

**Size**: `26` lines

**Functions:**
- `def test_player_tracer_starts_at_the_muzzle()`
- `def test_tracer_still_ends_at_the_hit_distance()`

---

### [`tests/test_tracer_tint.py`](tests/test_tracer_tint.py)
> *Graphics proofs: each weapon's tracer and muzzle flash carry its tint.*

**Size**: `67` lines

**Functions:**
- `def _fire_sim(wid)`
- `def test_each_tracer_records_the_firing_weapon()`
- `def test_tracer_node_uses_the_weapon_material()`
- `def test_flash_node_uses_the_weapon_material()`
- `def test_weapon_tints_are_distinct()`

---

### [`tests/test_ui.py`](tests/test_ui.py)
> *UI readability proofs: single HP/ammo source and a readable crosshair.*

**Size**: `130` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def test_hud_does_not_duplicate_hp_or_ammo()`
- `def test_crosshair_has_dark_backing_around_each_arm()`
- `def test_low_hp_edge_warning_is_still_drawn()`
- `def test_low_ammo_warning_at_quarter_magazine()`
- `def test_reload_bar_replaces_low_ammo_warning()`
- `def test_surge_timer_label_fits_inside_the_top_right_panel()`
- `def test_hud_reads_only_presentation_state()`

---

### [`tests/test_ui_center.py`](tests/test_ui_center.py)
> *UI readability proofs: top-center status lines stay centered as values grow.*

**Size**: `76` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _centered_errors(canvas, prefixes)`
- `def test_top_center_status_lines_are_centered()`
- `def test_surge_line_is_centered()`
- `def test_best_line_is_centered()`

---

### [`tests/test_viewmodel.py`](tests/test_viewmodel.py)
> *Graphics proofs: the first-person gun follows the camera and weapon.*

**Size**: `55` lines

**Functions:**
- `def _game()`
- `def test_viewmodel_exists_and_the_rig_follows_camera()`
- `def test_viewmodel_tints_with_active_weapon()`
- `def test_viewmodel_hides_on_death()`

---

### [`tests/test_viewmodel_bob.py`](tests/test_viewmodel_bob.py)
> *Combat-feel proof: the viewmodel sways with horizontal movement.*

**Size**: `71` lines

**Functions:**
- `def _game()`
- `def _offsets(g)`
- `def test_moving_viewmodel_sways_off_the_rest_pose()`
- `def test_viewmodel_bob_returns_to_rest_when_stopped()`
- `def test_viewmodel_bob_is_data_driven()`

---

### [`tests/test_viewmodel_grip.py`](tests/test_viewmodel_grip.py)
> *Combat-feel proof: the viewmodel reads as a held gun, not a floating bar.*

**Size**: `47` lines

**Functions:**
- `def _game()`
- `def _offsets(game, node)`
- `def test_viewmodel_has_a_grip_below_the_receiver()`
- `def test_grip_tints_with_the_active_weapon()`
- `def test_grip_hides_with_the_gun_on_death()`

---

### [`tests/test_viewmodel_recoil.py`](tests/test_viewmodel_recoil.py)
> *Combat-feel proof: the viewmodel punches with the existing fire kick.*

**Size**: `61` lines

**Functions:**
- `def _game()`
- `def _forward_projection(g, point)`
- `def test_firing_pulls_the_viewmodel_toward_the_player()`
- `def test_recoil_returns_to_rest_with_the_kick()`
- `def test_recoil_amount_is_data_driven()`

---

### [`tests/test_wall_depth.py`](tests/test_wall_depth.py)
> *Graphics proof: the arena boundary walls have vertical depth.*

**Size**: `41` lines

**Functions:**
- `def _game()`
- `def test_wall_pilasters_exist_and_share_one_material()`
- `def test_wall_pilasters_sit_on_all_four_walls()`

---

### [`tests/test_wall_texture.py`](tests/test_wall_texture.py)
> *Graphics proof: arena walls have a deterministic panel texture.*

**Size**: `36` lines

**Functions:**
- `def _wall_texture(game)`
- `def test_wall_material_has_a_panel_texture()`
- `def test_wall_texture_is_deterministic_and_distinct_from_covers()`

---

### [`tests/test_warden_armor.py`](tests/test_warden_armor.py)
> *Visual proof: the warden body carries an armor texture, not a flat slab.*

**Size**: `43` lines

**Functions:**
- `def _pixel(texture, x, y)`
- `def test_armor_texture_is_deterministic_and_plated()`
- `def test_warden_material_wraps_the_armor_texture()`
- `def test_live_warden_uses_the_textured_material()`

---

### [`tests/test_warden_cover.py`](tests/test_warden_cover.py)
> *Enemy proof: the warden slam is blocked by cover.*

**Size**: `43` lines

**Functions:**
- `def _slam(warden_z)`
- `def test_cover_blocks_the_warden_slam()`
- `def test_open_field_warden_slam_still_hits()`

---

### [`tests/test_weapon_enemy_tuning_bands.py`](tests/test_weapon_enemy_tuning_bands.py)
> *Survivors of the weapons/enemies mutation sweep, pinned by behaviour.*

**Size**: `116` lines

**Functions:**
- `def _aim(s, enemy)`
- `def _line(enemies)`
- `def test_every_enemy_has_coherent_shape_and_boss_cadence()` - *A zero speed/radius or a stubby body breaks movement/collision silently.*
- `def test_every_weapon_has_coherent_falloff_and_counts()` - *A falloff that begins past max range is dead data; counts must be positive.*
- `def test_scatter_fires_the_shipped_pellet_count()`
- `def test_lance_deals_the_shipped_damage()`
- `def test_lance_pierces_the_shipped_number_of_enemies()`
- `def test_pulse_falloff_applies_past_the_shipped_start_distance()`
- `def test_the_warden_uses_the_shipped_attack_cooldown()`

---

### [`tests/test_weapon_feel.py`](tests/test_weapon_feel.py)
> *Combat-feel proofs: reload duration and shot recoil are pinned.*

**Size**: `95` lines

**Functions:**
- `def _quiet_sim()`
- `def _reload_frames()` - *Empty the pulse magazine, reload, and count the frames until it is full.*
- `def _kick_after_one_shot()`
- `def test_a_pulse_reload_takes_about_one_second()` - *1.1 s at 60 Hz is 66 frames; the rifle must not become a 2.4 s slog.*
- `def test_one_shot_tilts_the_camera_by_under_a_degree()` - *kick_deg 0.6 is 0.0105 rad; doubling it doubles the climb per shot.*
- `def test_recoil_decays_back_to_rest()` - *The kick is a transient, not a permanent aim offset.*
- `def test_the_magazine_refills_to_its_declared_size()` - *Reload restores the magazine the weapon data promises, no more, no less.*

---

### [`tests/test_west_gap.py`](tests/test_west_gap.py)
> *Level proof: the west side of the jump platform is a real path.*

**Size**: `41` lines

**Functions:**
- `def _platform()`
- `def test_west_gap_is_player_width()`
- `def test_player_can_walk_behind_the_platform()`

---

### [`tests/test_win_history.py`](tests/test_win_history.py)
> *Progression proofs: campaign clears become run-history entries.*

**Size**: `165` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def _clear_game(tmp_path)`
- `def test_campaign_clear_records_a_win_run(tmp_path)`
- `def test_later_death_does_not_duplicate_the_win(tmp_path)`
- `def test_death_still_records_a_loss(tmp_path)`
- `def test_debrief_marks_wins_and_losses(tmp_path)`
- `def test_the_victory_frame_writes_the_profile_once(tmp_path)` - *A winning wave and the win run land in one atomic save, not two.*
- `def test_a_non_winning_wave_still_saves_its_bests_immediately(tmp_path)`

---

### [`tests/test_wins.py`](tests/test_wins.py)
> *Progression proofs: campaign wins are persisted and shown.*

**Size**: `81` lines

**Classes:**
- `class _Canvas`
  - Method `.__init__()`
  - Method `.rect(*args)`
  - Method `.text(*args)`
- `class _Hud`

**Functions:**
- `def test_schema_one_migrates_with_zero_wins(tmp_path)`
- `def _clear_game(tmp_path)`
- `def test_campaign_clear_persists_wins(tmp_path)`
- `def test_win_banner_shows_campaign_wins(tmp_path)`

---

### [`tests/test_wisp_bolt.py`](tests/test_wisp_bolt.py)
> *Combat-feel proof: a wisp attack draws a bolt from the wisp to the player.*

**Size**: `55` lines

**Functions:**
- `def _sim()`
- `def test_wisp_attack_traces_a_bolt_to_the_player()`
- `def test_wisp_bolt_uses_its_material()`

---

### [`tests/test_wisp_cue.py`](tests/test_wisp_cue.py)
> *Audio proof: a wisp shot gets its own warning cue.*

**Size**: `45` lines

**Functions:**
- `def _sim()`
- `def test_wisp_attack_emits_its_own_event()`
- `def test_wisp_bolt_gets_a_voice_and_caption()`

---
