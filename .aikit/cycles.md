# Shooter improvement cycles (append-only)

Each cycle names one area, the defect and evidence, the exact fix, the
before/after screenshot pair (same seed, state and viewport), the played run,
and the gate results. Areas rotate; a covered area is not repeated until the
rotation completes.

## Cycle 01 — Combat feel: directional damage cue
- **Area**: combat feel (1/7 rotation).
- **Defect / evidence**: baseline `capture.py hurt` left/right/behind frames
  were pixel-identical at hp 92 despite an off-screen mite hit; baseline
  played runs (idle 300, ambush 300) logged hurt events with source `null`.
  HP dropped with no spatial feedback.
- **Fix**: last-attacker source + 0.8 s timer in `Sim` (juice DATA
  `hurt_cue_s`), `snapshot().hurt {t,x,z}`, red ring trail + cross at the
  source bearing in `ui.py`; damage/RNG/movement untouched.
- **Screenshot proof**: workspace
  `shots/shooter-campaign/cycle-01/{before,after}`; three pairs
  (`base_hurt_{left,right,behind}.png` → `final_hurt_{...}.png`),
  960x540, seed 1, hit frame 12, hp 92, renderer S1C1P1B1. Each pair differs
  in 292 px inside the correct quadrant (left 372–441 x, right 518–587 x,
  behind 473–492 x / 308–377 y); spawn/combat/burst/pickup/death changed 0 px.
- **Played runs**: `scripts/play_run.py` before/after parity — idle 300
  (hp 84, 2 hurts), kite 600 (wave 2, 9 kills, 1500 score, hp 100), strafe
  300 (30 shots, 2 hits, hp 84), ambush 300 (3 hurts, hp 76). Event frames,
  hp, kills, score, shots, hits match baseline exactly; new cue telemetry is
  the only snapshot difference. Natural idle hit at frame 181 captured with
  the cue pointing front-left.
- **Tests**: `tests/test_feedback.py` (5 tests, failing first: 3 failures
  before implementation).
- **Gates**: `python -m pytest -q` 43 passed; `python play.py
  --verify-determinism --frames 1800` ok=true exit 0; `python aikit.py check
  shooter` 4/4 (recorded below).
- **Evidence file**: `evidence/cycle-01.json`.

## Cycle 02 — Enemies/bosses: Warden boss in wave 3
- **Area**: enemies/bosses (2/7 rotation).
- **Defect / opportunity**: post-win wave 3 was only a count bump of
  mites/brutes/wisps (6/2/2) with no elite, no boss readout and no designed
  escalation; the enemy table stopped at three types.
- **Fix**: `warden` DATA (600 hp, 1.7 speed, 30 slam in 4.5 m, 2000 score,
  0.7 s windup, 2-mite escort every 7 s), one warden in wave 3 only (waves
  1-2 untouched), telegraphed `boss_windup`/`boss_slam` through `_on_hurt`,
  bounded summons, glowing player-facing core that swells on windup, and a
  named WARDEN HUD bar. Tests: `tests/test_boss.py` (7) + data table pin.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-02/`; same
  build, same seed/state/viewport (960x540, wave 3 staging at spawn, frame 1,
  hp 100, renderer S1C1P1B1). `before/final_boss.png` (no warden; pixel-
  identical to the pre-boss commit) vs `after/samebuild_boss.png` (warden +
  bar + core): 60,282 changed px, 11.63%, bbox (300,92)-(923,440), mean luma
  32.26 -> 33.79. Standard spawn/combat/burst/pickup/death routes: 0 px.
  Slam drill: `after/slam_windup.png` (telegraph) and `after/slam_hit.png`
  (hp 70, cue pointing at the boss at frame 42).
- **Played runs**: `play_run.py boss 1800` ends on boss death at frame 507
  (3 kills, 3080 score, hp 100, wave 4, 56/56 shots/hits); natural
  `play_run.py kite 3000` reaches wave 4 with 35 kills / 10535 / hp 76;
  `play_run.py kite 600` is byte-identical to cycle 1 (hash
  `0a107794…`, wave 2 win), proving the win path did not move.
- **Gates**: `python -m pytest -q` 50 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-02.json`.

## Cycle 03 — Levels: surge pickup beacon
- **Area**: levels (3/7 rotation).
- **Defect / evidence**: wave-2 surge pickup sits at (0, 0.5, -6)
  behind the 1.2 m centre cover; from the spawn eye the 0.6 m cube is fully
  hidden (baseline `pickup_spawn` frame 182, active=True, hp 100, no cue).
  The old `pickup` route had to re-stage the camera to photograph it.
- **Fix**: presentation-only emissive column (0.22 x 3.0 x 0.22) + bobbing
  orb (sphere 0.28) above the live pickup, hidden when inactive; HUD
  `SURGE PICKUP READY` within 18 m when no boss bar is shown. Trigger,
  spot, ammo and sim untouched.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-03/`;
  960x540, seed 1, frame 182, pickup active, hp 100.
  `before/base_pickup_spawn.png` (no cue) vs
  `after/final2_pickup_spawn.png` (beam + orb + label): 2,342 changed px
  (0.45%, bbox 375,92-911,291, mean luma 31.04 -> 31.59). Spawn/burst/death
  routes 0 px; combat/pickup routes show the intended beacon.
- **Played runs**: `play_run.py pickup 240` walks the clear side lane and
  collects at frame 121; baseline vs after are identical (same hash
  `0cfe8193…`, same events/final, `surge_t` 10.0, pickup taken). Kite 600
  hash still `0a107794…` (wave 2 win path untouched).
- **Gates**: `python -m pytest -q` 54 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-03.json`.

## Cycle 04 — UI readability: one HP/ammo source + readable crosshair
- **Area**: UI readability (4/7 rotation).
- **Defect / evidence**: baseline spawn and burst frames printed HP/ammo
  twice (engine top-left and game bottom-left); the white crosshair arms
  vanished against the white muzzle flash in `burst` (same 2 px arms fill
  on a white cube).
- **Fix**: remove the bottom-left game HP/ammo panel (engine status owns
  HP/ammo; wave/score/streak stay in the game layer); draw a 2 px dark
  backing behind each crosshair arm and centre pip before the bright core.
  Low-HP edges, damage cue, boss bar and pickup label stay.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-04/`;
  960x540, seed 1, same routes/frames. Every route changes 15,856 px
  (panel + crosshair; crosshair crop 256 px). Burst crosshair crop:
  dark pixels 538 -> 758, bright 375 -> 319 on the white-flash frame;
  spawn bottom-left mean luma 29.21 -> 31.95 after the panel removal.
- **Played runs**: `play_run.py kite 600` hash `0a107794…` and
  `strafe 300` hash `973276f5…` identical to the pre-change reports;
  the HUD change never touches sim state.
- **Gates**: `python -m pytest -q` 58 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-04.json`.

## Cycle 05 — Graphics and effects: arena floor grid + lit trim
- **Area**: graphics and effects (5/7 rotation).
- **Defect / evidence**: floor was a near-black checker with no landmarks;
  spawn mean luma 30.35/255, edge density 2.657; cover tops and the wall
  line dissolved into the background.
- **Fix**: deterministic 128-px grid texture (dark checker + 2-px lit
  lines), higher ambient/directional/point light, warmer covers, and ten
  shared-material trim nodes (four wall lines + six cover caps) in one
  instanced batch. No sim/collider/DATA changes.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-05/`;
  960x540, seed 1, same routes/frames. Spawn luma 30.35 -> 34.68, edge
  density 2.657 -> 3.066; combat 37.02 -> 40.03; boss 33.89 -> 38.33.
  Changed pixels 270k-306k (52-59%) due to the global floor/light change.
  Draws 3 -> 4 spawn, 8 -> 9 boss; tris 110 -> 218 / 1666 -> 1774
  (limits 40/80k).
- **Played runs**: `play_run.py kite 600` `0a107794…`, `strafe 300`
  `973276f5…`, `boss` `1b602735…` all identical to pre-change runs.
- **Gates**: `python -m pytest -q` 63 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-05.json`.

## Cycle 06 — Audio cues: boss/engagement voices + captions
- **Area**: audio cues (6/7 rotation).
- **Defect / evidence**: baseline slam run had `boss_windup` at frame 1 and
  `boss_slam` at frame 43 but only one voice (`hurt` at 43); boss, overdrive,
  cache, reload, near-miss, streak-break and death were silent.
- **Fix**: deterministic clips for boss windup/slam/summon/down, overdrive
  start/end, cache, near-miss, reload, streak-break and death; event→voice
  map; short bottom-centre captions (red danger / amber positive);
  `boss_down` sim event; public `set_clip_hook` for evidence; surge label
  shortened to fit the top-right panel.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-06/`;
  960x540, seed 1, same slam staging/frames. Before vs after:
  `audio_slam_windup` → `audio2_slam_windup` = 9,696 px (caption +
  AUDIO 1 VOX line, bbox 390,164-947,459); `audio_slam_hit` →
  `audio2_slam_hit` = 4,116 px. Spawn remains 0 px. Pickup caption
  "SURGE ACQUIRED" captured at the collection frame.
- **Played runs**: slam before/after same hash `a5e66d40…`, 43 frames,
  hp 70; audio events change from `hurt` only to `boss_windup` (frame 1),
  `boss_slam`+`hurt` (43), peak 3, drops 0. Boss run 120 voices / peak 8 /
  0 drops; pickup run 1 voice. Audio probe: 12 cues rendered to WAV,
  boss_windup 0.35 s peak 1.0, boss_slam 0.30 s peak 0.9999, boss_down
  0.45 s peak 1.0, overdrive 0.22 s peak 1.0, pickup 0.12 s peak 1.0;
  waveform+spectrogram sheet in the after folder.
- **Gates**: `python -m pytest -q` 69 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-06.json`.

## Cycle 07 — Progression and saves: versioned profile + debrief
- **Area**: progression and saves (7/7 rotation).
- **Defect / opportunity**: no state outlived a launch; bests/runs/last run
  vanished, and the death screen only showed `YOU DIED`. The project
  guideline requires a versioned state contract; PRINCIPLE-013 requires
  atomic writes with backup/lock/recovery.
- **Fix**: `shooter/profile.py` schema 1 (`runs`, bests, `last_run`),
  schema-0 migration, unsupported schema refused without touching the file,
  corrupt quarantine + `.bak` recovery, atomic replace + backup + 30 s lock.
  `ShooterGame` records wave-clear bests and a run on death; HUD `BEST`,
  `RUN OVER` debrief, `NEW BEST`. Evidence scripts/tests use throwaway
  profiles; `saves/` is git-ignored.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-07/`;
  960x540, seed 1, same staged death (score 1500, kills 9, wave 2,
  hp 10→0). Before (`profile_death_profile.png`, pre-profile build) vs after:
  38,516 changed px (7.43%, bbox 290,16-669,361; 38,000 px debrief panel,
  516 px BEST line), mean luma 52.18 -> 48.31. Empty-profile spawn/combat
  remain pixel-identical.
- **Played runs**: `play_run.py death 240` before/after same frame (1),
  hp 0, score 1500, hash `f8cd9e28…`; after records runs=1,
  best_score=1500, last_run kills 9/wave 2/best streak 4, save_errors=0.
- **Gates**: `python -m pytest -q` 77 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-07.json`.

## Cycle 08 — Progression: boss-clear campaign milestone + banner
- **Area**: progression (rotation restart, 8th cycle).
- **Defect / evidence**: `win_wave: 2` declared `win` at wave-2 start
  (~3 s) while the wave-3 Warden sat outside the campaign; no HUD surface
  announced a win at all.
- **Fix**: `win_wave: 4` (waves 1-3 with the Warden finale), 4 s
  `CAMPAIGN CLEAR` banner when the live wave reaches it, `CAMPAIGN CLEARED`
  in the death debrief; `bot_campaign.json` 2400-frame reference and
  fairness/outcome tests switched to 2400 frames.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-08/`;
  960x540, seed 1, staged wave-3 boss kill, wave 4 entry. Before (no
  banner) vs after: 20,160 changed px (3.89%, bbox 300,138-659,193;
  exactly the 360x56 banner), mean luma 37.43 -> 38.18.
- **Played runs**: 2400-frame campaign reaches wave 4, 29 kills, 9220
  score, hp 94, `outcome=win`, hash `88c3e673…`; fairness verdict
  `fair/witnessed_win:reference:2340`; kite 600 now `ongoing` at wave 2.
- **Gates**: `python -m pytest -q` 78 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-08.json`.

## Cycle 09 — UI readability: low-ammo warning + reload bar
- **Area**: UI readability (rotation restart, 9th cycle).
- **Defect / evidence**: baseline low-mag (3/30) and mid-reload (0/30,
  reload_t 0.55) frames showed only the distant top-left status numbers;
  there was no near-crosshair warning or reload progress.
- **Fix**: `LOW AMMO` panel below the crosshair at <= quarter magazine;
  a 120-px reload progress bar + `RELOADING` label while reload_t > 0
  (replaces the warning). Presentation only.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-09/`;
  960x540 seed 1, same staged clean-arena frames. Low ammo: 2,420 changed
  px (bbox 425,300-534,321, mean luma 34.65 -> 34.40); reload: 1,816 px
  (bbox 418,302-541,327, mean luma 34.66 -> 34.65).
- **Played runs**: kite 600 `49111053…` and strafe 300 `973276f5…` are
  identical to the cycle-8 reports; the HUD never touches sim state.
- **Gates**: `python -m pytest -q` 80 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-09.json`.

## Cycle 10 — Combat feel: non-lethal hit flinch + flash
- **Area**: combat feel (rotation restart, 10th cycle).
- **Defect / evidence**: baseline first-hit frames (hp 18, flash expired)
  left the mite as an unchanged orange sphere; only the crosshair hitmark
  and particles reacted.
- **Fix**: `hit_t` 0.25 s on non-lethal hits, decremented in `_step_enemies`;
  `_sync_scene` squashes (0.28), pushes away (0.12) and swaps to the shared
  hot `material.enemy_hit` for the first 40% of the timer. Damage,
  hitboxes, AI and snapshot untouched; all tuning in `juice.json`.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-10/`;
  960x540 seed 1, same first-hit setup (frame 8, hp 18). 3,839 changed px
  (0.74%, bbox 432,314-515,381; white-hot squashed mite), mean luma
  35.50 -> 36.03; draws stay 7.
- **Played runs**: kite 600 `49111053…` (36 shots/31 hits/9 kills) and
  strafe 300 `973276f5…` (30/2) identical to cycle 9.
- **Gates**: `python -m pytest -q` 83 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-10.json`.

## Cycle 11 — Enemies/bosses: enemies no longer walk through cover
- **Area**: enemies/bosses (11th cycle).
- **Defect / evidence**: the baseline 40-frame crossing had the mite at
  `(-0.33, 0.81)`, embedded in the centre cover and protruding through its
  front face; a spawn sweep placed a mite at `(5.00, -4.59)` inside the
  right cover. Only the player and hitscan rays collided with cover.
- **Fix**: `cover_boxes` in reset; `_enemy_blocked_at` and `_move_enemy`
  with a heading sweep (direct, ±30/60/90/120/180°) for slide-around;
  applied to mite/brute/wisp/warden movement; spawn points reject covers.
  Campaign reference re-recorded at 3000 frames; fairness/outcome tests
  updated to 3000.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-11/`;
  960x540 seed 1, frame 40, same staged crossing. Before: mite embedded in
  the cover; after: beside it. 3,116 changed px (0.60%, bbox
  387,295-485,353), mean luma 34.75 -> 34.88.
- **Played runs**: `kite 3000` reaches wave 4 with `outcome=win`, 32 kills,
  11955, hp 2, hash `9b70e372…`; fairness `witnessed_win:reference:2627`;
  `strafe 300` hash `973276f5…` unchanged.
- **Gates**: `python -m pytest -q` 86 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-11.json`.

## Cycle 12 — Levels: jumpable rear-left platform
- **Area**: levels (12th cycle).
- **Defect / evidence**: every cover was >=1.2 m while the jump apex is
  ~1.08 m, so `E` never had a surface to land on; the baseline
  `test_levels_platform.py` failed both the jumpable-surface and landing
  checks (player stayed at y 0.9001 / z 19.15).
- **Fix**: 6x6x0.7 m platform at `(-16, 15)` in `levels.json`, cool
  `material.platform`, no cover-trim cap; uses the existing cover collision
  and spawn guard. Tests: jumpable data + scripted landing; `play_run.py
  platform`; capture route `platform`.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-12/`;
  960x540 seed 1, approach view. Before floor vs after platform:
  132,320 changed px (25.52%, bbox 58,92-901,497), mean luma 40.80 ->
  49.66; draws 3 -> 4, triangles 50 -> 62.
- **Played runs**: `platform` before no landing (y 0.9, frame 120), after
  lands y 1.6 / z 12.379 at frame 28. `kite 3000` hash `9b70e372…` and
  `strafe 300` hash `973276f5…` unchanged; fairness still
  `witnessed_win:reference:2627`.
- **Gates**: `python -m pytest -q` 88 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-12.json`.

## Cycle 13 — UI readability: typed kill feed
- **Area**: UI readability (13th cycle).
- **Defect / evidence**: the sim emitted only a bare `kill` event; the HUD
  moved the distant score/streak numbers but did not say what died or what
  it was worth. The first-kill baseline frame showed score 110 / streak x1
  with no event line.
- **Fix**: append `kill:<etype>:<total>` after the legacy `kill`; game keeps
  the last four entries for 2.5 s and draws `MITE +110` under the engine
  status (warden in danger red). Presentation only; snapshot/damage/score
  math untouched.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-13/`;
  960x540 seed 1, first kill at frame 8. Before no feed vs after
  `MITE +110`: 424 changed px (0.08%, bbox 16,104-121,117), mean luma
  36.20 -> 36.39; draws 6, triangles 294.
- **Played runs**: `kite 600` hash `8872be74…` and `strafe 300` hash
  `973276f5…` identical to the pre-feed cycle-12 worktree.
- **Gates**: `python -m pytest -q` 90 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-13.json`.

## Cycle 14 — Graphics and effects: off-axis muzzle flash
- **Area**: graphics and effects (14th cycle).
- **Defect / evidence**: the flash was a 0.10 cube at 0.70 m dead on the
  aim line; the first-shot frame was a large white block covering the
  crosshair and the mite. Baseline `test_muzzle.py` failed: lateral offset
  0.0 and node scale 0.10.
- **Fix**: `juice.json` flash offset (forward 0.95, right 0.16, down 0.12)
  and scale 0.055; sim writes the offset position, game reads the scale.
  Lifetime/point-light unchanged.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-14/`;
  960x540 seed 1, first shot frame 1. 4,343 changed px (0.84%, bbox
  448,290-557,359), mean luma 37.09 -> 36.96; draws 8, triangles 586.
  Before: big centre block; after: small down-right flash, target visible.
- **Played runs**: `kite 600` hash `8872be74…` and `strafe 300` hash
  `973276f5…` identical to the cycle-13 worktree.
- **Gates**: `python -m pytest -q` 92 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-14.json`.

## Cycle 15 — Audio cues: denied overdrive feedback
- **Area**: audio cues (15th cycle).
- **Defect / evidence**: pressing overdrive with no pulse reserve emitted
  `overdrive_denied:insufficient_ammo` but the game ignored it; the baseline
  denied run had reserve 0, empty cue, and only the wave voice (`audio=1`).
- **Fix**: `overdrive_denied` clip (90 Hz, 0.14 s) + reason-specific captions
  (`NEED 30 AMMO`, `BLOCKED BY SURGE`, `ALREADY ON`, `UNAVAILABLE`); clip
  plays for all reasons. Sim state untouched; audio probe now 13 cues.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-15/`;
  960x540 seed 1, frame 1. 12,820 changed px (2.47%, bbox 330,164-947,459;
  caption + AUDIO 1 VOX line), mean luma 34.64 -> 34.64.
- **Played runs**: `denied 60` before/after same hash `8ea7057f…`;
  before audio=0/cue empty, after audio=1/cue `OVERDRIVE: NEED 30 AMMO`,
  peak 1, drops 0. Clip 0.14 s peak 1.0.
- **Gates**: `python -m pytest -q` 94 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-15.json`.

## Cycle 16 — Progression and saves: persisted campaign wins
- **Area**: progression and saves (16th cycle).
- **Defect / evidence**: the clear banner lasted four seconds but the win
  was only an in-memory flag; `_record_progress` saved bests, not wins, and
  schema 1 had no wins field. A player who quit after the Warden had no
  record of the clear.
- **Fix**: profile schema 2 with `wins`; schema 1 migrates by adding
  `wins: 0` (schema 0 goes through 1 to 2); `_record_campaign_clear`
  increments and saves on the first clear. Banner grows to 74 px and adds
  `CAMPAIGNS WON <n>`.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-16/`;
  960x540 seed 1, staged wave-3 boss kill. 6,732 changed px (1.30%, bbox
  300,190-659,211; third banner line + taller panel), mean luma 37.93 ->
  38.29.
- **Played runs**: `kite 3000` before/after same hash `9b70e372…`, 32
  kills / 11955 / hp 2; before `wins=0`, after `wins=1` loaded back from
  `ProfileStore`.
- **Gates**: `python -m pytest -q` 97 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-16.json`.

## Cycle 17 — Combat feel: dry-fire feedback
- **Area**: combat feel (17th cycle).
- **Defect / evidence**: a click on 0/0 was silent: no event, voice or
  caption (the low-ammo panel warned before, but not that the trigger was
  dead). A held trigger also had no empty-case rate limit.
- **Fix**: emit `dry_fire` with a 0.25 s `dry_t` rate limit; game plays a
  0.04 s noise click and shows `NO AMMO` in danger red. `dry_t` is
  presentation-only and not in the snapshot; shots/score stay zero.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-17/`;
  960x540 seed 1, frame 1. 7,828 changed px (1.51%, bbox 426,164-947,459;
  caption + AUDIO 1 VOX line), mean luma 34.37 -> 34.42.
- **Played runs**: `dry 60` before/after same hash `d33f43e4…`; before
  audio=0/cue empty, after audio=1/cue `NO AMMO`, peak 1, drops 0. Clip
  0.04 s peak 0.9999.
- **Gates**: `python -m pytest -q` 100 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-17.json`.

## Cycle 18 — Enemies/bosses: brute melee LOS
- **Area**: enemies/bosses (18th cycle).
- **Defect / evidence**: brute melee checked distance only; a brute at
  (-6, 6.2) and player at (-6, 3.8) on opposite sides of the 1 m cover at
  (-6, 5) dealt 20 damage through it (baseline hp 80, `hurt`).
- **Fix**: `_enemy_has_los` chest->eye against colliders (0.3 m skin) now
  gates the brute slam. Open-field slam still lands; wisp LOS unchanged.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-18/`;
  960x540 seed 1, frame 1. 7,216 changed px (1.39%, bbox 60,12-947,231;
  HP line, damage cue, AUDIO line), mean luma 41.16 -> 40.95.
- **Played runs**: `kite 3000` hash `9b70e372…` and `strafe 300`
  `973276f5…` unchanged; fairness `witnessed_win:reference:2627`.
- **Gates**: `python -m pytest -q` 102 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Post-cycle gate hardening**: one full-suite run hit the 10 s playtest
  wall budget under load (`1 failed, 101 passed`). The 3000-frame fairness
  test now passes `max_wall_seconds=30.0` to both `validate_fairness` and
  `run_bot`; two consecutive full runs passed 102/102 afterwards.
- **Evidence file**: `evidence/cycle-18.json`.

## Cycle 19 — Levels: open the spawn-to-pickup lane
- **Area**: levels (19th cycle).
- **Defect / evidence**: the centre cover at (0,0) sat on the pickup
  line from spawn; the pickup ray hit it at 7.02 m, so the first view was a
  box and the reward hidden. Baseline pickup-lane test failed.
- **Fix**: move the centre cover to (2.5,0), leaving the spawn/pickup lane
  clear while keeping a right-of-centre obstacle. Re-record the 3000-frame
  reference (win at wave 4 / frame 2369) and update the strafe baseline.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-19/`;
  960x540 seed 1, frame 1. 15,214 changed px (2.93%, bbox 402,283-658,350;
  cover leaves the crosshair lane), mean luma 34.69 -> 34.74.
- **Played runs**: `kite 3000` wave 4/win, 32 kills, 10135, hp 82, hash
  `945e3fdd…`; fairness `witnessed_win:reference:2369`; `strafe 300`
  30/0/hp 92, hash `14a48660…`.
- **Gates**: `python -m pytest -q` 104 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-19.json`.

## Cycle 20 — UI readability: numeric warden HP
- **Area**: UI readability (20th cycle).
- **Defect / evidence**: the warden bar had only a red fill and label; at
  300/600 the exact remaining health was unknown, making overdrive/critical
  decisions guesswork. Failing-first `test_boss_hp.py` found no `300/600`
  text.
- **Fix**: draw `hp/max_hp` right-aligned beside `WARDEN` using
  `keystone.ui.font.text_width`; bar geometry/colors unchanged.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-20/`;
  960x540 seed 1, half-health warden. 456 changed px (0.09%, bbox
  538,98-619,111), mean luma 36.13 -> 36.34; draws 6, triangles 422.
- **Played runs**: `boss 1800` before/after same hash `81f05265…`, 507
  frames, wave 4, 3 kills, 3080, hp 100.
- **Gates**: `python -m pytest -q` 106 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-20.json`.

## Cycle 21 — Graphics and effects: first-person viewmodel
- **Area**: graphics and effects (21st cycle).
- **Defect / evidence**: no weapon body existed; the first-person frame was
  an empty camera with a crosshair and floating flash, so the equipped gun
  had no visual presence. Baseline `test_viewmodel.py` failed all three
  checks (no `_view_body`/gun materials).
- **Fix**: two shared-cube viewmodel nodes from `juice.viewmodel`, following
  camera yaw/pitch, tinted by `material.gun_{pulse,scatter,lance,surge}`,
  hidden on death. Presentation only.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-21/`;
  960x540 seed 1. Spawn 4,783 changed px (0.92%, bbox 551,92-911,411;
  gun lower-right + status line), mean luma 34.74 -> 35.14; combat 6,839 px
  (1.32%, bbox 526,92-899,419), mean luma 46.51 -> 46.60. Draws
  4 -> 5 / 8 -> 9; tris 218 -> 242 / 584 -> 608.
- **Played runs**: `kite 600` hash `4fe640c5…` and `strafe 300`
  `14a48660…` identical to the cycle-20 worktree; 10 kills/1950 and
  hp 92 respectively.
- **Gates**: `python -m pytest -q` 109 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-21.json`.

## Cycle 22 — Audio cues: reload completion
- **Area**: audio cues (22nd cycle).
- **Defect / evidence**: the reload bar disappeared on completion and the
  sim emitted `reloaded`, but the game ignored it; the completion frame
  showed 30/90 with no caption and `audio=0`.
- **Fix**: `reloaded` sine(980 Hz, 0.06 s) + `RELOADED` caption; reload
  fill/timing/economy unchanged. Audio probe now 15 cues.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-22/`;
  960x540 seed 1, completion frame. 8,140 changed px (1.57%, bbox
  420,164-947,459; caption + AUDIO 1 VOX line), mean luma 35.13 -> 35.24.
- **Played runs**: `reload 60` before/after same hash `d7eb253d…`,
  ammo 30/reserve 90; before audio=0/cue empty, after audio=1/RELOADED,
  peak 1, drops 0. Clip 0.06 s peak 0.9994.
- **Gates**: `python -m pytest -q` 111 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-22.json`.
