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
