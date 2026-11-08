# Shooter decisions (append-only)

## ADR-001: Hitscan-only combat v1
Date: 2026-11-02
Status: accepted
Context: 60fps + determinism on CPU, no GPU projectiles yet.
Decision: All weapons hitscan via `keystone.physics.raycast`/`ray_aabb`; no ballistic projectiles, no sphere pushout for shots.
Consequences: Sim O(n) per pellet, deterministic; beams need quaternion work deferred to tracer yaw-only boxes.

## ADR-002: Shared mesh/material payloads for auto-instancing
Date: 2026-11-02
Status: accepted
Context: Renderer groups by `id(mesh)+id(material)` into 1 instanced draw.
Decision: 3 enemy + floor/wall + tracer/flash/pickup payloads shared; never clone Material per enemy. Enemies pooled (24 Nodes), tracers pooled (16).
Consequences: ≤40 draws, <20k tris worst case; per-enemy tint via emissive would break batching, so not done.

## ADR-003: Juice is presentation + capped logic
Date: 2026-11-02
Status: accepted
Context: Juice must never cost frame time or break `--verify-determinism`.
Decision: `ParticleSystem(max=256)` logic-only; muzzle flash 60ms + tracer 80ms pooled Nodes; hit-stop 2-tick freeze (in snapshot); kick decay 8/s (in snapshot); audio pre-synthesized, ≤8 voices.
Consequences: Hash stable; HUD `FX LIVE` from `particles.alive_count()`.

## ADR-004: Fixed-seed determinism v1
Date: 2026-11-02
Status: accepted
Context: `run_simulation` does not seed RNG; `run_log` seeds global only.
Decision: `Sim(seed=1)` fixed; own `random.Random`, never global/time. `log.seed` ignored v1 (same hash for any seed, still deterministic).
Consequences: `--verify-determinism` green; varying seeds need factory-arg support later.

## ADR-005: Engine boundary
Date: 2026-11-02
Status: accepted
Context: `test_boundary.py` forbids genre code in `keystone/`.
Decision: Game lives `projects/shooter/`, imports `keystone` only; zero `projects/keystone/**` edits.
Consequences: Engine gates stay green; balance via `shooter/data/*.json` only.

## ADR-006: Bot evidence roles and proxy labeling
Date: 2026-11-03
Status: accepted
Context: Stage 4 check showed `bot_log.json` (assault 60+540) scores 39 shots / 0 hits and dies on the default map, so it cannot carry the minute-one fun claim alone.
Decision: `bot_log.json` is the movement + determinism proof (replay hash `8319b113…`); `bot_strafe.json` (strafe_fire 300: 30 shots / 2 hits / hp 84 / replay hash `10f56c10…`) is the minute-one fun proof; `shot_stage4_min30proxy.*` stays labeled proxy until a true sustained run with frame-time graphs lands.
Consequences: No new capture conventions; claims cite the log that proves them.

## ADR-007: Full-length soak evidence and budget semantics
Date: 2026-11-03
Status: accepted
Context: The sustain slice needed a surviving bot and honest frame-time/budget numbers for 108,000 frames (30 sim-minutes).
Decision: `shooter/bot.py:kite_step` (pure feedback policy: face nearest, hold 6-12 m, fire when aimed; uses the shipped ammo economy — pulse, surge pickup, scatter/lance fallback) drives `scripts/soak.py`, which records `bot_soak.json` plus derived `soak_report.json` (per-600-frame wall series, wave events, death frame, peak budgets). `plan_batches.draw_calls` is the naive per-node count (51 at synthetic 24-enemy + 16-tracer load); the gate-relevant numbers are `batched_calls`/`instanced_calls` (6 at that load, 5 at the natural 16-alive peak), per the renderer's auto-instancing.
Consequences: Soak result — waves 1-4 cleared, wave 5 reached frame 2323, death frame 2988 (wave-5 swarm), 37 kills / 6550 score / 190 shots / 144 hits; mean sim-step 0.08-0.25 ms across 180 chunks (worst single step 24.3 ms, disclosed); replay hash `ba6419e0…` identical via driver and `--replay`.

## ADR-008: Wave-5 wisp cut for the sustain loop
Date: 2026-11-03
Status: accepted
Context: The frozen kite bot died at frame 2988 in a corner trap against 8 mites + 1 brute + 3 wisps; the 5.5-speed ranged wisp bleed was the dose-limiting pressure (screened 4→2→1 deaths at 2988→3354→3885 with early hp trajectory 100/100/88 intact each time).
Decision: `shooter/data/levels.json` wave 5 goes wisp 4→1 (mites 10, brutes 4 unchanged); waves 1-4, all weapons/enemies/player tables, and all bot code frozen.
Consequences: New best — `bot_soak2.json` / `soak_report2.json`: wave-5 entry still frame 2323 at hp 64, death frame 3884 in open combat (no corner trap), 38 kills / 6650 score / 190 shots / 145 hits; replay hash `ce8156ec…` identical via driver and `--replay`; suite still 11 passed; timing/budget unchanged (flat, green).

## ADR-009: Visual pass — HUD dedupe, floor/covers, tracer orientation (no balance change)
Date: 2026-11-03
Status: accepted
Context: Screenshot audit (960×540 headless `Engine.capture` PNG+JSON pairs) showed: duplicated WAVE/SCORE (engine status + game canvas), game HP panel under the engine help bar, flat gray floor (UV-stretched texture, `checker_scale=0`), covers sharing the wall material, and fire tracers mirrored front-to-back through the camera (yaw used the camera-forward `atan2(dx,-dz)` convention on a +z-length cube, yaw-only with no pitch). Proof driver: `scripts/capture.py` (seeded routes spawn/combat/burst/pickup/death; Engine stepped with `kite_step`, never CLI-idle).
Decision: `shooter/ui.py` owns WAVE/SCORE top-center + HP/ammo panel moved above the help bar (scale-aware) + red edge flash ≤30hp + translucent death tint; `status()` shortened to `HP - weapon ammo` (`|` has no bitmap glyph and rendered as `?`); floor `checker_scale=0.5`; one shared `material.cover` (warm tan, still a single payload — instancing intact); tracer yaw `atan2(dx,dz)` + pitch `-atan2(dy,hypot)` so the beam connects muzzle to hit; flash 0.22→0.10, tracer 0.05→0.02 wide; `juice.json` tracer 0.08→0.15 s / flash 0.06→0.10 s (presentation-only, not in snapshot); pickup spot + sim trigger both read `levels.json:pickup` (value kept at 0,-6 — moving it to 3,-6 broke kite's collection and cost a full wave: death 3884→2484 — reverted); pairwise enemy separation tried and reverted for the same sustain regression (kite needs the ball's clean away-vector; stacking at peak density kept as known limitation).
Consequences: Suite 13 passed (added kite-hold-distance + strafe-baseline locks); kite600 hash `098951ee` unchanged; kite6000 reproduces baseline exactly (death 3884, wave 5, 38 kills, pickup taken); `shot_fix_{spawn,combat,burst,pickup,death}.png+json` prove every touched view; no weapon/enemy/player table numbers changed.

## ADR-010: Stage 0 triage — keep fix evidence, drop duplicates and stray logs
Date: 2026-11-03
Status: accepted
Context: Dirty tree held `shot_check_*` vs `shot_fix_*` pairs for all 5 routes, a truncated 6000-frame `soak_report.json` overwriting the 108000-frame full evidence, stray `600`/`600.bak` 6000-frame CommandLogs, and `__pycache__` dirs.
Decision: Keep `shot_fix_*` (ADR-009 cited proof; PNG bytes identical to `shot_check_*`, scene/stats/ui equal, only image path + top hash differ so `check` adds no proof) and commit it; delete `shot_check_*` duplicates; restore committed 108000-frame `soak_report.json` (death 2988, hash `ba6419e0…`); delete `600`/`600.bak` (duplicate stray logs; canonical logs stay `bot_soak.json`/`bot_soak2.json`) and `__pycache__` dirs.
Consequences: Tree clean except the landed `shot_fix_*` evidence; shooter 13 passed, keystone green, `--verify-determinism` 600 ok.

## ADR-011: Engine upgrade adoption — explicit renderer flags, outcome signal, kite reference
Date: 2026-11-03
Status: accepted
Context: Keystone added deterministic shadows/sRGB/post/bloom (all default-on) plus seeded `keystone.playtest`. Shooter inherited all four implicitly (`Scene` defaults) with no proof, and `snapshot()` had `score` but no `outcome`, so `validate_fairness` could only return `unknown`.
Decision: `shooter/data/grade.json` owns the four renderer flags as DATA; `shooter/game.py:build_scene` sets each `Scene.*.enabled` explicitly from it. `shooter/data/levels.json` gains `win_wave: 2`; `shooter/sim.py:snapshot` emits `outcome` (`lose` dead / `win` wave>=win_wave / `ongoing`). `bot_kite600.json` (kite 600 ActionStates, wave 2 / 9 kills / win) is the scripted reference DATA. `scripts/capture.py` gains `--no-*` toggles + profiler print (`draws/tris/inst/shadow_calls/map/flags`).
Consequences: Combat on-state profiler `draws=7 tris=810 inst=4 shadow_calls=17 map=1024 S1C1P1B1`, sim `18 shots/16 hits/4 kills/wave 2/hp 100` identical across all toggles (renderer never touches sim). Before/after luma: sRGB 35.57 vs 33.38, shadows 35.57 vs 35.36, post 35.57 vs 34.82, bloom 35.57 vs 34.89 — all change pixels, all kept (draws 7/40, tris 810/80000). Bots: random60 `unknown/no_reference_solution` hash `56a2f562…`, greedy300 `unknown` (score 0, random-equivalent) hash `027ea639…`, scripted kite `fair/witnessed_win:reference:181` hash `13cfa9be…` (`--expect-hash` pinned, exit 0). Death stays deterministic pinned `lose` via `test_player_can_die`, not a fair-blocker. Suite 16 passed.

## ADR-012: Sustain drift is engine-caused — no game re-tune (Stage 4 finding)
Date: 2026-11-04
Status: accepted
Context: Stage 4 re-ran the full 108000-frame sustain to temp on current code: death 2232, wave 4, 30 kills / 4750 score, hash `a6370ef2…` (mean 0.177ms, chunk_max 85.7ms, peak_alive 6) vs committed `soak_report2.json` baseline death 3884, wave 5, 38 kills / 6650 score, hash `ce8156ec…`. Wave timings diverge early (wave 3 at 717 vs 708, wave 4 at 1410 vs 1323). A `HEAD~1` baseline-code worktree on the same current engine reproduces death 2232 with identical wave events (hash `0a18b90b…`, outcome field being the only game diff), proving the drift is not from this stage's game changes (snapshot-only `outcome` + additive `win_wave` + same-True renderer flags cannot touch `step()`).
Decision: No game table changes to chase the drift — `weapons/enemies/levels` balance stays frozen per ADR-008, committed soak reports stay as historical baseline. Engine-side follow-up (physics: slopes step-up / platform carry / particle AABB / waves pushout, all landed after the sustain baseline) follows the engine prompt, never a game fork.
Consequences: Renderer adoption, fair kite verdict, and minute-one strafe lock stand; full-length sustain proof is blocked pending the engine prompt. Repro: `python scripts/soak.py 6000 <tmp-log> <tmp-rep>` (or 108000) on current code vs `soak_report2.json` — expect death 2232, not 3884.
Mechanism (bisected 2026-11-04, temp `probe.py`/`tracedump.py`, worktrees removed): last-good engine `9b4e8d5`/`3384d8a` reproduce death 3884 with baseline wave timings (180/708/1323/2323); first-bad is `2db2a78` slopes step-up (`keystone/character.py`). First divergence frame 507 at the center-cover corner (-1.17,-1.35): x -1.1709 vs -1.2211, y/z/combat identical. `_try_step_up` fires exactly 2× per 600 kite frames, 100% success. Root defect: on a wall-slide (one axis blocked, other free) it retries the FULL frame displacement from the raised position, so the free axis is applied a SECOND time (double slide); the flat-ground settle passes the rise/limit checks trivially. The commit's "defaults preserve steps" claim holds only for sims that never wall-slide. Suggested engine correction: retry only the blocked axis (or residual amounts). Game impact contained: divergence starts at frame 507, after the wave-2 win (~181) and the 300-frame strafe proof — fair verdict and minute-one evidence unaffected, re-verified green on engine HEAD `1218468` (suite 16/16).

## ADR-013: Engagement loop — variable rewards, honest near-miss, voluntary overdrive (Stage 2 revision)
Date: 2026-11-04
Status: accepted
Context: Stage 1 audit found 1.5 of 5 pillars (weak autonomy, partial competence-fairness) with variable reward, near-miss, and push-your-luck missing. Stage 2 verified the plan against CyberPulse decisions (`rewards.py` 70/20/10, `puzzles.py` near-miss, `engine.py:overdrive/break_combo/extraction_risk`, ADR-015 separate world RNG, ADR-019 one-shot SURGE cap + terminal guards) and shooter call sites (`sim.py` single RNG, `_switch` surge-away allowed, hitscan `ray_aabb`, `snapshot()->stable_hash`, `bot.py:kite_step`, `scripts/soak.py`). Ten Stage 1 assumptions were wrong (jackpot density, magnitude-vs-timing conflation, graze geometry unbuilt, almost-lost mislabeled, HP-cost ungrounded, surge tradeoff false, streak underspecified, single-stream RNG perturbation, bot return-rate claim, `aikit.py check` registration gap).
Decision: Port principles, not code, per Stage 2 §6: NEW `shooter/data/engagement.json` (schema 1: reward 0.85/0.12/×2.0/cache 0.03/+12/8s; streak +0.10 cap 0.50 break-on-hurt; near-miss ≤0.10 once/wave +6 reserve; overdrive 30 reserve/8s/×2; surge_lock true). `sim.py`: separate `reward_rng = Random(seed^0x9E3779B9)` for all engagement rolls; per-kill partition standard/critical/cache with streak bonus and overdrive doubling; single almost-won detector (post-hit survivor ≤10%) with one capped bonus per wave; CLUTCH flavor-only (never counted); voluntary `pressed=="overdrive"` with `overdrive_preview()` refusals (dead/already-on/surge-active/insufficient-ammo), 8s timer, any `hurt` breaks streak + timer; switching away from surge forfeits `surge_t`; snapshot gains `streak/best_streak/overdrive_t/rewards/near_miss/clutch/caches`. `game.py` exposes `overdrive` button; `ui.py` STREAK/OVERDRIVE/SURGE-LOCKED/NEAR-MISS lines (presentation-only); `bot.py:overdrive_step` measurement policy (kite + press when preview ok and streak≥3). Tests: NEW `tests/test_engagement.py` (12 tests: DATA validity, stream separation, 5000-roll partition, kill accounting, cap/break, near-miss honesty + cap, clutch exclusion, overdrive preview/cost/break/doubling, cache drop/pickup/expiry, surge forfeit, determinism + rewards==kills).
Consequences: Suite 28 passed (16 existing + 12 new); fair `witnessed_win` and strafe 30/2/84 pins hold; `--verify-determinism` green. Scripted proof (seeds 1-20, kite 600f): all reach wave 2, mean 8.4 kills / 1676 score / 0.35 near-miss; reward hist 0.875/0.089/0.036 over 168 kills vs stated 0.85/0.12/0.03. Overdrive policy (seeds 1-5): 3 presses/600f, scores 2390-3290 (+~60% vs kite baseline) with streak intact. Kite 6000f seed 1: wave 5, 43 kills / 9800, death tick 3577 (vs 2232 current-engine no-engagement baseline — extra cache ammo extends the run; trajectory otherwise unchanged). Ethics line holds: no HP costs, no currency, no fake near-misses (counter excludes clutch/low-HP warnings), no countdowns/logins; overdrive 8s capped, always breakable, surge lock disclosed in HUD. `aikit.py check shooter` still unregistered (pre-existing gap, out of scope). No `weapons/enemies/levels` balance touched; no engine files touched.

## ADR-014: Verification state on combined heads (game 9504b46 + engine f653b64)
Date: 2026-11-04
Status: accepted
Context: Peer engagement work (ADR-013) and engine swarm/batch fixes landed while sustain was blocked. Re-verified everything on combined current heads rather than assuming prior pins hold.
Decision: Keep `bot_kite600.json` as the CommandLog replay artifact; engine `load_actions` now rejects CommandLog-shaped files as `--script` (use `--replay` for audits, derive `{"actions": [...]}` to temp for CLI playtests — no committed duplicate). Pins re-captured, all verdicts hold: kite scripted `fair/witnessed_win:reference:181` hash `e5cfaf0e…` (same positions, score 610 vs 550 from variable rewards), random60 `unknown` hash `62cb2ed9…`, greedy300 `unknown` score 0 hash `993bb68a…`, 108k sustain death 3576 wave 5 / 43 kills / 9800 hash `ec703aa7…` (mean 0.0877ms, chunk_max 23.1ms, peak 7). Suite 28/28 green; keystone suite exit 0 on `f653b64`.
Consequences: The 2232→3576 sustain move is game-side (engagement caches/overdrive), not an engine fix — the `_try_step_up` double-slide defect stands and full-baseline proof (3884) still waits on the engine prompt. Minute-one strafe lock and fair verdict unaffected. Repro commands unchanged (outputs to temp).

## ADR-015: Wave-1 audit fixes — cache pickup, surge forfeit, mixer cap, test honesty
Date: 2026-11-04
Status: accepted
Context: Audit wave 1 (newest 10 commits) re-verified every finding with a repro before fixing. Three bugs were verified true; two nits and one vacuous test were code-evident.
Decision: (1) Cache pickup uses direct `aabb_overlap`, not the shared `TriggerTracker` — edge-triggering one shared "cache" name stranded all but one overlapping drop per frame (repro: two overlapping caches in wave 1 granted +12 once, second stranded until TTL expiry; after fix both grant same frame, +24). Surge pickup keeps the tracker (single volume, verified working). (2) Surge forfeit also zeroes `ammo["surge"]` — no input path switches back (slot1-3 only), so leftover rounds sat unreachable in the snapshot, and a programmatic re-select with ammo but no timer would arm a permanent timer-less gun (now the guard blocks it). (3) Voice cap uses public `Mixer.clear()` instead of `mixer._voices.pop(0)` — engine never drains voices, so the cap is load-bearing against unbounded growth; post-update invariant `voice_count <= 8` preserved. (4) `test_reward_stream_separate_and_reseedable` drops the `or True` tautology for real advance/reseed assertions. (5) Dead code removed: duplicate `yaw = pi` assignment, `if True` filter in `_sync_scene`.
Consequences: Suite 28/28 green; strafe 30/2/84 and kite determinism pins unchanged; no weapon/enemy/level DATA touched; no engine files touched. Left as-is (verified harmless): duplicated reload `elif` (unreachable with shipped DATA — only surge has `reload_s == 0` and surge reserve is always 0 — but load-bearing for modded tables), duplicated `_eng()` fallback defaults.

## ADR-016: Wave-2 audit — oldest history, dependency audit, docs drift, coverage
Date: 2026-11-04
Status: accepted
Context: Oldest commit (8854d3b: movement, hitscan, 3 enemies, capped juice) re-verified — all still present and pinned by tests (move/sprint/fire/hit/kill/die/score/determinism/budget). Dependency sweep: shooter + scripts + tests import stdlib and `keystone.*` only (no direct third-party deps); no packaging manifest needed (plugin loads via `--game` module path + `conftest.py` sys.path; suite green proves it).
Decision: (1) Tighten `_switch("surge")` guard to timer-only (`surge_t <= 0` blocks): the Wave-1 ammo fix exposed that a never-picked-up re-select (timer 0, ammo 0) armed a dead-end weapon — no fire, no reload, recoverable only via slots. No live caller switches to surge (pickup sets the timer directly), so behavior is unchanged except the dead end is now refused. Pinned by `test_surge_forfeit_relinquishes_ammo` (forfeit + never-taken paths). (2) Fix README drift: tree now lists `engagement.json`/`grade.json`/`test_engagement.py`/`test_audit.py`/`soak.py`/`capture.py`/evidence files; Controls rewritten to the actual live Engine map (E jump, one shot per click, slots/reload/overdrive headless-only). (3) FILED engine-side (out of scope here, ADR-005): Engine builds a plain `InputMap()` with defaults and offers no per-game bindings hook, so `fire/reload/slot1-3/overdrive/jump` action names can never arrive live — verified by code read (`app.py:57`, `input.py` defaults contain none of them). `tests/test_audit.py::test_live_input_limits_documented` pins the current boundary as a tripwire: it fails if the engine grows the hook, prompting a README update. (4) Coverage pins added (`tests/test_audit.py`, 6 tests): overlapping-cache same-frame pickup, surge forfeit + guard, voice-cap bound (12 forced voices trim to <= 8), overdrive policy press/refuse paths, HUD smoke incl. low-hp/death paths.
Consequences: Suite 34/34 green. No DATA or engine files touched. Live slots/reload/overdrive stay headless-only until the engine prompt lands a bindings hook.

## ADR-017: Wave-3 audit — post-launch fixes (dropped-SFX reset, surge/overdrive invariant, dry-bot dodge, HUD timer, reload dedupe)
Date: 2026-11-05
Status: accepted
Context: Audit of the last 3 pushes (525f6a1 gitignore, 46d7ee4 play.py launcher, b786627 dropped-SFX counting + README + license) plus full-tree re-verification (38 tests green, --verify-determinism 600 ok). Five gaps verified with repros before fixing; no DATA balance touched.
Decision: (1) `ShooterGame.build_scene` resets `dropped_sfx = 0` — a rebuild (Engine init calls build_scene) kept a stale counter while swapping in a fresh Mixer. `snapshot()` now surfaces `dropped_sfx` so soak/verify reports see drops without changing sim determinism (both runs gain the field together). (2) Surge pickup breaks an active overdrive timer (`overdrive_break`): preview already refuses overdrive while surge runs, so the reverse path must hold the invariant — previously both stacked (x2 surge). Pickup is the only surge entry (no live slot), so kite baselines are unaffected. (3) `kite_step` dry-on-every-gun now orbit-strafes instead of returning an empty ActionState — a parked bot is a dead bot; caches only spawn on kills, so this is survival-only, not income. (4) HUD surge line shows live seconds (`SURGE 7.3s - switching drops it`), mirroring the overdrive timer. (5) `sim.py` drops the dead `elif reload-pressed` auto-reload branch (subset of the standalone reload block; dead for shipped DATA since surge reserve is always 0; standalone covers modded surge tables). (6) README tree lists the tracked `.aikit/` files (guidelines/project/media/task_ledger), closing the b786627 explicit-tree drift.
Consequences: Suite 38/38 green (3 new pins: drop-reset+sparsnapshot, surge-breaks-overdrive, dry-dodge); strafe 30/2/84, kite wave-2 win, fair `witnessed_win`, and --verify-determinism 600 all hold. No weapons/enemies/levels/engagement/juice/grade numbers touched; no engine files touched.

## ADR-018: Directional damage cue (combat feel)
Date: 2026-11-07
Status: accepted
Context: The baseline `hurt` capture route (mite 2.2 m left/right/behind, first hit frame 12, hp 92) produced three pixel-identical frames: HP dropped and no HUD element said where the attack came from. The baseline played runs (idle 300: 2 hurts, hp 84; ambush 300: 3 hurts, hp 76) recorded source `null` in every hurt event. Off-screen attackers therefore damage the player with zero spatial feedback.
Decision: `Sim` records the last attacker position and time on every hurt (`hurt_from`, `hurt_t`, 0.8 s from `juice.json:hurt_cue_s`), resets both in `reset()`, and exposes `snapshot().hurt {t,x,z}`. `ui.py` draws a red dotted ring trail plus a cross at the source bearing relative to camera yaw, around the crosshair (never under the engine panels). Damage numbers, RNG, movement and all enemy/weapon DATA are untouched; the field is telemetry + presentation only. Tests: `tests/test_feedback.py` (source/timer recording, expiry, right/left/behind HUD placement, quiet HUD, deterministic hash path).
Consequences: Suite 43/43 green; `--verify-determinism --frames 1800` ok. Played-run parity vs baseline for idle/kite/strafe/ambush: same event frames, hp (84/100/84/76), kills, score, shots and hits; only the new `hurt` snapshot field moves the hash. Visual proof: three before/after pairs at 960x540, seed 1, frame 12, HP 92; each differs in exactly 292 px (0.056% of frame) inside the expected quadrant and 0 px on spawn/combat/burst/pickup/death routes. Evidence: `evidence/cycle-01.json`, images in workspace `shots/shooter-campaign/cycle-01/`.

## ADR-019: Warden boss in wave 3 (enemies/bosses)
Date: 2026-11-07
Status: accepted
Context: Post-win wave 3 repeated the same three-enemy roster (6 mites / 2 brutes / 2 wisps) and had no designed escalation; a 3000-frame kite run before the change would only meet more of the same. The enemy table had no elite, the HUD had no boss readout, and the wave-3 composition was a flat count bump.
Decision: Add `warden` DATA (hp 600, speed 1.7, slam 30 in 4.5 m, score 2000, windup 0.7 s, 2-mite escort every 7 s) to `enemies.json`; wave 3 gains one warden, waves 1-2 (the win path) and all existing tuning stay untouched. `sim.py` adds a slow advance, telegraphed `boss_windup`/`boss_slam` (via `_on_hurt` so streak/overdrive breaks work), bounded `boss_summon` mites, and wave queueing. `game.py` registers a 2.2 cube + emissive material and a glowing player-facing core that swells on windup; `ui.py` draws a named WARDEN bar. Tests: `tests/test_boss.py` (data/wave, windup/slam source, summons, kill score, queue, core, bar); `test_data_tables` now expects 4 enemies.
Consequences: Suite 50/50 green; `--verify-determinism` 1800 ok. Win path unchanged: kite 600 still wave 2 / 9 kills / 1500 / hp 100 and hash `0a107794…` identical to cycle 1. Boss-only played run (`play_run.py boss`) kills the warden at frame 507 (3 kills, 3080 score, hp 100, wave 4); natural 3000-frame campaign reaches wave 4 with 35 kills / 10535 / hp 76; close-range slam drill takes the 30 hit at frame 42 (hp 70) and the HUD cue points back at the source. Same-build wave-3 pair: no-boss vs boss differs in 60,282 px (11.63%, bbox 300,92–923,440); the current no-boss frame is pixel-identical to the pre-boss commit, and spawn/combat/burst/pickup/death routes stay 0 px. Draw budget: 6→8 calls, 1462→1666 tris at the staged load (limits 40/80k). Evidence: `evidence/cycle-02.json`, images in workspace `shots/shooter-campaign/cycle-02/`.

## ADR-020: Surge pickup beacon and label (levels)
Date: 2026-11-07
Status: accepted
Context: The wave-2 surge pickup sits at (0, 0.5, -6) behind the 1.2 m centre cover. From the spawn eye (0, 1.62, 8) the 0.6 m green cube is fully occluded: the baseline `pickup_spawn` frame (frame 182, pickup active, hp 100) shows no cue at all, and the existing `pickup` capture route had to move the camera to (3.5, 8) just to photograph the reward (ADR-009). A player who does not already know the spot has no visible reason to detour.
Decision: Presentation-only level affordance in `game.py`: a thin emissive column (cube mesh, 0.22 × 3.0 × 0.22) and a bobbing orb (sphere 0.28) above the pickup, using the existing `material.pickup`, visible only while `sim.pickup_active`; `ui.py` adds a `SURGE PICKUP READY` label when the player is within 18 m and no boss bar is showing. The pickup spot, trigger volume, ammo economy and sim state are untouched. Tests: `tests/test_levels.py` (hidden at wave 1, visible/positioned/shape while active, hidden after take, label distance gate, trigger parity).
Consequences: Suite 54/54 green; determinism 1800 ok; kite 600 hash still `0a107794…`. Baseline vs after pickup run: same frame 121, same hash `0cfe8193…`, same events and final (`surge_t` 10.0, taken true) — the beacon is presentation only. Visual pair at 960×540 seed 1 frame 182: 2,342 changed px (0.45%, bbox 375,92–911,291, mean luma 31.04→31.59); spawn/burst/death routes stay 0 px, while combat/pickup routes intentionally show the beacon. Draw budget 5→7 at the staged spawn view (limits 40/80k). Evidence: `evidence/cycle-03.json`, images in workspace `shots/shooter-campaign/cycle-03/`.

## ADR-021: Single-source HP/ammo and crosshair contrast (UI readability)
Date: 2026-11-07
Status: accepted
Context: Every baseline capture showed HP/ammo twice: engine status top-left (`HP 100 - PULSE 30/120`) and the game's bottom-left panel (`HP 100` / `PULSE 30/120`). The white crosshair also disappeared against the white muzzle-flash cube in the burst route; dark floor and bright flash cover the same 2 px arms.
Decision: Remove the game's bottom-left HP/ammo panel (the engine status already owns that fact; wave/score/streak stay in the game layer). Add a 2 px dark backing behind each crosshair arm and the centre pip, drawn before the bright core, so contrast survives any background. The low-HP edge warning, damage cue, boss bar, pickup label and death tint are unchanged. Tests: `tests/test_ui.py` (no duplicate HP/ammo, five dark backings plus five bright cores, low-HP edge warning, HUD purity) and the updated `test_draw_shooter_smoke` pin.
Consequences: Suite 58/58 green; determinism 1800 ok. Kite 600 hash `0a107794…` and strafe 300 hash `973276f5…` are identical to the pre-change runs, so the HUD remains presentation-only. Visual pairs at 960×540 seed 1 same route/frame: every route changes 15,856 px (bottom-left panel plus crosshair; crosshair crop alone 256 px); burst crosshair crop dark pixels 538→758 and bright pixels 375→319, measured on the white-flash frame; spawn bottom-left panel mean luma 29.21→31.95 (dark panel removed). Draw counts and triangles are unchanged. Evidence: `evidence/cycle-04.json`, images in workspace `shots/shooter-campaign/cycle-04/`.

## ADR-022: Arena floor grid and lit trim (graphics and effects)
Date: 2026-11-07
Status: accepted
Context: The baseline arena was a near-black checker floor with gray walls and brown covers; spawn mean luma 30.35/255, edge density 2.657, and no geometry separating cover tops or the wall line from the background. Covers read as flat blocks and the floor vanished under enemies/tracers.
Decision: Replace the 64-px checker with a deterministic 128-px `floor-grid` texture (dark checker base, 2-px lit grid lines, name-stable) and lift the lighting (ambient 0.30/0.32/0.38, directional 1.25, point 0.45, fog 0.006, warmer covers). Add ten presentation-only trim nodes (four wall lines + six cover caps) sharing one mesh/material pair so auto-instancing keeps one batch. No sim, collider, weapon, enemy or level DATA change.
Consequences: Suite 63/63 green; determinism 1800 ok; kite 600 (`0a107794…`), strafe 300 (`973276f5…`) and boss (`1b602735…`) hashes are identical to the pre-change runs, so the pass is render-only. Same-route visual pairs at 960×540 seed 1: spawn mean luma 30.35→34.68 (edge density 2.657→3.066), combat 37.02→40.03, boss 33.89→38.33; changed pixels 270k–306k (52–59%) because the floor/lighting is global. Draw calls 3→4 spawn and 8→9 boss, triangles 110→218 and 1666→1774 (limits 40/80k); instanced calls 5→6 at the boss load. Evidence: `evidence/cycle-05.json`, images in workspace `shots/shooter-campaign/cycle-05/`.

## ADR-023: Boss and engagement audio cues + visible captions (audio cues)
Date: 2026-11-07
Status: accepted
Context: The event map only voiced shoot/hit/kill/pickup/wave/hurt. A baseline close-range slam run (43 frames, hp 100→70, hash `a5e66d40…`) had `boss_windup` at frame 1 and `boss_slam` at frame 43 but produced exactly one voice (`hurt` at frame 43); boss, overdrive, cache, reload, near-miss, streak-break and death events were silent. Silent boss telegraphs make the visual swell the only warning.
Decision: Add deterministic clips for boss windup/slam/summon/down, overdrive start/end, cache, near-miss, reload, streak-break and death; map each sim event to its voice and a short bottom-centre caption (red for danger, amber otherwise). Emit `boss_down` from the warden kill path; expose `set_clip_hook` so evidence tooling can observe voices without touching a private attribute. Shorten the surge timer line to stay inside the top-right stats panel. Tests: `tests/test_audio.py` (boss windup/slam voices+captions, pickup cue, boss_down, caption expiry, clip hook) plus the updated surge-label fit pin.
Consequences: Suite 69/69 green; determinism 1800 ok. The slam play run before/after has the same frames (43), HP (70) and hash (`a5e66d40…`), but audio events go from `hurt` only to `boss_windup` (frame 1), `boss_slam` + `hurt` (frame 43); peak voices 3, dropped 0. Boss play run: 120 voices, peak 8, dropped 0; pickup run: one `pickup` voice. Caption screenshot pair: windup 9,696 changed px (caption + AUDIO 1 VOX line, bbox 390,164–947,459), slam 4,116 px; spawn stays 0 px. `scripts/audio_probe.py` renders 12 cues to `cues.wav` and a waveform+spectrogram sheet: boss_windup 0.35 s peak 1.0, boss_slam 0.30 s peak 0.9999, boss_down 0.45 s peak 1.0, overdrive 0.22 s peak 1.0, pickup 0.12 s peak 1.0. Evidence: `evidence/cycle-06.json`, images/audio in workspace `shots/shooter-campaign/cycle-06/`.

## ADR-024: Versioned run profile, BEST line and death debrief (progression and saves)
Date: 2026-11-07
Status: accepted
Context: Every launch created `Sim(seed=1)` with no persisted bests, run count or last run; the death screen only said `YOU DIED`. The project guideline requires a versioned state contract, and PRINCIPLE-013 requires atomic state writes with backup/lock/recovery. Evidence scripts also had to avoid touching a real player save while still exercising the run path.
Decision: Add `shooter/profile.py`: schema 1 `{runs, best_score, best_kills, best_wave, best_streak, last_run}`; schema 0 migrates, an unsupported schema raises without modifying the file (the game then disables persistence for that session), and corrupt JSON is quarantined while `.bak` is tried. Saves use Keystone's temp+fsync+atomic-replace writer with `.bak` plus a 30 s advisory lock and graceful `OSError` handling. `ShooterGame` records a best at wave clear and a full run (including `RUN OVER` debrief data) on death; `draw_ui` shows `BEST <score>` and a centered debrief with score/kills/wave/best streak/time plus `NEW BEST`. Evidence scripts and the suite use throwaway profile paths (conftest autouse fixture; capture/play/soak/audio probes use temp dirs); `saves/` is git-ignored.
Consequences: Suite 77/77 green; determinism 1800 ok; aikits 4/4. Staged death run before/after: same frame (1), HP (0), score (1500) and snapshot hash `f8cd9e28…`; after records `runs=1`, `best_score=1500`, `last_run={score:1500, kills:9, wave:2, best_streak:4, outcome:lose}` with `save_errors=0`; before has no profile. Same-state screenshot pair at 960×540: 38,516 changed px (7.43%, bbox 290,16–669,361; 38,000 px in the debrief panel, 516 px in the BEST line), mean luma 52.18→48.31 because the panel is dark. Spawn/combat frames with an empty throwaway profile stay pixel-identical. Evidence: `evidence/cycle-07.json`, images in workspace `shots/shooter-campaign/cycle-07/`.

## ADR-025: Boss-clear campaign milestone and CAMPAIGN CLEAR banner (progression)
Date: 2026-11-07
Status: accepted
Context: `win_wave: 2` made `snapshot.outcome` return `win` at the start of wave 2 — roughly three seconds into a run — while the wave-3 Warden boss sat outside the campaign and no HUD surface ever announced a win. The 2400-frame kite reference clears the boss and reaches wave 4 at frame 2340 (29 kills / 9220 / hp 94 / replay hash `88c3e673…`).
Decision: Move `win_wave` to 4 so the campaign is waves 1-3 with the Warden as the finale. `ShooterGame` sets `campaign_cleared` + a 4 s `campaign_clear_t` when the live wave reaches `win_wave`, draws a centered `CAMPAIGN CLEAR` banner, and adds `CAMPAIGN CLEARED` to the death debrief. Add `bot_campaign.json` (2400-frame CommandLog, verified through `--replay`) and switch the fairness/outcome tests to the 2400-frame reference. No enemy/weapon/level counts or boss tuning change; only the win threshold and its feedback.
Consequences: Suite 78/78 green; determinism 1800 ok; fairness verdict `fair` with `witnessed_win:reference:2340`; `test_outcome_signal` reaches wave 4 with `outcome="win"` and `campaign_cleared=True`; kite 600 now reports `ongoing` at wave 2 (hash moves only because `snapshot.outcome` changed). Visual pair at 960×540 seed 1, staged wave-3 boss kill: 20,160 changed px (3.89%, bbox 300,138–659,193; exactly the 360×56 banner), mean luma 37.43→38.18. Campaign play run: wave 4, 29 kills, 9220 score, hp 94, `outcome=win`. Evidence: `evidence/cycle-08.json`, images in workspace `shots/shooter-campaign/cycle-08/`.

## ADR-026: Low-ammo warning and reload bar (UI readability)
Date: 2026-11-07
Status: accepted
Context: Baseline low-mag (3/30) and mid-reload (0/30, reload_t 0.55) frames showed only the small engine-status numbers in the top-left; there was no near-crosshair clue and no reload progress. A player looking at the arena had to read a distant number to know the magazine was nearly dry.
Decision: In `draw_shooter`, when alive and not reloading, show a compact `LOW AMMO` panel below the crosshair at `mag <= mag_size // 4`; while `reload_t > 0`, replace it with a 120-px reload progress bar and `RELOADING` label (progress from the weapon's `reload_s`). Exact counts remain in the engine status line; the HUD layer is glanceable only. Tests: `tests/test_ui.py` quarter-mag threshold, reload bar/replacement, label fit.
Consequences: Suite 80/80 green; determinism 1800 ok. Kite 600 hash `49111053…` and strafe 300 hash `973276f5…` are unchanged from cycle 8, so the layer is presentation-only. Visual pairs at 960×540 seed 1: low-ammo frame 2,420 changed px (bbox 425,300–534,321, mean luma 34.65→34.40), reload frame 1,816 px (bbox 418,302–541,327, mean luma 34.66→34.65). Draw/triangle counts are unchanged. Evidence: `evidence/cycle-09.json`, images in workspace `shots/shooter-campaign/cycle-09/`.

## ADR-027: Non-lethal hit flinch + flash (combat feel)
Date: 2026-11-08
Status: accepted
Context: Baseline first-hit frames showed the mite unchanged: the only feedback was the crosshair hitmark, tracer and impact particles. A 7-frame-after-hit capture (muzzle flash expired, hp 18) still rendered the same orange sphere, so body shots gave no target reaction.
Decision: Add `hit_t` (0.25 s, `juice.hit_flinch_s`) on non-lethal hits and decrement it in `_step_enemies`. `game._sync_scene` applies a short squash (`hit_flinch_scale` 0.28 × remaining fraction), pushes the rendered enemy away from the player (`hit_flinch_push` 0.12), and uses a shared `material.enemy_hit` while the first 40% of the timer runs. Damage, hitboxes, movement, AI and the snapshot are untouched; all tuning stays in `juice.json`. Tests: `tests/test_combat_feel.py` (timer set, expiry with unchanged hp, scene squash/push/material and revert).
Consequences: Suite 83/83 green; determinism 1800 ok. Kite 600 hash `49111053…` and strafe 300 hash `973276f5…` are identical to cycle 9 (31 and 2 hits respectively), so the sim path is unchanged. Same-route first-hit pair at 960×540 seed 1, frame 8, hp 18: 3,839 changed px (0.74%, bbox 432,314–515,381; the mite is white-hot and squashed), mean luma 35.50→36.03; draw calls stay 7. Evidence: `evidence/cycle-10.json`, images in workspace `shots/shooter-campaign/cycle-10/`.

## ADR-028: Enemy cover collision, slide-around and spawn guard (enemies/bosses)
Date: 2026-11-08
Status: accepted
Context: The player and hitscan rays collided with the six arena covers, but `_step_enemies` moved every mite/brute/wisp/warden straight toward the player with only an arena clamp. A 40-frame staged crossing had the mite at `(-0.33, 0.81)`, inside the centre cover AABB, visibly protruding through its front face; a spawn sweep also placed a mite at `(5.00, -4.59)`, inside the right cover. Cover was decorative to enemies.
Decision: Store `cover_boxes` in reset; add `_enemy_blocked_at(x,z,radius)` and `_move_enemy` with a heading sweep (direct, ±30°, ±60°, ±90°, ±120°, 180°) so an enemy follows a cover edge instead of oscillating on its face. Apply it to all four enemy movement branches, and reject spawn points inside a cover (fallback `(0, -18)`). The wisp LOS and hitscan rules are unchanged. The campaign reference is re-recorded with the new movement: `bot_campaign.json` is now 3000 frames (win at wave-4 entry, 32 kills / 11955 / hp 2), and the fairness/outcome tests use 3000.
Consequences: Suite 86/86 green; determinism 1800 ok; fairness `fair/witnessed_win:reference:2627`. Staged same-state pair at 960×540 seed 1, frame 40: before the mite is embedded in the cover; after it is beside it, 3,116 changed px (0.60%, bbox 387,295–485,353), mean luma 34.75→34.88. Play run `kite 3000` reaches wave 4 with `outcome=win`, 32 kills, 11955, hp 2, hash `9b70e372…`; `strafe 300` hash `973276f5…` is unchanged. Evidence: `evidence/cycle-11.json`, images in workspace `shots/shooter-campaign/cycle-11/`.

## ADR-029: Jumpable rear-left platform (levels)
Date: 2026-11-08
Status: accepted
Context: Every cover was 1.2 m or taller, while the jump apex is about 1.08 m; `E`/`up` could never land on anything. The 86-test suite had no surface-jump proof, and the arena had no vertical landmark. The baseline test run (`tests/test_levels_platform.py` on commit `a0b40cb`) failed both the jumpable-surface check and the landing check (player stayed at y 0.9001 / z 19.15).
Decision: Add one 6×6×0.7 m platform at `(-16, 15)` to `levels.json`, rendered with a cool `material.platform` and no cover-trim cap. It participates in the existing cover collision (player can jump/land; enemies path around) and the spawn guard. Add `tests/test_levels_platform.py` (jumpable data + a scripted jump that lands at y 1.6001, z 12.879) and `play_run.py platform`; capture route `platform` stages the same approach view before/after.
Consequences: Suite 88/88 green; determinism 1800 ok; fairness remains `fair/witnessed_win:reference:2627`; `kite 3000` hash `9b70e372…` and `strafe 300` hash `973276f5…` are identical to cycle 11, so the corner platform does not move the measured combat path. Visual pair at 960×540 seed 1, approach view: 132,320 changed px (25.52%, bbox 58,92–901,497; the platform fills the rear-left corner), mean luma 40.80→49.66; draws 3→4, triangles 50→62. Scripted `platform` run: before no landing (y 0.9, frame 120); after lands at y 1.6 / z 12.379 at frame 28. Evidence: `evidence/cycle-12.json`, images in workspace `shots/shooter-campaign/cycle-12/`.

## ADR-030: Typed kill feed (UI readability)
Date: 2026-11-08
Status: accepted
Context: The sim emitted a bare `kill` event, and the HUD only changed the distant score/streak numbers; a kill did not say what died or what it was worth. A first-kill frame showed score 110 / streak x1 but no event line. There was no test for kill telemetry.
Decision: Append `kill:<etype>:<total>` after the existing `kill` event (the plain event still drives audio and legacy checks). `ShooterGame` keeps the last four feed entries for 2.5 s and draws `MITE +110` under the engine status panel, with warden entries in danger red. The feed is presentation-only; the snapshot and damage/score math are untouched. Tests: `tests/test_kill_feed.py` (typed event/amount, first kill feed, draw, 3 s expiry).
Consequences: Suite 90/90 green; determinism 1800 ok. Kite 600 hash `8872be74…` and strafe 300 hash `973276f5…` are identical to the pre-feed cycle-12 worktree, proving the feed adds no sim path. Same first-kill pair at 960×540 seed 1, frame 8: 424 changed px (0.08%, bbox 16,104–121,117; just the `MITE +110` line), mean luma 36.20→36.39; draws stay 6, triangles 294. Evidence: `evidence/cycle-13.json`, images in workspace `shots/shooter-campaign/cycle-13/`.

## ADR-031: Off-axis, small muzzle flash (graphics and effects)
Date: 2026-11-08
Status: accepted
Context: The muzzle flash was a 0.10 cube at 0.70 m directly on the eye/aim line. The first-shot capture at 960×540 showed a large white block covering both the crosshair and the mite at 6 m; the target was invisible during the 0.10 s flash. No test covered flash placement or size.
Decision: Move the flash to `forward 0.95 / right 0.16 / down 0.12` and scale it to `0.055`, all in `juice.json` DATA. The sim writes the offset position; the game reads the scale. The existing point-light boost and flash lifetime are unchanged. Tests: `tests/test_muzzle.py` (lateral offset/down/forward distance, node scale).
Consequences: Suite 92/92 green; determinism 1800 ok. Kite 600 hash `8872be74…` and strafe 300 hash `973276f5…` are identical to the pre-flash cycle-13 worktree, proving the change is presentation-only. Same first-shot pair at 960×540 seed 1, frame 1: 4,343 changed px (0.84%, bbox 448,290–557,359; the big centre flash becomes a small down-right flash and the mite stays visible), mean luma 37.09→36.96; draws stay 8, triangles 586. Evidence: `evidence/cycle-14.json`, images in workspace `shots/shooter-campaign/cycle-14/`.

## ADR-032: Overdrive-denial voice and caption (audio cues)
Date: 2026-11-08
Status: accepted
Context: Pressing overdrive with no pulse reserve emitted `overdrive_denied:insufficient_ammo`, but the game ignored it. The denied baseline run had reserve 0, no caption, and only the wave-clear voice (`audio=1`); the input looked broken. The other denial reasons (`surge_active`, `already_on`) were silent too.
Decision: Add a deterministic `overdrive_denied` square(90 Hz, 0.14 s) clip and handle the `overdrive_denied:<reason>` prefix in `_play_event`: insufficient ammo shows `OVERDRIVE: NEED <cost> AMMO`, surge shows `OVERDRIVE BLOCKED BY SURGE`, already-on shows `OVERDRIVE ALREADY ON`, and the clip plays for all reasons. Captions use the danger color. The sim event/reserve/damage state is untouched. Tests: `tests/test_denial.py` (voice/caption and snapshot parity with idle input); audio probe now reports 13 cues.
Consequences: Suite 94/94 green; determinism 1800 ok. The denied play run before/after has the same hash `8ea7057f…` and reserve 0; before `audio=0`/empty cue, after `audio=1`/`OVERDRIVE: NEED 30 AMMO`, peak 1, dropped 0. Visual pair at 960×540 seed 1, frame 1: 12,820 changed px (2.47%, bbox 330,164–947,459; caption + AUDIO 1 VOX status line), mean luma 34.64→34.64. Clip report: 0.14 s, peak 1.0. Evidence: `evidence/cycle-15.json`, images/audio in workspace `shots/shooter-campaign/cycle-15/`.

## ADR-033: Persist campaign wins and show them on the clear banner (progression/saves)
Date: 2026-11-08
Status: accepted
Context: Campaign clears were visible for four seconds but not persisted: `_record_progress` saved bests at the wave event, then `campaign_cleared` set only an in-memory flag. A player who quit after the Warden had no record of the win. The profile schema was 1 with no wins field, and a schema-1 file had to keep loading.
Decision: Bump the profile to schema 2 with a non-negative `wins` count; schema 1 migrates by adding `wins: 0` without losing bests/runs/last run, schema 0 migrates through 1 to 2, and unsupported schemas still refuse without touching the file. On the first campaign clear, `_record_campaign_clear` increments `wins` and saves atomically. The clear banner grows to 74 px and adds `CAMPAIGNS WON <n>`. Tests: `tests/test_wins.py` (schema-1 migration, persisted win, banner line) plus the updated schema-0 pin.
Consequences: Suite 97/97 green; determinism 1800 ok. Before/after campaign runs have the same hash `9b70e372…`, 32 kills / 11955 / hp 2; before profile `wins=0`, after `wins=1` (persisted through `ProfileStore.load`). Visual pair at 960×540 seed 1, staged wave-3 boss kill: 6,732 changed px (1.30%, bbox 300,190–659,211; the third banner line and taller panel), mean luma 37.93→38.29. Evidence: `evidence/cycle-16.json`, images in workspace `shots/shooter-campaign/cycle-16/`.

## ADR-034: Dry-fire feedback and rate limit (combat feel)
Date: 2026-11-08
Status: accepted
Context: The low-ammo panel warned before the fact, but a click on 0/0 was completely silent: no sim event, no voice, no caption. A held auto trigger also had no rate limit for the empty case, so a naive cue would spam the mixer every frame.
Decision: In the firing block, when the magazine and reserve are both empty, emit `dry_fire` and set `dry_t = 0.25 s` (`juice.dry_fire_cd_s`), decremented with the other timers. The game plays a 0.04 s noise click and shows `NO AMMO` in danger red. `dry_t` is presentation/rate-limit state and is not in the snapshot; shots/hits/score stay zero. Tests: `tests/test_dry_fire.py` (event on first click, suppression, repeat after cooldown, voice/caption, no shots/score).
Consequences: Suite 100/100 green; determinism 1800 ok. Dry play-run hash `d33f43e4…` is identical before/after; before `audio=0`/empty cue, after `audio=1`/`NO AMMO`, peak 1, dropped 0. Visual pair at 960×540 seed 1, frame 1: 7,828 changed px (1.51%, bbox 426,164–947,459; caption + AUDIO 1 VOX status line), mean luma 34.37→34.42. Clip report: 0.04 s, peak 0.9999. Evidence: `evidence/cycle-17.json`, images/audio in workspace `shots/shooter-campaign/cycle-17/`.

## ADR-035: Brute melee line-of-sight check (enemies/bosses)
Date: 2026-11-08
Status: accepted
Context: Mite/brute melee only checked distance. A brute at `(-6, 6.2)` and the player at `(-6, 3.8)` are on opposite sides of the 1 m-thick cover at `(-6, 5)`, but the 2.4 m gap is inside the 2.5 m slam range: the baseline first step dealt 20 damage through the cover (`hp 80`, `hurt`). Wisp attacks already had an inline LOS ray; brute did not.
Decision: Add `_enemy_has_los` (enemy chest -> player eye against `self.colliders`, with the existing 0.3 m skin) and require it for the brute slam. The open-field slam still lands (tested at `(10, 2)`), and the wisp's existing LOS path is unchanged. `tests/test_enemy_los.py` pins cover-blocked and open-field cases.
Consequences: Suite 102/102 green; determinism 1800 ok; fairness `witnessed_win:reference:2627` still holds. The cover scenario is hp 100 with no `hurt` after the fix vs hp 80/hurt before; same-frame visual pair at 960×540 seed 1, frame 1: 7,216 changed px (1.39%, bbox 60,12–947,231; HP line, damage cue, and AUDIO VOX line), mean luma 41.16→40.95. Full `kite 3000` hash `9b70e372…` and `strafe 300` hash `973276f5…` are unchanged. Evidence: `evidence/cycle-18.json`, images in workspace `shots/shooter-campaign/cycle-18/`.

## ADR-036: Open the spawn-to-pickup lane (levels)
Date: 2026-11-08
Status: accepted
Context: The player spawns at `(0, 0.9, 8)` facing -Z. The centre cover at `(0, 0)` sits on the line to the wave-2 pickup at `(0, 0.5, -6)`; the eye-level forward ray clears the 1.2 m cover, but the pickup ray hits it at 7.02 m, so the first view is a brown box and the reward is hidden. The baseline `test_spawn_lane.py` failed the pickup-lane assertion (`distance 7.022` through a 14.045 m ray).
Decision: Move the centre cover from `(0, 0)` to `(2.5, 0)` (same size/height). The spawn lane and the pickup line are now clear; the cover remains a right-of-centre obstacle for the player, enemies and bullets. Re-record the 3000-frame campaign reference (`bot_campaign.json`, new hash `945e3fdd…`, win at wave 4 / frame 2369) and update the strafe baseline to its new deterministic 30 shots / 0 hits / hp 92. Tests: `tests/test_spawn_lane.py` (forward and pickup rays), `test_strafe_baseline_locked` updated.
Consequences: Suite 104/104 green; determinism 1800 ok; fairness `fair/witnessed_win:reference:2369`. Same-frame spawn view pair at 960×540 seed 1: 15,214 changed px (2.93%, bbox 402,283–658,350; centre cover moves out of the crosshair lane), mean luma 34.69→34.74. `kite 3000` reaches wave 4 with `outcome=win`, 32 kills / 10135 / hp 82, hash `945e3fdd…`; `strafe 300` is 30/0/hp 92, hash `14a48660…`. Evidence: `evidence/cycle-19.json`, images in workspace `shots/shooter-campaign/cycle-19/`.

## ADR-037: Numeric warden HP on the boss bar (UI readability)
Date: 2026-11-08
Status: accepted
Context: The warden bar showed only a red fill and the `WARDEN` label. At 300/600 the player could see roughly half but had no exact remaining health, making overdrive/critical decisions guesswork. No test pinned the readout.
Decision: Draw `hp/max_hp` right-aligned beside the `WARDEN` label using `keystone.ui.font.text_width`; the fill bar, colors and positions are unchanged. Tests: `tests/test_boss_hp.py` (300/600 and 150/600 readouts).
Consequences: Suite 106/106 green; determinism 1800 ok. Boss play run before/after has the same hash `81f05265…` (507 frames, wave 4, 3 kills, 3080, hp 100), so this is presentation-only. Same half-health boss pair at 960×540 seed 1: 456 changed px (0.09%, bbox 538,98–619,111; the new numbers), mean luma 36.13→36.34; draws stay 6, triangles 422. Evidence: `evidence/cycle-20.json`, images in workspace `shots/shooter-campaign/cycle-20/`.

## ADR-038: First-person viewmodel with weapon tint (graphics and effects)
Date: 2026-11-08
Status: accepted
Context: The game had a crosshair, tracers and a floating muzzle flash but no weapon body; the first-person frame read as an empty camera. A player had no visual confirmation of the equipped gun beyond the small status text.
Decision: Add two shared-cube viewmodel nodes (body + barrel) driven by `juice.viewmodel` DATA: forward 0.62, right 0.21, down 0.17, body 0.055×0.055×0.26, barrel 0.030×0.030×0.26. They follow camera yaw/pitch (`right.cross(forward)` for up), tint with `material.gun_{pulse,scatter,lance,surge}`, and hide on death. Purely presentation; no sim state. Tests: `tests/test_viewmodel.py` (exists/follows yaw, weapon tint, death hide).
Consequences: Suite 109/109 green; determinism 1800 ok. Kite 600 hash `4fe640c5…` and strafe 300 hash `14a48660…` are identical to the cycle-20 worktree, proving the viewmodel adds no sim path. Spawn pair at 960×540 seed 1: 4,783 changed px (0.92%, bbox 551,92–911,411; gun lower-right plus DRAW/TRI status line), mean luma 34.74→35.14; combat pair: 6,839 px (1.32%, bbox 526,92–899,419), mean luma 46.51→46.60. Draws 4→5 spawn / 8→9 combat, triangles 218→242 / 584→608. Evidence: `evidence/cycle-21.json`, images in workspace `shots/shooter-campaign/cycle-21/`.

## ADR-039: Reload-completion voice and caption (audio cues)
Date: 2026-11-08
Status: accepted
Context: The reload bar filled and disappeared on completion, and the sim emitted a bare `reloaded` event, but the game ignored it. The baseline completion frame showed `PULSE 30/90` with no caption and `audio=0`; the player had to watch the bar vanish to know the gun was ready.
Decision: Add a deterministic `reloaded` sine(980 Hz, 0.06 s) clip and handle the `reloaded` event: play it at 0.45 gain and show `RELOADED` in the positive accent caption. The reload fill/timing/ammo economy are unchanged. Tests: `tests/test_reload_cue.py` (mag 30/reserve 90 parity, voice/caption, full ammo); the audio probe now reports 15 cues.
Consequences: Suite 111/111 green; determinism 1800 ok. The reload play run before/after has the same hash `d7eb253d…`, ammo 30/reserve 90 and reload_t 0; before `audio=0`/empty cue, after `audio=1`/`RELOADED`, peak 1, dropped 0. Same completion pair at 960×540 seed 1, frame 1: 8,140 changed px (1.57%, bbox 420,164–947,459; caption + AUDIO 1 VOX line), mean luma 35.13→35.24. Clip report: 0.06 s, peak 0.9994. Evidence: `evidence/cycle-22.json`, images/audio in workspace `shots/shooter-campaign/cycle-22/`.

## ADR-040: Bounded run history in the profile (progression/saves)
Date: 2026-11-08
Status: accepted
Context: The profile retained only `last_run`; after a second run the previous result was gone, so there was no way to compare recent sessions or show a run history in the debrief. The schema was 2 and old saves had to keep loading.
Decision: Bump to schema 3 with a newest-first `history` of at most five cleaned run records (score/kills/wave/best_streak/time_s/outcome). Schema 2 migrates with `history: []`; schema 1 still adds `wins` and then history; schema 0 goes through the chain. `_finish_run` appends the run, trims to five and saves with the existing atomic writer. The debrief draws `RECENT <scores>` from the profile (up to three). Tests: `tests/test_history.py` (schema-2 migration, six deaths keep five newest, debrief line); schema-0/1 pins updated.
Consequences: Suite 114/114 green; determinism 1800 ok. The death play run before/after has the same hash `f8cd9e28…`, 1 frame, score 1500, hp 0; before history `[]`, after `[1500]` persisted through `ProfileStore.load`. Same death/debrief pair at 960×540 seed 1 (profile seeded with 980/740 plus the current 1500): 8,844 changed px (1.71%, bbox 290,356–669,383; the RECENT line and taller panel), mean luma 48.31→47.21. Evidence: `evidence/cycle-23.json`, images in workspace `shots/shooter-campaign/cycle-23/`.

## ADR-041: Spread-aware reticle (combat feel)
Date: 2026-11-08
Status: accepted
Context: The crosshair half-gap was hardcoded at 8 px. Weapon spread is DATA: lance 0.1 deg, pulse 1.2, surge 2.5, scatter 4.5. The fixed gap matched the pulse but claimed 1/3.75 of the scatter cone and 12x the lance cone; the baseline test measured 8 px for all four.
Decision: Move the reticle tuning to `juice.json:reticle` (8 px gap at the pulse's 1.2 deg reference, a 3-40 px clamp, 4 px hitmark expansion) and add `ui.reticle_gap(sim)`, which scales the gap by `tan(weapon.spread_hip_deg) / tan(reference)`. `draw_shooter` uses it for the arm positions and keeps the hit color/backing. No sim, hitbox, spread or damage change.
Consequences: Suite 118/118 green (four new reticle tests); determinism 1800 ok; aikit 4/4. Drawn gaps are pulse 8, scatter 30, surge 17, lance 3; hitmark adds 4. The same staging pair changes only the crosshair: scatter 576 px, surge 448, lance 256, pulse control 0; mean luma moves by <=0.01. Played `kite 600` (hash `4fe640c5…`, 10 kills/1950/hp 100) and `strafe 300` (hash `14a48660…`, 30/0/hp 92) are identical before/after, and the live kite capture is pixel-identical. Evidence: `evidence/cycle-24.json`, images in workspace `shots/shooter-campaign/cycle-24/`.

## ADR-042: Vertical melee reach (enemies/bosses)
Date: 2026-11-08
Status: accepted
Context: Melee attacks used horizontal distance only. A 1.0 m mite beside the 0.7 m platform bit a player standing on top for 8 damage (hp 92 at frame 1; four bites over 200 frames left hp 68), so the jumpable platform provided no protection from short enemies. The baseline test failed exactly that case.
Decision: Add DATA `reach_up` (mite 0.30, brute 0.45, warden 0.45) and `Sim._in_melee_reach`, which compares the player's body origin (foot level) with the enemy's top plus its reach. Gate the mite bite, brute slam and warden slam; the wisp's ranged LOS path is untouched. Open-floor bites and the brute's existing cover LOS rule are unchanged.
Consequences: Suite 122/122 green (four new reach tests); determinism 1800 ok; aikit 4/4 after restoring the README evidence entry. `highground 200` goes from hp 68 / 4 hurts / hash `e30d3110…` to hp 100 / 0 hurts / hash `a605d8b4…`; `strafe 300` (`14a48660…`) and `kite 600` (`4fe640c5…`) keep their ground-path hashes. The platform pair at 960x540 seed 1 changes 7,276 px (1.41%, bbox 60,12-947,231), mean luma 73.41→73.38; the played capture changes 7,256 px. Evidence: `evidence/cycle-25.json`, images in workspace `shots/shooter-campaign/cycle-25/`.

## ADR-043: Spawn-origin markers (levels)
Date: 2026-11-08
Status: accepted
Context: Wave spawns are random, at least 10 m away and often off-screen or behind cover. The sim emitted a bare `spawn` event and the game ignored it, so enemies materialized with no cue; the baseline test found no marker state or nodes.
Decision: `_spawn_enemy` records `spawn_pos` (telemetry only, never in the snapshot). The game keeps up to four 0.7 s marks (`juice.spawn_mark`: 0.18 x 2.4 emissive column) and draws one at each origin. Presentation-only; spawn positions, counts, timing, RNG, damage and hashes are untouched.
Consequences: Suite 126/126 green (four new tests); determinism 1800 ok; aikit 4/4. The staged pair changes 386 px (0.07%, bbox 451,92-911,310; 126 px in the beam crop), mean luma 35.18→35.17, draws 6→7, triangles 562→574. `kite 600` keeps hash `4fe640c5…` and its 10 kills / 1950 / hp 100. Evidence: `evidence/cycle-26.json`, images in workspace `shots/shooter-campaign/cycle-26/`.

## ADR-044: Centered top-center HUD status (UI readability)
Date: 2026-11-08
Status: accepted
Context: The top-center HUD lines were drawn at fixed offsets (`cx - 90`, BEST `cx - 60`). At score 12345 the baseline test measured WAVE at x 390 vs 367 expected, STREAK 390 vs 427, OVERDRIVE 390 vs 379, NEAR-MISS 390 vs 415, SURGE 390 vs 307 and BEST 420 vs 427. The primary progress line therefore drifted right as values grew, and the secondary lines were not on a shared axis.
Decision: Add `ui._center(canvas, cx, y, text, color, scale)`, which draws at `cx - text_width(text, scale) // 2`, and use it for WAVE/SCORE, STREAK, OVERDRIVE, SURGE, NEAR-MISS and the pickup label. `game.draw_ui` centers BEST the same way. The line positions, font scale, colors and content are otherwise unchanged; no sim state or HUD facts move.
Consequences: Suite 129/129 green (three new centering tests); determinism 1800 ok; aikit 4/4. At 960×540 seed 1 with score 12345 / best 9999 / streak 7 / overdrive 5.0 / near-miss 3, the pair changes 4,724 px (0.91%, bbox 367,16-615,97; all top-band), mean luma 36.01→36.01, draws 5, triangles 242. `kite 600` keeps hash `4fe640c5…` and its 10 kills / 1950 / hp 100. Evidence: `evidence/cycle-27.json`, images in workspace `shots/shooter-campaign/cycle-27/`.

## ADR-045: Per-weapon tracer and flash tints (graphics/effects)
Date: 2026-11-08
Status: accepted
Context: The tracer pool and muzzle flash used one yellow/white material for every gun, and the tracer dict carried no weapon identity, so pulse, scatter, lance and surge fire looked the same. The baseline tint test failed all four checks.
Decision: `_fire` tags each tracer with the firing weapon (presentation telemetry, never in the snapshot). The game registers `material.tracer_{pulse,scatter,lance,surge}` and `material.flash_{...}` with distinct colors/emissives and assigns them in `_sync_scene`; pulse keeps the legacy yellow tracer and white flash as the control. The generic materials remain as fallbacks.
Consequences: Suite 133/133 green (four new tests); determinism 1800 ok; aikit 4/4. At 960×540 seed 1, first-shot pairs: pulse 0 px (control), scatter 882 px (0.17%, bbox 528,312-557,347), surge 226 px (0.04%), lance 62 px (0.01%); mean luma ~40.1; draws 9, triangles 542. `kite 600` keeps hash `4fe640c5…` and its 10 kills / 1950 / hp 100. Evidence: `evidence/cycle-28.json`, images in workspace `shots/shooter-campaign/cycle-28/`.

## ADR-046: Weapon-switch click and caption (audio cues)
Date: 2026-11-08
Status: accepted
Context: `_switch` emitted `switch:<weapon>`, but the game ignored the event. Slot changes altered the viewmodel tint and status text silently: the baseline test measured an empty cue, zero voices and no `switch_*` clips.
Decision: Add short square clicks for pulse (300 Hz), scatter (220 Hz) and lance (420 Hz), play the matching clip at 0.35 gain on `switch:<wid>`, and show the uppercase weapon name as the caption. Surge falls back to the pulse click. The sim switch timing, cooldown and ammo path are untouched.
Consequences: Suite 136/136 green (three new tests); determinism 1800 ok; aikit 4/4. The slot-2 pair at 960×540 seed 1 changes 7,828 px (1.51%, bbox 426,164-947,459; caption + AUDIO line), mean luma 35.10→35.20, draws 5, triangles 242. `switch 30` goes from audio 0 / empty cue to audio 3 / `PULSE`, with the same hash `f03a087f…` and 0 drops. Evidence: `evidence/cycle-29.json`, images in workspace `shots/shooter-campaign/cycle-29/`.

## ADR-047: Record campaign wins in run history (progression/saves)
Date: 2026-11-08
Status: accepted
Context: `_record_campaign_clear` incremented `wins` but never wrote `last_run` or `history`; only `_finish_run` on death did. The pre-fix 3000-frame campaign reached wave 4 with `wins=1`, `runs=0` and `history=[]`, so a win vanished from the record and the debrief showed raw scores with no outcome.
Decision: Extract `_record_run(outcome)` from `_finish_run`, sharing the run record, bests, save and `_run_recorded` guard. Death records `lose`; campaign clear increments `wins` and records `win`, so a later death cannot duplicate the same run. The debrief formats RECENT entries with `W`/`L`. The profile stays schema 3 because run records already carry `outcome`.
Consequences: Suite 140/140 green (four new tests); determinism 1800 ok; aikit 4/4. The seeded win+loss debrief pair at 960×540 seed 1 changes 656 px (0.13%, bbox 442,356-619,369), mean luma 51.36→51.40, draws 5, triangles 230. `kite 3000` goes from wins=1/runs=0/history=[] to wins=1/runs=1/history=[win 8935, wave 4, time 39, kills 28, streak 16], with the same hash `945e3fdd…` and final 32 kills / 10135 / hp 82. Evidence: `evidence/cycle-30.json`, images in workspace `shots/shooter-campaign/cycle-30/`.

## ADR-048: Kill-only crosshair marker (combat feel)
Date: 2026-11-08
Status: accepted
Context: The crosshair hitmarker was identical for a body hit and a kill. Kill sound, feed, particles and hitstop confirmed the result, but nothing at the aim point distinguished the final hit. The baseline test found no `killmark_t` timer and no red marker.
Decision: Add `juice.killmark_s` (0.18 s). `_fire` sets `killmark_t` only when an enemy dies; the timer decrements with the other presentation timers and is excluded from the snapshot. `draw_shooter` draws four red 5×5 corner ticks at `reticle gap + 6` while it runs. Damage, hitboxes, RNG, AI and the snapshot are untouched.
Consequences: Suite 144/144 green (four new tests); determinism 1800 ok; aikit 4/4. At 960×540 seed 1 the first-kill pair changes exactly 100 px (0.02%, bbox 460,250-500,290; four ticks), mean luma 37.00→36.99, draws 7, triangles 318. `kite 600` keeps hash `4fe640c5…` and its 10 kills / 1950 / hp 100. Evidence: `evidence/cycle-31.json`, images in workspace `shots/shooter-campaign/cycle-31/`.

## ADR-049: Warden slam-radius ground ring (enemies/bosses)
Date: 2026-11-08
Status: accepted
Context: The warden's 0.7 s windup had a caption, a distinct voice, a swelling body and a pulsing core, but the 4.5 m slam radius existed only as data. In the staged windup frame the player could not tell whether they were inside the damage radius; the baseline test measured `ring=0`.
Decision: Build `juice.slam_ring` (24 segments, 0.20 × 0.025 tiles) as 24 shared-cube nodes using the wall mesh and one orange emissive material. `_sync_scene` places them on the floor at the warden's DATA `range` from its live position whenever a warden is alive with `windup_t > 0`, and hides them otherwise. The ring is presentation-only: windup, slam timing, damage, RNG and the snapshot are untouched.
Consequences: Suite 148/148 green (four new tests); determinism 1800 ok; aikit 4/4. At 960×540 seed 1 with the warden at (0,1.1,2.0) and windup 0.483, the pair changes 3,560 px (0.69%, bbox 55,92-911,539), mean luma 36.96→37.56, draws 7→8, triangles 446→698. `slam 180` keeps hash `4580b9da…`, 43 frames, hp 70, 1 hurt, audio 3, peak 3, 0 drops. Evidence: `evidence/cycle-32.json`, images in workspace `shots/shooter-campaign/cycle-32/`.

## ADR-050: Off-screen surge-pickup edge tag (levels)
Date: 2026-11-08
Status: accepted
Context: The wave-2 surge pickup has a world beacon and a top-center `SURGE PICKUP READY` label within 18 m, but facing away left the player with a label and no direction. The staged spawn frame facing +Z showed the label and no edge cue; the baseline test failed the off-screen case.
Decision: In the existing pickup-label branch, compute the bearing from camera yaw and draw a green `SURGE` chip (68×26) at the screen edge in that direction when `|bearing| > 1.35` rad; clamp its center inside 48 px horizontally and 140 px top / 150 px bottom. The chip is presentation-only; the pickup trigger, spot and sim state are untouched.
Consequences: Suite 151/151 green (three new tests); determinism 1800 ok; aikit 4/4. At 960×540 seed 1 the pair changes 1,768 px (0.34%, bbox 446,377-513,402), mean luma 34.12→34.18, draws 5, triangles 62. `pickup 240` keeps hash `7f84f3e9…`, 147 frames, hp 100, audio 1, 0 drops. Evidence: `evidence/cycle-33.json`, images in workspace `shots/shooter-campaign/cycle-33/`.

## ADR-051: Width-following death debrief (UI readability)
Date: 2026-11-08
Status: accepted
Context: The death debrief used a fixed 380 px panel. After the cycle-30 W/L markers, a six-digit RECENT line measured 406 px at x 310, ending at 716 while the panel ended at 670, so the history spilled onto the floor. The baseline fit test failed.
Decision: Compute `widest` from the extra lines and keep at least 340 px, set `panel_width = max(380, widest + 40)`, center the panel on `cx`, and draw every debrief line from `panel_left + 20`. Normal-score layouts remain exactly 380 px wide; the fixed text column moves with the panel for consistent margins.
Consequences: Suite 153/153 green (two new tests); determinism 1800 ok; aikit 4/4. The seeded six-digit pair at 960×540 seed 1 changes 15,022 px (2.9%, bbox 257,262-715,383), mean luma 51.61→50.55, draws 5, triangles 230. `death 240` keeps hash `f8cd9e28…`, 1 frame, hp 0, score 1500, audio 2, 0 drops. Evidence: `evidence/cycle-34.json`, images in workspace `shots/shooter-campaign/cycle-34/`.

## ADR-052: Arena wall pilasters (graphics/effects)
Date: 2026-11-08
Status: accepted
Context: The four boundary walls were flat gray planes with a single cyan top trim; the spawn view had no vertical rhythm or depth. An initial 16-pilaster version (4 per wall) looked right but pushed the frame-budget plan to 45 draw calls (shadow calls 40) against the 40 limit, failing `test_frame_budget`.
Decision: Add 8 shared-cube pilasters (0.18 × 3.0 × 0.18) at ±10 m on the long walls and ±10 m on the short walls, one `material.pilaster` and the shared wall mesh, flush inside the arena. They are decoration only: no colliders, no sim state. The count is 8 rather than 16 to stay under the 40-draw plan (37 calls, 32 shadow calls).
Consequences: Suite 155/155 green (two new tests); determinism 1800 ok; aikit 4/4. At 960×540 seed 1 the spawn pair changes 1,296 px (0.25%, bbox 97,92-911,301), mean luma 35.14→35.20, draws 5→6, triangles 242→290. `kite 600` keeps hash `4fe640c5…` and its 10 kills / 1950 / hp 100. Evidence: `evidence/cycle-35.json`, images in workspace `shots/shooter-campaign/cycle-35/`.

## ADR-053: Hostile-inbound spawn voice (audio cues)
Date: 2026-11-08
Status: accepted
Context: The sim emits `spawn` and the game draws a 0.7 s origin marker (cycle 26), but the event was silent: the staged frame measured `cue='' voices=0`, so a spawn behind the player or cover gave no warning.
Decision: Add a deterministic 0.08 s noise `spawn` clip at 0.30 gain. `_play_event("spawn")` plays it for every spawn and shows `HOSTILE INBOUND` only when no cue is active, so the caption cannot spam at the 0.8 s spawn cadence. The marker, spawn position, timing, RNG and sim state are untouched.
Consequences: Suite 157/157 green (two new tests); determinism 1800 ok; aikit 4/4. The staged frame at 960×540 seed 1 changes 10,312 px (1.99%, bbox 378,164-947,459; caption + AUDIO line), mean luma 35.23→35.34, draws 8, triangles 622. `kite 600` goes from audio 90 to 101 (11 natural spawns) with the same hash `4fe640c5…`, 10 kills / 1950 / hp 100, peak 8, 0 drops. Evidence: `evidence/cycle-36.json`, images in workspace `shots/shooter-campaign/cycle-36/`.

## ADR-054: Career totals in the death debrief (progression/saves)
Date: 2026-11-08
Status: accepted
Context: The profile stores lifetime `runs` and `wins`, but the run-over debrief only showed bests and RECENT entries; `CAMPAIGNS WON` appeared transiently on the clear banner. A player could not see their career totals on the death screen. The baseline test found no RUNS/WINS row.
Decision: Append `RUNS <profile.runs>  WINS <profile.wins>` to the debrief extras when runs > 0. It sits after RECENT; the cycle-34 width/height calculation already accommodates the row. No schema, save-format or run-record change.
Consequences: Suite 159/159 green (two new tests); determinism 1800 ok; aikit 4/4. The seeded win/loss death pair at 960×540 seed 1 (profile runs=4, wins=1) changes 8,608 px (1.66%, bbox 290,378-669,405), mean luma 51.42→50.06, draws 6, triangles 278. `death 240` keeps hash `f8cd9e28…`, 1 frame, hp 0, score 1500, audio 2, 0 drops. Evidence: `evidence/cycle-37.json`, images in workspace `shots/shooter-campaign/cycle-37/`.

## ADR-055: Visible wisp bolt (combat feel)
Date: 2026-11-08
Status: accepted
Context: The wisp's ranged attack was an instant hitscan with no visual projectile. The staged hit frame measured hp 94 and `tracers=[]`; only the red damage cue revealed the attack, so the source/line of fire was unreadable.
Decision: When a wisp attack passes its LOS check, append a 0.12 s tracer from the wisp chest to the player eye tagged `weapon="wisp"`; the game registers `material.tracer_wisp` (violet/blue) and the existing per-weapon tracer material mapping uses it. Damage, LOS, cooldown, RNG and the snapshot are untouched.
Consequences: Suite 161/161 green (two new tests); determinism 1800 ok; aikit 4/4. The staged hit pair at 960×540 seed 1 changes 2,962 px (0.57%, bbox 714,92-911,539), mean luma 35.92→35.89, draws 7→8, triangles 314→326. `kite 3000` keeps hash `945e3fdd…`, 32 kills / 10135 / hp 82, 3 hurts, 458 audio, peak 8, 0 drops. Evidence: `evidence/cycle-38.json`, images in workspace `shots/shooter-campaign/cycle-38/`.

## ADR-056: Warden summon origin markers (enemies/bosses)
Date: 2026-11-08
Status: accepted
Context: `boss_summon` had a caption and a distinct voice, but the two summoned mites appeared with no origin cue; only normal `spawn` events used the marker pool. The staged summon frame measured `positions=0 marks=0` while the cue was already visible.
Decision: `_summon_mites` records each clamped escort spawn in `summon_positions` (presentation telemetry, not in the snapshot); `_play_event("boss_summon")` inserts a spawn mark for each position into the existing 0.7 s marker pool, capped at `MAX_SPAWN_MARKS`. Summon count, positions, attack cooldowns, damage and RNG are unchanged.
Consequences: Suite 163/163 green (two new tests); determinism 1800 ok; aikit 4/4. The staged summon pair at 960×540 seed 1 changes 6,296 px (1.21%, bbox 302,92-935,406), mean luma 38.49→38.75, draws 9→10, triangles 1134→1158. `boss 1800` keeps hash `81f05265…`, 507 frames, 3 kills, 3080, hp 100, 56/56, 121 audio, peak 8, 0 drops. Evidence: `evidence/cycle-39.json`, images in workspace `shots/shooter-campaign/cycle-39/`.

## ADR-057: Lit rim on the jump platform (levels)
Date: 2026-11-08
Status: accepted
Context: The 0.7 m platform is the only walkable elevated surface; cycle 05 skipped its lit cap because the top must stay clear. From the approach view it looked like a solid blue cover, with no cue that it is jumpable.
Decision: Add two lit trim strips (6.1 × 0.08 × 0.10) on the long top edges at y 0.74, sharing `material.trim` with the existing wall/cover trim batch. They are decoration only, with no colliders or sim state. The count is two rather than four to keep the frame-budget plan under 40 (shadow calls 32→34, draws unchanged).
Consequences: Suite 165/165 green (two new tests); determinism 1800 ok; aikit 4/4; frame budget green. The approach pair at 960×540 seed 1 changes 14,003 px (2.7%, bbox 51,92-908,399), mean luma 49.08→48.24, draws 6, triangles 98→122. `platform 120` keeps hash `c1603d79…`, 28 frames, hp 100, score 250, landed, audio 1, 0 drops. Evidence: `evidence/cycle-40.json`, images in workspace `shots/shooter-campaign/cycle-40/`.

## ADR-058: Show the streak score bonus (UI readability)
Date: 2026-11-08
Status: accepted
Context: The HUD showed `STREAK xN` but hid the score multiplier: 10% per kill, capped at 50%, broken on hurt. The player could not see the stake the streak represents without reverse-engineering the score. The baseline test found no bonus helper or percentage.
Decision: Add `Sim.streak_bonus()` returning `min(streak_cap, streak_per * streak)` and render `STREAK xN  +P%` in the existing centered line. The streak math, scoring, break-on-hurt and snapshot are untouched.
Consequences: Suite 167/167 green (two new tests); determinism 1800 ok; aikit 4/4. At 960×540 seed 1 with streak 7 the line changes 864 px (0.17%, bbox 391,52-568,65), mean luma 35.43→35.51, draws 6, triangles 290. `kite 600` keeps hash `4fe640c5…`, 10 kills / 1950 / hp 100, 101 audio, peak 8, 0 drops. Evidence: `evidence/cycle-41.json`, images in workspace `shots/shooter-campaign/cycle-41/`.

## ADR-059: Shrinking enemy death silhouette (graphics/effects)
Date: 2026-11-08
Status: accepted
Context: A killed enemy node disappeared on the kill frame. The burst, feed, sound, hitstop and killmark all played, but the body had no exit transition, so the final hit read as a sudden deletion.
Decision: Add `juice.death_fx_s` (0.15 s) and `_Enemy.death_t`, set when an enemy dies and decremented for dead enemies in `_step_enemies`. `_sync_scene` shows a dead enemy while `death_t > 0`, shrinking it to zero and using `material.enemy_hit`; then the node hides. `death_t` is excluded from the snapshot; damage, AI, movement and RNG are untouched.
Consequences: Suite 170/170 green (three new tests); determinism 1800 ok; aikit 4/4. Two frames after a kill at 960×540 seed 1 the pair changes 3,255 px (0.63%, bbox 438,92-923,373), mean luma 38.25→38.64, draws 9→10, triangles 378→698. `kite 600` keeps hash `4fe640c5…`, 10 kills / 1950 / hp 100, 101 audio, peak 8, 0 drops. Evidence: `evidence/cycle-42.json`, images in workspace `shots/shooter-campaign/cycle-42/`.

## ADR-060: Brute slam voice and caption (audio cues)
Date: 2026-11-08
Status: accepted
Context: The warden has dedicated windup/slam voices, but the brute's 20-damage slam only produced the generic `hurt` clip and the damage-direction cue. The staged close-range hit measured events `['hurt']`, cue `''`, one voice, so the strongest normal-enemy attack had no distinct audio identity.
Decision: Emit `brute_slam` in the brute attack branch before the existing hurt event; add a 0.15 s noise clip and a danger `BRUTE SLAM` caption. The hurt clip still plays. Damage, LOS, cooldown, RNG and the snapshot are untouched.
Consequences: Suite 172/172 green (two new tests); determinism 1800 ok; aikit 4/4. The staged hit pair at 960×540 seed 1 changes 3,800 px (0.73%, bbox 408,164-827,459), mean luma 48.55→48.22, draws 7, triangles 302. `brute 60` records `brute_slam` + `hurt` at frame 1, hp 80, peak 2, 0 drops, hash `830dcbe4…`; `kite 600` keeps hash `4fe640c5…` and its 10 kills / 1950 / hp 100. Evidence: `evidence/cycle-43.json`, images in workspace `shots/shooter-campaign/cycle-43/`.

## ADR-061: Career bests in the death debrief (progression/saves)
Date: 2026-11-08
Status: accepted
Context: The profile persists `best_kills`, `best_wave` and `best_streak`, but the run-over debrief showed the current run's streak/time, the recent history and runs/wins; the top BEST line exposed only the score. Career bests were invisible on the screen where progress matters most.
Decision: Append `BEST KILLS <best_kills>  WAVE <best_wave>  STREAK <best_streak>` to the debrief extras when any value is non-zero. The cycle-34 width/height calculation already accommodates the row. No schema, save or run-record change.
Consequences: Suite 174/174 green (two new tests); determinism 1800 ok; aikit 4/4. The seeded bests 12/4/6 pair at 960×540 seed 1 changes 21,392 px (4.13%, bbox 275,262-684,427), mean luma 50.07→48.15, draws 6, triangles 278. `death 240` keeps hash `f8cd9e28…`, 1 frame, hp 0, score 1500, audio 3, 0 drops. Evidence: `evidence/cycle-44.json`, images in workspace `shots/shooter-campaign/cycle-44/`.

## ADR-062: Kill bounty at the crosshair (combat feel)
Date: 2026-11-08
Status: accepted
Context: The kill reward was visible only in the top-left kill feed. The crosshair killmark confirmed the kill, but the bounty value was far from the aim point, so the moment's reward read separately from the shot.
Decision: On `kill:<type>:<total>`, set `score_pop` with the text `+N` and a 0.6 s lifetime (`juice.score_pop_s`). `update` decrements it; `draw_ui` draws it at `cx + 22, cy + 16` in the accent color. The top-left feed remains. Presentation only; the sim and snapshot are untouched.
Consequences: Suite 177/177 green (three new tests); determinism 1800 ok; aikit 4/4. Two frames after the first kill at 960×540 seed 1 the pair changes 192 px (0.04%, bbox 502,286-547,299), mean luma 38.64→38.67, draws 10, triangles 698. `kite 600` keeps hash `4fe640c5…`, 10 kills / 1950 / hp 100, 101 audio, peak 8, 0 drops. Evidence: `evidence/cycle-45.json`, images in workspace `shots/shooter-campaign/cycle-45/`.

## ADR-063: Crosshair target health (enemies/bosses)
Date: 2026-11-08
Status: accepted
Context: Only the warden had a health bar. Mites, brutes and wisps showed hit flinch and a death silhouette, but their remaining health was invisible, so the player could not tell whether one more shot would finish a target. The staged crosshair-on-mite frame measured `target=None`.
Decision: Add read-only `Sim.aim_target()`: cast the eye-forward ray, find the nearest live enemy hitbox, and reject targets behind a wall. `draw_shooter` renders a 120×6 bar plus `TYPE hp/max` above the crosshair for non-warden targets; the warden keeps its dedicated top bar. No damage, AI, RNG or snapshot change.
Consequences: Suite 181/181 green (four new tests); determinism 1800 ok; aikit 4/4. The damaged-mite pair at 960×540 seed 1 changes 1,744 px (0.34%, bbox 418,200-541,227), mean luma 35.48→35.84, draws 7, triangles 610. `kite 600` keeps hash `4fe640c5…`, 10 kills / 1950 / hp 100, 101 audio, peak 8, 0 drops. Evidence: `evidence/cycle-46.json`, images in workspace `shots/shooter-campaign/cycle-46/`.

## ADR-064: Jump-platform launch pad (levels)
Date: 2026-11-08
Status: accepted
Context: The cycle-40 rim marks the platform top, but the floor spot to jump from was unmarked; from the approach the player saw the edge with no launch cue. The before frame showed only the rim.
Decision: Add one flat lit trim pad (1.4 × 0.02 × 1.4) at `(-16, 0.02, 11.2)`, 0.8 m before the south platform edge, sharing `material.trim`. It is decoration only: no collider or sim state. One node keeps the frame-budget plan at 40 (shadow calls 34→35).
Consequences: Suite 183/183 green (two new tests); determinism 1800 ok; aikit 4/4; frame budget green. The approach pair at 960×540 seed 1 changes 7,994 px (1.54%, bbox 361,92-899,539), mean luma 48.24→49.47, draws 6, triangles 122→134. `platform 120` keeps hash `c1603d79…`, 28 frames, hp 100, score 250, landed, audio 1, 0 drops. Evidence: `evidence/cycle-47.json`, images in workspace `shots/shooter-campaign/cycle-47/`.

## ADR-065: Pickup edge tag during boss fights (UI readability)
Date: 2026-11-08
Status: accepted
Context: The pickup top label and edge tag shared one `boss is None` guard. With a live warden and the pickup still active (wave 3 if not taken), both disappeared; the staged frame showed only the warden bar, so the boss fight erased the pickup direction. The top label must stay suppressed because the boss bar occupies that space.
Decision: Split the cues. The `SURGE PICKUP READY` top label remains gated on no boss; the off-screen `SURGE` edge chip shows whenever the pickup is active, within 18 m and outside the forward view, regardless of the boss. The beacon, trigger and sim state are untouched.
Consequences: Suite 186/186 green (three new tests); determinism 1800 ok; aikit 4/4. The boss + pickup pair at 960×540 seed 1 changes 1,768 px (0.34%, bbox 446,377-513,402), mean luma 34.71→34.77, draws 6, triangles 98. `kite 3000` keeps hash `945e3fdd…`, 32 kills / 10135 / hp 82, 458 audio, peak 8, 0 drops; that run takes the pickup in wave 2, so the tag itself is a staged UI proof. Evidence: `evidence/cycle-48.json`, images in workspace `shots/shooter-campaign/cycle-48/`.

## ADR-066: Arena cover panel texture (graphics/effects)
Date: 2026-11-08
Status: accepted
Context: The six covers were flat brown boxes. The floor had a grid texture and the walls had trim/pilasters, but the covers had no surface detail and read as plain blocks. The before spawn frame showed uniform cover faces.
Decision: Generate a deterministic 64×64 grayscale `cover-panel` texture (2-px seam border, 16-px horizontal bands) and apply it to the existing `material.cover` with `checker_scale=1.0`; the brown base color still tints it. No new nodes, draw calls, colliders or sim state.
Consequences: Suite 188/188 green (two new tests); determinism 1800 ok; aikit 4/4. The spawn pair at 960×540 seed 1 changes 25,683 px (4.95%, bbox 0,262-959,442), mean luma 35.24→34.09, draws 6, triangles 290 (unchanged). `kite 600` keeps hash `4fe640c5…`, 10 kills / 1950 / hp 100, 101 audio, peak 8, 0 drops. Evidence: `evidence/cycle-49.json`, images in workspace `shots/shooter-campaign/cycle-49/`.

## ADR-067: Wisp bolt warning (audio cues)
Date: 2026-11-08
Status: accepted
Context: The wisp bolt became visible in cycle 38, but the attack was silent until the hit; the only sound was the generic `hurt` clip. The warden and brute have dedicated attack cues; the ranged wisp had none. The staged hit measured events `['hurt']`, cue `''`, one voice.
Decision: Emit `wisp_bolt` in the wisp attack branch before the hurt event; add a 0.08 s 1200 Hz sine and a danger `WISP BOLT` caption. The bolt, LOS, damage, cooldown and snapshot are untouched; the hurt clip still plays after it.
Consequences: Suite 190/190 green (two new tests); determinism 1800 ok; aikit 4/4. The staged hit pair at 960×540 seed 1 changes 3,488 px (0.67%, bbox 414,164-815,459), mean luma 34.78→34.64, draws 8, triangles 326. `kite 3000` goes from 458 to 461 audio (3 natural bolts) with the same hash `945e3fdd…`, 32 kills / 10135 / hp 82, 3 hurts, peak 8, 0 drops. Evidence: `evidence/cycle-50.json`, images in workspace `shots/shooter-campaign/cycle-50/`.

## ADR-068: Full five-run history in the debrief (progression/saves)
Date: 2026-11-08
Status: accepted
Context: The profile stores a five-run history (cycle 23), but the debrief rendered only `history[:3]`; the two oldest persisted runs were never shown. The baseline test found only the first three scores, so the stored contract and the UI disagreed.
Decision: Build all five entries in the debrief; show the first three on `RECENT` and the remaining two on a second `HISTORY` line. The cycle-34 dynamic panel width/height already contain the added line. No schema, save-format or run-record change.
Consequences: Suite 191/191 green (one new test); determinism 1800 ok; aikit 4/4. The four-seeded-runs plus current-1500 pair at 960×540 seed 1 changes 12,064 px (2.33%, bbox 275,378-684,449), mean luma 48.16→46.79, draws 6, triangles 278. `death 240` keeps hash `f8cd9e28…`, 1 frame, hp 0, score 1500, audio 3, 0 drops. Evidence: `evidence/cycle-51.json`, images in workspace `shots/shooter-campaign/cycle-51/`.

## ADR-069: Damage camera jolt (combat feel)
Date: 2026-11-08
Status: accepted
Context: Taking damage already had a hurt clip and a directional HUD cue, but the camera stayed exactly at the sim eye; the hit had no physical jolt. The baseline test measured the camera equal to `sim.eye()` while `hurt_t=0.4`.
Decision: In `_sync_scene`, while `hurt_t > 0`, offset the camera position by a short deterministic shake: `amp = min(1, hurt/0.3) * 0.035`, `x = sin(time*55)*amp`, `y = cos(time*47)*amp*0.6`, z unchanged. The camera yaw/pitch, aim ray, hitscan, viewmodel origin and snapshot are untouched; the HUD is screen-space and stays fixed.
Consequences: Suite 193/193 green (two new tests); determinism 1800 ok; aikit 4/4. The right-side first-hit pair at 960×540 seed 1 changes 110,566 px (21.33%, bbox 0,235-959,539), mean luma 34.24→34.20, draws 6, triangles 290. `ambush 180` keeps hash `ca6d9711…`, 180 frames, hp 84, 2 hurts, audio 2, peak 2, 0 drops. Evidence: `evidence/cycle-52.json`, images in workspace `shots/shooter-campaign/cycle-52/`.

## ADR-070: Target bar yields to the death screen (enemies/bosses)
Date: 2026-11-08
Status: accepted
Context: The cycle-46 crosshair target-health bar was drawn even with `sim.alive=False`. On the death frame a brute under the crosshair put `BRUTE 120/120` over `YOU DIED`; the baseline test measured the label still present after death.
Decision: Add the `sim.alive` guard to the target-bar condition. The bar remains for live non-warden targets; the warden bar and the death screen are otherwise unchanged. This is draw-only and changes no sim state.
Consequences: Suite 195/195 green (two new tests); determinism 1800 ok; aikit 4/4. The death-frame pair at 960×540 seed 1 changes 1,548 px (0.30%, bbox 403,200-556,227), mean luma 49.41→49.08, draws 6, triangles 278. `death 240` keeps hash `f8cd9e28…`, 1 frame, hp 0, score 1500, audio 3, peak 3, 0 drops. Evidence: `evidence/cycle-53.json`, images in workspace `shots/shooter-campaign/cycle-53/`.

## ADR-071: Pulsing launch pad (levels)
Date: 2026-11-08
Status: accepted
Context: The cycle-47 launch pad marked the jump spot, but it was static and could blend into the floor grid at approach distance; the before frame measured a constant 1.4 scale with no motion.
Decision: In `_sync_scene`, pulse the existing `_approach_pad` scale by `1 + 0.08*sin(time*3)`; position and flat height stay fixed. No new nodes, draws, colliders or sim state. The jump path is untouched.
Consequences: Suite 196/196 green (one new test); determinism 1800 ok; aikit 4/4. The approach pair at 960×540 seed 1 (time 0.5) changes 1,629 px (0.31%, bbox 352,498-607,539), mean luma 49.47→49.71, draws 6, triangles 134. `platform 120` keeps hash `c1603d79…`, 28 frames, hp 100, score 250, landed, audio 1, 0 drops. Evidence: `evidence/cycle-54.json`, images in workspace `shots/shooter-campaign/cycle-54/`.

## ADR-072: Low-ammo count at the crosshair (UI readability)
Date: 2026-11-08
Status: accepted
Context: The near-crosshair low-ammo warning said only `LOW AMMO`; the exact magazine count lived in the top-left engine status, so the player could not tell 3 rounds from 1 at the aim point, which changes the reload decision. The baseline test measured the countless label.
Decision: Show `LOW AMMO <mag>` and widen the panel from 110 to 150 px so two-digit magazines fit. The engine status remains the full ammo source (weapon + magazine + reserve); the sim and all ammo values are untouched.
Consequences: Suite 199/199 green (three new tests); determinism 1800 ok; aikit 4/4. The magazine-3 pair at 960×540 seed 1 changes 1,448 px (0.28%, bbox 405,300-554,321), mean luma 34.04→34.02, draws 6, triangles 290. `strafe 300` keeps hash `14a48660…`, 30 shots, hp 92, 1 hurt, 36 audio, peak 8, 0 drops. Evidence: `evidence/cycle-55.json`, images in workspace `shots/shooter-campaign/cycle-55/`.

## ADR-073: Wall panel texture (graphics/effects)
Date: 2026-11-08
Status: accepted
Context: The four boundary walls were flat gray boxes. Cycle 49 gave the covers a panel texture, but the arena shell still read as untextured slabs at spawn and along sightlines; the baseline test measured `material.wall.texture=None` and `checker_scale=0`.
Decision: Add `_wall_panel_texture()` (deterministic 64x64 grayscale: 8 px vertical seams, 16-row horizontal bands and rivets) and bind it to `material.wall` with `checker_scale=0.15`. Material-only: same wall nodes, mesh, draw calls, colliders and sim. The gray-blue color still tints the grayscale detail.
Consequences: Suite 201/201 green (two new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The spawn pair at 960x540 seed 1 changes 34,064 px (6.57%, bbox 0,236-959,307), mean luma 34.09 -> 32.49, draws 6, triangles 290. `kite 600` keeps hash `4fe640c5...`, 10 kills, hp 100, score 1950, 39 shots/37 hits, audio 101, peak 8, 0 drops. Evidence: `evidence/cycle-56.json`, images in workspace `shots/shooter-campaign/cycle-56/`.

## ADR-074: Surge-forfeit cue (audio cues)
Date: 2026-11-08
Status: accepted
Context: Switching from the surge pickup to slot 1-3 forfeits the remaining surge timer and its stranded ammo. The sim emits `surge_forfeit`, but `_play_event` had no branch, so the player heard only the ordinary switch click and read the new weapon name; the loss looked like a free weapon change.
Decision: Map the existing event to a distinct 0.22 s 120 Hz voice and a danger `SURGE FORFEIT` caption. The switch click still plays; a one-frame pending flag lets the forfeit caption win over the weapon name. Sim, ammo, timer and input paths are untouched.
Consequences: Suite 204/204 green (three new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The forfeit pair at 960x540 seed 1 changes 3,060 px (0.59%, bbox 390,164-815,459), draws 6, triangles 290. `forfeit 6` before/after same hash `3fe96786...`, audio 1 -> 2, clips `switch_pulse` -> `surge_forfeit` + `switch_pulse`, cue PULSE -> SURGE FORFEIT, hp 100, 0 drops. Evidence: `evidence/cycle-57.json`, WAV/spectrogram and images in workspace `shots/shooter-campaign/cycle-57/`.

## ADR-075: Visible profile save failure (progression/saves)
Date: 2026-11-08
Status: accepted
Context: `_save_profile` only incremented `profile_save_errors`; the death debrief looked normal while the run was lost. A profile parent that could not be created raised `FileExistsError` out of the finish, and a held lock already made `save` return False. Neither outcome reached the player.
Decision: Wrap the store save in `_save_profile` so an `OSError` counts as a failure instead of escaping, and put a red `PROFILE NOT SAVED` line first in the debrief extras when `profile_save_errors > 0`. The profile schema, save format, lock policy and sim are untouched.
Consequences: Suite 207/207 green (three new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The locked-profile death pair at 960x540 seed 1 changes 13,320 px (2.57%, bbox 281,334-678,449), mean luma 47.08 -> 45.72, draws 6, triangles 278. `save_fail 240` before/after same death hash `f8cd9e28...`, profile runs 1, save_errors 1, last_run recorded, hp 0, 0 drops. Evidence: `evidence/cycle-58.json`, images in workspace `shots/shooter-campaign/cycle-58/`.

## ADR-076: Viewmodel recoil punch (combat feel)
Date: 2026-11-08
Status: accepted
Context: Firing added `sim.kick` and the camera pitched with it, but the first-person gun was rigidly camera-parented: the gun never moved relative to the view, so the kick read as the world tilting instead of the weapon punching.
Decision: Offset the two existing viewmodel nodes along the view basis by `recoil_back` 0.10 m and `recoil_up` 0.08 m, scaled by `min(1, |kick| / 4 degrees)`, with both amounts in `juice.viewmodel`. No new nodes, materials, draw calls, aim rays, hitboxes or sim state; the offset returns to rest with the existing kick decay.
Consequences: Suite 210/210 green (three new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The scatter fire-frame pair at 960x540 seed 1 changes 7,141 px (1.38%, bbox 551,334-671,425), mean luma 35.28 -> 35.18, draws 10, triangles 886. `strafe 300` keeps hash `14a48660...`, 30 shots, hp 92, 1 hurt, audio 36, peak 8, 0 drops. Evidence: `evidence/cycle-59.json`, images in workspace `shots/shooter-campaign/cycle-59/`.

## ADR-077: Cover-safe warden escorts (enemies/bosses)
Date: 2026-11-08
Status: accepted
Context: `_summon_mites` picked a random 1.2-2.4 m ring around the warden and clamped only to the arena bounds. Against the low platform or a cover box, escort mites could materialize inside the collider and stay stuck. The baseline test reproduced 2 blocked escorts with the warden at (-16, 1.1, 11) and seed 1.
Decision: Check each candidate against the shared cover boxes with the mite radius. Retry the ring up to 12 times and skip a candidate if it never clears; count, `max_alive`, RNG determinism and the `boss_summon` event stay intact. No new state, node or draw.
Consequences: Suite 211/211 green (one new 20-seed test); determinism 1800 ok (hash a1528cee); aikit 4/4. The platform-edge pair at 960x540 seed 1 changes 5,248 px (1.01%, bbox 371,141-596,281), mean luma 71.24 -> 71.28, draws 11, triangles 1182. `summon 60` before/after: 2 blocked -> 0, both runs hp 100 for 60 frames with 0 hurts and 0 drops; positions move from (-16.09,12.79)/(-17.91,11.62) to (-15.71,9.73)/(-13.86,11.39). Evidence: `evidence/cycle-60.json`, images in workspace `shots/shooter-campaign/cycle-60/`.

## ADR-078: Full platform landing perimeter (levels)
Date: 2026-11-08
Status: accepted
Context: The cycle-40 platform-rim proof names four shared strips, but the code emitted only the two long edges. From the east or west the 0.7 m platform's edge was an unlit dark seam against the side face, so the landing perimeter was inconsistent.
Decision: Build `_platform_frame_mesh()` as four thin cubes merged into one `MeshData` and replace the two long-edge nodes with one `platform-rim` node. The frame shares `material.trim`, sits on the top edge, and adds no colliders or sim state. A merged mesh keeps one node and one shadow draw; the custom mesh costs one additional batched draw (7 vs 6) but stays well under the 40-draw gate.
Consequences: Suite 211/211 green (two updated rim tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The approach pair at 960x540 seed 1 changes 5,403 px (1.04%, bbox 51,92-908,399; 5,111 px in the 3D scene, bbox 51,305-908,399), mean luma 44.04 -> 44.40, draws 7, triangles 158, shadow calls 34 (one fewer than before). `platform 120` keeps hash `c1603d79...`, 28 frames, landed at y 1.6, hp 100, score 250, 0 drops. Evidence: `evidence/cycle-61.json`, images in workspace `shots/shooter-campaign/cycle-61/`.

## ADR-079: Empty-reserve warning at the crosshair (UI readability)
Date: 2026-11-08
Status: accepted
Context: The cycle-55 low-ammo panel shows `LOW AMMO <mag>`, but with zero reserve rounds the player cannot reload. The warning looked like an ordinary low-magazine prompt and implied a reload would help; the full reserve count lived only in the top-left engine status.
Decision: Read the equipped weapon's reserve in the HUD; when the low-ammo branch runs and reserve is zero, add a red `NO RESERVE` second line and grow the panel from 150x22 to 150x40. With reserve rounds the panel keeps its existing size and label. Draw-only: no sim, ammo, input or save change.
Consequences: Suite 213/213 green (two new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The magazine-3, reserve-0 pair at 960x540 seed 1 changes 2,768 px (0.53%, bbox 405,321-554,339), mean luma 32.33 -> 32.36, draws 6, triangles 290. `dry 60` keeps hash `d33f43e4...`, ammo 0/reserve 0, cue NO AMMO, 11 frames, hp 100, audio 1, 0 drops. Evidence: `evidence/cycle-62.json`, images in workspace `shots/shooter-campaign/cycle-62/`.

## ADR-080: Pickup collection orb pop (graphics/effects)
Date: 2026-11-08
Status: accepted
Context: The surge pickup beam and orb vanished on the trigger frame; the only feedback was the `SURGE ACQUIRED` caption. A major power-up had no world-space payoff, so the collection read as the beacon simply disappearing.
Decision: Keep the existing pickup orb visible for 0.30 s after collection, growing by a 1.5x factor (to 2.5x at the end) and rising 0.9 m while the beam hides. Tuning lives in `juice.pickup_fx_s/scale/rise`; the timer and transform are presentation-only, using the existing node, mesh and material. The trigger, ammo, surge timer and sim are untouched.
Consequences: Suite 215/215 green (two new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The staged six-frame pair at 960x540 seed 1 changes 15,698 px (3.03%, bbox 411,92-899,257; 15,386 px in the 3D scene, bbox 411,116-555,257), mean luma 14.19 -> 17.73, draws 3, triangles 146, shadow calls 35. `pickup 300` keeps hash `7f84f3e9...`, 147 frames, wave 2, hp 100, audio 1, 0 drops. Evidence: `evidence/cycle-63.json`, images in workspace `shots/shooter-campaign/cycle-63/`.

## ADR-081: Critical-kill cue (audio cues)
Date: 2026-11-08
Status: accepted
Context: Critical kills roll at 12% and pay double bounty, but the sim's `critical` event was unmapped. The only signals were the generic kill voice and a larger score pop, so the reward was not legible as critical.
Decision: Map the existing `critical` event to a 0.08 s 1760 Hz sine at 0.55 gain and an accent `CRITICAL` caption. The generic kill voice still plays; the reward roll, bounty, kill feed, streak and sim state are untouched. The event order keeps the caption because the following `kill:` branch only updates the feed.
Consequences: Suite 218/218 green (three new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The forced-critical pair at 960x540 seed 1 changes 3,204 px (0.62%, bbox 420,164-827,459), mean luma 35.70 -> 35.60, draws 10, triangles 698; audio voices 3 -> 4. `kite 3000` keeps the campaign hash `945e3fdd...` and records exactly 4 critical clips (audio 462 -> 466, peak 8, 0 drops, 32 kills, hp 82). WAV/spectrogram report a 0.08 s voice at peak 1.0. Evidence: `evidence/cycle-64.json`, audio in workspace `shots/shooter-campaign/cycle-64/`.

## ADR-082: Disabled-profile warning on the debrief (progression/saves)
Date: 2026-11-08
Status: accepted
Context: An unsupported profile schema makes `load` raise, so `ShooterGame` sets `profile_disabled=True`. `_save_profile` and `_record_progress` then return early, but the death debrief looked normal: the player saw a scored run with no sign that nothing would persist.
Decision: Add a red `PROFILE DISABLED` line first in the debrief extras when `profile_disabled` is true, taking precedence over `PROFILE NOT SAVED`. The schema refusal, no-overwrite guard, in-memory run record and debrief behavior are unchanged.
Consequences: Suite 220/220 green (two new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The schema-99 death pair at 960x540 seed 1 changes 9,692 px (1.87%, bbox 290,334-669,383), mean luma 51.24 -> 49.91, draws 6, triangles 278. `profile_bad 240` before/after same death hash `f8cd9e28...`, disabled true, last_run recorded, runs 0, save_errors 0, hp 0, 0 drops; the schema-99 file is preserved byte-for-byte. Evidence: `evidence/cycle-65.json`, images in workspace `shots/shooter-campaign/cycle-65/`.

## ADR-083: Reload viewmodel dip (combat feel)
Date: 2026-11-08
Status: accepted
Context: The reload bar and completion cue existed, but the first-person gun stayed rigidly at hip through the whole reload, so the weapon felt static while the magazine filled.
Decision: Dip the existing viewmodel nodes along the view basis by `reload_drop` 0.12 m and `reload_back` 0.06 m on a `sin(pi * phase)` curve derived from `reload_t / reload_s`, returning to rest at completion. Amounts live in `juice.viewmodel`; no new nodes, draws, sim timing, ammo or input changes.
Consequences: Suite 223/223 green (three new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The mid-reload pair at 960x540 seed 1 changes 12,027 px (2.32%, bbox 551,333-673,529), mean luma 32.60 -> 32.83, draws 6, triangles 290; the gun body drops from y 1.450 to 1.330. `reload 60` keeps hash `d7eb253d...`, 6 frames, ammo 30/reserve 90, cue RELOADED, hp 100, audio 1, 0 drops. Evidence: `evidence/cycle-66.json`, images in workspace `shots/shooter-campaign/cycle-66/`.

## ADR-084: Entity-safe warden escorts (enemies/bosses)
Date: 2026-11-08
Status: accepted
Context: Cycle 60 rejected escort positions that overlapped covers, but the ring starts at 1.2 m while the warden radius is 1.0 m and the mite radius 0.5 m. Escorts could spawn inside the boss or overlap a previously placed escort; seed 12 put both mites inside the warden footprint, and seeds 23/37 produced overlapping pairs.
Decision: Reject any ring candidate within mite radius + enemy radius + `summon_clearance` of a live enemy, including the warden and already-placed escorts, and retry 16 times. `summon_clearance` is DATA-owned on the warden (0.04 m). The cover check, count, `max_alive`, deterministic RNG order and `boss_summon` event remain. Summon positions change, so the 3000-frame fairness reference `bot_campaign.json` was re-recorded from the winning adaptive kite run (33 kills, score 12545, wave 4, hp 64, hash `d1631a1e...`); the fairness test still replays a witnessed win.
Consequences: Suite 224/224 green (one new 40-seed test); determinism 1800 ok (hash a1528cee); aikit 4/4. The seed-12 pair at 960x540 changes 5,488 px (1.06%, bbox 375,230-542,358), mean luma 34.50 -> 33.85, draws 10, triangles 1158. `summon_overlap 5` before/after: boss overlaps 1 -> 0, boss gaps 1.21/1.53 -> 2.03/1.87, pair gap 1.84 -> 2.38, both runs hp 100 for 5 frames with 0 hurts and 0 drops. Evidence: `evidence/cycle-67.json`, images in workspace `shots/shooter-campaign/cycle-67/`.

## ADR-085: Seal the campaign on clear (levels)
Date: 2026-11-08
Status: accepted
Context: Campaign clear is recorded when the live wave reaches 4, but `_build_wave` had already queued wave 4 and the sim kept spawning it during the four-second victory banner. A staged win reproduced four live wave-4 enemies (mite, brute, mite, wisp) and four spawn voices while the `CAMPAIGN CLEAR` banner was still up; a completed run could be attacked.
Decision: Add `Sim.victory` and `seal_campaign()`: clear the queue, set `spawn_t` to infinity, skip wave-clear advancement after victory, and guard `_build_wave`. `ShooterGame` calls `seal_campaign()` when it sets `campaign_cleared`. The banner, win recording, wave number, HUD and all level geometry are unchanged; there is no new difficulty tuning.
Consequences: Suite 225/225 green (one new test); determinism 1800 ok (hash a1528cee); aikit 4/4; the existing fairness replay still witnesses a win without a reference re-record. The three-second banner pair at 960x540 seed 1 changes 18,368 px (3.54%, bbox 367,12-947,459), mean luma 34.13 -> 34.19, draws 8 -> 6, triangles 942 -> 290. `campaign 180` before/after: alive enemies 4 -> 0, audio 9 -> 5, victory false -> true, wave 4 and banner 1.0 s in both, hp 100, 0 hurts, 0 drops. Evidence: `evidence/cycle-68.json`, images in workspace `shots/shooter-campaign/cycle-68/`.

## ADR-086: Persistent campaign-complete line (UI readability)
Date: 2026-11-08
Status: accepted
Context: Cycle 68 sealed wave construction at the campaign win, so the arena is empty after the four-second clear banner. Once the banner expires the HUD looks like an ordinary wave-4 lull, with no enemies and no message explaining that the run is complete.
Decision: Draw a compact accent `CAMPAIGN COMPLETE` line at y=116 when `sim.alive`, `sim.victory` is set and `campaign_clear_t` has expired. The existing `CAMPAIGN CLEAR` banner keeps the screen while its timer runs, so the lines never double up. Draw-only: no sim, wave, save, camera or input change.
Consequences: Suite 228/228 green (three new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The 300-frame post-banner pair at 960x540 seed 1 changes 988 px (0.19%, bbox 379,116-580,129), mean luma 33.07 -> 33.40, draws 6, triangles 290. `campaign 300` before/after keeps hash `236ec766...`, wave 4, victory true, banner 0, no enemies, hp 100, audio 5, 0 drops. Evidence: `evidence/cycle-69.json`, images in workspace `shots/shooter-campaign/cycle-69/`.

## ADR-087: Visible ammo-cache drops (graphics/effects)
Date: 2026-11-08
Status: accepted
Context: The reward stream drops an ammo cache on 3% of kills and keeps it for 8 seconds, but `game.py` had no cache node. The cache was invisible, so players could only collect it by accident; the only cue was the collection sound/caption after walking over it.
Decision: Add a pool of four hidden nodes sharing `mesh.pickup` and a new amber emissive `material.cache`, and show one per active `sim.caches` entry with a small spin/bob at the recorded position. Pool size caps presentation at four; lifetime, pickup volume, reserve amount and reward RNG stay in sim. No colliders, save data or sim fields change.
Consequences: Suite 231/231 green (three new tests); determinism 1800 ok (hash a1528cee); aikit 4/4; the frame-budget test still passes. The staged pair at 960x540 seed 1 changes 5,406 px (1.04%, bbox 426,92-911,423; 5,130 px in the 3D scene, bbox 426,346-515,423), mean luma 32.45 -> 33.49, draws 7, triangles 302, shadow calls 35. `kite 3000` keeps hash `54bdc60c...`, 30 kills, hp 76, audio 437, 0 drops, 2 cache rewards and 1 cache collection; before/after are identical because this is scene-only. Evidence: `evidence/cycle-70.json`, images in workspace `shots/shooter-campaign/cycle-70/`.

## ADR-088: Ammo-cache drop cue (audio cues)
Date: 2026-11-08
Status: accepted
Context: Cycle 70 made dropped ammo caches visible, but the `cache_drop` event stayed unmapped. The cache appeared silently; only its later collection had a voice and caption, so a player looking away from the kill could miss the drop entirely.
Decision: Map `cache_drop` to a distinct 0.05 s 1320 Hz sine at 0.5 gain and an accent `AMMO CACHE DROP` caption. The collection (`CACHE AMMO`) and kill voices remain; cache lifetime, reserve amount, reward RNG and sim state are untouched.
Consequences: Suite 234/234 green (three new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The forced-drop pair at 960x540 seed 1 changes 5,388 px (1.04%, bbox 378,164-827,459), mean luma 35.78 -> 35.71, draws 11, triangles 710; audio voices 3 -> 4. `kite 3000` keeps hash `54bdc60c...` and records exactly 2 cache_drop clips at frames 570/1455 (audio 437 -> 439) while the same run collects 1 cache, with 0 drops. WAV/spectrogram report a 0.05 s voice at peak 1.0. Evidence: `evidence/cycle-71.json`, audio in workspace `shots/shooter-campaign/cycle-71/`.

## ADR-089: Visible corrupt-profile recovery (progression/saves)
Date: 2026-11-08
Status: accepted
Context: `ProfileStore._recover` quarantines a corrupt file and falls back to `.bak` or defaults, but the game could not tell which happened. A corrupt save with no backup silently reset wins/history behind a normal debrief; a backup restore was equally invisible.
Decision: Record `recovered` and `recovered_from_backup` on the store during `_recover`, expose them on `ShooterGame`, and add a debrief line: red `PROFILE RESET` when defaults were used, amber `PROFILE RECOVERED` when `.bak` restored the profile. Priority is disabled profile, then recovery, then save error. Quarantine names, backup policy, schema checks and atomic saves are unchanged.
Consequences: Suite 238/238 green (four new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The corrupt-without-backup death pair at 960x540 seed 1 changes 13,136 px (2.53%, bbox 281,334-678,449), mean luma 47.08 -> 45.68, draws 6, triangles 278. `profile_corrupt 240` before/after same death hash `f8cd9e28...`, recovered false -> true, from_backup false, last_run recorded, runs 1, save_errors 0, hp 0, 0 drops; the corrupt file is quarantined and a new profile saved. Evidence: `evidence/cycle-72.json`, images in workspace `shots/shooter-campaign/cycle-72/`.

## ADR-090: Movement viewmodel bob (combat feel)
Date: 2026-11-08
Status: accepted
Context: The first-person gun stayed rigidly locked to the camera while walking or sprinting; only recoil and reload moved it. Movement read as a floating camera rather than a carried weapon.
Decision: Add a deterministic figure-eight bob to the existing viewmodel nodes while grounded: `bob_right` 0.022 m and `bob_up` 0.016 m at 8 Hz, scaled by horizontal speed up to 6.4 m/s. Amounts live in `juice.viewmodel`; the bob is zero at rest and in the air. No sim, movement, aim, draw or save change.
Consequences: Suite 241/241 green (three new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The sprint pair at 960x540 seed 1 changes 3,043 px (0.59%, bbox 551,333-665,411), mean luma 30.73 -> 30.68, draws 6, triangles 242; the gun body moves from x 0.210 to 0.232 at the captured phase. `strafe 300` keeps hash `14a48660...`, 30 shots, hp 92, 1 hurt, audio 36, peak 8, 0 drops. Evidence: `evidence/cycle-73.json`, images in workspace `shots/shooter-campaign/cycle-73/`.

## ADR-091: Close the brute melee dead zone (enemies/bosses)
Date: 2026-11-08
Status: accepted
Context: The brute movement branch advanced only while farther than 3.0 m, but the slam required distance <=2.5 m. A brute at 2.7 m from a stationary player therefore stood still forever, outside its own range; the reproduced run stayed at hp 100 with no events for 180 frames.
Decision: Change the movement gate to `dist > attack_range`, so the brute closes the final half metre and enters its existing slam range. Damage, range, reach, cooldown, pause behavior, LOS and all other enemy branches are unchanged; no new data or nodes.
Consequences: Suite 242/242 green (one new test); determinism 1800 ok (hash a1528cee); aikit 4/4; the recorded fairness reference still replays a witnessed win without re-recording. The idle pair at 960x540 seed 1 changes 101,970 px (19.67%, bbox 0,12-959,539), mean luma 38.04 -> 38.39, draws 7, triangles 302. `brute_gap 180` before/after: hp 100 -> 80, hurts 0 -> 1, audio 0 -> 2, brute_slam now fires; both runs stay alive at wave 2. Evidence: `evidence/cycle-74.json`, images in workspace `shots/shooter-campaign/cycle-74/`.

## ADR-092: Platform base frame (levels)
Date: 2026-11-08
Status: accepted
Context: The low platform's dark side face merged into the floor from the approach. The cycle-61 frame marked the top landing edge but not the 0.7 m step, so its height was ambiguous from the ground. A first attempt placed base strips on the same inside footprint and they were completely occluded by the platform volume.
Decision: Extend `_platform_frame_mesh` with a `bottom_y` level and outset the base strips by their thickness so they sit just outside the platform footprint at y 0.00-0.08. Top and base now live in one 8-strip mesh, one node and one shadow draw; material, colliders and sim are unchanged.
Consequences: Suite 244/244 green (two new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The farther approach pair at 960x540 seed 1 changes 1,178 px (0.23%, bbox 344,92-899,298; 1,038 px in the 3D scene, bbox 344,293-615,298), mean luma 39.44 -> 39.57, draws 7, triangles 218. `platform 120` keeps hash `c1603d79...`, 28 frames, landed at y 1.6, hp 100, score 250, 0 drops. Evidence: `evidence/cycle-75.json`, images in workspace `shots/shooter-campaign/cycle-75/`.

## ADR-093: Critical tag in the kill feed (UI readability)
Date: 2026-11-08
Status: accepted
Context: Cycle 64 added a transient `CRITICAL` caption and chime, but the persistent kill feed still recorded `MITE +220` with no marker. Once the caption faded, a critical kill was indistinguishable from a normal kill except by comparing scores.
Decision: Set a same-update pending flag when the sim's `critical` event arrives and consume it in the following `kill:<type>:<total>` entry: prefix `CRIT `, store `critical=True`, and draw that entry in accent orange ahead of the normal white/warden-red colors. Normal kills and the 2.5 s feed lifetime are unchanged; no sim, reward or save data changes.
Consequences: Suite 246/246 green (two new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The forced-critical pair at 960x540 seed 1 changes 900 px (0.17%, bbox 16,104-181,117), mean luma 35.60 -> 35.62, draws 10, triangles 698. `kite 3000` keeps hash `54bdc60c...`, 30 kills, hp 76, 4 hurts, audio 439, 0 drops, 4 critical rewards. Evidence: `evidence/cycle-76.json`, images in workspace `shots/shooter-campaign/cycle-76/`.

## ADR-094: Overdrive weapon glow (graphics/effects)
Date: 2026-11-08
Status: accepted
Context: Overdrive is a prominent eight-second x2 state, but only the HUD timer line changed. The held weapon kept its normal material, so the power-up had no first-person visual state.
Decision: Register a brighter per-weapon `material.gun_<weapon>_od` variant and select it for both viewmodel nodes while `overdrive_t > 0`; fall back to the normal material when the timer ends. Variants brighten color, specular, shininess and emissive; no new nodes, draws, colliders, sim state or timer changes.
Consequences: Suite 248/248 green (two new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The staged pair at 960x540 seed 1 changes 5,338 px (1.03%, bbox 546,326-655,411), mean luma 32.74 -> 33.19, draws 6, triangles 290. `overdrive 10` before/after same hash `7c1080ce...`, 10 frames, t 7.83, reserve 90, cue OVERDRIVE, hp 100, audio 1, 0 drops. Evidence: `evidence/cycle-77.json`, images in workspace `shots/shooter-campaign/cycle-77/`.

## ADR-095: Clutch wave-clear cue (audio cues)
Date: 2026-11-08
Status: accepted
Context: The sim emitted `clutch` when a wave cleared at 30 HP or less, but the game ignored it; only the generic wave voice/caption played. A notable survival moment vanished into an ordinary WAVE CLEAR.
Decision: Map `clutch` to a 0.12 s 520 Hz square voice and a `CLUTCH CLEAR` caption. Because the wave-clear event follows in the same update, a one-frame pending flag keeps the clutch caption while still playing the wave voice; normal clears keep WAVE CLEAR. No sim, HP, score or save change.
Consequences: Suite 251/251 green (three new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The low-HP clear pair at 960x540 seed 1 changes 1,260 px (0.24%, bbox 396,164-827,459), mean luma 34.00 -> 33.99, draws 9, triangles 434; voices 1 -> 2. `clutch 1` before/after same hash `ae293bcd...`, wave 2, hp 30, count 1, cue WAVE CLEAR -> CLUTCH CLEAR, audio 1 -> 2, 0 drops. WAV/spectrogram report a 0.12 s voice at peak 1.0. Evidence: `evidence/cycle-78.json`, audio in workspace `shots/shooter-campaign/cycle-78/`.

## ADR-096: Clear the stale save warning after a retry (progression/saves)
Date: 2026-11-08
Status: accepted
Context: Cycle 58 made failed profile writes visible via `profile_save_errors`, a lifetime counter. One transient locked write therefore left `PROFILE NOT SAVED` on every later debrief, even after a later save succeeded, falsely implying current progress was unsafe.
Decision: Track `profile_save_failed` as the latest write outcome: set it on failure, clear it on success, and base the debrief warning on it. Keep `profile_save_errors` as the lifetime telemetry counter for soak/evidence. Atomic writes and schema policy are unchanged.
Consequences: Suite 253/253 green (two new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The failed-then-successful pair at 960x540 seed 1 changes 13,360 px (2.58%, bbox 281,334-678,449), mean luma 45.91 -> 47.28, draws 9, triangles 422: warning present before, absent after, with both runs at save_errors 1. `save_retry 120` before/after same hash `99f337e7...`, 2 frames, wave 2, hp 0, audio 4, last_run recorded, runs 1, save_errors 1, save_failed false, 0 drops. Evidence: `evidence/cycle-79.json`, images in workspace `shots/shooter-campaign/cycle-79/`.

## ADR-097: Pulsing low-health edge warning (combat feel)
Date: 2026-11-08
Status: accepted
Context: The <=30 HP warning was a static 0.28-alpha red edge. Critical health looked identical at every moment and could blend into the scene.
Decision: Pulse the four edge strips' alpha between 0.20 and 0.44 at 6 Hz from `sim.time`, with the range and rate in `juice.low_hp_cue`. Draw-only: no sim, HP, damage, camera or save change.
Consequences: Suite 255/255 green (two new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The hp-30 peak pair at 960x540 seed 1 changes 17,856 px (3.44%, bbox 0,0-959,539), mean luma 33.20 -> 33.63, draws 6, triangles 290. `clutch 1` before/after keeps hash `ae293bcd...`, hp 30, wave 2, cue CLUTCH CLEAR, audio 2, 0 drops. Evidence: `evidence/cycle-80.json`, images in workspace `shots/shooter-campaign/cycle-80/`.

## ADR-098: Warden slam obeys cover LOS (enemies/bosses)
Date: 2026-11-08
Status: accepted
Context: The warden slam applied its 30-damage hit on distance and vertical reach only. Unlike the brute and wisp branches, it never checked line of sight, so a slam behind the 2 m north cover still damaged the player at 70 HP in the reproduced frame.
Decision: Add the shared `_enemy_has_los()` gate to the warden slam damage condition. The windup, slam event, ring, 4.5 m range, reach and cooldown are unchanged; open-field slams still hit.
Consequences: Suite 257/257 green (two new tests); determinism 1800 ok (hash a1528cee); aikit 4/4; the fairness reference still replays a win without re-recording. The covered-slam pair at 960x540 seed 1 changes 123,656 px (23.85%, bbox 0,12-959,539), mean luma 60.76 -> 61.14, draws 8, triangles 302. `warden_cover 10` before/after: hp 70 -> 100, hurts 1 -> 0, audio 2 -> 1, wave 3 in both; hashes differ by design. Evidence: `evidence/cycle-81.json`, images in workspace `shots/shooter-campaign/cycle-81/`.

## ADR-099: Player-width west platform gap (levels)
Date: 2026-11-08
Status: accepted
Context: The low platform's west face sat 0.5 m from the wall, narrower than the 0.7 m player body. The visible rear strip looked walkable but blocked the player at z 11.65; only a full detour around the east/south sides worked.
Decision: Move the platform center 0.5 m east (x -16.0 to -15.5), widening the west strip to 1.0 m while keeping its 6x6 footprint, 0.7 m height, rim, base frame and launch pad data-driven. No new nodes or collision tuning.
Consequences: Suite 259/259 green (two new tests); determinism 1800 ok (hash a1528cee); aikit 4/4; the fairness reference still replays a win without re-recording. The west-approach pair at 960x540 seed 1 changes 19,128 px (3.69%, bbox 0,305-494,539), mean luma 53.40 -> 52.36, draws 7, triangles 218. `west_gap 240` before/after: final z 11.65 -> 19.15, both hp 100, 0 hurts, 0 drops; hashes differ by design. Evidence: `evidence/cycle-82.json`, images in workspace `shots/shooter-campaign/cycle-82/`.

## ADR-100: Warden bar yields on death (UI readability)
Date: 2026-11-08
Status: accepted
Context: Cycle 53 hid the crosshair target bar on death, but the warden bar was still drawn whenever an alive warden existed. A boss-fight death showed `WARDEN 600/600` over `YOU DIED` and the run debrief.
Decision: Gate the warden bar block with `sim.alive`, matching the target bar. The live boss bar, boss core, damage, AI and save state are unchanged.
Consequences: Suite 261/261 green (two new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The death-frame pair at 960x540 seed 1 changes 4,864 px (0.94%, bbox 338,98-621,127), mean luma 33.15 -> 32.55, draws 7, triangles 470. `boss_death 10` before/after same hash `f1c79051...`, hp 0, boss alive, last_run recorded, audio 3, 0 drops. Evidence: `evidence/cycle-83.json`, images in workspace `shots/shooter-campaign/cycle-83/`.

## ADR-101: Tracers start at the gun muzzle (graphics/effects)
Date: 2026-11-08
Status: accepted
Context: Player tracer beams began at the camera eye, so they appeared to leave the crosshair while the viewmodel sat lower-right. The gun looked detached from its shots even though the muzzle flash was aligned.
Decision: Add `Sim.muzzle_position()` using the DATA viewmodel barrel forward/right/down values plus half the barrel length, and use that point for the tracer `x0/y0/z0`. The hitscan ray, damage origin, spread, wisp tracers and all sim state stay unchanged; only the drawn beam start moves.
Consequences: Suite 263/263 green (two new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The clean-shot pair at 960x540 seed 1 changes 5,583 px (1.08%, bbox 350,268-559,539), mean luma 34.19 -> 34.34, draws 9, triangles 322; the start moves from eye (0.00,1.62,8.00) to muzzle (0.21,1.43,7.03). `strafe 300` keeps hash `14a48660...`, 30 shots, hp 92, 1 hurt, audio 36, peak 8, 0 drops. Evidence: `evidence/cycle-84.json`, images in workspace `shots/shooter-campaign/cycle-84/`.

## ADR-102: Overdrive-kill reward cue (audio cues)
Date: 2026-11-08
Status: accepted
Context: Kills during the eight-second x2 overdrive emitted `overdrive_hit`, but the game ignored it; only the normal kill voice and doubled score pop acknowledged the payoff.
Decision: Map `overdrive_hit` to a distinct 0.07 s 760 Hz square voice at 0.55 gain and an `OVERDRIVE KILL` caption; when a critical is already pending, the caption reads `OVERDRIVE CRIT` while the kill feed still gets its CRIT tag. Reward math, kill voice and sim state are unchanged.
Consequences: Suite 266/266 green (three new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The forced-kill pair at 960x540 seed 1 changes 5,076 px (0.98%, bbox 384,164-827,459), mean luma 36.72 -> 36.64, draws 10, triangles 698; audio voices 3 -> 4. `overdrive_kill 1` before/after same hash `00065237...`, 1 kill, score 220, t 2.98, cue '' -> OVERDRIVE KILL, audio 3 -> 4, 0 drops. WAV/spectrogram report a 0.07 s voice at peak 1.0. Evidence: `evidence/cycle-85.json`, audio in workspace `shots/shooter-campaign/cycle-85/`.

## ADR-103: Restore a backup when the main profile is missing (progression/saves)
Date: 2026-11-08
Status: accepted
Context: After a corrupt main was quarantined and `.bak` loaded in memory, quitting before the next save left no main file. On the next launch `load()` caught `FileNotFoundError` and returned defaults without consulting the backup, silently discarding the recovered best/wins.
Decision: Extract `ProfileStore._backup_profile()` (read, validate, normalize, set `recovered`/`recovered_from_backup`) and call it both inside `_recover` and on `FileNotFoundError`. A missing main with a valid backup restores the backup; a first launch with neither still returns defaults. Schema, quarantine and atomic write policy are unchanged.
Consequences: Suite 269/269 green (three new tests); determinism 1800 ok (hash a1528cee); aikit 4/4. The restart pair at 960x540 seed 1 changes 13,048 px (2.52%, bbox 281,16-678,427), mean luma 48.20 -> 47.05, draws 6, triangles 278. `profile_backup_restart 240` before/after same death hash `f8cd9e28...`: best_score 1500 -> 4321, wins 0 -> 2, recovered false -> true, from_backup false -> true, runs 1, 0 drops. Evidence: `evidence/cycle-86.json`, images in workspace `shots/shooter-campaign/cycle-86/`.

## ADR-104: Telegraph the brute slam (combat feel)
Date: 2026-11-08
Status: accepted
Context: The brute dealt its 20-damage slam on the first in-range frame. Unlike the warden, it had no windup event, caption or visual tell, so the hit could not be read or dodged; only the post-hit `brute_slam`/`hurt` cues fired.
Decision: Split the brute attack into a 0.35 s windup and a delayed slam. The windup emits `brute_windup`, plays a 0.14 s 140 Hz square at 0.55 gain, shows a `BRUTE WINDUP` caption and swells the body by a 10% sine; the slam event, damage, range, LOS, vertical reach and 2.0 s cooldown are unchanged, and the slam re-checks range/LOS/reach at impact so stepping out during the tell dodges it. Tuning lives in `enemies.json` as `windup_s`; old tests step through the tell instead of asserting a first-frame hit.
Consequences: Suite 271/271 green (two new windup tests; three tests updated for the delay); determinism 1800 ok (hash a1528cee); aikit 4/4. The one-update pair at 960x540 seed 1 changes 34,916 px (6.74%, bbox 0,56-959,539), mean luma 38.59 -> 39.04, draws 7, triangles 302; before reads `BRUTE SLAM`/HP 80, after `BRUTE WINDUP`/HP 100. `brute_windup 60` moves the hurt from frame 1 to frame 23 while hp still ends at 80; `brute_gap 240` and `brute 60` still take the slam, and the campaign fairness reference still wins. Audio probe: 21 cues, brute windup 0.14 s peak 1.0. Evidence: `evidence/cycle-87.json`, images/audio in workspace `shots/shooter-campaign/cycle-87/`.

## ADR-105: Keep enemy crowds apart (enemies/bosses)
Date: 2026-11-08
Status: accepted
Context: Enemy movement was cover-aware but had no enemy-enemy term, so mites converging on the same player-ring point stacked at one coordinate: four staged mites ended at (-0.02, 6.83) with min pair gap 0.000 and read as a single blob, while every bite came from that one point.
Decision: Add Sim._separate_enemies(), a deterministic soft-spacing pass after enemy movement: alive pairs closer than the sum of their DATA radii plus enemy_separation.clearance are pushed apart by half the deficit at enemy_separation.strength, up to three passes. A cover blocks a nudge, the arena clamp still applies, and an exact stack uses a stable golden-angle direction derived from pair indices, so no RNG is consumed. Tuning lives in levels.json (strength 0.5, clearance 0.02, passes 3). Because the witnessed campaign actions no longer won with spacing, ot_campaign.json was re-recorded from the adaptive kite run (win at frame 2486, wave 4, 30 kills, score 11560, hp 38, hash b425a57...).
Consequences: Suite 273/273 green (two new tests); determinism 1800 ok (hash b25db520, new enemy positions by design); aikit 4/4. The staged four-mite pair at 960x540 seed 1 changes 67,147 px (12.95%, bbox 0,398-946,539), mean luma 35.32 -> 42.80, draws 7, triangles 1570. enemy_spacing 90 before/after: final slack -1.0 -> +0.02, overlap frames 90 -> 16, both hp 100 with 0 hurts and 0 drops; kite 3000 wins at wave 4 with 30 kills / 11560 / hp 38. Evidence: evidence/cycle-88.json, images in workspace shots/shooter-campaign/cycle-88/.

## ADR-106: Drive the warden core with a keystone state machine (testbed)
Date: 2026-11-08
Status: accepted
Context: The shooter is the testbed for Keystone. Keystone recently added deterministic parameter-driven animation state machines (keystone.animation_state), a file-backed .kstate library (keystone.state_machine_library), and scene pose application (keystone.animation.apply_pose); the shooter still hand-rolled the boss core's binary windup swell as 1.0 + 0.18. The new functions needed a real consumer, not a synthetic demo.
Decision: Author shooter/data/warden_core.kstate through StateMachineLibrary.save with two looping scale clips on the warden-core node (calm breathe 1.0-1.06 over 1.2 s, charge pulse 1.0-1.32 over 0.5 s) and two transitions on the existing windup parameter. At runtime ShooterGame.build_scene loads the machine through StateMachineLibrary.load; _sync_scene(dt) sets the parameter from the warden's windup_t, advances the machine, calls pply_pose, and re-anchors the sampled core transform to the sim position. A missing asset falls back to the old static pulse. Sim damage, timing and the deterministic hash never read the machine.
Consequences: Suite 278/278 green (five new tests covering the library entry, clip targets, calm-to-charge transitions, game wiring and the no-warden guard); determinism 1800 ok (hash b25db520); aikit 4/4. The charge-peak pair at 960x540 seed 1 changes 10,679 px (2.06%, bbox 366,230-541,477), mean luma 36.57 -> 37.21, draws 9, triangles 650; before the core sits at 1.18 with no machine, after it peaks at 1.32 in charge. slam 60 before/after share hash 4580b9da..., 43 frames, hp 70, one hurt and identical windup/slam frames. Evidence: evidence/cycle-89.json, images in workspace shots/shooter-campaign/cycle-89/.

## ADR-107: Move the launch-pad pulse onto a keystone lifecycle component (testbed)
Date: 2026-11-08
Status: accepted
Context: Keystone recently added a deterministic component lifecycle (ComponentRuntime, commit f8e4aaa): hook-bearing components on scene nodes start once, update per fixed tick in traversal order and stop in reverse. The shooter testbed had no consumer; the launch pad's pulse was another hardcoded sine inside _sync_scene.
Decision: Add PadPulseComponent (update hook only) and attach one instance to the existing platform-pad node. ShooterGame.build_scene creates and starts one ComponentRuntime; update advances it with the fixed dt before the scene sync, and the pad's base/amplitude/speed now live in juice.json:pad_pulse. Remove the old _sync_scene sine block. The pad node, material, draw calls and collision are unchanged; the component only writes the node transform.
Consequences: Suite 279/279 green (two lifecycle tests: the started runtime, 32 ticks, pulse peak and fresh-build base); determinism 1800 ok (hash b25db520); aikit 4/4. The same-view pair at 960x540 seed 1 changes exactly 0 px (bbox null), mean luma 41.05 -> 41.05, draws 7, triangles 218: the keystone lifecycle reproduces the old pulse pixel-for-pixel. platform 120 before/after share hash c1603d79..., 28 frames, score 250, hp 100, 0 hurts. Evidence: evidence/cycle-90.json, images in workspace shots/shooter-campaign/cycle-90/.

## ADR-108: Build the warden core from a keystone material graph (testbed)
Date: 2026-11-08
Status: accepted
Context: Keystone supports declarative material graphs that validate and evaluate JSON node graphs into a Material. The shooter testbed still registered the boss core as a hardcoded Material(color, specular, shininess, emissive), so the graph evaluator and its checker/texture path had no consumer.
Decision: Add shooter/data/core_material.json with a 16x16 core-checker checker node feeding a material node (color 1.0/0.88/0.55, emissive 1.0/0.48/0.08, specular 0.8, shininess 64, metallic 0.1, roughness 0.4). ShooterGame.build_scene loads the document, validates/evaluates it through MaterialGraph.from_dict(...).evaluate() and registers the result as material.boss_core; the node, sphere mesh, geometry and sim are unchanged.
Consequences: Suite 282/282 green (three graph tests: evaluation, deterministic checker, game registration); determinism 1800 ok (hash b25db520); aikit 4/4. The charge-peak pair at 960x540 seed 1 changes 10,627 px (2.05%, bbox 421,230-541,351), mean luma 37.21 -> 36.42, draws 9, triangles 650; the core now shows a mechanical checker pattern instead of a smooth orb. slam 60 before/after share hash 4580b9da..., 43 frames, hp 70, one hurt. Evidence: evidence/cycle-91.json, images in workspace shots/shooter-campaign/cycle-91/.
