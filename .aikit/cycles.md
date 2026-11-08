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

## Cycle 23 — Progression and saves: bounded run history
- **Area**: progression and saves (23rd cycle).
- **Defect / evidence**: only `last_run` persisted; after a second run the
  previous result was gone, so the debrief had no run comparison. Baseline
  schema 2 had no history.
- **Fix**: schema 3 newest-first `history` (max five, cleaned), schema-2
  migration with `history: []`, append/trim in `_finish_run`, and a
  `RECENT <scores>` line in the debrief. Schema 0/1 chains still migrate.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-23/`;
  960x540 seed 1, seeded 980/740 plus current 1500. 8,844 changed px
  (1.71%, bbox 290,356-669,383; RECENT line/taller panel), mean luma
  48.31 -> 47.21.
- **Played runs**: `death 240` before/after same hash `f8cd9e28…`;
  before history `[]`, after `[1500]` persisted through `ProfileStore`.
- **Gates**: `python -m pytest -q` 114 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-23.json`.

## Cycle 24 - Combat feel: spread-aware reticle
- **Area**: combat feel (24th cycle).
- **Defect / evidence**: the HUD always drew the same 8 px crosshair
  half-gap. Hip-fire DATA spans 0.1 deg (lance), 1.2 (pulse), 2.5 (surge)
  and 4.5 (scatter): at 10 m the scatter cone is +/-0.79 m while the reticle
  claimed +/-0.23 m, and the lance claimed 12x its real cone. Baseline
  `tests/test_reticle.py` measured `{pulse: 8, scatter: 8, lance: 8,
  surge: 8}` and failed 4/4.
- **Fix**: add `juice.json:reticle` (8 px / 1.2 deg reference, 3-40 px
  clamp, 4 px hitmark expansion) and `ui.reticle_gap()`; draw the arms from
  the equipped weapon's `spread_hip_deg`. Pulse stays exactly 8 px;
  scatter 30, surge 17, lance 3. No sim/weapon DATA change.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-24/`;
  960x540 seed 1, frames 1-4, same target/camera/renderer S1C1P1B1.
  scatter 576 px (0.11%, bbox 440,230-519,309), lance 256 px (0.05%, bbox
  462,252-497,287), surge 448 px (0.09%, bbox 453,243-506,296), mean luma
  35.51 -> 35.52 / 35.45 -> 35.46 / 35.92 -> 35.93; pulse control and the
  live kite frame are pixel-identical (0 px).
- **Played runs**: `kite 600` before/after same hash `4fe640c5...`,
  10 kills / 1950 / hp 100, 39 shots / 37 hits, 90 audio, peak 8, drops 0;
  `strafe 300` same hash `14a48660...`, 30 shots / 0 hits / hp 92.
- **Gates**: `python -m pytest -q` 118 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-24.json`.

## Cycle 25 - Enemies/bosses: vertical melee reach
- **Area**: enemies/bosses (25th cycle).
- **Defect / evidence**: a 1.0 m mite at the base of the 0.7 m platform
  dealt 8 damage to a player standing on top (hp 92 at frame 1; 4 bites
  over 200 frames left hp 68). Melee checked horizontal distance only, so
  the jumpable platform gave no protection from short enemies.
- **Fix**: add DATA `reach_up` (mite 0.30, brute 0.45, warden 0.45) and
  `Sim._in_melee_reach` (player body origin vs enemy top + reach); gate
  the mite bite, brute slam and warden slam. Open-floor bites are
  unchanged; the 1.4 m brute and 2.2 m warden still reach the platform
  edge. Wisp ranged attacks are unchanged.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-25/`;
  960x540 seed 1, frame 1, same staging. Before hp 92 + red bite cue +
  `AUDIO 1 VOX`; after hp 100, no cue. 7,276 changed px (1.41%, bbox
  60,12-947,231), mean luma 73.41 -> 73.38; the 200-frame played capture
  changes 7,256 px (1.40%), mean luma 73.42 -> 73.38.
- **Played runs**: `highground 200` before hp 68 / 4 hurts / 4 audio /
  hash `e30d3110...`; after hp 100 / 0 hurts / 0 audio / hash
  `a605d8b4...`. Ground parity: `strafe 300` hash `14a48660...`
  (30 shots / 0 hits / hp 92) and `kite 600` hash `4fe640c5...`
  (10 kills / 1950 / hp 100), both unchanged.
- **Gates**: `python -m pytest -q` 122 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-25.json`.

## Cycle 26 - Levels: readable enemy spawn points
- **Area**: levels (26th cycle).
- **Defect / evidence**: the sim emitted a bare `spawn` event but the game
  ignored it, so a wave enemy appeared at its random origin with no visual
  cue. The baseline `test_spawn_mark.py` found no `spawn_marks`/`_spawn_nodes`
  (4/4 failed), and the staged frame had no beam.
- **Fix**: `_spawn_enemy` records `spawn_pos` (telemetry only, never in the
  snapshot); the game keeps up to four `spawn_marks` (`juice.spawn_mark`:
  0.7 s life, 0.18 x 2.4 column) and draws a short emissive column at the
  origin. Spawn positions, counts, timing, RNG and damage are unchanged.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-26/`;
  960x540 seed 1, frame 1, same staged spawn at (0,0.5,-6) and camera.
  386 changed px (0.07%, bbox 451,92-911,310; 126 px in the beam crop),
  mean luma 35.18 -> 35.17; draws 6 -> 7, triangles 562 -> 574.
- **Played runs**: `kite 600` keeps the cycle-25 hash `4fe640c5...`
  (10 kills / 1950 / hp 100, 39 shots / 37 hits, 90 audio, peak 8,
  drops 0); natural wave spawns create markers without touching the sim.
- **Gates**: `python -m pytest -q` 126 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-26.json`.

## Cycle 27 - UI readability: centered top-center status
- **Area**: UI readability (27th cycle).
- **Defect / evidence**: every top-center line used a fixed x offset
  (`cx - 90`, BEST `cx - 60`). At score 12345 the baseline test measured
  WAVE at x 390 (expected 367), STREAK 390 (427), OVERDRIVE 390 (379),
  NEAR-MISS 390 (415), SURGE 390 (307) and BEST 420 (427); the primary
  progress line drifted right as the score grew.
- **Fix**: add `ui._center` (text_width-based) and center WAVE/SCORE,
  STREAK, OVERDRIVE, SURGE, NEAR-MISS and the pickup label; center BEST
  from `text_width` in `game.draw_ui`. No sim/HUD content change.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-27/`;
  960x540 seed 1, frame 1, wave 3, score 12345, best 9999, streak 7,
  overdrive 5.0s, near-miss 3. 4,724 changed px (0.91%, bbox
  367,16-615,97, all in the top band), mean luma 36.01 -> 36.01; draws 5,
  triangles 242.
- **Played runs**: `kite 600` keeps hash `4fe640c5...` (10 kills / 1950 /
  hp 100, 39 shots / 37 hits, 90 audio, peak 8, drops 0).
- **Gates**: `python -m pytest -q` 129 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-27.json`.

## Cycle 28 - Graphics and effects: per-weapon fire tints
- **Area**: graphics and effects (28th cycle).
- **Defect / evidence**: every weapon shared one yellow tracer material and
  one white flash material; the tracer dict had no weapon identity, so
  pulse/scatter/lance/surge fire looked identical. Baseline
  `tests/test_tracer_tint.py` failed 4/4 (no `weapon` key, no
  `material.tracer_*`/`material.flash_*`).
- **Fix**: `_fire` records the firing weapon on the non-snapshot tracer
  dict; the game registers four tracer and four flash materials (scatter
  orange, lance cyan, surge green; pulse keeps the legacy yellow/white)
  and assigns them in `_sync_scene`. No sim state, damage, hitboxes or
  snapshot change.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-28/`;
  960x540 seed 1, first-shot frames 1-4, 600 hp brute at 6 m. Pulse
  control 0 px; scatter 882 px (0.17%, bbox 528,312-557,347), surge
  226 px (0.04%, bbox 528,324-557,355), lance 62 px (0.01%, bbox
  528,325-530,346); mean luma ~40.1; draws 9, triangles 542.
- **Played runs**: `kite 600` keeps hash `4fe640c5...` (10 kills / 1950 /
  hp 100, 39 shots / 37 hits, 90 audio, peak 8, drops 0).
- **Gates**: `python -m pytest -q` 133 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-28.json`.

## Cycle 29 - Audio cues: weapon-switch click and caption
- **Area**: audio cues (29th cycle).
- **Defect / evidence**: `_switch` emitted `switch:<weapon>` but
  `_play_event` ignored it, so slot changes were silent. Baseline
  `tests/test_switch_cue.py` found an empty cue, zero voices and no
  `switch_*` clips (2/3 failed).
- **Fix**: add `switch_pulse` (300 Hz), `switch_scatter` (220 Hz) and
  `switch_lance` (420 Hz) short square clicks; handle `switch:<wid>` by
  playing the matching clip at 0.35 gain and showing the uppercase
  weapon caption. No sim/weapon timing change.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-29/`;
  960x540 seed 1, frame 1, slot 2. Before no caption/audio; after
  `SCATTER` + `AUDIO 1 VOX`: 7,828 changed px (1.51%, bbox
  426,164-947,459), mean luma 35.10 -> 35.20; draws 5, triangles 242.
- **Played runs**: `switch 30` before audio 0 / cue empty / voices 0;
  after audio 3 / cue `PULSE` / voices 3; same hash `f03a087f...`,
  0 drops.
- **Gates**: `python -m pytest -q` 136 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-29.json`.

## Cycle 30 - Progression and saves: record campaign wins
- **Area**: progression and saves (30th cycle).
- **Defect / evidence**: `_record_campaign_clear` only incremented `wins`;
  `last_run` and `history` were written by `_finish_run` on death alone.
  The pre-fix 3000-frame campaign run reached wave 4 with `wins=1` but
  `runs=0` and `history=[]`, and the debrief printed scores without
  outcomes. Baseline `test_win_history.py` failed 3/4.
- **Fix**: extract `_record_run(outcome)`; death records `lose`, campaign
  clear records `win`; `_run_recorded` prevents a later death from
  duplicating the win. The debrief appends `W`/`L` to RECENT scores.
  Profile schema stays 3 (outcome was already in the run record).
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-30/`;
  960x540 seed 1, seeded win 980 + loss 740, staged death 1500. Before
  `RECENT 1500 / 980 / 740`; after `RECENT 1500L / 980W / 740L`:
  656 changed px (0.13%, bbox 442,356-619,369), mean luma 51.36 -> 51.40;
  draws 5, triangles 230.
- **Played runs**: `kite 3000` before wins=1/runs=0/history=[]; after
  wins=1/runs=1/history=[win 8935, wave 4, time 39, kills 28, streak 16];
  same hash `945e3fdd...`, final 32 kills / 10135 / hp 82.
- **Gates**: `python -m pytest -q` 140 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-30.json`.

## Cycle 31 - Combat feel: kill-only crosshair marker
- **Area**: combat feel (31st cycle).
- **Defect / evidence**: a kill used the same crosshair hitmark as a
  non-lethal body hit; the only kill-specific cues were sound, feed,
  particles and hitstop, none at the aim point. Baseline
  `tests/test_killmark.py` failed 4/4 (no `killmark_t`, no red ticks).
- **Fix**: add `juice.killmark_s` 0.18; set `killmark_t` on a kill and
  decrement it, never in the snapshot; draw four red 5x5 corner ticks at
  `gap + 6` while it runs. No damage/RNG/AI change.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-31/`;
  960x540 seed 1, first-kill frame after 7 idle steps. 100 changed px
  (0.02%, bbox 460,250-500,290, exactly four ticks), mean luma
  37.00 -> 36.99; draws 7, triangles 318; kill feed/streak/audio identical.
- **Played runs**: `kite 600` keeps hash `4fe640c5...` (10 kills / 1950 /
  hp 100, 39 shots / 37 hits, 90 audio, peak 8, drops 0).
- **Gates**: `python -m pytest -q` 144 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-31.json`.

## Cycle 32 - Enemies/bosses: warden slam-radius ring
- **Area**: enemies/bosses (32nd cycle).
- **Defect / evidence**: during the 0.7 s warden windup the boss swelled
  and the caption/audio warned, but the 4.5 m slam radius had no ground
  cue. The staged windup frame measured `ring=0`; the player could not
  tell whether they were inside. Baseline `test_slam_ring.py` failed 4/4.
- **Fix**: add 24 shared-cube ground tiles at the warden's DATA `range`
  (`juice.slam_ring`: segments 24, width 0.20, height 0.025), visible only
  while a live warden has `windup_t > 0`; hidden otherwise. Presentation
  only; slam timing/damage are unchanged.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-32/`;
  960x540 seed 1, warden at (0,1.1,2.0), windup 0.483. Before no ring;
  after 24 orange tiles: 3,560 changed px (0.69%, bbox 55,92-911,539),
  mean luma 36.96 -> 37.56; draws 7 -> 8, triangles 446 -> 698.
- **Played runs**: `slam 180` before/after same hash `4580b9da...`,
  43 frames, hp 70, 1 hurt, audio 3, peak 3, drops 0.
- **Gates**: `python -m pytest -q` 148 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-32.json`.

## Cycle 33 - Levels: off-screen surge-pickup direction
- **Area**: levels (33rd cycle).
- **Defect / evidence**: the pickup beacon and the `SURGE PICKUP READY`
  label name the reward, but when the pickup is behind the player there
  is no direction. The staged frame at spawn facing +Z had the label and
  no tag; baseline `test_pickup_arrow.py` failed 1/3.
- **Fix**: draw a green `SURGE` edge chip at the pickup bearing when it
  is active, within 18 m, no boss is shown and `|bearing| > 1.35` rad;
  the chip is clamped to the screen edges. Presentation-only; trigger,
  spot and sim state are untouched.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-33/`;
  960x540 seed 1, pickup active, player at spawn facing +Z. Before label
  only; after label + green chip: 1,768 changed px (0.34%, bbox
  446,377-513,402), mean luma 34.12 -> 34.18; draws 5, triangles 62.
- **Played runs**: `pickup 240` before/after same hash `7f84f3e9...`,
  147 frames, hp 100, audio 1, peak 1, drops 0.
- **Gates**: `python -m pytest -q` 151 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-33.json`.

## Cycle 34 - UI readability: fit wide debrief history
- **Area**: UI readability (34th cycle).
- **Defect / evidence**: cycle 30's W/L markers widened the RECENT line;
  with six-digit scores it measured 406 px at x 310 inside the fixed
  380 px debrief panel (text ended at 716, panel at 670). Baseline
  `test_debrief_width.py` failed the fit check.
- **Fix**: size the debrief panel from its longest extra line
  (`max(380, widest + 40)`), center it, and draw every line from its
  left margin. Normal scores keep the 380 px layout.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-34/`;
  960x540 seed 1, seeded 999999W/888888L/777777W, staged death 999999.
  Before overflow; after a 446 px panel contains
  `RECENT 999999L / 999999W / 888888L`: 15,022 changed px (2.9%, bbox
  257,262-715,383), mean luma 51.61 -> 50.55; draws 5, triangles 230.
- **Played runs**: `death 240` before/after same hash `f8cd9e28...`,
  1 frame, hp 0, score 1500, audio 2, peak 2, drops 0.
- **Gates**: `python -m pytest -q` 153 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-34.json`.

## Cycle 35 - Graphics and effects: arena wall depth
- **Area**: graphics and effects (35th cycle).
- **Opportunity**: the four boundary walls were flat 3 m gray planes
  with only a cyan top trim; the spawn view had no vertical rhythm.
- **Fix**: add 8 shared-cube vertical pilasters (0.18 x 3.0 x 0.18) at
  +/-10 m on the long walls and +/-10 m on the short walls, using one
  `material.pilaster`; decoration only (no colliders, no sim state).
  An initial 16-pilaster version failed the 40-draw plan at 45 calls
  (shadow 40), so the final count is 8 (plan 37, shadow 32).
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-35/`;
  960x540 seed 1, spawn view. 1,296 changed px (0.25%, bbox
  97,92-911,301), mean luma 35.14 -> 35.20; draws 5 -> 6, triangles
  242 -> 290, shadow calls 24 -> 32.
- **Played runs**: `kite 600` keeps hash `4fe640c5...` (10 kills / 1950 /
  hp 100, 39 shots / 37 hits, 90 audio, peak 8, drops 0).
- **Gates**: `python -m pytest -q` 155 passed; determinism 1800 ok; aikit
  `check shooter` 4/4; frame-budget plan 37 <= 40.
- **Evidence file**: `evidence/cycle-35.json`.

## Cycle 36 - Audio cues: hostile-inbound spawn voice
- **Area**: audio cues (36th cycle).
- **Defect / evidence**: the sim emits `spawn` and the game draws a short
  origin marker, but the event was silent. The staged spawn frame had
  `cue='' voices=0`; off-screen spawns gave no warning.
- **Fix**: add an 0.08 s `spawn` noise clip at 0.30 gain; when no cue is
  active, show `HOSTILE INBOUND` (the caption is rate-limited, the clip
  plays for every spawn). The spawn marker and all sim state are
  untouched.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-36/`;
  960x540 seed 1, staged spawn at (0,0.5,-6). Before marker only; after
  marker + `HOSTILE INBOUND` + `AUDIO 1 VOX`: 10,312 changed px (1.99%,
  bbox 378,164-947,459), mean luma 35.23 -> 35.34; draws 8, triangles 622.
- **Played runs**: `kite 600` before audio 90 / after 101 (11 natural
  spawns), same hash `4fe640c5...`, 10 kills / 1950 / hp 100,
  39 shots / 37 hits, peak 8, drops 0.
- **Gates**: `python -m pytest -q` 157 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-36.json`.

## Cycle 37 - Progression and saves: career totals in the debrief
- **Area**: progression and saves (37th cycle).
- **Opportunity**: the profile tracks lifetime `runs`/`wins`, but the
  death debrief showed only bests and recent runs; the clear banner was
  the only wins display. The baseline `test_career_debrief.py` found no
  `RUNS`/`WINS` row.
- **Fix**: append `RUNS <n>  WINS <m>` to the debrief extras when the
  profile has runs; the cycle-34 dynamic panel width/height already
  contain the extra row. No schema or save-format change.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-37/`;
  960x540 seed 1, seeded win/loss profile, staged death; profile runs=4,
  wins=1. Before no row; after `RUNS 4  WINS 1` and a taller panel:
  8,608 changed px (1.66%, bbox 290,378-669,405), mean luma
  51.42 -> 50.06; draws 6, triangles 278.
- **Played runs**: `death 240` before/after same hash `f8cd9e28...`,
  1 frame, hp 0, score 1500, audio 2, peak 2, drops 0.
- **Gates**: `python -m pytest -q` 159 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-37.json`.

## Cycle 38 - Combat feel: visible wisp bolt
- **Area**: combat feel (38th cycle).
- **Defect / evidence**: the wisp's ranged hit was instant and invisible;
  the staged hit frame had hp 94 and `tracers=[]`, with only the red
  damage cue showing the attack. Baseline `test_wisp_bolt.py` failed 2/2.
- **Fix**: on a wisp hit, append a 0.12 s tracer from the wisp chest to
  the player eye tagged `weapon="wisp"`; the game registers
  `material.tracer_wisp` (violet) and the existing tracer pool maps it.
  Damage, LOS, attack cooldown and the snapshot are unchanged.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-38/`;
  960x540 seed 1, wisp at (5,0.4,4), first hit frame. Before hp 94 with
  no bolt; after hp 94 + violet bolt: 2,962 changed px (0.57%, bbox
  714,92-911,539), mean luma 35.92 -> 35.89; draws 7 -> 8, triangles
  314 -> 326.
- **Played runs**: `kite 3000` same hash `945e3fdd...` (32 kills / 10135
  / hp 82, 3 hurts, 458 audio, peak 8, drops 0).
- **Gates**: `python -m pytest -q` 161 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-38.json`.

## Cycle 39 - Enemies/bosses: warden summon origin markers
- **Area**: enemies/bosses (39th cycle).
- **Opportunity**: `boss_summon` had its own audio and caption, but the
  two summoned mites appeared with no origin cue; only normal `spawn`
  events used the marker pool. The staged frame measured
  `positions=0 marks=0` with the cue already showing.
- **Fix**: `_summon_mites` records the clamped escort positions in
  `summon_positions` (presentation only, not in the snapshot);
  `_play_event("boss_summon")` adds a spawn mark for each position (cap
  4). The existing caption/audio and all summon behavior are unchanged.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-39/`;
  960x540 seed 1, warden at (0,1.1,2.0), `summon_cd=0`. Before cue only;
  after cue + two orange origin beams: 6,296 changed px (1.21%, bbox
  302,92-935,406), mean luma 38.49 -> 38.75; draws 9 -> 10, triangles
  1134 -> 1158.
- **Played runs**: `boss 1800` before/after same hash `81f05265...`,
  507 frames, 3 kills, 3080, hp 100, 56/56, 121 audio, peak 8, drops 0.
- **Gates**: `python -m pytest -q` 163 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-39.json`.

## Cycle 40 - Levels: lit rim on the jump platform
- **Area**: levels (40th cycle).
- **Opportunity**: the 0.7 m jump platform has a walkable top, so cycle 05
  deliberately skipped its lit cap; from the approach it reads like a
  solid blue cover with no jumpable edge.
- **Fix**: add two lit trim strips (6.1 x 0.08 x 0.10) on the long top
  edges at y 0.74, sharing `material.trim` with the existing trim batch.
  Decoration only: no colliders, no sim state. Two strips (not four)
  keep the frame-budget plan under 40; shadow calls 32 -> 34.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-40/`;
  960x540 seed 1, approach view at (-16,9.5) facing +Z. 14,003 changed
  px (2.7%, bbox 51,92-908,399), mean luma 49.08 -> 48.24; draws 6,
  triangles 98 -> 122.
- **Played runs**: `platform 120` before/after same hash `c1603d79...`,
  28 frames, hp 100, score 250, landed, audio 1, peak 1, drops 0.
- **Gates**: `python -m pytest -q` 165 passed; determinism 1800 ok; aikit
  `check shooter` 4/4; frame budget green.
- **Evidence file**: `evidence/cycle-40.json`.

## Cycle 41 - UI readability: show the streak bonus
- **Area**: UI readability (41st cycle).
- **Defect / evidence**: the HUD showed `STREAK xN` but not the score
  bonus (10% per kill, capped at 50%) that breaks on hurt; the stake the
  player is protecting was invisible. Baseline `test_streak_bonus.py`
  failed 2/2 (no helper, no percentage).
- **Fix**: add `Sim.streak_bonus()` (public, `min(cap, per * streak)`)
  and show `STREAK xN  +P%` in the existing centered line. No sim
  behavior, damage or snapshot change.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-41/`;
  960x540 seed 1, wave 3, score 1234, streak 7. Before `STREAK x7`;
  after `STREAK x7  +50%`: 864 changed px (0.17%, bbox 391,52-568,65),
  mean luma 35.43 -> 35.51; draws 6, triangles 290.
- **Played runs**: `kite 600` keeps hash `4fe640c5...` (10 kills / 1950
  / hp 100, 39 shots / 37 hits, 101 audio, peak 8, drops 0).
- **Gates**: `python -m pytest -q` 167 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-41.json`.

## Cycle 42 - Graphics and effects: enemy death silhouette
- **Area**: graphics and effects (42nd cycle).
- **Opportunity**: a killed enemy node disappeared on the kill frame; the
  burst, feed, sound, hitstop and killmark played, but the body had no
  exit transition. The baseline `test_death_fx.py` failed 3/3.
- **Fix**: add `juice.death_fx_s` 0.15 and `_Enemy.death_t`, set on a
  kill and decremented for dead enemies; `_sync_scene` renders a dead
  enemy as a shrinking white-hot silhouette (`material.enemy_hit`)
  before hiding it. `death_t` is not in the snapshot; damage, AI and RNG
  are unchanged.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-42/`;
  960x540 seed 1, two frames after the first kill. Before only the
  impact/kill particles; after a white shrinking mite: 3,255 changed px
  (0.63%, bbox 438,92-923,373), mean luma 38.25 -> 38.64; draws
  9 -> 10, triangles 378 -> 698.
- **Played runs**: `kite 600` keeps hash `4fe640c5...` (10 kills / 1950
  / hp 100, 101 audio, peak 8, drops 0).
- **Gates**: `python -m pytest -q` 170 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-42.json`.

## Cycle 43 - Audio cues: brute slam voice
- **Area**: audio cues (43rd cycle).
- **Defect / evidence**: the brute's 20-damage slam produced only the
  generic `hurt` clip; the warden has dedicated slam cues. The staged
  close-range hit measured events `['hurt']`, cue `''`, one voice.
- **Fix**: emit `brute_slam` in the brute attack branch; add a 0.15 s
  noise clip and a danger `BRUTE SLAM` caption. Damage, LOS, cooldown
  and the snapshot are unchanged; the generic hurt clip still plays.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-43/`;
  960x540 seed 1, brute at 1.5 m, first hit frame. Before hp 80 + empty
  cue + 1 voice; after hp 80 + `BRUTE SLAM` + `AUDIO 2 VOX`:
  3,800 changed px (0.73%, bbox 408,164-827,459), mean luma
  48.55 -> 48.22; draws 7, triangles 302.
- **Played runs**: `brute 60` hp 80, 1 hurt, audio events frame 1
  `brute_slam` + `hurt`, peak 2, drops 0, hash `830dcbe4...`;
  `kite 600` keeps hash `4fe640c5...` (no brute hit on that path).
- **Gates**: `python -m pytest -q` 172 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-43.json`.

## Cycle 44 - Progression and saves: career bests in the debrief
- **Area**: progression and saves (44th cycle).
- **Opportunity**: the profile tracks `best_kills`, `best_wave` and
  `best_streak`; the top BEST line exposed only the score, while the
  debrief showed the current run's numbers. Career bests were never
  visible. Baseline `test_best_row.py` found no row.
- **Fix**: append `BEST KILLS <n>  WAVE <n>  STREAK <n>` to the debrief
  extras when any best is non-zero; the cycle-34 dynamic width/height
  contain it. No schema or save-format change.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-44/`;
  960x540 seed 1, seeded bests 12/4/6, staged death. Before no row;
  after the row and a taller/wider panel: 21,392 changed px (4.13%, bbox
  275,262-684,427), mean luma 50.07 -> 48.15; draws 6, triangles 278.
- **Played runs**: `death 240` before/after same hash `f8cd9e28...`,
  1 frame, hp 0, score 1500, audio 3, peak 3, drops 0.
- **Gates**: `python -m pytest -q` 174 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-44.json`.

## Cycle 45 - Combat feel: kill bounty at the crosshair
- **Area**: combat feel (45th cycle).
- **Opportunity**: the kill reward (e.g. `MITE +110`) appeared only in the
  top-left feed; the crosshair killmark confirmed the kill but not the
  bounty, so the reward was away from the aim point. Baseline
  `test_score_pop.py` failed 3/3.
- **Fix**: on `kill:<type>:<total>`, set `score_pop` (`+N`, 0.6 s from
  `juice.score_pop_s`), decrement it in `update`, and draw it at
  `cx + 22, cy + 16` in the accent color. Presentation only; no sim or
  snapshot change.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-45/`;
  960x540 seed 1, two frames after the first kill. Before no pop at the
  crosshair; after `+110`: 192 changed px (0.04%, bbox 502,286-547,299),
  mean luma 38.64 -> 38.67; draws 10, triangles 698.
- **Played runs**: `kite 600` keeps hash `4fe640c5...` (10 kills / 1950
  / hp 100, 39 shots / 37 hits, 101 audio, peak 8, drops 0).
- **Gates**: `python -m pytest -q` 177 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-45.json`.

## Cycle 46 - Enemies/bosses: crosshair target health
- **Area**: enemies/bosses (46th cycle).
- **Opportunity**: only the warden had a health bar; mites, brutes and
  wisps showed hit flinch and death, but not remaining health, so the
  player could not tell when one more shot would finish a target. The
  staged crosshair-on-mite frame had `target=None`.
- **Fix**: add read-only `Sim.aim_target()` (nearest live enemy under the
  forward ray, behind no wall) and draw a compact bar plus
  `TYPE hp/max` above the crosshair for non-warden targets. The warden
  keeps its dedicated top bar. No sim behavior or snapshot change.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-46/`;
  960x540 seed 1, mite at 6 m with 18/30 hp. Before no target UI; after
  `MITE 18/30` and an orange fill: 1,744 changed px (0.34%, bbox
  418,200-541,227), mean luma 35.48 -> 35.84; draws 7, triangles 610.
- **Played runs**: `kite 600` keeps hash `4fe640c5...` (10 kills / 1950
  / hp 100, 101 audio, peak 8, drops 0).
- **Gates**: `python -m pytest -q` 181 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-46.json`.

## Cycle 47 - Levels: jump-platform launch pad
- **Area**: levels (47th cycle).
- **Opportunity**: the rim marks the platform top, but the floor launch
  spot was unmarked; the approach showed the edge with no "jump here"
  cue. The before frame had only the rim.
- **Fix**: add one flat lit trim pad (1.4 x 0.02 x 1.4) at
  `(-16, 0.02, 11.2)` before the south edge, sharing `material.trim`.
  Decoration only: no collider, no sim state. One node keeps the
  frame-budget plan at 40 (shadow calls 34 -> 35).
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-47/`;
  960x540 seed 1, approach view at (-16,9.5) facing +Z. Before rim only;
  after rim + cyan pad: 7,994 changed px (1.54%, bbox 361,92-899,539),
  mean luma 48.24 -> 49.47; draws 6, triangles 122 -> 134.
- **Played runs**: `platform 120` before/after same hash `c1603d79...`,
  28 frames, hp 100, score 250, landed, audio 1, peak 1, drops 0.
- **Gates**: `python -m pytest -q` 183 passed; determinism 1800 ok; aikit
  `check shooter` 4/4; frame budget green.
- **Evidence file**: `evidence/cycle-47.json`.

## Cycle 48 - UI readability: pickup tag during boss fights
- **Area**: UI readability (48th cycle).
- **Defect / evidence**: the pickup top label and edge tag shared one
  `boss is None` guard. With a live warden and the pickup still active
  (wave 3 if not taken), both vanished; the staged frame labels were
  `['WARDEN','600/600',...]` with no direction. Baseline
  `test_pickup_boss_tag.py` failed the boss case.
- **Fix**: split the cues. The top `SURGE PICKUP READY` label stays
  suppressed while a boss bar occupies that space; the off-screen
  `SURGE` edge chip now shows whenever the pickup is active, within
  18 m and off-screen, regardless of the boss. Presentation-only.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-48/`;
  960x540 seed 1, live warden + active pickup, facing away. Before boss
  bar only; after boss bar + bottom-edge `SURGE`: 1,768 changed px
  (0.34%, bbox 446,377-513,402), mean luma 34.71 -> 34.77; draws 6,
  triangles 98.
- **Played runs**: `kite 3000` same campaign hash `945e3fdd...` (32
  kills / 10135 / hp 82, 3 hurts, 458 audio, peak 8, drops 0); the run
  takes the pickup in wave 2, so the boss-pickup tag itself is a staged
  UI proof.
- **Gates**: `python -m pytest -q` 186 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-48.json`.

## Cycle 49 - Graphics and effects: arena cover panels
- **Area**: graphics and effects (49th cycle).
- **Opportunity**: the six covers were flat brown boxes; the floor has a
  grid and the walls have trim/pilasters, but the covers had no surface
  detail. The before frame showed plain blocks.
- **Fix**: generate a deterministic 64x64 grayscale `cover-panel`
  texture (seam border, 16-px bands) and apply it to the existing
  `material.cover` with `checker_scale=1.0`; the brown color still tints
  it. No new nodes, draw calls or colliders.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-49/`;
  960x540 seed 1, spawn view. 25,683 changed px (4.95%, bbox
  0,262-959,442), mean luma 35.24 -> 34.09; draws 6, triangles 290
  (unchanged).
- **Played runs**: `kite 600` keeps hash `4fe640c5...` (10 kills / 1950
  / hp 100, 101 audio, peak 8, drops 0).
- **Gates**: `python -m pytest -q` 188 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-49.json`.

## Cycle 50 - Audio cues: wisp bolt warning
- **Area**: audio cues (50th cycle).
- **Defect / evidence**: the wisp bolt is visible (cycle 38) but silent
  until it hits; the only sound was the generic `hurt` clip. The staged
  hit measured events `['hurt']`, cue `''`, one voice.
- **Fix**: emit `wisp_bolt` in the wisp attack branch; add a 0.08 s
  1200 Hz sine and a danger `WISP BOLT` caption. The bolt, LOS, damage,
  cooldown and snapshot are unchanged; the hurt clip still plays.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-50/`;
  960x540 seed 1, wisp at (5,0.4,4), first hit. Before bolt + hurt only;
  after bolt + `WISP BOLT` + `AUDIO 2 VOX`: 3,488 changed px (0.67%,
  bbox 414,164-815,459), mean luma 34.78 -> 34.64; draws 8, triangles 326.
- **Played runs**: `kite 3000` audio 458 -> 461 (3 natural bolts), same
  hash `945e3fdd...`, 32 kills / 10135 / hp 82, 3 hurts, peak 8,
  drops 0.
- **Gates**: `python -m pytest -q` 190 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-50.json`.

## Cycle 51 - Progression and saves: full five-run history
- **Area**: progression and saves (51st cycle).
- **Opportunity**: the profile stores a five-run history (cycle 23), but
  the debrief rendered only `history[:3]`; the two oldest persisted runs
  were never visible. The baseline test found only three scores.
- **Fix**: build all five entries; show the first three on `RECENT` and
  the remaining two on a second `HISTORY` line. The cycle-34 dynamic
  panel width/height contain both lines. No schema or save change.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-51/`;
  960x540 seed 1, four seeded runs plus the current 1500. Before
  `RECENT 1500L / 980L / 860L`; after adds `HISTORY 740L / 620L` and a
  taller panel: 12,064 changed px (2.33%, bbox 275,378-684,449), mean
  luma 48.16 -> 46.79; draws 6, triangles 278.
- **Played runs**: `death 240` before/after same hash `f8cd9e28...`,
  1 frame, hp 0, score 1500, audio 3, peak 3, drops 0.
- **Gates**: `python -m pytest -q` 191 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-51.json`.

## Cycle 52 - Combat feel: damage camera jolt
- **Area**: combat feel (52nd cycle).
- **Defect / evidence**: taking damage had a sound and a directional cue,
  but the camera stayed exactly at the eye; the hit had no physical
  jolt. The baseline test measured the camera equal to `sim.eye()` with
  `hurt_t=0.4`.
- **Fix**: while `hurt_t > 0`, offset the camera position by a short
  deterministic shake (`amp = min(1, hurt/0.3) * 0.035`;
  `x = sin(time*55)*amp`, `y = cos(time*47)*amp*0.6`). The aim ray,
  hitscan, viewmodel origin and snapshot are untouched.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-52/`;
  960x540 seed 1, right-side first hit at frame 12. Before the steady
  eye view; after the jolted scene while the HUD stays fixed:
  110,566 changed px (21.33%, bbox 0,235-959,539), mean luma
  34.24 -> 34.20; draws 6, triangles 290.
- **Played runs**: `ambush 180` before/after same hash `ca6d9711...`,
  180 frames, hp 84, 2 hurts, audio 2, peak 2, drops 0.
- **Gates**: `python -m pytest -q` 193 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-52.json`.

## Cycle 53 - Enemies/bosses: target bar yields on death
- **Area**: enemies/bosses (53rd cycle).
- **Defect / evidence**: the cycle-46 crosshair target-health bar was
  drawn even with `sim.alive=False`; on the death frame a brute under
  the crosshair put `BRUTE 120/120` over `YOU DIED`. Baseline
  `test_target_dead.py` measured `['BRUTE 120/120', ..., 'YOU DIED']`.
- **Fix**: add the `sim.alive` guard to the target-bar condition. The
  bar remains for live targets; the warden and death screen are
  unchanged. Presentation only.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-53/`;
  960x540 seed 1, brute at 1 m, death frame. Before the bar overlapped
  `YOU DIED`; after only the clean death screen: 1,548 changed px
  (0.30%, bbox 403,200-556,227), mean luma 49.41 -> 49.08; draws 6,
  triangles 278.
- **Played runs**: `death 240` before/after same hash `f8cd9e28...`,
  1 frame, hp 0, score 1500, audio 3, peak 3, drops 0.
- **Gates**: `python -m pytest -q` 195 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-53.json`.

## Cycle 54 - Levels: pulsing launch pad
- **Area**: levels (54th cycle).
- **Opportunity**: the cycle-47 launch pad was static and could blend
  into the floor grid at approach distance; the before frame measured
  `pad_scale=1.4` with no motion.
- **Fix**: pulse the existing `_approach_pad` scale with
  `1 + 0.08*sin(time*3)` in `_sync_scene`; no new nodes, draws or
  colliders. The jump/landing path is untouched.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-54/`;
  960x540 seed 1, approach view at time 0.5. Pad 1.4 -> 1.512:
  1,629 changed px (0.31%, bbox 352,498-607,539), mean luma
  49.47 -> 49.71; draws 6, triangles 134.
- **Played runs**: `platform 120` before/after same hash `c1603d79...`,
  28 frames, hp 100, score 250, landed, audio 1, peak 1, drops 0.
- **Gates**: `python -m pytest -q` 196 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-54.json`.

## Cycle 55 - UI readability: low-ammo count
- **Area**: UI readability (55th cycle).
- **Defect / evidence**: the near-crosshair low-ammo warning was binary
  `LOW AMMO`; the exact magazine count lived only in the top-left engine
  status, so the player could not tell 3 rounds from 1 at the aim point.
  The baseline test measured `['LOW AMMO', ...]` with no count.
- **Fix**: show `LOW AMMO <mag>` and widen the panel from 110 to 150 px
  so two-digit magazines fit. The engine status remains the full ammo
  source; no sim change.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-55/`;
  960x540 seed 1, pulse magazine 3. Before `LOW AMMO`; after
  `LOW AMMO 3`: 1,448 changed px (0.28%, bbox 405,300-554,321), mean
  luma 34.04 -> 34.02; draws 6, triangles 290.
- **Played runs**: `strafe 300` before/after same hash `14a48660...`,
  30 shots, hp 92, 1 hurt, 36 audio, peak 8, drops 0.
- **Gates**: `python -m pytest -q` 199 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-55.json`.

## Cycle 56 - Graphics and effects: wall panel texture
- **Area**: graphics and effects (56th cycle).
- **Opportunity**: the four boundary walls were flat gray boxes. Cycle 49
  textured the covers, but the arena shell still read as untextured slabs
  at spawn and along long sightlines; the baseline test measured
  `material.wall.texture=None` with no checker scale.
- **Fix**: deterministic 64x64 grayscale `wall-panel` texture (8 px
  vertical seams, 16-row horizontal bands, rivets) on the existing
  `material.wall`, with `checker_scale=0.15`. Material-only: same wall
  nodes, mesh, draws, colliders and sim. Close-up inspection shows the
  seams stay level; no new geometry.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-56/`;
  960x540 seed 1, spawn view facing the north wall. 34,064 changed px
  (6.57%, bbox 0,236-959,307), mean luma 34.09 -> 32.49; draws 6,
  triangles 290.
- **Played runs**: `kite 600` before/after same hash `4fe640c5...`,
  10 kills, hp 100, score 1950, 39 shots/37 hits, audio 101, peak 8,
  drops 0.
- **Gates**: `python -m pytest -q` 201 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-56.json`.

## Cycle 57 - Audio cues: surge-forfeit warning
- **Area**: audio cues (57th cycle).
- **Defect / evidence**: switching from the surge pickup to slot 1-3
  forfeits the remaining surge timer and its stranded ammo. The sim emits
  `surge_forfeit`, but `_play_event` had no branch, so the baseline run
  logged only `switch_pulse` with the caption `PULSE` and one voice; the
  loss looked like an ordinary weapon change.
- **Fix**: map the event to a distinct 0.22 s 120 Hz voice and a danger
  `SURGE FORFEIT` caption. The switch click still plays; a one-frame
  pending flag keeps the forfeit caption from being overwritten by the
  weapon name. Sim, ammo, timer and input paths are untouched.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-57/`;
  960x540 seed 1, surge armed then slot1. Before `PULSE`; after
  `SURGE FORFEIT`: 3,060 changed px (0.59%, bbox 390,164-815,459), mean
  luma 32.59 -> 32.53; draws 6, triangles 290. New voice inspected in
  `cues.wav` and `cues_spectrogram.png` (0.22 s, 120 Hz, peak 1.0).
- **Played runs**: `forfeit 6` before/after same hash `3fe96786...`,
  audio 1 -> 2, clips `switch_pulse` -> `surge_forfeit` + `switch_pulse`,
  hp 100, 0 drops.
- **Gates**: `python -m pytest -q` 204 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-57.json`.

## Cycle 58 - Progression and saves: visible save failure
- **Area**: progression and saves (58th cycle).
- **Defect / evidence**: a failed profile write only incremented
  `profile_save_errors`; the death debrief looked normal while the run was
  lost. A profile parent that could not be created raised `FileExistsError`
  out of the finish. The baseline test showed a normal debrief with no
  warning for both cases.
- **Fix**: catch `OSError` from the store save and count it as a failed
  save, then show a red `PROFILE NOT SAVED` line first in the debrief
  extras. Profile schema, save format, lock policy and sim are untouched.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-58/`;
  960x540 seed 1, profile lock held, staged brute death. 13,320 changed px
  (2.57%, bbox 281,334-678,449), mean luma 47.08 -> 45.72; draws 6,
  triangles 278.
- **Played runs**: `save_fail 240` before/after same death hash
  `f8cd9e28...`, profile runs 1, save_errors 1, last_run recorded, hp 0,
  peak 3, 0 drops.
- **Gates**: `python -m pytest -q` 207 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-58.json`.

## Cycle 59 - Combat feel: viewmodel recoil punch
- **Area**: combat feel (59th cycle).
- **Opportunity**: firing already kicked the camera, but the first-person
  gun was rigidly camera-parented and never moved relative to the view;
  the kick read as the world tilting rather than the weapon punching.
- **Fix**: offset the two existing viewmodel nodes back 0.10 m and up
  0.08 m at the 4-degree kick cap, scaled by the current kick and owned by
  `juice.viewmodel` (`recoil_back`, `recoil_up`). No new nodes, draws,
  aim rays, hitboxes or sim state; the gun settles with kick decay.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-59/`;
  960x540 seed 1, one scatter shot at a 2 m mite. Gun moves up/back:
  7,141 changed px (1.38%, bbox 551,334-671,425), mean luma
  35.28 -> 35.18; draws 10, triangles 886. The first pass pulled the gun
  slightly downward, so `recoil_up` was raised 0.05 -> 0.08 and the frame
  re-captured.
- **Played runs**: `strafe 300` before/after same hash `14a48660...`,
  30 shots, hp 92, 1 hurt, 36 audio, peak 8, drops 0.
- **Gates**: `python -m pytest -q` 210 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-59.json`.

## Cycle 60 - Enemies/bosses: cover-safe warden escorts
- **Area**: enemies and bosses (60th cycle).
- **Defect / evidence**: `_summon_mites` picked a random 1.2-2.4 m ring
  around the warden and clamped only to the arena bounds, so escorts could
  spawn inside a cover box and stay stuck. The baseline test with the
  warden at (-16, 1.1, 11) and seed 1 reproduced two blocked positions.
- **Fix**: reject ring candidates that overlap a cover at the mite radius,
  retry up to 12 times, and skip a candidate that never clears. Count,
  `max_alive`, RNG determinism and the summon event are unchanged; no new
  nodes, draws or save data.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-60/`;
  960x540 seed 1, forced summon by the low platform, camera over its edge.
  Before the platform surface cuts through both mites/markers; after they
  stand clear in front of the warden. 5,248 changed px (1.01%, bbox
  371,141-596,281), mean luma 71.24 -> 71.28; draws 11, triangles 1182.
- **Played runs**: `summon 60` before/after same staging: blocked escorts
  2 -> 0, both hp 100 for 60 frames, 0 hurts, 0 drops; positions move from
  (-16.09,12.79)/(-17.91,11.62) to (-15.71,9.73)/(-13.86,11.39).
- **Gates**: `python -m pytest -q` 211 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-60.json`.

## Cycle 61 - Levels: full platform landing perimeter
- **Area**: levels (61st cycle).
- **Defect / evidence**: the cycle-40 rim proof names four shared
  strips, but the code emitted only the two long edges. From the east or
  west the platform edge was an unlit dark seam against the side face, so
  the landing perimeter was inconsistent.
- **Fix**: build `_platform_frame_mesh()` as four thin cubes merged into
  one `MeshData` and replace the two long-edge nodes with one
  `platform-rim` node. It shares `material.trim`, adds no colliders or sim
  state, keeps one node and one shadow draw; the custom mesh costs one
  extra batched draw (7 vs 6), still far under the 40-draw gate.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-61/`;
  960x540 seed 1, approach view from the south. The side edges gain the
  lit frame: 5,403 changed px (1.04%, bbox 51,92-908,399; 5,111 px in the
  3D scene, bbox 51,305-908,399), mean luma 44.04 -> 44.40; draws 7,
  triangles 158, shadow calls 34 (one fewer).
- **Played runs**: `platform 120` before/after same hash `c1603d79...`,
  28 frames, landed at y 1.6, hp 100, score 250, audio 1, 0 drops.
- **Gates**: `python -m pytest -q` 211 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-61.json`.

## Cycle 62 - UI readability: empty-reserve warning
- **Area**: UI readability (62nd cycle).
- **Defect / evidence**: the cycle-55 low-ammo panel shows
  `LOW AMMO <mag>`, but with zero reserve rounds the player cannot reload.
  The warning looked like an ordinary low-magazine prompt and implied a
  reload would help; the reserve count lived only in the top-left status.
- **Fix**: read the equipped weapon's reserve in the HUD; when the
  low-ammo branch runs and reserve is zero, add a red `NO RESERVE` second
  line and grow the panel from 150x22 to 150x40. With reserve rounds the
  panel keeps its existing size and label. Draw-only.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-62/`;
  960x540 seed 1, pulse magazine 3 with reserve 0. 2,768 changed px
  (0.53%, bbox 405,321-554,339), mean luma 32.33 -> 32.36; draws 6,
  triangles 290.
- **Played runs**: `dry 60` before/after same hash `d33f43e4...`,
  ammo 0/reserve 0, cue NO AMMO, 11 frames, hp 100, audio 1, drops 0.
- **Gates**: `python -m pytest -q` 213 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-62.json`.

## Cycle 63 - Graphics and effects: pickup collection pop
- **Area**: graphics and effects (63rd cycle).
- **Opportunity**: the surge pickup beam and orb vanished on the trigger
  frame; the only feedback was the `SURGE ACQUIRED` caption, so a major
  power-up had no world-space payoff.
- **Fix**: keep the existing pickup orb visible for 0.30 s after
  collection, growing by a 1.5x factor (to 2.5x at the end) and rising
  0.9 m while the beam hides.
  Tuning lives in `juice.pickup_fx_s/scale/rise`; the timer and transform
  are presentation-only. No new nodes, meshes, materials or sim changes.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-63/`;
  960x540 seed 1, six frames after the surge trigger. 15,698 changed px
  (3.03%, bbox 411,92-899,257; 15,386 px in the 3D scene, bbox
  411,116-555,257), mean luma 14.19 -> 17.73; draws 3, triangles 146,
  shadow calls 35. The first 3.0x growth covered the crosshair, so the
  scale was tuned to 1.5 and the pair re-captured.
- **Played runs**: `pickup 300` before/after same hash `7f84f3e9...`,
  147 frames, wave 2, hp 100, audio 1, drops 0.
- **Gates**: `python -m pytest -q` 215 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-63.json`.

## Cycle 64 - Audio cues: critical-kill reward
- **Area**: audio cues (64th cycle).
- **Defect / evidence**: critical kills roll at 12% and pay double
  bounty, but the `critical` event was unmapped. The only signals were the
  generic kill voice and a larger score pop, so the reward was not legible
  as critical.
- **Fix**: map the existing event to a 0.08 s 1760 Hz sine at 0.55 gain and
  an accent `CRITICAL` caption. The generic kill voice still plays; reward
  roll, bounty, kill feed, streak and sim state are untouched.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-64/`;
  960x540 seed 1, forced critical on a 1 hp mite. 3,204 changed px
  (0.62%, bbox 420,164-827,459), mean luma 35.70 -> 35.60; draws 10,
  triangles 698; voices 3 -> 4. WAV/spectrogram: 0.08 s voice, peak 1.0.
- **Played runs**: `kite 3000` before/after same hash `945e3fdd...`,
  exactly 4 natural critical clips at frames 705/779/943/2486, audio
  462 -> 466, 32 kills, hp 82, peak 8, 0 drops.
- **Gates**: `python -m pytest -q` 218 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-64.json`.

## Cycle 65 - Progression/saves: disabled-profile warning
- **Area**: progression and saves (65th cycle).
- **Defect / evidence**: an unsupported profile schema sets
  `profile_disabled`; `_save_profile` and `_record_progress` then return
  early, but the death debrief looked normal. The player saw a scored run
  with no sign that nothing would persist. The baseline test found a
  normal debrief.
- **Fix**: add a red `PROFILE DISABLED` line first in the debrief extras
  when `profile_disabled` is true, taking precedence over `PROFILE NOT
  SAVED`. Schema refusal, no-overwrite guard, in-memory run record and
  debrief behavior are unchanged.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-65/`;
  960x540 seed 1, schema-99 profile, staged brute death. 9,692 changed px
  (1.87%, bbox 290,334-669,383), mean luma 51.24 -> 49.91; draws 6,
  triangles 278.
- **Played runs**: `profile_bad 240` before/after same death hash
  `f8cd9e28...`, disabled true, last_run recorded, runs 0, save_errors 0,
  hp 0, 0 drops; the schema-99 file stays byte-for-byte unchanged.
- **Gates**: `python -m pytest -q` 220 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-65.json`.

## Cycle 66 - Combat feel: reload viewmodel dip
- **Area**: combat feel (66th cycle).
- **Opportunity**: the reload bar and completion cue existed, but the
  first-person gun stayed rigidly at hip through the whole reload, so the
  weapon felt static while the magazine filled.
- **Fix**: dip the existing viewmodel nodes down 0.12 m and back 0.06 m on
  a `sin(pi*phase)` curve from `reload_t / reload_s`, returning to rest at
  completion. Amounts live in `juice.viewmodel reload_drop/reload_back`;
  no new nodes, draws, sim timing, ammo or input changes.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-66/`;
  960x540 seed 1, pulse reload held at half duration. 12,027 changed px
  (2.32%, bbox 551,333-673,529), mean luma 32.60 -> 32.83; draws 6,
  triangles 290; gun body y 1.450 -> 1.330.
- **Played runs**: `reload 60` before/after same hash `d7eb253d...`,
  6 frames, ammo 30/reserve 90, cue RELOADED, hp 100, audio 1, drops 0.
- **Gates**: `python -m pytest -q` 223 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-66.json`.

## Cycle 67 - Enemies/bosses: entity-safe warden escorts
- **Area**: enemies and bosses (67th cycle).
- **Defect / evidence**: cycle 60 rejected cover-blocked escorts, but the
  ring starts at 1.2 m while the warden radius is 1.0 m and the mite
  radius 0.5 m. Escorts could spawn inside the boss or overlap a previous
  escort; seed 12 put both mites inside the warden footprint, and seeds
  23/37 produced overlapping pairs.
- **Fix**: reject any candidate within mite radius + enemy radius + 0.04 m
  of a live enemy (warden and already-placed escorts included), retry 16
  times. `summon_clearance` is DATA-owned on the warden; cover check,
  count, `max_alive`, RNG order and summon event remain. Summon positions
  change, so `bot_campaign.json` was re-recorded from the winning adaptive
  kite run (33 kills, score 12545, wave 4, hp 64,
  hash `d1631a1e...`); the fairness test still replays a witnessed win.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-67/`;
  960x540 seed 12, forced centre warden summon. Before: both mites embedded
  in the warden; after: clear. 5,488 changed px (1.06%, bbox
  375,230-542,358), mean luma 34.50 -> 33.85; draws 10, triangles 1158.
- **Played runs**: `summon_overlap 5` seed 12 before/after boss overlaps
  1 -> 0, boss gaps 1.21/1.53 -> 2.03/1.87, pair gap 1.84 -> 2.38; both
  hp 100, 0 hurts, 0 drops. Re-recorded reference: 3000 frames, 33 kills,
  score 12545, wave 4, hp 64, hash `d1631a1e...`.
- **Gates**: `python -m pytest -q` 224 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-67.json`.

## Cycle 68 - Levels: seal the campaign on clear
- **Area**: levels (68th cycle).
- **Defect / evidence**: campaign clear is recorded at wave-4 entry, but
  the sim had already queued wave 4 and kept spawning it during the
  four-second banner. A staged win reproduced four live wave-4 enemies and
  four spawn voices while `CAMPAIGN CLEAR` was up; a completed run could be
  attacked.
- **Fix**: add `Sim.victory` and `seal_campaign()` — clear the queue, set
  `spawn_t` to infinity, skip wave-clear advancement and guard
  `_build_wave`. `ShooterGame` calls it when setting `campaign_cleared`.
  Banner, win recording, wave number, HUD and geometry are unchanged.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-68/`;
  960x540 seed 1, warden kill at wave 3, 180 frames into the banner.
  Before: live wave-4 enemies and HOSTILE INBOUND; after: empty arena under
  the same banner. 18,368 changed px (3.54%, bbox 367,12-947,459), mean
  luma 34.13 -> 34.19; draws 8 -> 6, triangles 942 -> 290.
- **Played runs**: `campaign 180` before/after alive enemies 4 -> 0,
  audio 9 -> 5, victory false -> true, wave 4 and banner 1.0 s in both,
  hp 100, 0 hurts, 0 drops. The existing fairness replay still wins
  without a reference re-record.
- **Gates**: `python -m pytest -q` 225 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-68.json`.

## Cycle 69 - UI readability: persistent campaign-complete line
- **Area**: UI readability (69th cycle).
- **Defect / evidence**: cycle 68 seals wave construction at the campaign
  win, so the arena is empty after the four-second clear banner. Once the
  banner expires the HUD looks like an ordinary wave-4 lull, with no enemies
  and no message explaining that the run is complete.
- **Fix**: draw a compact accent `CAMPAIGN COMPLETE` line at y=116 when
  `sim.alive`, `sim.victory` is set and `campaign_clear_t` has expired. The
  existing `CAMPAIGN CLEAR` banner keeps the screen while it runs, so the
  lines never double up. Draw-only; no sim, wave or save changes.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-69/`;
  960x540 seed 1, 300 frames after the warden kill. 988 changed px
  (0.19%, bbox 379,116-580,129), mean luma 33.07 -> 33.40; draws 6,
  triangles 290.
- **Played runs**: `campaign 300` before/after same hash `236ec766...`,
  wave 4, victory true, banner 0, no enemies, hp 100, audio 5, drops 0.
- **Gates**: `python -m pytest -q` 228 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-69.json`.

## Cycle 70 - Graphics/effects: visible ammo-cache drops
- **Area**: graphics and effects (70th cycle).
- **Defect / evidence**: the sim drops an ammo cache on 3% of kills for
  eight seconds, but `game.py` had no cache node. The cache was invisible
  and could only be collected by accident; the only cue was after pickup.
- **Fix**: add a pool of four hidden nodes sharing `mesh.pickup` and a new
  amber emissive `material.cache`, and show one per active `sim.caches`
  entry with a small spin/bob. Pool caps presentation at four; lifetime,
  pickup volume, reserve amount and reward RNG stay in sim. No colliders,
  save data or sim fields change.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-70/`;
  960x540 seed 1, one staged cache at (0,4). 5,406 changed px (1.04%,
  bbox 426,92-911,423; 5,130 px in the 3D scene, bbox 426,346-515,423),
  mean luma 32.45 -> 33.49; draws 7, triangles 302, shadow calls 35. The
  frame-budget test still passes.
- **Played runs**: `kite 3000` before/after same hash `54bdc60c...`,
  30 kills, hp 76, audio 437, 0 drops, 2 cache rewards and 1 collection.
- **Gates**: `python -m pytest -q` 231 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-70.json`.

## Cycle 71 - Audio cues: ammo-cache drop cue
- **Area**: audio cues (71st cycle).
- **Defect / evidence**: cycle 70 made dropped ammo caches visible, but
  `cache_drop` stayed unmapped. The cache appeared silently; only its later
  collection had a voice/caption, so a player looking away from the kill
  could miss the drop entirely.
- **Fix**: map `cache_drop` to a distinct 0.05 s 1320 Hz sine at 0.5 gain
  and an accent `AMMO CACHE DROP` caption. Collection and kill cues remain;
  cache lifetime, reserve, reward RNG and sim state are untouched.
- **Screenshot proof**: workspace `shots/shooter-campaign/cycle-71/`;
  960x540 seed 1, forced cache drop on a 1 hp mite. 5,388 changed px
  (1.04%, bbox 378,164-827,459), mean luma 35.78 -> 35.71; draws 11,
  triangles 710; voices 3 -> 4. WAV/spectrogram: 0.05 s voice, peak 1.0.
- **Played runs**: `kite 3000` before/after same hash `54bdc60c...`,
  exactly 2 cache_drop clips at frames 570/1455, audio 437 -> 439, 1 cache
  collected, 30 kills, hp 76, 4 hurts, 0 drops.
- **Gates**: `python -m pytest -q` 234 passed; determinism 1800 ok; aikit
  `check shooter` 4/4.
- **Evidence file**: `evidence/cycle-71.json`.
