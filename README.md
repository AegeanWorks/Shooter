# Shooter (Keystone plug-in)

<!-- aegean:media:start -->
<p align="center"><img src="assets/social-preview.svg" alt="Shooter social preview" width="100%"></p>
<p align="center"><a href="LICENSE"><img src="https://img.shields.io/badge/license-AGL--1.1-7048e8" alt="License"></a> <a href="https://github.com/AegeanWorks/AIKit"><img src="https://img.shields.io/badge/AIKit-integrated-6f42c1" alt="AIKit Integrated"></a></p>
<!-- aegean:media:end -->


Fast arena shooter on the Keystone engine. Engine owns render/loop/input/serialization (`projects/keystone`); this package owns state/rules/scene and loads via `--game shooter.game:ShooterGame`.

> **Archived**: Reforge audit complete: 252 commits audited, 0 findings; ADR corruption repaired and delivered (archived 2026-11-20). This project is read-only; its GitHub repository is archived.

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
# Keystone capture route: hashed PNG/report summary, diffable across runs
python scripts/route_evidence.py --out shots/route-proof
python scripts/route_evidence.py --out shots/route-new --compare shots/route-proof/route-summary.json
# campaign reference: clears the wave-3 warden and wins at wave 4
python play.py --replay bot_campaign.json
```

## Keystone Testbed

The shooter is the living consumer for Keystone's runtime additions:

| Keystone feature | Shooter consumer | Test |
|---|---|---|
| `AnimationStateMachine` + `StateMachineLibrary` (`.kstate`) + `apply_pose` | warden core calm/charge pulse | `tests/test_boss_anim_state.py` |
| `ComponentRuntime` lifecycle | launch-pad pulse component | `tests/test_pad_pulse.py` |
| `MaterialGraph` | warden core checker material | `tests/test_core_material_graph.py` |
| `Prefab` + `PrefabLibrary` (`.kprefab`) | 3-root pickup beacon | `tests/test_pickup_prefab.py` |
| `MaterialLibrary` (`.kmaterial`) | ammo-cache material | `tests/test_cache_material_library.py` |
| `GameSession` web/editor/JSON API | describe/scene/editor/simulate | `tests/test_keystone_web_api.py` |
| `CommandLog`/`verify_log` + `TriggerTracker` + `ParticleSystem` + `plan_batches` + `SpatialGrid` | replay, trigger edges, particle bursts, batch plan, broadphase | `tests/test_keystone_mechanics.py` |
| `AnimationLibrary` + `Track`/`AnimationController` + `apply_pose` | `.kanim` clips, sampling, crossfade, events, poses | `tests/test_keystone_animation_mechanics.py` |
| `Mixer` + `AssetRegistry` | bus gain/mixdown/voice cap, dependencies/duplicates/hot reload | `tests/test_keystone_audio_assets.py` |
| `audio_spatial.SoundSource` + `distance_gain` + `spatial_report` | spawn warning voice attenuates by distance, JSON report | `tests/test_keystone_audio_spatial_mechanics.py` |
| `CameraShaker` + `camera_shaker_report` | damage jolt composed onto an immutable base camera pose, base-vs-pose report | `tests/test_keystone_camera_shaker_mechanics.py` |
| `CameraRig` | viewmodel parts on the overlay layer with camera-space offsets, root follows the camera | `tests/test_keystone_camera_rig_mechanics.py` |
| `rng.RandomStream` + `fork` | sim-isolated presentation gain variety, JSON-safe stream state | `tests/test_keystone_rng_mechanics.py` |
| `picking.raycast_scene` + `hit_report` | scene-level crosshair probe, overlay nodes excluded, JSON hit report | `tests/test_keystone_picking_mechanics.py` |
| `NavGrid`/`find_path`/`smooth_path` + `PathFollower` | spawn-to-pickup arena route and world waypoints, no sim coupling | `tests/test_keystone_navigation_mechanics.py` |
| `content.mesh_digest` + `material_digest` | content identity for registered render assets as a JSON digest map | `tests/test_keystone_content_mechanics.py` |
| `TileMap` + `tilemap_report` | shipped arena as a round-trippable tile document with colliders and merged mesh | `tests/test_keystone_tilemap_mechanics.py` |
| `BlendSpace1D` + `BlendSample` | enemy idle clips blended by shipped HP, JSON report and sampled pose | `tests/test_keystone_animation_blend_mechanics.py` |
| `extract_root_motion` + `in_place_pose` + `root_motion_report` | shipped idle clip subject deltas and in-place proof as JSON | `tests/test_keystone_root_motion_mechanics.py` |
| `AnimationStateMachine` | shipped idle clips in an authored parameter-driven state preview | `tests/test_keystone_animation_state_mechanics.py` |
| `steering.Agent`/`seek`/`arrive`/`separation`/`steer` | AI-visible enemy wish vectors from live state and DATA speeds | `tests/test_keystone_steering_mechanics.py` |
| `schema_diff.current_versions` | live Keystone contract versions as a JSON query for AI/soak | `tests/test_keystone_schema_diff_mechanics.py` |
| `errors.KeystoneError` | structured why/fix on data failures with the rendered player message | `tests/test_keystone_errors_mechanics.py` |
| `NavAgent` + `nav_agent_report` | local spawn-to-pickup route plan and progress preview from the shipped arena | `tests/test_keystone_nav_agent_mechanics.py` |
| `RootMotionPresenter` + `root_motion_presenter_report` | local container rig driven by a shipped clip, with applied-child report | `tests/test_keystone_root_motion_presenter_mechanics.py` |
| `nav_authoring.grid_from_boxes` | NavGrid rasterized from live collision boxes with explicit floor exclusion | `tests/test_keystone_nav_authoring_mechanics.py` |
| `persistence.VersionedStore` | profile schema, migrations and corrupt recovery probed in a throwaway store | `tests/test_keystone_persistence_mechanics.py` |
| `_version.__version__` | authoritative engine version as a JSON query for evidence and AI | `tests/test_keystone_version_mechanics.py` |
| `CharacterBody`/`CharacterController` + `FixedStepClock` | gravity, grounding, step-up, cover slide, catch-up | `tests/test_keystone_physics_mechanics.py` |
| `Ray`/`ray_aabb`/`ray_sphere` + `SceneLibrary` | filtered hits, sphere pushout, `.kscene` round trip | `tests/test_keystone_raycast_scene_mechanics.py` |
| `GameSession` editor actions | scene groups, layer visibility, lock/hide, prefab overrides/nesting | `tests/test_keystone_scene_editor_mechanics.py` |
| `GameSession` authoring actions | undo/redo, play restore, materials, animation keys, diff/validate | `tests/test_keystone_authoring_mechanics.py` |
| `skin`/`gltf`/`gpu.sprites` | skin points/meshes, glTF import, sprite scale/alpha/billboard | `tests/test_keystone_skinning_gltf_sprite_mechanics.py` |
| `InputMap`/`ActionState` + UI + `png`/`obj_loader`/`batch` | contexts/pressed-held, canvas clipping, PNG/OBJ, merge_batches | `tests/test_keystone_input_ui_asset_mechanics.py` |
| `create_server` HTTP console | health/describe/scene/inspector, simulate, editor, 404/405/400 | `tests/test_keystone_http_server_mechanics.py` |
| `project`/`export` | manifest create/load/validate, CLI validate/export, hashed bundle, launcher | `tests/test_keystone_project_export_mechanics.py` |
| `PerspectiveCamera` + `culling` | look_at/clamp/move, projection edges, nested/hidden/skinned frustum culling | `tests/test_keystone_camera_culling_mechanics.py` |
| Engine loop + `HumanOverlay` + CLI | fixed-step run, pause menu/pause, `--expect-hash`/`--replay` | `tests/test_keystone_engine_loop_mechanics.py` |
| `component_codec` | dataclass/custom codecs, scene/prefab round trips, lifecycle | `tests/test_keystone_component_codec_mechanics.py` |
| `library_trash` | scene/prefab delete, unique trash, suffix isolation, restores | `tests/test_keystone_library_trash_mechanics.py` |
| `analysis` | frame stats/hashes, node/material metadata, report diff, pixel-diff PNG | `tests/test_keystone_analysis_mechanics.py` |
| `agents` | action clamps/wrappers, observe hash, report summary, audit tamper chain | `tests/test_keystone_agent_mechanics.py` |
| `asset_io` | loaders/suffixes, fingerprints, kinds, ReloadReport | `tests/test_keystone_asset_io_mechanics.py` |
| `mesh_builder` | quad/box counts, mesh merge, matrix normals, skinned concat/mode | `tests/test_keystone_mesh_builder_mechanics.py` |
| `serialization` | binary/JSON atomic writes, backup chain, BOM reads, temp cleanup | `tests/test_keystone_serialization_mechanics.py` |
| `primitives` | cube/plane/cone/cylinder/sphere counts, bounds, normals, UVs | `tests/test_keystone_primitives_mechanics.py` |
| `gpu.instancing` | grouping, culling, ordering, savings, skinned exclusion | `tests/test_keystone_instancing_mechanics.py` |
| `playtest` | canon/signals, policies, transcripts/diffs, reports, fairness verdicts | `tests/test_keystone_playtest_mechanics.py` |
| `Scene` graph | queries, IDs, parenting, traversal, visibility | `tests/test_keystone_scene_graph_mechanics.py` |
| `History` | push/undo/redo, copy isolation, branch discard, capacity, clear | `tests/test_keystone_history_mechanics.py` |
| `scene_snapshot` | nodes/transforms, camera/environment, assets, validation, restore | `tests/test_keystone_scene_snapshot_mechanics.py` |
| `scene_diff` | empty/added/removed/changed nodes, sections, validation | `tests/test_keystone_scene_diff_mechanics.py` |
| `batch` | static/skinned planning, world-space merges, exclusions, invariants | `tests/test_keystone_batch_mechanics.py` |
| `png`/`texture` | RGBA round trip/flip, corruption, texture sha, checker | `tests/test_keystone_png_texture_mechanics.py` |
| `obj_loader` | normals/UVs, negative indices, quads, homogeneous vertices, errors | `tests/test_keystone_obj_loader_mechanics.py` |
| `gltf_import` | suffix detection, prefab/registry saves, textures, re-import, errors | `tests/test_keystone_gltf_import_mechanics.py` |
| `gltf` loader | sources/GLB, buffers, accessors, validation, registry | `tests/test_keystone_gltf_loader_mechanics.py` |
| `schema`/public API | exports/version agreement, editor actions, describe parity, CubeDemo determinism | `tests/test_keystone_api_contract_mechanics.py` |
| `AnimationLibrary` + `AnimationController` | enemy idle `.kanim` clips, sampling, crossfade, sim parity | `tests/test_enemy_animation.py` |
| `bind_input` + digit keys | live slots/reload/overdrive/fire/jump, dead-key diagnostics | `tests/test_live_bindings.py` |
| `asset_io` + `obj_loader` + `reload` | .obj crate, suffix inference, hot-reload rebinding | `tests/test_cache_asset.py` |
| `broadphase.SpatialGrid` | cell-size-independent answers, edge-cell registration, insertion order, cell budget, degraded queries | `tests/test_keystone_broadphase_mechanics.py` |

`ShooterGame.testbed_report()` returns every no-argument report above in one
JSON-safe document (engine, contracts, nav, animation, steering, picking,
assets, bot, storage, presentation) — the single entry point for AI and soak
consumers. Its `sources` list names every composed report, and a reflective test
fails if a new no-arg report is added without being wired in.

```powershell
python play.py --describe
python play.py --simulate --frames 120
python play.py --serve --port 8901   # GET /api/health, /api/scene; POST /api/simulate
```

## What's Inside

```text
projects/shooter/
├── shooter/
│   ├── __init__.py      <- plug-in exports
│   ├── game.py          <- ShooterGame: ops/draw_ui, Scene sync, viewmodel/cues, boss beacons, HUD/debrief, floor/cover/pad, mixer/captions
│   ├── sim.py           <- deterministic sim: move/weapons/enemies/waves/boss/summons/particles
│   ├── bot.py           <- headless bot scripts (move/fire/assault/kite/overdrive_step)
│   ├── ui.py            <- single-source HUD: crosshair/status/streak/target/kill-feed/boss-pickup arrows
│   ├── profile.py       <- versioned, atomic run profile (bests, wins, runs, W/L history, debrief, quarantine recovery flags)
│   ├── anim.py          <- .kanim enemy idle clips and controller binding
│   ├── asset_pipeline.py <- file-backed .obj registration and fallback
│   └── data/
│       ├── anim/           <- enemy idle .kanim clips (mite/brute/wisp/warden)
│       ├── weapons.json    <- 4 guns (pulse/scatter/lance/surge)
│       ├── enemies.json    <- mite/brute/wisp/warden boss + melee reach
│       ├── levels.json     <- arena + low jump platform + open spawn lane + 5 waves (wave 3 warden) + win_wave 4
│       ├── juice.json      <- tracer/flash, viewmodel, reticle, spawn mark, killmark, score pop, slam ring, death fx, particles, hitstop, flinch
│       ├── engagement.json <- reward/streak/near-miss/overdrive tuning
│       ├── grade.json      <- renderer flags adopted as DATA
│       ├── campaign_clear.kpath <- authored victory fly-around (CameraPathLibrary)
│       ├── warden_core.kstate <- keystone state machine: calm/charge core pulse
│       ├── core_material.json <- keystone material graph: checker boss core
│       ├── pickup_beacon.kprefab <- keystone multi-root prefab: pickup/beam/orb
│       ├── cache_material.kmaterial <- keystone material library: ammo cache
│       └── cache_crate.obj <- ammo-cache crate mesh (0.6 body + lid rim)
├── tests/
│   ├── conftest.py         <- adds keystone + shooter to sys.path
│   ├── test_shooter.py     <- move/shoot/hit/kill/die/score/determinism/budget
│   ├── test_engagement.py  <- odds/stream/overdrive/lock/determinism
│   ├── test_feedback.py    <- hurt-source telemetry + directional HUD cue
│   ├── test_boss.py        <- warden data/wave/slam/summon/kill/bar/core
│   ├── test_boss_anim_state.py <- keystone .kstate core calm/charge pulse
│   ├── test_core_material_graph.py <- keystone material graph drives the core
│   ├── test_pickup_prefab.py <- keystone .kprefab instantiation, ids/payloads
│   ├── test_cache_material_library.py <- keystone .kmaterial cache material
│   ├── test_keystone_web_api.py <- GameSession describe/scene/editor/simulate
│   ├── test_keystone_mechanics.py <- replay/triggers/particles/batching/broadphase
│   ├── test_keystone_broadphase_mechanics.py <- cell-size invariance, edge cells, ordering, budget
│   ├── test_keystone_audio_spatial_mechanics.py <- spawn warning voice uses Keystone distance attenuation
│   ├── test_keystone_camera_shaker_mechanics.py <- base pose immutability and base-vs-shaken report
│   ├── test_keystone_camera_rig_mechanics.py <- overlay-layer viewmodel, camera-space offsets, rig sync
│   ├── test_keystone_rng_mechanics.py <- forked presentation stream, snapshot restore, sim isolation
│   ├── test_keystone_picking_mechanics.py <- crosshair scene probe, overlay exclusion, sim isolation
│   ├── test_keystone_evidence_mechanics.py <- named capture routes, reproducible hash, checkpoint diff
│   ├── test_keystone_navigation_mechanics.py <- arena A* route, smoothed waypoints, follower report
│   ├── test_keystone_content_mechanics.py <- content digests for shipped render assets
│   ├── test_keystone_tilemap_mechanics.py <- arena tile document round-trip, colliders, merged mesh
│   ├── test_keystone_animation_blend_mechanics.py <- enemy idle clips in an HP-keyed blend space
│   ├── test_keystone_root_motion_mechanics.py <- idle clip root deltas and in-place pose proof
│   ├── test_keystone_animation_state_mechanics.py <- authored idle state machine, threat-driven transitions
│   ├── test_keystone_steering_mechanics.py <- enemy seek/arrive/separation and clamped wish vectors
│   ├── test_keystone_schema_diff_mechanics.py <- live contract versions, no copied literals
│   ├── test_keystone_errors_mechanics.py <- structured why/fix on data failures, message preserved
│   ├── test_keystone_nav_agent_mechanics.py <- local NavAgent route plan and progress preview
│   ├── test_keystone_root_motion_presenter_mechanics.py <- local rig container pose and applied child
│   ├── test_keystone_nav_authoring_mechanics.py <- collision-box nav grid, floor exclusion, clearance
│   ├── test_keystone_nav_unification_mechanics.py <- one authoritative nav grid for plan and authoring
│   ├── test_keystone_arena_layout_mechanics.py <- shared arena layout and world-to-cell conversion
│   ├── test_keystone_report_resets_mechanics.py <- one shake-reset path across rebuild and cinematics
│   ├── test_keystone_bot_nav_grid_mechanics.py <- bot preview uses the authoritative nav grid
│   ├── test_keystone_pose_json_mechanics.py <- one JSON-safe pose serializer for animation reports
│   ├── test_keystone_presentation_resets_mechanics.py <- one rebuild reset for camera, shake and audio state
│   ├── test_data_tuning_bands.py <- cache TTL, overdrive duration and alive cap pinned by behaviour
│   ├── test_weapon_enemy_tuning_bands.py <- pellets, damage, pierce, falloff and boss cadence
│   ├── test_testbed_report_mechanics.py <- one JSON entry point for all on-demand reports
│   ├── test_keystone_persistence_mechanics.py <- profile store lifecycle probe in a throwaway dir
│   ├── test_keystone_version_mechanics.py <- authoritative engine version as a JSON query
│   ├── test_los_broadphase.py <- enemy LOS uses the wave grid, verdicts match a full scan
│   ├── test_death_camera_path.py <- death cinematic drives the camera, snapshot untouched
│   ├── test_campaign_camera_path.py <- victory fly-around loads a shipped .kpath, falls back cleanly
│   ├── test_mechanics_contract.py <- declared core stays headless, seeded, one-way
│   ├── test_new_run.py <- Enter restarts after death or victory, profile kept
│   ├── test_new_run_integration.py <- real bot run, end, restart, second run
│   ├── test_repo_line_endings.py <- lf rule vs committed blobs, no phantom modifications
│   ├── test_launchers.py <- cmd/sh double-click entry points, arg forwarding, Why/Fix
│   ├── test_readme_commands.py <- documented play.py commands run and verified
│   ├── test_python_floor.py <- no 3.11+/3.12+ syntax or stdlib for the 3.10 promise
│   ├── test_profile_safety.py <- save/lock/quarantine/backup failure modes
│   ├── test_audio_resilience.py <- mixer refusals counted, never fatal
│   ├── test_data_integrity.py <- broken data files name the file and the fix
│   ├── test_data_defaults.py <- missing juice keys keep the shipped behaviour
│   ├── test_cross_process_determinism.py <- same hash across processes and hash seeds
│   ├── test_jump_feel.py <- jump apex and coyote window pinned
│   ├── test_weapon_feel.py <- pulse reload duration and per-shot recoil pinned
│   ├── test_juice_tuning.py <- juice.json presentation constants pinned by observable design bands
│   ├── test_rebuild_isolation.py <- build_scene reassigns its 50-attribute surface
│   ├── test_keystone_ui_menu_mechanics.py <- pause-menu model, closed engine dispatch
│   ├── test_keystone_camera_path_editor_mechanics.py <- shipped .kpath save/list/preview/trash over HTTP
│   ├── test_keystone_frame_report_hash_mechanics.py <- report hash covers the artifact path, not pixels only
│   ├── test_keystone_animation_mechanics.py <- .kanim/sampling/crossfade/events/apply_pose
│   ├── test_keystone_audio_assets.py <- mixer buses/mixdown, asset deps/hot reload
│   ├── test_keystone_physics_mechanics.py <- gravity/step-up/cover slide/fixed-step clock
│   ├── test_keystone_raycast_scene_mechanics.py <- rays/sphere pushout/.kscene round trip
│   ├── test_keystone_scene_editor_mechanics.py <- scene groups/layers/locks/prefab overrides
│   ├── test_keystone_authoring_mechanics.py <- undo/redo/play/materials/animation keys/diff
│   ├── test_keystone_skinning_gltf_sprite_mechanics.py <- skinning/glTF import/sprite math
│   ├── test_keystone_input_ui_asset_mechanics.py <- input/UI/PNG-OBJ/merge_batches
│   ├── test_keystone_http_server_mechanics.py <- real GET/POST/editor routes and statuses
│   ├── test_keystone_project_export_mechanics.py <- manifests, validation, export bundle/launcher
│   ├── test_keystone_engine_loop_mechanics.py <- engine loop/clock, pause overlay, CLI gates
│   ├── test_keystone_component_codec_mechanics.py <- component codecs/scene/prefab/lifecycle
│   ├── test_keystone_camera_culling_mechanics.py <- camera math + nested/hidden/skinned culling
│   ├── test_keystone_library_trash_mechanics.py <- scene/prefab trash, uniqueness, restore safety
│   ├── test_keystone_analysis_mechanics.py <- frame stats, report/pixel diff
│   ├── test_keystone_agent_mechanics.py <- action clamps, observe hash, audit chain
│   ├── test_keystone_asset_io_mechanics.py <- loaders, fingerprints, kinds, reload report
│   ├── test_keystone_mesh_builder_mechanics.py <- quad/box, merge, matrix normals, skin concat
│   ├── test_keystone_serialization_mechanics.py <- binary/JSON atomic, backup, BOM, temp cleanup
│   ├── test_keystone_primitives_mechanics.py <- cube/plane/cone/cylinder/sphere geometry
│   ├── test_keystone_instancing_mechanics.py <- grouping, culling, ordering, savings
│   ├── test_keystone_playtest_mechanics.py <- canon, policies, transcripts, reports, fairness
│   ├── test_keystone_scene_graph_mechanics.py <- queries, IDs, parenting, traversal, visibility
│   ├── test_keystone_history_mechanics.py <- undo/redo, copy isolation, capacity
│   ├── test_keystone_scene_snapshot_mechanics.py <- nodes, camera/environment, assets, restore
│   ├── test_keystone_scene_diff_mechanics.py <- added/removed/changed nodes, sections, validation
│   ├── test_keystone_batch_mechanics.py <- static/skinned planning, merges, exclusions
│   ├── test_keystone_png_texture_mechanics.py <- PNG flip/corruption, texture sha, checker
│   ├── test_keystone_obj_loader_mechanics.py <- normals/UVs, negative indices, quads, errors
│   ├── test_keystone_gltf_import_mechanics.py <- glTF prefab/registry saves, textures, errors
│   ├── test_keystone_gltf_loader_mechanics.py <- GLB/source, buffers, accessors, validation
│   ├── test_keystone_api_contract_mechanics.py <- exports, schema versions, describe parity, determinism
│   ├── test_enemy_animation.py <- .kanim idle clips, crossfade, uniform scale, sim parity
│   ├── test_live_bindings.py <- bind_input keys through InputMap into the sim
│   ├── test_levels.py      <- pickup beacon visibility/label + trigger parity
│   ├── test_ui.py          <- single HP/ammo source, crosshair contrast, HUD purity
│   ├── test_graphics.py    <- floor grid, shared trim batch, draw budget
│   ├── test_audio.py       <- boss/engagement voices, captions, clip hook
│   ├── test_profile.py     <- schema/backup/quarantine, run record, debrief
│   ├── test_combat_feel.py <- non-lethal hit flinch, expiry, scene squash
│   ├── test_enemy_cover.py <- cover collision, slide-around, spawn guard
│   ├── test_levels_platform.py <- jumpable low platform + landing proof
│   ├── test_kill_feed.py   <- typed kill event, feed draw/expiry
│   ├── test_critical_killfeed.py <- CRIT prefix/color in the persistent feed
│   ├── test_overdrive_glow.py <- per-weapon overdrive viewmodel materials
│   ├── test_clutch_cue.py <- clutch wave-clear voice/caption priority
│   ├── test_muzzle.py      <- off-axis flash offset and small node scale
│   ├── test_denial.py      <- denied overdrive voice/caption + state parity
│   ├── test_wins.py        <- schema-2 migration, persisted wins, win banner
│   ├── test_dry_fire.py    <- rate-limited dry fire, NO AMMO voice/caption
│   ├── test_enemy_los.py   <- brute melee LOS; open-field attack parity
│   ├── test_spawn_lane.py  <- clear spawn->pickup cover lane
│   ├── test_boss_hp.py     <- numeric WARDEN HP readout
│   ├── test_viewmodel.py   <- camera-rig gun, weapon tint, death hide
│   ├── test_viewmodel_grip.py <- camera-space grip anchor, weapon tint, death hide
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
│   ├── test_platform_rim.py <- jump-platform four-edge lit frame, shared trim
│   ├── test_platform_base.py <- platform base frame and step readability
│   ├── test_streak_bonus.py <- 10%/kill cap 50%, shown as STREAK +P%
│   ├── test_death_fx.py    <- death timer, shrinking white silhouette
│   ├── test_boss_death_fx.py <- boss ember flash, scale cap
│   ├── test_brute_slam.py  <- brute_slam event, clip, caption
│   ├── test_brute_windup.py <- brute windup tell, delayed slam, swell/caption
│   ├── test_enemy_spacing.py <- melee crowds keep their combined DATA radii
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
│   ├── test_pad_pulse.py   <- keystone lifecycle pulse on the launch pad
│   ├── test_lowammo_count.py <- LOW AMMO <mag> near the crosshair
│   ├── test_no_reserve.py  <- NO RESERVE second line only when reserve is empty
│   ├── test_pickup_pop.py  <- surge collection orb burst and clear
│   ├── test_critical_cue.py <- critical kill voice, caption, standard-kill parity
│   ├── test_profile_disabled.py <- disabled schema warns on the debrief, file preserved
│   ├── test_reload_dip.py  <- viewmodel dip/return during reload, DATA-driven
│   ├── test_summon_overlap.py <- escorts stay clear of the warden and each other
│   ├── test_campaign_seal.py <- cleared campaign stops wave-4 spawns
│   ├── test_campaign_complete.py <- persistent post-banner completion line
│   ├── test_cache_visual.py <- dropped ammo caches render from a shared pool
│   ├── test_cache_asset.py <- .obj crate registration, fallback, reload report
│   ├── test_warden_armor.py <- deterministic armor texture and live material
│   ├── test_cache_drop_cue.py <- cache drop voice/caption, standard-kill parity
│   ├── test_profile_recovery.py <- corrupt-profile flags and debrief reset/recovered
│   ├── test_profile_backup_restart.py <- missing-main backup restore on restart
│   ├── test_wall_texture.py <- deterministic wall panel texture, no new draws
│   ├── test_surge_forfeit_cue.py <- surge-forfeit voice + caption, switch parity
│   ├── test_save_error.py <- failed profile write warns, unwritable parent no crash
│   ├── test_save_retry.py <- later successful save clears the stale warning
│   ├── test_lowhp_pulse.py <- low-health edge alpha pulse and healthy guard
│   ├── test_warden_cover.py <- warden slam blocked by cover, open-field hit
│   ├── test_west_gap.py <- player-width west platform strip and walk-through
│   ├── test_boss_dead_ui.py <- warden bar hidden on death, shown live
│   ├── test_tracer_muzzle.py <- player tracer starts at the viewmodel muzzle
│   ├── test_overdrive_kill_cue.py <- overdrive kill voice/caption, normal parity
│   ├── test_viewmodel_recoil.py <- kick-driven gun back/up offset and settle
│   ├── test_viewmodel_bob.py <- speed-driven sway, rest and DATA checks
│   ├── test_brute_gap.py <- brute closes its 2.5-3.0 m dead zone
│   ├── test_summon_cover.py <- warden escorts never spawn inside covers
│   └── test_audit.py       <- wave-1/2 audit regression pins
├── scripts/
│   ├── record_bot.py  <- emit CommandLog for --replay
│   ├── soak.py        <- full-length sustain soak + timing/budget report
│   ├── play_run.py    <- played-run routes (idle/kite/strafe/ambush/boss/slam/.../campaign)
│   ├── audio_probe.py <- render cue voices to WAV + waveform/spectrogram evidence
│   ├── capture.py     <- seeded screenshot routes (spawn/combat/pickup/boss/slam/.../death)
│   ├── route_evidence.py <- Keystone capture route: hashed PNG/report summary + diff
│   └── keystone_manifest_asset_repro.py <- minimal upstream repro: manifest-asset validation duplicate
├── evidence/          <- cycle-NNN.json per cycle plus before/after capture pairs
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
├── shot_fix_burst.json     <- burst capture report
├── shot_fix_combat.json    <- combat capture report
├── shot_fix_death.json     <- death capture report
├── shot_fix_pickup.json    <- pickup capture report
├── shot_fix_spawn.json     <- spawn capture report
├── shot_min1.json          <- minute-1 capture report
├── shot_soak.json          <- soak capture report
├── shot_stage4_min1.json   <- stage-4 capture report
├── shot_stage4_min30proxy.json <- stage-4 proxy capture report
└── .aikit/
    ├── decisions.md     <- append-only ADRs
    ├── cycles.md        <- append-only improvement-cycle record
    ├── guidelines.md    <- agent working agreement
    ├── project.json     <- project metadata
    ├── media.json       <- brand/media manifest
    ├── task_ledger.json <- disruption-recovery ledger
    ├── task_ledger_archive.jsonl <- archived ledger checkpoints
    └── codebase_map.md  <- generated AST map (update_knowledge_base.py)
```

## Controls (live Engine bindings)

Live play uses the Engine default map plus `ShooterGame.bind_input`:
W/S/A/D move, E or Space jump, mouse look, left-click or F fire, 1/2/3
weapon slots, R reload, J voluntary overdrive, Shift sprint, P pause,
H hide UI, F1 cursor, Esc quit. `--describe` reports the merged bindings
and any declared button the engine cannot bind. The rear-left corner has
a 0.7 m platform; E/Space can land on it (other covers are too tall).

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
