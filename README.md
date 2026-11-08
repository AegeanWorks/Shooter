# Shooter (Keystone plug-in)

<!-- aegean:media:start -->
<p align="center"><img src="assets/social-preview.svg" alt="Shooter social preview" width="100%"></p>
<p align="center"><a href="LICENSE"><img src="https://img.shields.io/badge/license-AGL--1.1-7048e8" alt="License"></a> <a href="https://github.com/AegeanWorks/AIKit"><img src="https://img.shields.io/badge/AIKit-integrated-6f42c1" alt="AIKit Integrated"></a></p>
<!-- aegean:media:end -->


Fast arena shooter on the Keystone engine. Engine owns render/loop/input/serialization (`projects/keystone`); this package owns state/rules/scene and loads via `--game shooter.game:ShooterGame`.

## 30-Second Cold-Start Quick Reference

- **Runtime Prerequisites**: Python 3.10+, Keystone pinned stack (numpy 2.5.3, PyOpenGL 3.1.10, glfw 2.11.0, pytest 9.1.1); OpenGL 3.3-capable GPU for rendered runs (headless sim needs no GPU).
- **One-click start**: double-click `start-shooter.cmd` (Windows) or run `./start-shooter.sh` (macOS/Linux).
- **Canonical Regression Shield Gate**:
  ```powershell
  # from projects/shooter
  python -m pytest -q
  ```

## One-click start

Double-click `start-shooter.cmd` (Windows) or run `./start-shooter.sh`
(macOS/Linux) — no terminal setup, no `PYTHONPATH`. It launches the live
windowed game via `play.py`:

```powershell
# from anywhere; extra args pass straight to Keystone
python projects/shooter/play.py
python projects/shooter/play.py --simulate --frames 600
python projects/shooter/play.py --describe
```

`play.py` resolves its own folder, adds `projects/shooter` +
`projects/keystone` to `sys.path`, checks Python 3.10+ and the sibling
Keystone checkout, then runs `keystone --game shooter.game:ShooterGame`.

## Prerequisites

- Python 3.10+, Keystone pinned stack (numpy 2.5.3, PyOpenGL 3.1.10, glfw 2.11.0, pytest 9.1.1)
- OpenGL 3.3-capable GPU driver for rendered runs (headless sim needs no GPU)

## Test

```powershell
# from projects/shooter
python -m pytest -q
# engine gate (from projects/keystone)
python -m pytest -q
# headless bot proofs (no GPU)
$env:PYTHONPATH="C:\Users\Yunus-Emre\Desktop\portable_agent_kit\projects\keystone;C:\Users\Yunus-Emre\Desktop\portable_agent_kit\projects\shooter"
python -m keystone --game shooter.game:ShooterGame --describe
python -m keystone --game shooter.game:ShooterGame --simulate --frames 600 --trace
python -m keystone --game shooter.game:ShooterGame --verify-determinism --frames 1800
python -m keystone --game shooter.game:ShooterGame --headless --frames 1 --size 960x540 --ui --out shot.png --report shot.json
# campaign reference: clears the wave-3 warden and wins at wave 4
python play.py --replay bot_campaign.json
```

## What's Inside

```text
projects/shooter/
├── shooter/
│   ├── __init__.py      <- plug-in exports
│   ├── game.py          <- ShooterGame: five ops + draw_ui, Scene sync, viewmodel, boss core/beacon/slam ring, spawn/summon marks, fire tints, wisp bolts/warning, death silhouettes, brute cues, crosshair bounty, damage jolt, switch cues, win/career/full-history debrief, floor grid/cover panels/trim/pilasters/platform rim/pulsing pad, mixer + captions
│   ├── sim.py           <- deterministic sim: move/weapons/enemies/waves/boss/hit-reaction/cover-slide/particles
│   ├── bot.py           <- headless bot scripts (move/fire/assault/kite/overdrive_step)
│   ├── ui.py            <- single-source HUD: spread-aware crosshair, centered status, streak bonus, target health (hidden on death), kill marker, low-ammo count/reload, kill-feed, damage, boss/pickup direction (tag survives boss)
│   ├── profile.py       <- versioned, atomic run profile (bests, wins, runs, W/L history, debrief)
│   └── data/
│       ├── weapons.json    <- 4 guns (pulse/scatter/lance/surge)
│       ├── enemies.json    <- mite/brute/wisp/warden boss + melee reach
│       ├── levels.json     <- arena + low jump platform + open spawn lane + 5 waves (wave 3 warden) + win_wave 4
│       ├── juice.json      <- tracer/flash, viewmodel, reticle, spawn mark, killmark, score pop, slam ring, death fx, particles, hitstop, flinch
│       ├── engagement.json <- reward/streak/near-miss/overdrive tuning
│       └── grade.json      <- renderer flags adopted as DATA
├── tests/
│   ├── conftest.py         <- adds keystone + shooter to sys.path
│   ├── test_shooter.py     <- move/shoot/hit/kill/die/score/determinism/budget
│   ├── test_engagement.py  <- odds/stream/overdrive/lock/determinism
│   ├── test_feedback.py    <- hurt-source telemetry + directional HUD cue
│   ├── test_boss.py        <- warden data/wave/slam/summon/kill/bar/core
│   ├── test_levels.py      <- pickup beacon visibility/label + trigger parity
│   ├── test_ui.py          <- single HP/ammo source, crosshair contrast, HUD purity
│   ├── test_graphics.py    <- floor grid, shared trim batch, draw budget
│   ├── test_audio.py       <- boss/engagement voices, captions, clip hook
│   ├── test_profile.py     <- schema/backup/quarantine, run record, debrief
│   ├── test_combat_feel.py <- non-lethal hit flinch, expiry, scene squash
│   ├── test_enemy_cover.py <- cover collision, slide-around, spawn guard
│   ├── test_levels_platform.py <- jumpable low platform + landing proof
│   ├── test_kill_feed.py   <- typed kill event, feed draw/expiry
│   ├── test_muzzle.py      <- off-axis flash offset and small node scale
│   ├── test_denial.py      <- denied overdrive voice/caption + state parity
│   ├── test_wins.py        <- schema-2 migration, persisted wins, win banner
│   ├── test_dry_fire.py    <- rate-limited dry fire, NO AMMO voice/caption
│   ├── test_enemy_los.py   <- brute melee LOS; open-field attack parity
│   ├── test_spawn_lane.py  <- clear spawn->pickup cover lane
│   ├── test_boss_hp.py     <- numeric WARDEN HP readout
│   ├── test_viewmodel.py   <- camera-follow gun, weapon tint, death hide
│   ├── test_reload_cue.py  <- reload-completion voice/caption + ammo parity
│   ├── test_history.py     <- schema-3 migration, capped run history, RECENT line
│   ├── test_reticle.py     <- per-weapon hip-fire reticle gap; pulse reference
│   ├── test_melee_reach.py <- platform high-ground vertical melee reach
│   ├── test_spawn_mark.py  <- wave-spawn origin marker, expiry, parity
│   ├── test_ui_center.py   <- top-center WAVE/STREAK/OVERDRIVE/SURGE/BEST centering
│   ├── test_tracer_tint.py <- per-weapon tracer/flash materials, distinct tints
│   ├── test_switch_cue.py  <- weapon-switch click + caption, distinct slot clips
│   ├── test_win_history.py <- campaign win recorded, no duplicate, W/L debrief
│   ├── test_killmark.py    <- kill-only timer, red corner ticks, expiry
│   ├── test_slam_ring.py   <- warden windup ring radius, visibility, DATA
│   ├── test_pickup_arrow.py <- off-screen pickup edge tag, ahead/inactive gates
│   ├── test_debrief_width.py <- wide W/L history fits the debrief panel
│   ├── test_wall_depth.py  <- 8 wall pilasters, shared material, budget-safe
│   ├── test_spawn_cue.py   <- spawn voice + rate-limited HOSTILE INBOUND
│   ├── test_career_debrief.py <- RUNS/WINS career row, hidden without runs
│   ├── test_wisp_bolt.py   <- wisp chest->eye tracer and violet material
│   ├── test_summon_mark.py <- warden escort positions, spawn marks
│   ├── test_platform_rim.py <- jump-platform lit edge, shared trim
│   ├── test_streak_bonus.py <- 10%/kill cap 50%, shown as STREAK +P%
│   ├── test_death_fx.py    <- death timer, shrinking white silhouette
│   ├── test_brute_slam.py  <- brute_slam event, clip, caption
│   ├── test_best_row.py    <- career bests row, hidden at zero
│   ├── test_score_pop.py   <- +N bounty at the crosshair, expiry
│   ├── test_target_hp.py   <- crosshair target HP bar, warden exclusion
│   ├── test_approach_pad.py <- platform launch pad, trim material, position
│   ├── test_pickup_boss_tag.py <- pickup edge tag survives a boss fight
│   ├── test_cover_texture.py <- deterministic cover panel, no new draws
│   ├── test_wisp_cue.py    <- wisp_bolt event, 1200 Hz clip, caption
│   ├── test_recent_five.py <- all five stored runs across RECENT/HISTORY
│   ├── test_hurt_shake.py  <- hurt_t camera jolt, sim hash unchanged
│   ├── test_target_dead.py <- target bar hidden on the death screen
│   ├── test_pad_pulse.py   <- launch pad sine scale pulse
│   ├── test_lowammo_count.py <- LOW AMMO <mag> near the crosshair
│   ├── test_wall_texture.py <- deterministic wall panel texture, no new draws
│   └── test_audit.py       <- wave-1/2 audit regression pins
├── scripts/
│   ├── record_bot.py  <- emit CommandLog for --replay
│   ├── soak.py        <- full-length sustain soak + timing/budget report
│   ├── play_run.py    <- played-run evidence: idle/kite/strafe/ambush/boss/slam/brute/pickup/highground/switch
│   ├── audio_probe.py <- render cue voices to WAV + waveform/spectrogram evidence
│   └── capture.py     <- seeded routes (spawn/combat/pickup/hurt/boss/slam/reticle/highground/spawn_mark/score_center/tracer_tint/switch_cue/win_history/killmark/slam_ring/pickup_arrow/debrief_width/wall_depth/spawn_cue/wisp_bolt/summon_mark/platform_rim/streak_bonus/death_fx/brute_slam/score_pop/target_hp/boss_pickup/cover_texture/history5/platform_pulse/death)
├── evidence/
│   ├── cycle-01.json  <- improvement-cycle 1 proof: diffs, runs, gate results
│   ├── cycle-02.json  <- improvement-cycle 2 proof: boss pair, runs, gate results
│   ├── cycle-03.json  <- improvement-cycle 3 proof: beacon pair, pickup run, gates
│   ├── cycle-04.json  <- improvement-cycle 4 proof: HUD pair, crosshair, runs, gates
│   ├── cycle-05.json  <- improvement-cycle 5 proof: arena pair, luma, budget, runs
│   ├── cycle-06.json  <- improvement-cycle 6 proof: audio events, captions, WAV, gates
│   ├── cycle-07.json  <- improvement-cycle 7 proof: profile save, debrief pair, runs
│   ├── cycle-08.json  <- improvement-cycle 8 proof: campaign-clear pair, fairness run
│   ├── cycle-09.json  <- improvement-cycle 9 proof: low-ammo/reload HUD pair, runs
│   ├── cycle-10.json  <- improvement-cycle 10 proof: hit-flinch pair, same-hash runs
│   ├── cycle-11.json  <- improvement-cycle 11 proof: cover-slide pair, fairness run
│   ├── cycle-12.json  <- improvement-cycle 12 proof: jump-platform pair, landing run
│   ├── cycle-13.json  <- improvement-cycle 13 proof: kill-feed pair, same-hash runs
│   ├── cycle-14.json  <- improvement-cycle 14 proof: muzzle-flash pair, same-hash runs
│   ├── cycle-15.json  <- improvement-cycle 15 proof: denied-overdrive cue pair, WAV
│   ├── cycle-16.json  <- improvement-cycle 16 proof: persisted-wins banner pair, runs
│   ├── cycle-17.json  <- improvement-cycle 17 proof: dry-fire cue pair, same-hash run
│   ├── cycle-18.json  <- improvement-cycle 18 proof: cover LOS pair, same-hash runs
│   ├── cycle-19.json  <- improvement-cycle 19 proof: open spawn lane pair, campaign run
│   ├── cycle-20.json  <- improvement-cycle 20 proof: numeric boss-HP pair, same-hash run
│   ├── cycle-21.json  <- improvement-cycle 21 proof: first-person gun pair, same-hash runs
│   ├── cycle-22.json  <- improvement-cycle 22 proof: reload-cue pair, same-hash run
│   ├── cycle-23.json  <- improvement-cycle 23 proof: persisted-history debrief pair, run
│   ├── cycle-24.json  <- improvement-cycle 24 proof: spread-reticle pairs, same-hash runs
│   ├── cycle-25.json  <- improvement-cycle 25 proof: high-ground melee pair, reach run
│   ├── cycle-26.json  <- improvement-cycle 26 proof: spawn-marker pair, same-hash run
│   ├── cycle-27.json  <- improvement-cycle 27 proof: centered status pair, same-hash run
│   ├── cycle-28.json  <- improvement-cycle 28 proof: per-weapon fire-tint pairs, same-hash run
│   ├── cycle-29.json  <- improvement-cycle 29 proof: weapon-switch cue pair, same-hash run
│   ├── cycle-30.json  <- improvement-cycle 30 proof: win-history debrief pair, campaign run
│   ├── cycle-31.json  <- improvement-cycle 31 proof: kill-marker crosshair pair, same-hash run
│   ├── cycle-32.json  <- improvement-cycle 32 proof: slam-radius ring pair, same-hash run
│   ├── cycle-33.json  <- improvement-cycle 33 proof: pickup edge-tag pair, same-hash run
│   ├── cycle-34.json  <- improvement-cycle 34 proof: wide-debrief pair, same-hash run
│   ├── cycle-35.json  <- improvement-cycle 35 proof: wall-depth pair, same-hash run
│   ├── cycle-36.json  <- improvement-cycle 36 proof: spawn-voice pair, same-hash run
│   ├── cycle-37.json  <- improvement-cycle 37 proof: career-debrief pair, same-hash run
│   ├── cycle-38.json  <- improvement-cycle 38 proof: wisp-bolt pair, campaign run
│   ├── cycle-39.json  <- improvement-cycle 39 proof: summon-marker pair, same-hash boss run
│   ├── cycle-40.json  <- improvement-cycle 40 proof: platform-rim pair, same-hash platform run
│   ├── cycle-41.json  <- improvement-cycle 41 proof: streak-bonus pair, same-hash run
│   ├── cycle-42.json  <- improvement-cycle 42 proof: death-silhouette pair, same-hash run
│   ├── cycle-43.json  <- improvement-cycle 43 proof: brute-slam cue pair, brute drill
│   ├── cycle-44.json  <- improvement-cycle 44 proof: career-bests debrief pair, same-hash run
│   ├── cycle-45.json  <- improvement-cycle 45 proof: crosshair bounty pop, same-hash run
│   ├── cycle-46.json  <- improvement-cycle 46 proof: target-health pair, same-hash run
│   ├── cycle-47.json  <- improvement-cycle 47 proof: platform launch-pad pair, same-hash run
│   ├── cycle-48.json  <- improvement-cycle 48 proof: boss-pickup tag pair, campaign run
│   ├── cycle-49.json  <- improvement-cycle 49 proof: cover-panel pair, same-hash run
│   ├── cycle-50.json  <- improvement-cycle 50 proof: wisp-bolt cue pair, campaign run
│   ├── cycle-51.json  <- improvement-cycle 51 proof: five-run history pair, same-hash run
│   ├── cycle-52.json  <- improvement-cycle 52 proof: damage camera-jolt pair, same-hash run
│   ├── cycle-53.json  <- improvement-cycle 53 proof: clean death screen pair, same-hash run
│   ├── cycle-54.json  <- improvement-cycle 54 proof: platform pulse pair, same-hash run
│   ├── cycle-55.json  <- improvement-cycle 55 proof: low-ammo count pair, same-hash run
│   └── cycle-56.json  <- improvement-cycle 56 proof: wall-panel pair, same-hash run
├── saves/                   <- local player profile (git-ignored, created on first run)
├── play.py                 <- one-click launcher (path setup + game start, passes args through)
├── start-shooter.cmd       <- Windows double-click entry point (python/play.py)
├── start-shooter.sh        <- macOS/Linux entry point (python3 play.py)
├── .gitignore              <- bytecode, caches, session evidence
├── README.md               <- this file
├── LICENSE                 <- Aegean Game License 1.1 (personal play)
├── LICENSES/               <- machine-readable license texts (REUSE)
├── COMMERCIAL.md            <- paid use terms (ACL-1.0)
├── ASSETS.md                <- asset provenance for packs/ports
├── REUSE.toml               <- copyright + license inventory
├── assets/                 <- logo.svg + social-preview.svg (brand)
├── bot_kite600.json        <- minute-one kite reference (first two waves)
├── bot_campaign.json       <- 3000-frame campaign reference (boss clear, wave 4)
├── bot_log.json            <- command-log sample
├── bot_soak.json           <- sustain soak script
├── bot_soak2.json          <- second sustain soak script
├── bot_strafe.json         <- strafe drill script
├── soak_report.json        <- sustain evidence trail
├── soak_report2.json       <- second sustain evidence trail
├── spin_actions.json       <- spin action sample
├── shot_combat.json        <- headless combat capture report
├── shot_combat.png         <- headless combat capture image
├── shot_fix_burst.json     <- burst capture report
├── shot_fix_burst.png      <- burst capture image
├── shot_fix_combat.json    <- combat capture report
├── shot_fix_combat.png    <- combat capture image
├── shot_fix_death.json     <- death capture report
├── shot_fix_death.png      <- death capture image
├── shot_fix_pickup.json    <- pickup capture report
├── shot_fix_pickup.png     <- pickup capture image
├── shot_fix_spawn.json     <- spawn capture report
├── shot_fix_spawn.png      <- spawn capture image
├── shot_min1.json          <- minute-1 capture report
├── shot_min1.png           <- minute-1 capture image
├── shot_soak.json          <- soak capture report
├── shot_soak.png           <- soak capture image
├── shot_stage4_min1.json   <- stage-4 capture report
├── shot_stage4_min1.png    <- stage-4 capture image
├── shot_stage4_min30proxy.json <- stage-4 proxy capture report
├── shot_stage4_min30proxy.png  <- stage-4 proxy capture image
└── .aikit/
    ├── decisions.md     <- append-only ADRs
    ├── cycles.md        <- append-only improvement-cycle record
    ├── guidelines.md    <- agent working agreement
    ├── project.json     <- project metadata
    ├── media.json       <- brand/media manifest
    └── task_ledger.json <- disruption-recovery ledger
```

## Controls (live Engine bindings)

Live play uses the Engine's default key map only — the Engine builds a
plain `InputMap()` with no per-game bindings hook, so just these reach
the sim: W/S forward/back, A/D strafe, E jump, mouse look, left-click
fire (one shot per click). `1/2/3` weapon slots, `R` reload, and voluntary
overdrive have no live key binding yet (engine-side gap, filed — see
ADR-016); drive them via headless `ActionState` scripts (`shooter.bot`
kite/overdrive policies), `--replay` logs, or the `bot_kite600.json`
reference. Shift sprint, P pause, H hide UI, F1 cursor, Esc quit. The rear-left
corner has a 0.7 m platform; `E` jump can land on it (the other covers are too
tall to jump).

The campaign now clears after the wave-3 Warden boss (wave 4 entry): the HUD shows a
`CAMPAIGN CLEAR` banner for four seconds, and the death debrief remembers it as
`CAMPAIGN CLEARED`.

## Progress and saves

Best score, kills, wave and streak, campaign wins, the run count, a newest-first history of
the last five runs and the last-run summary persist in `saves/profile.json` (git-ignored,
created on first run). The store is versioned: schema 0 migrates through 1 and 2 to 3; an
unsupported schema is refused without touching the file (persistence is disabled for that
session); a corrupt file is quarantined and the `.bak` is tried. Writes use
a temp file + fsync + atomic replace with a backup, under a short advisory lock. The HUD shows
`BEST <score>` once one exists, and the death screen reports the run (`RUN OVER`, score, kills,
wave, best streak, time) plus `NEW BEST` when the run beats the loaded best and
`RECENT <scores>` from the saved run history.

<!-- aegean:brand-assets:start -->
## 🎨 Brand Assets

> **AI-Generated Brand Artwork.** The banner and logo are **AI-generated brand assets**. They are illustrative and may not literally depict every feature or the full project scope.
<!-- aegean:brand-assets:end -->

## 📜 License

<!-- aegean:license:start -->
Free for personal play under the Aegean Game License 1.1 (AGL-1.1); see [LICENSE](LICENSE). It is DRM-free: Licensor ships no DRM and a distributor may not add it. Streaming, modding and free mods are allowed. Commercial use, paid mods and AI training need the Aegean Commercial License 1.0 (ACL-1.0); see [COMMERCIAL.md](COMMERCIAL.md).
<!-- aegean:license:end -->
