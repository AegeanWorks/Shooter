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
│   ├── game.py          <- ShooterGame: five ops + draw_ui, Scene sync, viewmodel, boss core/beacon, floor grid/trim, mixer + cue captions
│   ├── sim.py           <- deterministic sim: move/weapons/enemies/waves/boss/hit-reaction/cover-slide/particles
│   ├── bot.py           <- headless bot scripts (move/fire/assault/kite/overdrive_step)
│   ├── ui.py            <- single-source HUD: crosshair/ammo alert/reload/wave/score/streak/kill-feed/overdrive/damage/boss/pickup
│   ├── profile.py       <- versioned, atomic run profile (bests, wins, runs, debrief)
│   └── data/
│       ├── weapons.json    <- 4 guns (pulse/scatter/lance/surge)
│       ├── enemies.json    <- mite/brute/wisp/warden boss
│       ├── levels.json     <- arena + low jump platform + open spawn lane + 5 waves (wave 3 warden) + win_wave 4
│       ├── juice.json      <- tracer/flash offset/scale, viewmodel, particle caps, hitstop, flinch
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
│   └── test_audit.py       <- wave-1/2 audit regression pins
├── scripts/
│   ├── record_bot.py  <- emit CommandLog for --replay
│   ├── soak.py        <- full-length sustain soak + timing/budget report
│   ├── play_run.py    <- played-run evidence: idle/kite/strafe/ambush/boss/slam/pickup reports
│   ├── audio_probe.py <- render cue voices to WAV + waveform/spectrogram evidence
│   └── capture.py     <- seeded routes (spawn/combat/burst/pickup/pickup_spawn/hurt/boss/slam/death)
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
│   └── cycle-21.json  <- improvement-cycle 21 proof: first-person gun pair, same-hash runs
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

Best score, kills, wave and streak, campaign wins, the run count and the last-run summary
persist in `saves/profile.json` (git-ignored, created on first run). The store is versioned:
schema 0 migrates through 1 to 2; an unsupported schema is refused without touching the file
(persistence is disabled for that session); a corrupt file is quarantined and the `.bak` is tried. Writes use
a temp file + fsync + atomic replace with a backup, under a short advisory lock. The HUD shows
`BEST <score>` once one exists, and the death screen reports the run (`RUN OVER`, score, kills,
wave, best streak, time) plus `NEW BEST` when the run beats the loaded best.

<!-- aegean:brand-assets:start -->
## 🎨 Brand Assets

> **AI-Generated Brand Artwork.** The banner and logo are **AI-generated brand assets**. They are illustrative and may not literally depict every feature or the full project scope.
<!-- aegean:brand-assets:end -->

## 📜 License

<!-- aegean:license:start -->
Free for personal play under the Aegean Game License 1.1 (AGL-1.1); see [LICENSE](LICENSE). It is DRM-free: Licensor ships no DRM and a distributor may not add it. Streaming, modding and free mods are allowed. Commercial use, paid mods and AI training need the Aegean Commercial License 1.0 (ACL-1.0); see [COMMERCIAL.md](COMMERCIAL.md).
<!-- aegean:license:end -->
