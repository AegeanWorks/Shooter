"""Boltshooter: Keystone plug-in shooter. Engine owns loop/render/input.

Game owns state/rules/scene. Five ops + optional draw_ui. All tuning in
shooter/data/*.json, never hardcoded one-offs.
"""

from __future__ import annotations

import json
import math
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

from keystone._version import __version__ as KEYSTONE_VERSION
from keystone.animation import apply_pose
from keystone.animation_blend import BlendSample, BlendSpace1D
from keystone.animation_state import AnimationStateMachine
from keystone.assets import AssetRegistry
from keystone.audio import Mixer, noise, sine, square
from keystone.audio_spatial import SoundSource, distance_gain, spatial_report
from keystone.camera import PerspectiveCamera
from keystone.camera_rig import CameraRig
from keystone.character import CharacterBody, CharacterController
from keystone.content import material_digest, mesh_digest
from keystone.errors import KeystoneError
from keystone.camera_shake import CameraShake, shake_report
from keystone.camera_shaker import CameraShaker, camera_shaker_report
from keystone.camera_path import (
    CameraKey,
    CameraPath,
    CameraPathPlayer,
    camera_path_player_report,
)
from keystone.camera_path_library import CameraPathLibrary
from keystone.geometry import Material, MeshData
from keystone.lifecycle import ComponentRuntime
from keystone.material_graph import MaterialGraph
from keystone.material_library import MaterialLibrary
from keystone.math3d import Quat, Vec3
from keystone.nav_agent import NavAgent, nav_agent_report
from keystone.nav_authoring import grid_from_boxes
from keystone.navigation import PathFollower, grid_path_points, navigation_report
from keystone.pathfinding import NavGrid, find_path, path_report, smooth_path
from keystone.persistence import VersionedStore
from keystone.serialization import write_json_atomic
from keystone.prefab_library import PrefabLibrary
from keystone.physics import Ray
from keystone.picking import hit_report, raycast_scene
from keystone.primitives import cone, cube, plane, sphere
from keystone.rng import RandomStream
from keystone.root_motion import extract_root_motion, in_place_pose, root_motion_report
from keystone.root_motion_body import RootMotionBody
from keystone.root_motion_presenter import RootMotionPresenter, root_motion_presenter_report
from keystone.scene import BloomSettings, ColorSettings, DirectionalLight, Node, PointLight, PostSettings, Scene, ShadowSettings, Transform
from keystone.schema_diff import current_versions
from keystone.state_machine_library import StateMachineLibrary
from keystone.steering import Agent, arrive, seek, separation, steer, steering_report
from keystone.texture import TextureData
from keystone.tilemap import TileMap, tilemap_report
from keystone.ui.font import text_width

from .anim import CLIP_NAMES, TYPES, EnemyAnimations
from .asset_pipeline import CACHE_CRATE, register_cache_crate
from .profile import SCHEMA, ProfileStore, _migrate_v0, _migrate_v1, _migrate_v2, default_profile
from .sim import Sim
from .ui import draw_shooter

MAX_ENEMIES = 24
MAX_TRACERS = 16
MAX_SPAWN_MARKS = 4
MAX_CACHES = 4


def _pose_json(pose: dict[str, Transform]) -> dict[str, dict]:
    """One JSON-safe, six-decimal view of a sampled pose for AI reports."""
    result: dict[str, dict] = {}
    for key, transform in pose.items():
        result[key] = {
            "position": [round(transform.position.x, 6), round(transform.position.y, 6),
                         round(transform.position.z, 6)],
            "rotation": [round(transform.rotation.w, 6), round(transform.rotation.x, 6),
                         round(transform.rotation.y, 6), round(transform.rotation.z, 6)],
            "scale": [round(transform.scale.x, 6), round(transform.scale.y, 6),
                      round(transform.scale.z, 6)],
        }
    return result

# Fixed set of render assets whose content identity is exposed to AI/soak runs.
DIGEST_ASSETS = (
    "mesh.floor", "mesh.wall", "mesh.mite", "mesh.brute", "mesh.warden",
    "material.floor", "material.wall", "material.mite", "material.warden",
    "material.enemy_hit",
)


DEATH_CINEMATIC_DEFAULTS = {
    "body_height": 0.85,
    "start_forward": 4.0,
    "start_fov": 75.0,
    "keys": (
        {"time": 0.7, "angle": 0.0, "radius": 2.0, "height_above_eye": 1.15, "height": None, "fov": 68.0},
        {"time": 2.1, "angle": 0.9, "radius": 3.2, "height_above_eye": None, "height": 2.15, "fov": 58.0},
        {"time": 3.4, "angle": 1.9, "radius": 4.6, "height_above_eye": None, "height": 2.65, "fov": 52.0},
    ),
}


def _number(value: object, label: str, fallback: float, *, minimum: float = 0.0) -> float:
    """Read one finite tuning number at or above ``minimum``, or fall back."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return fallback
    number = float(value)
    if not math.isfinite(number) or number < minimum:
        return fallback
    return number


def _lens(value: object, label: str, fallback: float) -> float:
    """Read one finite field of view strictly between 0 and 180 degrees."""
    number = _number(value, label, fallback)
    return number if 0.0 < number < 180.0 else fallback


def _death_cinematic_tuning(juice: object) -> dict:
    """Read the death-cinematic block from juice.json, falling back per field.

    The path is procedural (anchored to where the run ended and which way the
    player faced), so it is not a static .kpath document; its numbers are still
    DATA. Every value a bad edit could make unusable -- a lens outside 0..180,
    a zero look-ahead, a non-positive orbit radius, or key times that do not
    strictly increase -- falls back to the built-in default, so a malformed
    block can never raise inside CameraKey or CameraPath during the death
    screen.
    """
    block = (juice or {}).get("death_cinematic") if isinstance(juice, dict) else None
    if not isinstance(block, dict):
        block = {}
    defaults = DEATH_CINEMATIC_DEFAULTS
    tuning = {
        "body_height": _number(block.get("body_height"), "body_height", defaults["body_height"]),
        "start_forward": _number(block.get("start_forward"), "start_forward", defaults["start_forward"], minimum=1e-3),
        "start_fov": _lens(block.get("start_fov"), "start_fov", defaults["start_fov"]),
        "keys": [],
    }
    raw_keys = block.get("keys")
    if not isinstance(raw_keys, list) or not raw_keys:
        raw_keys = []
    fallback_keys = defaults["keys"]
    for index, fallback in enumerate(fallback_keys):
        raw = raw_keys[index] if index < len(raw_keys) and isinstance(raw_keys[index], dict) else {}
        above = raw.get("height_above_eye")
        height = raw.get("height")
        key = {
            "time": _number(raw.get("time"), "key time", fallback["time"]),
            "angle": _number(raw.get("angle"), "key angle", fallback["angle"]),
            "radius": _number(raw.get("radius"), "key radius", fallback["radius"], minimum=1e-3),
            "height_above_eye": (
                _number(above, "key height_above_eye", fallback["height_above_eye"])
                if above is not None
                else None
            ),
            "height": (
                _number(height, "key height", fallback["height"])
                if height is not None
                else None
            ),
            "fov": _lens(raw.get("fov"), "key fov", fallback["fov"]),
        }
        if key["height"] is None and key["height_above_eye"] is None:
            key["height_above_eye"] = fallback["height_above_eye"]
            key["height"] = fallback["height"]
        tuning["keys"].append(key)
    # CameraPath requires strictly increasing key times and the builder opens
    # with its own key at 0.0, so the first orbit key must be strictly after
    # that. A bad custom time would raise there, so fall back to every
    # authored default time at once.
    times = [key["time"] for key in tuning["keys"]]
    invalid = times[0] <= 0.0 or any(
        later <= earlier for earlier, later in zip(times, times[1:])
    )
    if invalid:
        for key, fallback in zip(tuning["keys"], fallback_keys):
            key["time"] = fallback["time"]
    return tuning


@dataclass
class PadPulseComponent:
    """Keystone lifecycle component: pulse the launch pad deterministically."""

    base: float = 1.4
    amplitude: float = 0.08
    speed: float = 3.0
    elapsed: float = 0.0
    ticks: int = 0

    def update(self, context) -> None:
        self.elapsed += float(context.dt)
        self.ticks += 1
        pulse = 1.0 + self.amplitude * math.sin(self.elapsed * self.speed)
        node = context.node
        node.transform = Transform(
            position=node.transform.position,
            scale=Vec3(self.base * pulse, 0.02, self.base * pulse),
        )


def _floor_grid_texture(size: int = 128, cell: int = 16) -> TextureData:
    """Deterministic dark floor with brighter 2-px grid lines (no image file)."""
    base = (0.075, 0.090, 0.130)
    alt = (0.095, 0.115, 0.160)
    line = (0.22, 0.30, 0.40)
    pixels = bytearray(size * size * 4)
    for y in range(size):
        for x in range(size):
            if x % cell < 2 or y % cell < 2:
                color = line
            elif (x // cell + y // cell) % 2 == 0:
                color = base
            else:
                color = alt
            offset = (y * size + x) * 4
            pixels[offset : offset + 4] = bytes(
                (round(color[0] * 255), round(color[1] * 255), round(color[2] * 255), 255)
            )
    return TextureData(size, size, bytes(pixels), name="floor-grid")


def _cover_panel_texture(size: int = 64) -> TextureData:
    """Deterministic grayscale panel detail for the arena covers."""
    base, seam, band = 230, 120, 190
    pixels = bytearray(size * size * 4)
    for y in range(size):
        for x in range(size):
            if x < 2 or y < 2 or x >= size - 2 or y >= size - 2:
                value = seam
            elif y % 16 < 2:
                value = band
            else:
                value = base
            offset = (y * size + x) * 4
            pixels[offset : offset + 4] = bytes((value, value, value, 255))
    return TextureData(size, size, bytes(pixels), name="cover-panel")


def _wall_panel_texture(size: int = 64) -> TextureData:
    """Deterministic grayscale panel detail for the boundary walls.

    Narrow vertical seams and a horizontal band every 16 rows read as
    architectural paneling along the 41 m walls; the material's gray-blue
    tint supplies the color. Rivets sit inside each panel face.
    """
    base, seam, band, rivet = 205, 88, 155, 235
    pixels = bytearray(size * size * 4)
    for y in range(size):
        for x in range(size):
            if x < 2 or y < 2 or x >= size - 2 or y >= size - 2:
                value = seam
            elif x % 8 < 1:
                value = seam
            elif y % 16 < 2:
                value = band
            elif 3 <= x % 8 <= 4 and 5 <= y % 16 <= 6:
                value = rivet
            else:
                value = base
            offset = (y * size + x) * 4
            pixels[offset : offset + 4] = bytes((value, value, value, 255))
    return TextureData(size, size, bytes(pixels), name="wall-panel")


def _warden_armor_texture(size: int = 64) -> TextureData:
    """Deterministic grayscale armor plates for the campaign boss body.

    A 16-px plate grid with dark seams, a mid-plate band and bright rivets
    gives the 2.2 m warden cube a surface that reads as armor; the material's
    dark-red tint supplies the color.
    """
    base, seam, band, rivet = 210, 74, 150, 246
    pixels = bytearray(size * size * 4)
    for y in range(size):
        for x in range(size):
            if x < 2 or y < 2 or x >= size - 2 or y >= size - 2:
                value = seam
            elif x % 16 < 2 or y % 16 < 2:
                value = seam
            elif 4 <= x % 16 <= 5 and 4 <= y % 16 <= 5:
                value = rivet
            elif y % 16 in (8, 9):
                value = band
            else:
                value = base
            offset = (y * size + x) * 4
            pixels[offset : offset + 4] = bytes((value, value, value, 255))
    return TextureData(size, size, bytes(pixels), name="warden-armor")


def _platform_frame_mesh(
    width: float, depth: float, thickness: float, height: float,
    bottom_y: float | None = None,
) -> MeshData:
    """Four thin top-edge strips, plus a matching base frame when requested."""
    base = cube(1.0)
    levels = (0.0,) if bottom_y is None else (0.0, bottom_y)
    positions: list[tuple[float, float, float]] = []
    normals: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    indices: list[int] = []
    offset = 0
    for level in levels:
        extra = 0.0 if level == 0.0 else 2.0 * thickness
        w = width + extra
        d = depth + extra
        strips = (
            (0.0, d / 2.0 - thickness / 2.0, w, thickness),
            (0.0, -d / 2.0 + thickness / 2.0, w, thickness),
            (-w / 2.0 + thickness / 2.0, 0.0, thickness, d),
            (w / 2.0 - thickness / 2.0, 0.0, thickness, d),
        )
        for cx, cz, sx, sz in strips:
            for p, n, uv in zip(base.positions, base.normals, base.uvs):
                positions.append(
                    (p[0] * sx + cx, p[1] * height + level, p[2] * sz + cz)
                )
                normals.append(n)
                uvs.append(uv)
            indices.extend(index + offset for index in base.indices)
            offset += len(base.positions)
    return MeshData(tuple(positions), tuple(normals), tuple(uvs), tuple(indices))


class ShooterGame:
    name = "shooter"

    def __init__(self, profile_path: str | Path | None = None) -> None:
        self.sim = Sim(seed=1)
        self._presentation_rng = RandomStream(int(self.sim.seed)).fork("presentation")
        self.scene = Scene()
        self.assets = AssetRegistry()
        self.mixer = Mixer()
        self.dropped_sfx = 0
        self.sound_cue = ""
        self.sound_cue_t = 0.0
        self.sound_cue_color = (1.0, 0.62, 0.20, 1.0)
        self._forfeit_cue_pending = False
        self._clutch_cue_pending = False
        self._critical_kill_pending = False
        self._pickup_fx_t = 0.0
        self.kill_feed: list[dict] = []
        self.score_pop: dict | None = None
        self._clip_hook = None
        self._clips: dict = {}
        self.profile_store = (
            ProfileStore(profile_path) if profile_path is not None else ProfileStore.default()
        )
        self.profile_disabled = False
        self.profile_save_errors = 0
        self.profile_save_failed = False
        try:
            self.profile = self.profile_store.load()
        except ValueError:
            self.profile = default_profile()
            self.profile_disabled = True
        self.profile_recovered = bool(getattr(self.profile_store, "recovered", False))
        self.profile_recovered_from_backup = bool(
            getattr(self.profile_store, "recovered_from_backup", False)
        )
        self.run_new_best = False
        self.last_run = None
        self.campaign_cleared = False
        self.campaign_clear_t = 0.0
        self._run_recorded = False
        self._run_start_best = int(self.profile.get("best_score", 0))
        self._enemy_nodes: list[Node] = []
        self._tracer_nodes: list[Node] = []
        self._spawn_nodes: list[Node] = []
        self._cache_nodes: list[Node] = []
        self._slam_ring: list[Node] = []
        self._wall_pilasters: list[Node] = []
        self._platform_rim: list[Node] = []
        self._approach_pad: Node | None = None
        self.spawn_marks: list[dict] = []
        self._flash: Node | None = None
        self._view_body: Node | None = None
        self._view_barrel: Node | None = None
        self._view_grip: Node | None = None
        self._pickup: Node | None = None
        self._pickup_beam: Node | None = None
        self._pickup_orb: Node | None = None
        self._boss_core: Node | None = None
        self._boss_anim = None
        self._boss_pose: dict = {}
        self._enemy_anim: EnemyAnimations | None = None
        self._pad_pulse: PadPulseComponent | None = None
        self._lifecycle: ComponentRuntime | None = None
        self.asset_reload_report: dict | None = None
        self._asset_reload_t = 0.0
        self._death_camera: CameraPathPlayer | None = None
        self.death_camera_report: dict | None = None
        self._clear_camera: CameraPathPlayer | None = None
        self.campaign_camera_report: dict | None = None
        self._shake = CameraShake(
            seed=0, amplitude=0.05, rotation_amplitude=0.012, frequency=18.0, decay=2.4
        )
        self._base_camera = PerspectiveCamera()
        self._shaker = CameraShaker(self._base_camera, self._shake)
        self.camera_shake_report: dict | None = None
        self.camera_shaker_report: dict | None = None
        self._built = False

    def _clear_shake_reports(self) -> None:
        """One reset for trauma and both camera-shake reports.

        build_scene and both cinematic starts must agree on this: a hit on the
        killing blow must not leave a stale shake report behind a camera path.
        """
        self._shake.reset()
        self.camera_shake_report = None
        self.camera_shaker_report = None

    def _reset_presentation_reports(self) -> None:
        """Clear every presentation report when a new scene is built.

        Camera paths and their reports, shake state and the spatial audio probe
        must all start empty on a rebuild; shake has its own shared reset so
        cinematics can reuse it.
        """
        self._death_camera = None
        self.death_camera_report = None
        self._clear_camera = None
        self.campaign_camera_report = None
        self._clear_shake_reports()
        self.spatial_audio_report = None

    # ---- five-operation contract --------------------------------------
    def build_scene(self) -> Scene:
        self.sim.reset()
        # Presentation variety gets its own forked stream: draws here can never
        # advance the sim's combat or reward RNG, so the replay hash is stable.
        self._presentation_rng = RandomStream(int(self.sim.seed)).fork("presentation")
        self.scene = Scene()
        self._reset_presentation_reports()
        # Deliberate renderer adoption (grade.json as DATA, never inherited
        # by accident). Engine defaults are all-on; setting each flag here
        # proves the game wants them on with before/after evidence.
        try:
            import json as _json
            from pathlib import Path as _Path

            _grade = _json.loads((_Path(__file__).parent / "data" / "grade.json").read_text(encoding="utf-8"))
            _ren = dict(_grade.get("renderer", {}))
        except (OSError, ValueError, TypeError, AttributeError):
            _ren = {}
        self.scene.shadow = ShadowSettings(enabled=bool(_ren.get("shadows", True)))
        self.scene.color = ColorSettings(enabled=bool(_ren.get("srgb", True)))
        self.scene.post = PostSettings(enabled=bool(_ren.get("post", True)))
        self.scene.bloom = BloomSettings(enabled=bool(_ren.get("bloom", True)))
        self.assets = AssetRegistry()
        self.mixer = Mixer()
        self.dropped_sfx = 0
        self.sound_cue = ""
        self.sound_cue_t = 0.0
        self._forfeit_cue_pending = False
        self._clutch_cue_pending = False
        self._critical_kill_pending = False
        self._pickup_fx_t = 0.0
        self.run_new_best = False
        self.last_run = None
        self.campaign_cleared = False
        self.campaign_clear_t = 0.0
        self.kill_feed = []
        self.spawn_marks = []
        self._run_recorded = False
        self._run_start_best = int(self.profile.get("best_score", 0))
        self.particles = self.sim.particles

        self.assets.register("mesh.floor", plane(40.0))
        self.assets.register("mesh.wall", cube(1.0))
        self.assets.register("mesh.mite", sphere(0.5, segments=16, rings=10))
        self.assets.register("mesh.brute", cube(1.4))
        self.assets.register("mesh.wisp", cone(0.4, 0.9, segments=12))
        self.assets.register("mesh.warden", cube(2.2))
        self.assets.register("mesh.tracer", cube(1.0))
        self.assets.register("mesh.flash", cube(1.0))
        self.assets.register("mesh.pickup", cube(0.6))
        self.assets.register("mesh.boss_core", sphere(0.35, segments=12, rings=8))
        self.assets.register("mesh.beacon_orb", sphere(0.28, segments=10, rings=6))
        grid = _floor_grid_texture()
        self.assets.register("texture.floor", grid)
        self.assets.register("material.floor", Material(color=Vec3(1, 1, 1), specular=0.08, shininess=8.0, texture=grid, checker_scale=0.5))
        wall_panel = _wall_panel_texture()
        self.assets.register("texture.wall", wall_panel)
        self.assets.register("material.wall", Material(color=Vec3(0.40, 0.43, 0.50), specular=0.25, shininess=24.0, texture=wall_panel, checker_scale=0.15))
        cover_panel = _cover_panel_texture()
        self.assets.register("texture.cover", cover_panel)
        self.assets.register("material.cover", Material(color=Vec3(0.64, 0.50, 0.32), specular=0.15, shininess=18.0, texture=cover_panel, checker_scale=1.0))
        self.assets.register("material.platform", Material(color=Vec3(0.38, 0.50, 0.58), specular=0.2, shininess=24.0))
        self.assets.register("material.trim", Material(color=Vec3(0.18, 0.62, 0.72), specular=0.5, shininess=48.0, emissive=Vec3(0.05, 0.34, 0.42)))
        self.assets.register("material.mite", Material(color=Vec3(0.95, 0.45, 0.15), specular=0.4, shininess=48.0, emissive=Vec3(0.55, 0.18, 0.02)))
        self.assets.register("material.brute", Material(color=Vec3(0.60, 0.40, 0.90), specular=0.4, shininess=48.0, metallic=0.2, roughness=0.5))
        self.assets.register("material.wisp", Material(color=Vec3(0.30, 0.85, 1.00), specular=0.6, shininess=64.0, emissive=Vec3(0.10, 0.45, 0.55)))
        warden_armor = _warden_armor_texture()
        self.assets.register("texture.warden", warden_armor)
        self.assets.register("material.warden", Material(color=Vec3(0.62, 0.09, 0.10), specular=0.35, shininess=32.0, emissive=Vec3(0.38, 0.02, 0.02), metallic=0.15, roughness=0.65, texture=warden_armor, checker_scale=0.3))
        self.assets.register("material.enemy_hit", Material(color=Vec3(1.0, 0.96, 0.86), specular=0.8, shininess=64.0, emissive=Vec3(1.0, 0.62, 0.28)))
        self.assets.register("material.boss_death", Material(color=Vec3(1.0, 0.42, 0.12), specular=0.8, shininess=64.0, emissive=Vec3(1.0, 0.30, 0.04)))
        for wid, color, glow in (
            ("pulse", (0.36, 0.44, 0.56), (0.04, 0.08, 0.14)),
            ("scatter", (0.54, 0.36, 0.22), (0.12, 0.05, 0.01)),
            ("lance", (0.22, 0.44, 0.54), (0.02, 0.10, 0.14)),
            ("surge", (0.24, 0.52, 0.36), (0.02, 0.12, 0.05)),
        ):
            self.assets.register(
                f"material.gun_{wid}",
                Material(color=Vec3(*color), specular=0.55, shininess=48.0, emissive=Vec3(*glow)),
            )
            boost_color = tuple(min(1.0, c * 1.25 + 0.06) for c in color)
            boost_glow = tuple(min(1.0, g * 1.6 + 0.08) for g in glow)
            self.assets.register(
                f"material.gun_{wid}_od",
                Material(
                    color=Vec3(*boost_color), specular=0.65, shininess=64.0,
                    emissive=Vec3(*boost_glow),
                ),
            )
        self.assets.register("material.tracer", Material(color=Vec3(1.0, 0.85, 0.30), emissive=Vec3(0.9, 0.65, 0.15)))
        self.assets.register("material.flash", Material(color=Vec3(1.0, 1.0, 1.0), emissive=Vec3(1.0, 0.9, 0.6)))
        # Per-weapon fire tints: the tracer and muzzle flash say which gun
        # fired without reading the status line.
        for wid, color, glow in (
            ("pulse", (1.0, 0.85, 0.30), (0.90, 0.65, 0.15)),
            ("scatter", (1.0, 0.50, 0.15), (0.90, 0.25, 0.04)),
            ("lance", (0.35, 0.85, 1.00), (0.05, 0.45, 0.80)),
            ("surge", (0.35, 1.00, 0.55), (0.05, 0.55, 0.18)),
            ("wisp", (0.70, 0.55, 1.00), (0.40, 0.20, 0.70)),
        ):
            self.assets.register(
                f"material.tracer_{wid}",
                Material(color=Vec3(*color), emissive=Vec3(*glow)),
            )
        for wid, color, glow in (
            ("pulse", (1.00, 0.95, 0.75), (1.00, 0.90, 0.60)),
            ("scatter", (1.00, 0.65, 0.25), (1.00, 0.35, 0.05)),
            ("lance", (0.55, 0.90, 1.00), (0.20, 0.60, 0.90)),
            ("surge", (0.50, 1.00, 0.65), (0.10, 0.70, 0.30)),
        ):
            self.assets.register(
                f"material.flash_{wid}",
                Material(color=Vec3(*color), emissive=Vec3(*glow)),
            )
        self.assets.register("material.pickup", Material(color=Vec3(0.25, 1.0, 0.45), emissive=Vec3(0.10, 0.55, 0.20)))
        # Keystone material library: the dropped ammo-cache material is a
        # committed .kmaterial document; a missing file keeps the same
        # hardcoded fallback so presentation never blocks play.
        try:
            cache_material = MaterialLibrary(
                Path(__file__).parent / "data"
            ).load("cache_material")
        except (KeyError, OSError, ValueError):
            cache_material = Material(color=Vec3(1.0, 0.68, 0.22), specular=0.5, shininess=48.0, emissive=Vec3(0.82, 0.38, 0.04))
        self.assets.register("material.cache", cache_material)
        # Keystone material graph: the boss core is a declarative checker
        # material document, evaluated through keystone.material_graph.
        core_graph = MaterialGraph.from_dict(
            json.loads(
                (Path(__file__).parent / "data" / "core_material.json").read_text(
                    encoding="utf-8"
                )
            )
        )
        self.assets.register("material.boss_core", core_graph.evaluate())

        self.scene.background = Vec3(0.035, 0.045, 0.07)
        self.scene.sky = Vec3(0.01, 0.015, 0.04)
        self.scene.ambient = Vec3(0.30, 0.32, 0.38)
        self.scene.fog_density = 0.006
        self.scene.camera.position = Vec3(0.0, 1.62, 8.0)
        self.scene.camera.fov_y = 75.0
        self.scene.camera.yaw = 0.0
        self.scene.camera.pitch = 0.0
        self.scene.camera.look_at(Vec3(0.0, 1.4, 0.0))
        self.scene.light = DirectionalLight(direction=Vec3(-0.45, -1.0, -0.35), color=Vec3(1.0, 0.93, 0.82), intensity=1.25)
        self.scene.point_light = PointLight(position=Vec3(0.0, 2.5, 8.0), color=Vec3(1.0, 0.8, 0.5), intensity=0.45, radius=14.0)

        floor = self.assets.require("mesh.floor").payload
        floor_mat = self.assets.require("material.floor").payload
        self.scene.add(Node("floor", id="floor", mesh=floor, material=floor_mat))
        wall_mesh = self.assets.require("mesh.wall").payload
        wall_mat = self.assets.require("material.wall").payload

        def wall(node_id: str, x: float, y: float, z: float, sx: float, sy: float, sz: float, mat=None) -> None:
            self.scene.add(Node(node_id, id=node_id, transform=Transform(position=Vec3(x, y, z), scale=Vec3(sx, sy, sz)), mesh=wall_mesh, material=mat if mat is not None else wall_mat))

        size = 20.0
        wall("wall-n", 0.0, 1.5, -20.0, 41.0, 3.0, 1.0)
        wall("wall-s", 0.0, 1.5, 20.0, 41.0, 3.0, 1.0)
        wall("wall-w", -20.0, 1.5, 0.0, 1.0, 3.0, 41.0)
        wall("wall-e", 20.0, 1.5, 0.0, 1.0, 3.0, 41.0)
        cover_mat = self.assets.require("material.cover").payload
        platform_mat = self.assets.require("material.platform").payload
        for i, c in enumerate(self.sim.levels["arena"]["covers"]):
            mat = platform_mat if float(c["h"]) < 1.0 else cover_mat
            wall(f"cover-{i}", float(c["x"]), float(c["h"]) / 2.0, float(c["z"]), float(c["w"]), float(c["h"]), float(c["d"]), mat=mat)

        # Arena trim: one shared mesh/material so the 10 lit edges stay in a
        # single instanced batch. Purely visual (no colliders, no sim state).
        trim_mat = self.assets.require("material.trim").payload
        for name, x, y, z, sx, sy, sz in (
            ("trim-wall-n", 0.0, 2.94, -19.52, 40.0, 0.08, 0.08),
            ("trim-wall-s", 0.0, 2.94, 19.52, 40.0, 0.08, 0.08),
            ("trim-wall-w", -19.52, 2.94, 0.0, 0.08, 0.08, 40.0),
            ("trim-wall-e", 19.52, 2.94, 0.0, 0.08, 0.08, 40.0),
        ):
            wall(name, x, y, z, sx, sy, sz, mat=trim_mat)
        for i, c in enumerate(self.sim.levels["arena"]["covers"]):
            if float(c["h"]) < 1.0:
                continue  # the low platform has a walkable top, not a lit cap
            wall(
                f"trim-cover-{i}", float(c["x"]), float(c["h"]) + 0.04, float(c["z"]),
                float(c["w"]) + 0.08, 0.08, float(c["d"]) + 0.08, mat=trim_mat,
            )

        # Jump-platform rim: one shared frame mesh with four thin strips on
        # the top edges. Decoration only, no colliders, no sim; one node and
        # one shadow draw keep the level affordance budget-safe.
        self._platform_rim = []
        platform = next(
            (c for c in self.sim.levels["arena"]["covers"] if float(c["h"]) < 1.0),
            None,
        )
        if platform is not None:
            px, pz = float(platform["x"]), float(platform["z"])
            pw, pd, ph = (float(platform["w"]), float(platform["d"]),
                          float(platform["h"]))
            trim_mat = self.assets.require("material.trim").payload
            frame = _platform_frame_mesh(pw, pd, 0.10, 0.08, bottom_y=-ph)
            self.assets.register("mesh.platform_frame", frame)
            node = Node(
                "platform-rim", id="platform-rim",
                transform=Transform(position=Vec3(px, ph + 0.04, pz)),
                mesh=frame, material=trim_mat,
            )
            self.scene.add(node)
            self._platform_rim.append(node)
            pad_cfg = dict(self.sim.juice.get("pad_pulse", {}))
            pad_base = float(pad_cfg.get("base", 1.4))
            pad = Node(
                "platform-pad", id="platform-pad",
                transform=Transform(
                    position=Vec3(px, 0.02, pz - pd / 2.0 - 0.8),
                    scale=Vec3(pad_base, 0.02, pad_base),
                ),
                mesh=wall_mesh, material=trim_mat,
            )
            self.scene.add(pad)
            self._approach_pad = pad
            self._pad_pulse = PadPulseComponent(
                base=pad_base,
                amplitude=float(pad_cfg.get("amplitude", 0.08)),
                speed=float(pad_cfg.get("speed", 3.0)),
            )
            pad.add_component(self._pad_pulse)

        # Wall pilasters: shared vertical strips that give the four flat
        # boundary walls depth. Decoration only (no colliders, no sim).
        self.assets.register(
            "material.pilaster",
            Material(color=Vec3(0.50, 0.58, 0.66), specular=0.25,
                     shininess=32.0, emissive=Vec3(0.02, 0.06, 0.08)),
        )
        pilaster_mat = self.assets.require("material.pilaster").payload
        positions = [
            (x, z)
            for x in (-10.0, 10.0)
            for z in (-19.4, 19.4)
        ]
        positions += [
            (x, z)
            for z in (-10.0, 10.0)
            for x in (-19.4, 19.4)
        ]
        self._wall_pilasters = []
        for index, (x, z) in enumerate(positions):
            node = Node(
                f"pilaster-{index:02d}", id=f"pilaster-{index:02d}",
                transform=Transform(position=Vec3(x, 1.5, z),
                                    scale=Vec3(0.18, 3.0, 0.18)),
                mesh=wall_mesh, material=pilaster_mat,
            )
            self.scene.add(node)
            self._wall_pilasters.append(node)

        # enemy pool (shared payloads -> auto-instancing)
        self._enemy_nodes = []
        for i in range(MAX_ENEMIES):
            node = Node(f"enemy-{i:02d}", id=f"enemy-{i:02d}", visible=False,
                        mesh=self.assets.require("mesh.mite").payload,
                        material=self.assets.require("material.mite").payload)
            self.scene.add(node)
            self._enemy_nodes.append(node)
        # tracer pool
        self._tracer_nodes = []
        tracer_mesh = self.assets.require("mesh.tracer").payload
        tracer_mat = self.assets.require("material.tracer").payload
        for i in range(MAX_TRACERS):
            node = Node(f"tracer-{i:02d}", id=f"tracer-{i:02d}", visible=False,
                        mesh=tracer_mesh, material=tracer_mat)
            self.scene.add(node)
            self._tracer_nodes.append(node)
        flash_mesh = self.assets.require("mesh.flash").payload
        flash_mat = self.assets.require("material.flash").payload
        self._flash = Node("muzzle", id="muzzle", visible=False, mesh=flash_mesh, material=flash_mat)
        self.scene.add(self._flash)
        # First-person viewmodel: Keystone's CameraRig owns the camera-space
        # attachment, so the parts are overlay-layer children that level
        # geometry cannot cut through; _sync_scene sets their local offsets.
        gun_mesh = self.assets.require("mesh.wall").payload
        gun_mat = self.assets.require("material.gun_pulse").payload
        self._view_rig = CameraRig(self.scene.camera)
        self._view_rig.attach_to(self.scene)
        self._view_body = self._view_rig.attach(
            "viewmodel-body", mesh=gun_mesh, material=gun_mat
        )
        self._view_barrel = self._view_rig.attach(
            "viewmodel-barrel", mesh=gun_mesh, material=gun_mat
        )
        # Grip under the receiver: the silhouette reads as a held weapon
        # instead of a bar floating above the floor. Presentation only.
        self._view_grip = self._view_rig.attach(
            "viewmodel-grip", mesh=gun_mesh, material=gun_mat
        )
        pickup_mesh = self.assets.require("mesh.pickup").payload
        pickup_mat = self.assets.require("material.pickup").payload
        self._pickup_spot = self.sim.levels.get("pickup", {"x": 0.0, "y": 0.5, "z": -6.0})
        # Keystone prefab: the reward marker is a committed multi-root
        # .kprefab (cube + beam + orb) instantiated at build time; its
        # mesh/material ids resolve through the game asset registry.
        try:
            pickup_prefab = PrefabLibrary(
                Path(__file__).parent / "data", registry=self.assets
            ).load("pickup_beacon")
        except (KeyError, OSError, ValueError):
            pickup_prefab = None
        if pickup_prefab is not None:
            (
                self._pickup,
                self._pickup_beam,
                self._pickup_orb,
            ) = pickup_prefab.instantiate(self.scene, instance="pickup")
        else:
            self._pickup = Node("surge-pickup", id="surge-pickup", visible=False,
                                transform=Transform(position=Vec3(
                                    float(self._pickup_spot["x"]), float(self._pickup_spot["y"]), float(self._pickup_spot["z"]))),
                                mesh=pickup_mesh, material=pickup_mat)
            self.scene.add(self._pickup)
            # Pickup beacon: a thin emissive column + bobbing orb above the surge
            # spot so the reward is visible over the centre cover from spawn.
            self._pickup_beam = Node(
                "surge-beam", id="surge-beam", visible=False,
                mesh=self.assets.require("mesh.wall").payload, material=pickup_mat,
            )
            self.scene.add(self._pickup_beam)
            self._pickup_orb = Node(
                "surge-orb", id="surge-orb", visible=False,
                mesh=self.assets.require("mesh.beacon_orb").payload, material=pickup_mat,
            )
            self.scene.add(self._pickup_orb)
        # Ammo-cache pool: a committed .obj crate loaded through the keystone
        # asset pipeline (suffix inference, fingerprint, hot reload). A
        # missing file falls back to the previous cube so play never blocks.
        register_cache_crate(self.assets, Path(__file__).parent / "data", pickup_mesh)
        crate_mesh = self.assets.require(CACHE_CRATE).payload
        self.asset_reload_report = None
        self._asset_reload_t = 0.0
        self._cache_nodes = []
        cache_mat = self.assets.require("material.cache").payload
        for index in range(MAX_CACHES):
            node = Node(
                f"ammo-cache-{index}", id=f"ammo-cache-{index}", visible=False,
                mesh=crate_mesh, material=cache_mat,
            )
            self.scene.add(node)
            self._cache_nodes.append(node)
        self._boss_core = Node(
            "warden-core", id="warden-core", visible=False,
            mesh=self.assets.require("mesh.boss_core").payload,
            material=self.assets.require("material.boss_core").payload,
        )
        self.scene.add(self._boss_core)
        # Spawn markers: short-lived emissive columns at the wave-spawn
        # origin. Presentation only; the sim emits `spawn`, the game owns
        # the timer.
        self.assets.register(
            "material.spawn_mark",
            Material(color=Vec3(1.0, 0.35, 0.18), specular=0.4,
                     shininess=32.0, emissive=Vec3(0.75, 0.12, 0.03)),
        )
        spawn_mat = self.assets.require("material.spawn_mark").payload
        self._spawn_nodes = []
        for i in range(self._spawn_mark_cap()):
            node = Node(f"spawn-mark-{i}", id=f"spawn-mark-{i}", visible=False,
                        mesh=wall_mesh, material=spawn_mat)
            self.scene.add(node)
            self._spawn_nodes.append(node)
        # Warden slam ring: a dashed ground circle at the DATA range,
        # visible only during the windup. Presentation-only.
        self.assets.register(
            "material.slam_ring",
            Material(color=Vec3(1.0, 0.45, 0.15), specular=0.3,
                     shininess=24.0, emissive=Vec3(0.8, 0.2, 0.03)),
        )
        ring_cfg = dict(self.sim.juice.get("slam_ring", {}))
        ring_segments = max(4, int(ring_cfg.get("segments", 24)))
        self._slam_ring = []
        for i in range(ring_segments):
            node = Node(f"slam-ring-{i}", id=f"slam-ring-{i}", visible=False,
                        mesh=wall_mesh,
                        material=self.assets.require("material.slam_ring").payload)
            self.scene.add(node)
            self._slam_ring.append(node)

        # pre-synthesized deterministic SFX (no per-frame synth)
        self._clips = {
            "shoot": square(180.0, 0.08, name="shoot"),
            "scatter": noise(0.12, seed=5, name="scatter"),
            "lance": square(440.0, 0.12, name="lance"),
            "hit": noise(0.05, seed=9, name="hit"),
            "kill": sine(220.0, 0.15, name="kill"),
            "overdrive_hit": square(760.0, 0.07, name="overdrive_hit"),
            "critical": sine(1760.0, 0.08, name="critical"),
            "pickup": sine(880.0, 0.12, name="pickup"),
            "hurt": square(110.0, 0.15, name="hurt"),
            "wave": sine(660.0, 0.20, name="wave"),
            "clutch": square(520.0, 0.12, name="clutch"),
            # Boss / engagement cues: each event gets a distinct voice; the
            # matching caption makes the cue visible as well as audible.
            "boss_windup": square(70.0, 0.35, name="boss_windup"),
            "boss_slam": noise(0.30, seed=17, name="boss_slam"),
            "brute_slam": noise(0.15, seed=33, name="brute_slam"),
            "brute_windup": square(140.0, 0.14, name="brute_windup"),
            "wisp_bolt": sine(1200.0, 0.08, name="wisp_bolt"),
            "boss_summon": square(310.0, 0.12, name="boss_summon"),
            "boss_down": sine(330.0, 0.45, name="boss_down"),
            "spawn": noise(0.08, seed=31, name="spawn"),
            "overdrive": sine(520.0, 0.22, name="overdrive"),
            "overdrive_end": sine(260.0, 0.18, name="overdrive_end"),
            "overdrive_denied": square(90.0, 0.14, name="overdrive_denied"),
            "dry_fire": noise(0.04, seed=23, name="dry_fire"),
            "cache": sine(1040.0, 0.08, name="cache"),
            "cache_drop": sine(1320.0, 0.05, name="cache_drop"),
            "reload": noise(0.06, seed=21, name="reload"),
            "reloaded": sine(980.0, 0.06, name="reloaded"),
            "switch_pulse": square(300.0, 0.05, name="switch_pulse"),
            "switch_scatter": square(220.0, 0.06, name="switch_scatter"),
            "switch_lance": square(420.0, 0.05, name="switch_lance"),
            "surge_forfeit": square(120.0, 0.22, name="surge_forfeit"),
            "near_miss": sine(1320.0, 0.06, name="near_miss"),
            "streak_break": square(140.0, 0.12, name="streak_break"),
            "death": square(60.0, 0.50, name="death"),
        }
        # Keystone runtime feature: a file-backed animation state machine
        # drives the warden core's calm/charge pulse. Presentation only; the
        # sim, damage and deterministic hash never read it.
        try:
            self._boss_anim = StateMachineLibrary(
                Path(__file__).parent / "data"
            ).load("warden_core")
        except (KeyError, OSError, ValueError):
            self._boss_anim = None
        self._boss_pose = {}
        # Keystone animation library: each enemy type's idle motion is a
        # committed .kanim clip; a missing clip set keeps the static look.
        try:
            self._enemy_anim = EnemyAnimations()
        except (KeyError, OSError, ValueError):
            self._enemy_anim = None
        # Keystone runtime feature: deterministic component lifecycle. The
        # pad pulse is one component on the pad node, started once and
        # updated by the fixed-step game loop.
        self._lifecycle = ComponentRuntime(self.scene)
        self._lifecycle.start()
        self._built = True
        self._sync_scene()
        return self.scene

    def set_clip_hook(self, hook) -> None:
        """Attach an optional (clip, gain) observer for evidence tooling."""
        self._clip_hook = hook

    def reload_assets(self):
        """Re-read changed file-backed assets and rebind scene nodes; expose report."""
        report = self.assets.reload(self.scene)
        self.asset_reload_report = report.describe()
        return report

    def _start_death_camera(self) -> None:
        """Build the death cinematic around where the run ended.

        Presentation only: the pose never feeds `sim.eye()`, damage, RNG or the
        snapshot, so the determinism hash is untouched. A one-shot path that
        rises off the shoulder, orbits the body and settles wide gives the
        debrief a readable final frame instead of a frozen first-person view.
        """
        tuning = _death_cinematic_tuning(self.sim.juice)
        eye = self.sim.eye()
        fwd = self.sim.forward()
        body = Vec3(eye.x, tuning["body_height"], eye.z)
        # ground-plane heading so the orbit does not tilt with look pitch
        flat = Vec3(fwd.x, 0.0, fwd.z)
        flat = flat.normalized() if flat.length_squared() > 1e-9 else Vec3(0.0, 0.0, -1.0)

        def orbit(key: dict) -> CameraKey:
            """One key on a circle around the body, measured from the heading."""
            cos_a, sin_a = math.cos(key["angle"]), math.sin(key["angle"])
            offset_x = flat.x * cos_a - flat.z * sin_a
            offset_z = flat.z * cos_a + flat.x * sin_a
            height = (
                eye.y + key["height_above_eye"]
                if key["height_above_eye"] is not None
                else key["height"]
            )
            return CameraKey.look_at(
                key["time"],
                Vec3(
                    body.x - offset_x * key["radius"],
                    height,
                    body.z - offset_z * key["radius"],
                ),
                body,
                fov_y=key["fov"],
            )

        keys = (
            # start exactly where the player was looking, so the cut is invisible
            CameraKey.look_at(
                0.0,
                eye,
                eye + fwd * tuning["start_forward"],
                fov_y=tuning["start_fov"],
            ),
            *(orbit(key) for key in tuning["keys"]),
        )
        path = CameraPath(keys)
        self._death_camera = CameraPathPlayer(path)
        self.death_camera_report = camera_path_player_report(self._death_camera)
        # A cinematic owns the camera, so no shake is applied while it runs;
        # a hit on the killing blow must not leave a stale report behind it.
        self._clear_shake_reports()

    def _start_campaign_clear_camera(self) -> None:
        """Play the authored victory fly-around from a shipped .kpath document.

        The cinematic is DATA (``shooter/data/campaign_clear.kpath``), so it can
        be re-authored without touching code. Presentation only: a missing or
        corrupt document falls back to the first-person view and records why in
        ``campaign_camera_report`` instead of breaking the victory screen.
        """
        try:
            library = CameraPathLibrary(Path(__file__).parent / "data")
            path = library.load("campaign_clear")
        except (KeyError, OSError, TypeError, ValueError) as exc:
            self._clear_camera = None
            self.campaign_camera_report = {"error": str(exc)}
            return
        self._clear_camera = CameraPathPlayer(path)
        self.campaign_camera_report = camera_path_player_report(self._clear_camera)
        # Same rule as the death cinematic: the path owns the camera.
        self._clear_shake_reports()

    def _play_clip(self, clip, gain: float) -> None:
        """Play one SFX clip, counting (never hiding) a mixer refusal.

        Audio must never crash gameplay, but a refusal used to vanish into
        `except ValueError: pass`. Counting drops keeps the failure visible
        to soak reports without changing the deterministic sim.

        ``TypeError`` is caught as well as ``ValueError``: both are what
        ``Mixer.play`` raises for a refusal (a non-clip, a mismatched sample
        rate, a bad bus, gain or pitch). Catching only ``ValueError`` meant a
        ``TypeError`` from the audio layer would have crashed the frame, which
        is exactly what this docstring promises cannot happen.
        """
        if self._clip_hook is not None:
            self._clip_hook(clip, gain)
        try:
            self.mixer.play(clip, bus="sfx", gain=gain)
        except (TypeError, ValueError):
            self.dropped_sfx += 1

    def _presentation_gain(self, gain: float) -> float:
        """Bounded per-event gain variation from the presentation-only stream."""
        return float(gain) * self._presentation_rng.uniform(0.95, 1.05)

    def presentation_rng_report(self) -> dict:
        """JSON-safe state of the presentation stream for reproducible AI runs."""
        return {"schema": 1, "stream": self._presentation_rng.snapshot().to_dict()}

    def _run_ended(self) -> bool:
        """True when the current run is over: the player is down or the campaign sealed."""
        return (not self.sim.alive) or bool(self.campaign_cleared)

    def _restart_ready(self) -> bool:
        """True when Enter should start a new run.

        Both endings protect their last shot: the victory banner owns the screen
        for its four seconds, and the death cinematic for its full run, so a
        player mashing confirm while dying cannot skip the debrief that shows
        the run's score and history. A death with no cinematic (a failed path
        build) is restartable immediately.
        """
        if not self.sim.alive:
            return self._death_camera is None or bool(self._death_camera.done)
        return bool(self.campaign_cleared) and self.campaign_clear_t <= 0.0

    def new_run(self) -> None:
        """Start a fresh run after a death or a sealed campaign.

        The profile persists (wins, history, bests); only the run's sim, scene
        and presentation reset, which is exactly what build_scene does.
        """
        self.build_scene()

    def update(self, dt: float, actions) -> None:
        if not self._built:
            self.build_scene()
        ended_before = self._run_ended()
        pressed = set(getattr(actions, "pressed", frozenset()))
        if ended_before and "confirm" in pressed and self._restart_ready():
            self.new_run()
            return
        events = self.sim.step(float(dt), actions)
        self._forfeit_cue_pending = False
        self._clutch_cue_pending = False
        self._critical_kill_pending = False
        for e in events:
            self._play_event(e)
        if "died" in events:
            self._finish_run()
            self._start_death_camera()
        elif "wave" in events:
            self._record_progress()
        if self._campaign_win_reached():
            self.campaign_cleared = True
            self.campaign_clear_t = 4.0
            self.sim.seal_campaign()
            self._record_campaign_clear()
            self._start_campaign_clear_camera()
        self.campaign_clear_t = max(0.0, self.campaign_clear_t - float(dt))
        self._pickup_fx_t = max(0.0, self._pickup_fx_t - float(dt))
        for entry in self.kill_feed:
            entry["t"] = float(entry.get("t", 0.0)) - float(dt)
        self.kill_feed = [entry for entry in self.kill_feed if entry["t"] > 0.0][:4]
        if self.score_pop is not None:
            self.score_pop["t"] = float(self.score_pop.get("t", 0.0)) - float(dt)
            if self.score_pop["t"] <= 0.0:
                self.score_pop = None
        for mark in self.spawn_marks:
            mark["t"] = float(mark.get("t", 0.0)) - float(dt)
        self.spawn_marks = [mark for mark in self.spawn_marks if mark["t"] > 0.0]
        self.sound_cue_t = max(0.0, self.sound_cue_t - float(dt))
        # cap voices: deterministic mixdown cost bounded via the public API
        # only (post-update invariant stays voice_count <= 8)
        if self.mixer.voice_count() > 8:
            self.mixer.clear()
        if self._lifecycle is not None:
            self._lifecycle.update(float(dt))
        # File-backed assets poll once per second (not per frame): a changed
        # .obj hot-reloads and the report stays visible to diagnostics.
        self._asset_reload_t += float(dt)
        if self._asset_reload_t >= 1.0:
            self._asset_reload_t = 0.0
            self.reload_assets()
        self._sync_scene(float(dt))

    def _cue(self, text: str, danger: bool = False) -> None:
        self.sound_cue = text
        self.sound_cue_t = 0.9
        self.sound_cue_color = (1.0, 0.30, 0.30, 1.0) if danger else (1.0, 0.62, 0.20, 1.0)

    def _save_profile(self) -> None:
        if self.profile_disabled:
            return
        try:
            saved = self.profile_store.save(self.profile)
        except OSError:
            # A path that cannot even create its parent must lose the run,
            # not crash the finish; the debrief carries the warning.
            saved = False
        if not saved:
            self.profile_save_errors += 1
            self.profile_save_failed = True
        else:
            self.profile_save_failed = False

    def _record_campaign_clear(self) -> None:
        if self.profile_disabled:
            return
        self.profile["wins"] = int(self.profile.get("wins", 0)) + 1
        self._record_run("win")

    def _campaign_win_reached(self) -> bool:
        """True when this frame seals the campaign.

        One predicate, used by the update loop and by _record_progress, so the
        victory frame cannot write the profile twice: the wave's bests and the
        win run land in a single atomic save.
        """
        return (
            not self.campaign_cleared
            and bool(self.sim.alive)
            and int(self.sim.wave) >= int(self.sim.levels.get("win_wave", 4))
        )

    def _record_progress(self) -> None:
        """Persist a new best at wave clear, even if the player later quits."""
        if self.profile_disabled:
            return
        sim = self.sim
        changed = False
        for key, value in (
            ("best_score", int(sim.score)),
            ("best_kills", int(sim.kills)),
            ("best_wave", int(sim.wave)),
            ("best_streak", int(sim.best_streak)),
        ):
            if value > int(self.profile.get(key, 0)):
                self.profile[key] = value
                changed = True
        # A winning wave saves nothing here: _record_campaign_clear writes the
        # same bests together with the win run in one atomic save, so the
        # victory frame performs a single fsync-backed write instead of two.
        # The window where the bests exist only in memory is the rest of this
        # frame, and a crash there also loses the run record they belong to.
        if changed and not self._campaign_win_reached():
            self._save_profile()

    def _record_run(self, outcome: str) -> None:
        """Append one finished run (death or campaign clear) to the profile."""
        if self._run_recorded:
            return
        self._run_recorded = True
        sim = self.sim
        run = {
            "score": int(sim.score),
            "kills": int(sim.kills),
            "wave": int(sim.wave),
            "best_streak": int(sim.best_streak),
            "time_s": int(round(float(sim.time))),
            "outcome": outcome,
        }
        self.last_run = run
        self.run_new_best = int(run["score"]) > self._run_start_best
        if self.profile_disabled:
            return
        self.profile["runs"] = int(self.profile.get("runs", 0)) + 1
        self.profile["last_run"] = run
        history = list(self.profile.get("history", []))
        history.insert(0, dict(run))
        self.profile["history"] = history[:5]
        for profile_key, run_key in (
            ("best_score", "score"), ("best_kills", "kills"),
            ("best_wave", "wave"), ("best_streak", "best_streak"),
        ):
            if int(run[run_key]) > int(self.profile.get(profile_key, 0)):
                self.profile[profile_key] = int(run[run_key])
        self._save_profile()

    def _finish_run(self) -> None:
        self._record_run("lose")

    def _spawn_mark_cap(self) -> int:
        """The DATA-owned marker cap; MAX_SPAWN_MARKS only when the key is absent.

        One read for the node pool and both event paths, so raising the value in
        juice.json really raises the visible cap instead of only growing a list
        that has no nodes to draw it.
        """
        cfg = dict(self.sim.juice.get("spawn_mark", {}))
        return max(1, int(cfg.get("max", MAX_SPAWN_MARKS)))

    def _play_event(self, event: str) -> None:
        """Map one sim event to its audio voice and on-screen caption."""
        if event.startswith("overdrive_denied:"):
            reason = event.split(":", 1)[1]
            if reason == "insufficient_ammo":
                cost = int(self.sim.overdrive_preview().get("cost", 30))
                self._cue(f"OVERDRIVE: NEED {cost} AMMO", danger=True)
            elif reason == "surge_active":
                self._cue("OVERDRIVE BLOCKED BY SURGE", danger=True)
            elif reason == "already_on":
                self._cue("OVERDRIVE ALREADY ON", danger=True)
            else:
                self._cue("OVERDRIVE UNAVAILABLE", danger=True)
            self._play_clip(self._clips["overdrive_denied"], 0.55)
            return
        if event.startswith("kill:"):
            parts = event.split(":")
            if len(parts) == 3:
                critical = self._critical_kill_pending
                self._critical_kill_pending = False
                prefix = "CRIT " if critical else ""
                self.kill_feed.insert(
                    0,
                    {
                        "text": f"{prefix}{parts[1].upper()} +{parts[2]}",
                        "t": 2.5,
                        "danger": parts[1] == "warden",
                        "critical": critical,
                    },
                )
                self.kill_feed = self.kill_feed[:4]
                self.score_pop = {
                    "text": f"+{parts[2]}",
                    "t": float(self.sim.juice.get("score_pop_s", 0.6)),
                }
            return
        if event == "surge_forfeit":
            self._play_clip(self._clips["surge_forfeit"], 0.6)
            self._cue("SURGE FORFEIT", danger=True)
            self._forfeit_cue_pending = True
            return
        if event.startswith("switch:"):
            wid = event.split(":", 1)[1]
            clip = self._clips.get(f"switch_{wid}", self._clips.get("switch_pulse"))
            if clip is not None:
                self._play_clip(clip, 0.35)
            if self._forfeit_cue_pending:
                self._forfeit_cue_pending = False
            else:
                self._cue(wid.upper())
            return
        if event == "spawn":
            cfg = dict(self.sim.juice.get("spawn_mark", {}))
            pos = getattr(self.sim, "spawn_pos", None)
            if pos is not None:
                self.spawn_marks.insert(0, {
                    "x": float(pos.x), "z": float(pos.z),
                    "t": float(cfg.get("life_s", 0.7)),
                })
                self.spawn_marks = self.spawn_marks[:self._spawn_mark_cap()]
            # Positional warning voice: the sim already publishes the spawn
            # position, so Keystone's distance model attenuates the clip while
            # the game's one Mixer keeps owning buses, pitch and the voice cap.
            gain = 0.30
            try:
                source = SoundSource(position=pos, clip=self._clips["spawn"], gain=gain)
                listener = self.sim.eye()
                self.spatial_audio_report = spatial_report(listener, [source])
                gain = source.gain * distance_gain(listener, source)
            except (TypeError, ValueError):
                # A bad position must never turn a warning into a crash.
                self.spatial_audio_report = None
            self._play_clip(self._clips["spawn"], gain)
            if self.sound_cue_t <= 0.0:
                self._cue("HOSTILE INBOUND")
            return
        if event == "dry_fire":
            self._play_clip(self._clips["dry_fire"], 0.35)
            self._cue("NO AMMO", danger=True)
            return
        if event == "shoot":
            w = self.sim.weapon
            clip = self._clips.get(
                {"pulse": "shoot", "scatter": "scatter", "lance": "lance", "surge": "shoot"}.get(w, "shoot"),
                self._clips["shoot"],
            )
            self._play_clip(clip, self._presentation_gain(0.7))
        elif event == "hit":
            self._play_clip(self._clips["hit"], 0.5)
        elif event == "kill":
            self._play_clip(self._clips["kill"], 0.8)
        elif event == "critical":
            self._play_clip(self._clips["critical"], 0.55)
            self._cue("CRITICAL")
            self._critical_kill_pending = True
        elif event == "overdrive_hit":
            self._play_clip(self._clips["overdrive_hit"], 0.55)
            self._cue(
                "OVERDRIVE CRIT" if self._critical_kill_pending else "OVERDRIVE KILL"
            )
        elif event == "boss_down":
            self._play_clip(self._clips["boss_down"], 1.0)
            self._cue("WARDEN DOWN")
        elif event == "boss_windup":
            self._play_clip(self._clips["boss_windup"], 0.8)
            self._cue("WARDEN WINDUP", danger=True)
        elif event == "boss_slam":
            self._play_clip(self._clips["boss_slam"], 0.9)
            self._cue("WARDEN SLAM", danger=True)
        elif event == "brute_slam":
            self._play_clip(self._clips["brute_slam"], 0.7)
            self._cue("BRUTE SLAM", danger=True)
        elif event == "brute_windup":
            self._play_clip(self._clips["brute_windup"], 0.55)
            self._cue("BRUTE WINDUP", danger=True)
        elif event == "wisp_bolt":
            self._play_clip(self._clips["wisp_bolt"], 0.65)
            self._cue("WISP BOLT", danger=True)
        elif event == "boss_summon":
            self._play_clip(self._clips["boss_summon"], 0.7)
            self._cue("WARDEN SUMMON", danger=True)
            cfg = dict(self.sim.juice.get("spawn_mark", {}))
            for pos in list(getattr(self.sim, "summon_positions", []))[:self._spawn_mark_cap()]:
                self.spawn_marks.insert(0, {
                    "x": float(pos.x), "z": float(pos.z),
                    "t": float(cfg.get("life_s", 0.7)),
                })
            self.spawn_marks = self.spawn_marks[:self._spawn_mark_cap()]
        elif event == "clutch":
            self._play_clip(self._clips["clutch"], 0.6)
            self._cue("CLUTCH CLEAR")
            self._clutch_cue_pending = True
        elif event in ("pickup", "wave"):
            self._play_clip(self._clips["pickup" if event == "pickup" else "wave"], 0.7)
            if event == "wave" and self._clutch_cue_pending:
                self._clutch_cue_pending = False
            else:
                self._cue("SURGE ACQUIRED" if event == "pickup" else "WAVE CLEAR")
            if event == "pickup":
                self._pickup_fx_t = float(self.sim.juice.get("pickup_fx_s", 0.30))
        elif event == "hurt":
            self._play_clip(self._clips["hurt"], 0.8)
            self._shake.add(0.6)
        elif event == "reload":
            self._play_clip(self._clips["reload"], 0.45)
            self._cue("RELOADING")
        elif event == "reloaded":
            self._play_clip(self._clips["reloaded"], 0.45)
            self._cue("RELOADED")
        elif event == "cache":
            self._play_clip(self._clips["cache"], 0.6)
            self._cue("CACHE AMMO")
        elif event == "cache_drop":
            self._play_clip(self._clips["cache_drop"], 0.5)
            self._cue("AMMO CACHE DROP")
        elif event == "near_miss_bonus":
            self._play_clip(self._clips["near_miss"], 0.5)
            self._cue("NEAR MISS +6")
        elif event == "overdrive":
            self._play_clip(self._clips["overdrive"], 0.8)
            self._cue("OVERDRIVE")
        elif event == "overdrive_end":
            self._play_clip(self._clips["overdrive_end"], 0.6)
            self._cue("OVERDRIVE END")
        elif event == "overdrive_break":
            self._play_clip(self._clips["overdrive_end"], 0.7)
            self._cue("OVERDRIVE BROKEN", danger=True)
        elif event == "streak_break":
            self._play_clip(self._clips["streak_break"], 0.4)
            self._cue("STREAK LOST", danger=True)
        elif event == "died":
            self._play_clip(self._clips["death"], 0.9)

    def _sync_scene(self, dt: float = 0.0) -> None:
        sim = self.sim
        warden = next(
            (e for e in sim.enemies if e.alive and e.etype == "warden"), None
        )
        # Keystone state machine: advance one frame and keep the sampled pose
        # for the warden core. The parameter is the existing sim windup flag.
        if self._boss_anim is not None:
            charging = warden is not None and warden.windup_t > 0.0
            self._boss_anim.set_parameter("windup", 1.0 if charging else 0.0)
            self._boss_pose = self._boss_anim.advance(float(dt))
        cam = self.scene.camera
        eye = sim.eye()
        if self._death_camera is not None:
            # Death cinematic: presentation only, so the aim ray keeps starting
            # from the sim eye and the snapshot hash stays untouched. The path
            # is one-shot and clamps on its final wide pose.
            pose = self._death_camera.advance(float(dt))
            cam.position = pose.position
            cam.yaw = pose.yaw
            cam.pitch = pose.pitch
            cam.fov_y = pose.fov_y
        elif self._clear_camera is not None:
            # Victory fly-around from the authored .kpath document; same
            # presentation-only rule as the death cinematic.
            pose = self._clear_camera.advance(float(dt))
            cam.position = pose.position
            cam.yaw = pose.yaw
            cam.pitch = pose.pitch
            cam.fov_y = pose.fov_y
        else:
            # Trauma-based shake: Keystone owns both the deterministic noise
            # and the composition onto an immutable base pose. The sim eye is
            # still the aim origin, so none of this reaches the snapshot.
            self._shake.update(float(dt))
            base = self._base_camera
            base.position = eye
            base.yaw = sim.yaw
            base.pitch = max(-1.55, min(1.55, sim.pitch + sim.kick))
            base.fov_y = cam.fov_y
            posed = self._shaker.pose()
            cam.position = posed.position
            cam.yaw = posed.yaw
            cam.pitch = posed.pitch
            self.camera_shake_report = (
                shake_report(self._shake) if self._shake.trauma > 0.0 else None
            )
            self.camera_shaker_report = (
                camera_shaker_report(self._shaker) if self._shake.trauma > 0.0 else None
            )
        if self.scene.point_light is not None:
            base = Vec3(eye.x, eye.y + 0.4, eye.z)
            boost = 1.2 if sim.flash_t > 0.0 else 0.4
            self.scene.point_light = replace(self.scene.point_light, position=base, intensity=boost)
        mesh_by_type = {
            "mite": (self.assets.require("mesh.mite").payload, self.assets.require("material.mite").payload, Vec3(1, 1, 1)),
            "brute": (self.assets.require("mesh.brute").payload, self.assets.require("material.brute").payload, Vec3(1, 1, 1)),
            "wisp": (self.assets.require("mesh.wisp").payload, self.assets.require("material.wisp").payload, Vec3(1, 1, 1)),
            "warden": (self.assets.require("mesh.warden").payload, self.assets.require("material.warden").payload, Vec3(1, 1, 1)),
        }
        hit_mat = self.assets.require("material.enemy_hit").payload
        boss_death_mat = self.assets.require("material.boss_death").payload
        hit_span = max(1e-6, float(self.sim.juice.get("hit_flinch_s", 0.25)))
        death_span = max(1e-6, float(self.sim.juice.get("death_fx_s", 0.15)))
        death_caps = dict(self.sim.juice.get("death_fx_scale", {}))
        ordered = sorted(sim.enemies, key=lambda e: (0 if e.alive else 1, e.etype))
        for i, node in enumerate(self._enemy_nodes):
            if i < len(ordered) and (ordered[i].alive or ordered[i].death_t > 0.0):
                e = ordered[i]
                mesh, mat, _ = mesh_by_type[e.etype]
                node.mesh = mesh
                node.visible = True
                if not e.alive:
                    # Brief shrink so the kill has a body exit. The boss uses
                    # a warm flash and a per-type cap: a full-size white 2.2 m
                    # cube filled the campaign-clear frame.
                    k = max(0.0, min(1.0, e.death_t / death_span))
                    s = k * float(death_caps.get(e.etype, 1.0))
                    node.material = boss_death_mat if e.etype == "warden" else hit_mat
                    node.transform = Transform(
                        position=e.pos, scale=Vec3(s, s, s)
                    )
                    continue
                node.material = hit_mat if e.hit_t > hit_span * 0.4 else mat
                # death squash: scale down when hp low (presentation from sim hp)
                frac = max(0.4, min(1.0, e.hp / max(1, self.sim.enemy_defs[e.etype]["hp"])))
                s = 0.6 + 0.4 * frac
                if e.etype == "warden":
                    # Boss telegraph: brief swelling during the slam windup so
                    # the 30-damage hit is readable before it lands.
                    s = 1.0 + (0.10 * math.sin(self.sim.time * 26.0) if e.windup_t > 0.0 else 0.0)
                elif e.etype == "brute" and e.windup_t > 0.0:
                    s *= 1.0 + 0.10 * math.sin(self.sim.time * 26.0)
                # Hit reaction: a short squash + push away from the player.
                # Presentation only; the sim hitbox and damage never move.
                flinch = 0.0
                push = 0.0
                if e.hit_t > 0.0:
                    k = min(1.0, e.hit_t / hit_span)
                    flinch = float(self.sim.juice.get("hit_flinch_scale", 0.28)) * k
                    push = float(self.sim.juice.get("hit_flinch_push", 0.12)) * k
                dx = e.pos.x - sim.player_pos.x
                dz = e.pos.z - sim.player_pos.z
                length = math.hypot(dx, dz)
                ux, uz = (dx / length, dz / length) if length > 1e-6 else (0.0, 0.0)
                # Keystone .kanim idle: rotation and a uniform breathe scale
                # layer on top of the sim position and combat squash. Only
                # presentation reads it, so the sim hash is untouched.
                idle = (
                    self._enemy_anim.offset(i, e.etype, dt)
                    if self._enemy_anim is not None
                    else None
                )
                rotation = idle.rotation if idle is not None else Quat()
                breathe = idle.scale.x if idle is not None else 1.0
                node.transform = Transform(
                    position=Vec3(e.pos.x + ux * push, e.pos.y, e.pos.z + uz * push),
                    rotation=rotation,
                    scale=Vec3(
                        s * (1.0 + flinch) * breathe,
                        s * (1.0 - flinch) * breathe,
                        s * (1.0 + flinch) * breathe,
                    ),
                )
            else:
                node.visible = False
        for i, node in enumerate(self._tracer_nodes):
            if i < len(sim.tracers):
                t = sim.tracers[i]
                x0, y0, z0, x1, y1, z1 = t["x0"], t["y0"], t["z0"], t["x1"], t["y1"], t["z1"]
                dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
                length = max(0.3, math.sqrt(dx * dx + dy * dy + dz * dz))
                # Cube length axis is +/-z: yaw maps +z onto the beam
                # (atan2(dx,-dz) is the camera-forward convention and mirrors
                # the beam front-to-back through the viewer). Pitch included
                # so the beam visually connects muzzle to hit.
                yaw = math.atan2(dx, dz) if (abs(dx) + abs(dz)) > 1e-6 else 0.0
                pitch = -math.atan2(dy, math.hypot(dx, dz))
                node.visible = True
                try:
                    node.material = self.assets.require(
                        f"material.tracer_{t.get('weapon', 'pulse')}"
                    ).payload
                except KeyError:
                    node.material = self.assets.require("material.tracer").payload
                node.transform = Transform(
                    position=Vec3((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0),
                    rotation=Quat.from_axis_angle(Vec3(0.0, 1.0, 0.0), yaw)
                    * Quat.from_axis_angle(Vec3(1.0, 0.0, 0.0), pitch),
                    scale=Vec3(0.02, 0.02, length),
                )
            else:
                node.visible = False
        if self._flash is not None:
            if sim.flash_t > 0.0:
                self._flash.visible = True
                try:
                    self._flash.material = self.assets.require(
                        f"material.flash_{sim.weapon}"
                    ).payload
                except KeyError:
                    self._flash.material = self.assets.require("material.flash").payload
                scale = float(self.sim.juice.get("flash_scale", 0.055))
                self._flash.transform = Transform(position=sim.flash_pos, scale=Vec3(scale, scale, scale))
            else:
                self._flash.visible = False
        if self._boss_core is not None:
            boss = warden
            self._boss_core.visible = boss is not None
            if boss is not None:
                # Glowing core on the face turned toward the player. Purely
                # visual: it follows the boss and its scale comes from the
                # keystone state-machine pose (calm breathe / charge pulse).
                dx = sim.player_pos.x - boss.pos.x
                dz = sim.player_pos.z - boss.pos.z
                length = math.hypot(dx, dz)
                ux, uz = (dx / length, dz / length) if length > 1e-6 else (0.0, -1.0)
                pos = Vec3(boss.pos.x + ux * 1.25, boss.pos.y + 0.35, boss.pos.z + uz * 1.25)
                if self._boss_anim is not None and "warden-core" in self._boss_pose:
                    self._boss_core.transform = Transform(position=pos)
                    apply_pose(self.scene, self._boss_pose, mask={"rotation", "scale"})
                else:
                    pulse = 1.0 + (0.18 if boss.windup_t > 0.0 else 0.0)
                    self._boss_core.transform = Transform(
                        position=pos,
                        rotation=Quat(),
                        scale=Vec3(pulse, pulse, pulse),
                    )
        if self._pickup is not None:
            self._pickup.visible = bool(sim.pickup_active)
            if sim.pickup_active:
                spin = (sim.time * 1.5) % math.tau
                self._pickup.transform = Transform(
                    position=Vec3(float(self._pickup_spot["x"]),
                                  float(self._pickup_spot["y"]) + 0.15 * math.sin(sim.time * 3.0),
                                  float(self._pickup_spot["z"])),
                    rotation=Quat.from_axis_angle(Vec3(0.0, 1.0, 0.0), spin),
                )
        if self._view_body is not None and self._view_barrel is not None:
            # The rig root carries the camera pose; each part declares only a
            # camera-space offset, so there is no world basis math here.
            cfg = self.sim.juice.get("viewmodel", {})
            self._view_rig.sync()
            recoil = min(1.0, abs(sim.kick) / math.radians(4.0))
            recoil_back = float(cfg.get("recoil_back", 0.0)) * recoil
            recoil_up = float(cfg.get("recoil_up", 0.0)) * recoil
            reload_t = float(getattr(sim, "reload_t", 0.0))
            reload_curve = 0.0
            if reload_t > 0.0:
                wdef = sim.weapons.get(sim.weapon, {})
                duration = float(wdef.get("reload_s", 0.0))
                if duration > 0.0:
                    phase = max(0.0, min(1.0, 1.0 - reload_t / duration))
                    reload_curve = math.sin(math.pi * phase)
            reload_drop = float(cfg.get("reload_drop", 0.0)) * reload_curve
            reload_back = float(cfg.get("reload_back", 0.0)) * reload_curve
            speed = math.hypot(float(sim.hvel.x), float(sim.hvel.z))
            bob = min(1.0, speed / max(1e-6, float(cfg.get("bob_speed", 6.4))))
            if not sim.body.on_ground:
                bob = 0.0
            phase = sim.time * float(cfg.get("bob_hz", 8.0))
            bob_right = float(cfg.get("bob_right", 0.0)) * bob * math.sin(phase)
            bob_up = float(cfg.get("bob_up", 0.0)) * bob * math.cos(phase)
            def gun_offset(forward_d: float, right_d: float, down_d: float) -> Vec3:
                """Camera-space offset: +X right, +Y up, -Z forward."""
                return Vec3(right_d, -down_d, -forward_d)

            self._view_body.visible = bool(sim.alive)
            self._view_barrel.visible = bool(sim.alive)
            self._view_grip.visible = bool(sim.alive)
            if sim.alive:
                self._view_body.transform = Transform(
                    position=gun_offset(
                        float(cfg.get("forward", 0.40)) - recoil_back - reload_back,
                        float(cfg.get("right", 0.18)) + bob_right,
                        float(cfg.get("down", 0.16)) - recoil_up + reload_drop - bob_up,
                    ),
                    scale=Vec3(
                        float(cfg.get("body_width", 0.07)),
                        float(cfg.get("body_height", 0.07)),
                        float(cfg.get("body_length", 0.30)),
                    ),
                )
                self._view_barrel.transform = Transform(
                    position=gun_offset(
                        float(cfg.get("barrel_forward", 0.62)) - recoil_back - reload_back,
                        float(cfg.get("right", 0.18)) + bob_right,
                        float(cfg.get("barrel_down", 0.20)) - recoil_up + reload_drop - bob_up,
                    ),
                    scale=Vec3(
                        float(cfg.get("barrel_size", 0.035)),
                        float(cfg.get("barrel_size", 0.035)),
                        float(cfg.get("barrel_length", 0.32)),
                    ),
                )
                self._view_grip.transform = Transform(
                    position=gun_offset(
                        float(cfg.get("grip_forward", 0.52)) - recoil_back - reload_back,
                        float(cfg.get("right", 0.18)) + bob_right,
                        float(cfg.get("grip_down", 0.30)) - recoil_up + reload_drop - bob_up,
                    ),
                    scale=Vec3(
                        float(cfg.get("grip_width", 0.05)),
                        float(cfg.get("grip_height", 0.11)),
                        float(cfg.get("grip_length", 0.06)),
                    ),
                )
                gun_id = f"material.gun_{sim.weapon}"
                if float(getattr(sim, "overdrive_t", 0.0)) > 0.0:
                    gun_id += "_od"
                try:
                    gun_mat = self.assets.require(gun_id).payload
                except KeyError:
                    gun_mat = self.assets.require("material.gun_pulse").payload
                self._view_body.material = gun_mat
                self._view_barrel.material = gun_mat
                self._view_grip.material = gun_mat
        ring_cfg = dict(self.sim.juice.get("slam_ring", {}))
        ring_w = float(ring_cfg.get("width", 0.20))
        ring_h = float(ring_cfg.get("height", 0.025))
        ring_boss = next(
            (e for e in sim.enemies if e.alive and e.etype == "warden"),
            None,
        )
        show_ring = ring_boss is not None and ring_boss.windup_t > 0.0
        ring_radius = float(self.sim.enemy_defs["warden"]["range"])
        for i, node in enumerate(self._slam_ring):
            node.visible = bool(show_ring)
            if show_ring:
                angle = math.tau * i / max(1, len(self._slam_ring))
                node.transform = Transform(
                    position=Vec3(
                        ring_boss.pos.x + math.cos(angle) * ring_radius,
                        ring_h / 2.0,
                        ring_boss.pos.z + math.sin(angle) * ring_radius,
                    ),
                    scale=Vec3(ring_w, ring_h, ring_w),
                )
        mark_cfg = dict(self.sim.juice.get("spawn_mark", {}))
        mark_w = float(mark_cfg.get("width", 0.18))
        mark_h = float(mark_cfg.get("height", 2.4))
        for i, node in enumerate(self._spawn_nodes):
            if i < len(self.spawn_marks):
                m = self.spawn_marks[i]
                node.visible = True
                node.transform = Transform(
                    position=Vec3(float(m["x"]), mark_h / 2.0, float(m["z"])),
                    scale=Vec3(mark_w, mark_h, mark_w),
                )
            else:
                node.visible = False
        if self._pickup_beam is not None and self._pickup_orb is not None:
            active = bool(sim.pickup_active)
            fx_t = float(getattr(self, "_pickup_fx_t", 0.0))
            self._pickup_beam.visible = active
            self._pickup_orb.visible = bool(active or fx_t > 0.0)
            if active:
                bx = float(self._pickup_spot["x"])
                by = float(self._pickup_spot["y"])
                bz = float(self._pickup_spot["z"])
                self._pickup_beam.transform = Transform(
                    position=Vec3(bx, by + 1.35, bz),
                    rotation=Quat.from_axis_angle(Vec3(0.0, 1.0, 0.0), (sim.time * 0.9) % math.tau),
                    scale=Vec3(0.22, 3.0, 0.22),
                )
                self._pickup_orb.transform = Transform(
                    position=Vec3(bx, by + 2.95 + 0.14 * math.sin(sim.time * 3.0), bz),
                    scale=Vec3(1.0, 1.0, 1.0),
                )
            elif fx_t > 0.0:
                # Collection pop: reuse the orb, expanding and rising as the
                # beam disappears. Presentation only; no new node or draw.
                duration = max(1e-6, float(sim.juice.get("pickup_fx_s", 0.30)))
                k = max(0.0, min(1.0, 1.0 - fx_t / duration))
                size = 1.0 + float(sim.juice.get("pickup_fx_scale", 1.5)) * k
                rise = float(sim.juice.get("pickup_fx_rise", 0.9)) * k
                self._pickup_orb.transform = Transform(
                    position=Vec3(
                        float(self._pickup_spot["x"]),
                        float(self._pickup_spot["y"]) + 2.95 + rise,
                        float(self._pickup_spot["z"]),
                    ),
                    scale=Vec3(size, size, size),
                )
        for i, node in enumerate(self._cache_nodes):
            if i < len(sim.caches):
                cache = sim.caches[i]
                node.visible = True
                spin = (sim.time * 2.0 + i * 1.7) % math.tau
                node.transform = Transform(
                    position=Vec3(
                        float(cache["x"]),
                        max(0.2, float(cache.get("y", 0.5)) - 0.2)
                        + 0.05 * math.sin(sim.time * 3.0 + i),
                        float(cache["z"]),
                    ),
                    rotation=Quat.from_axis_angle(Vec3(0.0, 1.0, 0.0), spin),
                )
            else:
                node.visible = False

    def crosshair_pick(self) -> dict:
        """JSON-safe answer to 'what world node is under the crosshair'.

        A query rather than per-frame state: raycast_scene computes world bounds
        for every visible mesh, so casting on every simulation frame made the
        whole test gate roughly four times slower (cycle 180 measurement).
        Keystone skips overlay and hidden nodes, so the camera-rig viewmodel
        and the muzzle flash can never be reported as hits.
        """
        hit = raycast_scene(
            self.scene,
            Ray(self.sim.eye(), self.sim.forward(), 100.0),
            ignore=("muzzle",),
        )
        return hit_report(hit)

    def asset_digest_report(self) -> dict:
        """Stable content digests for the registered render assets.

        Keystone's digests describe payload content rather than object identity,
        so an AI/soak consumer can compare two separately built registries.
        """
        digests: dict[str, str] = {}
        for name in DIGEST_ASSETS:
            payload = self.assets.require(name).payload
            if isinstance(payload, MeshData):
                digests[name] = mesh_digest(payload)
            elif isinstance(payload, Material):
                digests[name] = material_digest(payload)
        return {"schema": 1, "count": len(digests), "digests": digests}

    def testbed_report(self) -> dict:
        """One JSON-safe view of every no-argument on-demand report.

        AI/soak consumers can inspect the whole plug-in with one call; each
        family keeps its own report untouched, so existing consumers are
        unaffected. No sim or scene state is written.
        """
        return {
            "schema": 1,
            "engine": self.engine_version_report(),
            "contracts": self.keystone_contract_report(),
            "nav": {
                "plan": self.nav_plan_report(),
                "authoring": self.nav_authoring_report(),
                "tiles": self.arena_tile_report(),
            },
            "animation": {
                "blend": self.enemy_blend_report(),
                "states": self.enemy_state_preview(),
                "root_motion": self.idle_root_motion_report(),
                "presenter": self.idle_presenter_preview(),
            },
            "steering": self.enemy_steering_report(),
            "picking": self.crosshair_pick(),
            "assets": self.asset_digest_report(),
            "bot": self.bot_nav_preview(),
            "storage": self.profile_store_probe(),
            "presentation": self.presentation_rng_report(),
            # Self-describing coverage: every no-arg report/probe is named here,
            # so a reflective test can catch a future report added but not wired.
            "sources": sorted((
                "arena_tile_report", "asset_digest_report", "enemy_steering_report",
                "engine_version_report", "keystone_contract_report", "nav_plan_report",
                "presentation_rng_report", "profile_store_probe",
            )),
        }

    def engine_version_report(self) -> dict:
        """The authoritative Keystone version, as a JSON-safe AI/soak query."""
        return {"schema": 1, "engine_version": KEYSTONE_VERSION}

    def profile_store_probe(self) -> dict:
        """Exercise the shipped profile contract in a throwaway directory.

        Fresh load, save/reload, v0 migration and corrupt recovery all run
        against a temporary VersionedStore, so the real player profile is never
        read or written and the sim stays untouched.
        """
        migrations = {0: _migrate_v0, 1: _migrate_v1, 2: _migrate_v2}
        with tempfile.TemporaryDirectory(prefix="shooter-profile-probe-") as directory:
            path = Path(directory) / "profile.json"

            def store() -> VersionedStore:
                return VersionedStore(
                    path, schema=SCHEMA, default=default_profile,
                    migrations=migrations,
                )

            fresh = store().load()
            saved = store().save(fresh.state)
            reloaded = store().load()
            write_json_atomic(path, {"schema": 0, "data": {"runs": 4, "wins": 1}})
            old = store().load()
            path.write_text("{broken", encoding="utf-8")
            corrupt = store().load()
        return {
            "schema": 1,
            "store_schema": SCHEMA,
            "fresh": {"source": fresh.source, "schema": fresh.state["schema"]},
            "saved": saved,
            "reloaded": {"source": reloaded.source, "schema": reloaded.state["schema"]},
            "old": {
                "migrated": old.migrated,
                "schema": old.state["schema"],
                "runs": old.state["runs"],
            },
            "corrupt": {
                "source": corrupt.source,
                "quarantined": corrupt.quarantined,
                "schema": corrupt.state["schema"],
            },
        }

    def nav_authoring_report(self, clearance: float = 0.2) -> dict:
        """NavGrid authored from the same collider authority as the route plan."""
        width, _cell, _origin = self._arena_layout()
        boxes = list(self.sim.colliders)
        walls = [box for box in boxes if box.center.y + box.half_extents.y > 0.1]
        grid = self._nav_grid(clearance)
        plan = self.nav_plan_report()["pathfinding"]
        start = (int(plan["start"][0]), int(plan["start"][1]))
        goal = (int(plan["goal"][0]), int(plan["goal"][1]))
        result = find_path(grid, start, goal, diagonal=True)
        return {
            "schema": 1,
            "width": width,
            "height": width,
            "clearance": float(clearance),
            "boxes": len(walls),
            "floor_excluded": len(boxes) - len(walls),
            "blocked": len(grid.blocked),
            "start_open": grid.is_open(start),
            "goal_open": grid.is_open(goal),
            "path": path_report(result),
        }

    def idle_presenter_preview(self, frames: int = 12) -> dict:
        """Step a local root-motion rig and report its container pose.

        A tiny throwaway Scene holds the container and one animated child so
        the presenter can apply the shipped clip's in-place pose. The game's
        own scene, sim and replay hash are never involved.
        """
        scene = Scene()
        container = Node("preview-container", id="preview-container")
        scene.add(container)
        Node("subject", id="subject", parent=container)
        body = CharacterBody(
            position=Vec3(0.0, 0.9, 0.0),
            half_extents=Vec3(0.5, 0.9, 0.5),
            velocity=Vec3(),
            on_ground=True,
        )
        rig = RootMotionBody(
            self._enemy_anim.clips["warden_idle"], "subject",
            CharacterController(gravity=24.0), body,
        )
        presenter = RootMotionPresenter(rig, container)
        before = root_motion_presenter_report(presenter)
        pose: dict = {}
        for _ in range(max(0, int(frames))):
            pose, _motion = presenter.step(scene, 1.0 / 60.0)
        return {
            "schema": 1,
            "container": before["container"],
            "before": before,
            "after": root_motion_presenter_report(presenter),
            "updated": list(presenter.last_updated),
            "pose_nodes": sorted(pose),
        }

    def bot_nav_preview(self, frames: int = 30) -> dict:
        """Plan spawn -> pickup with a local NavAgent and advance it in isolation.

        The grid and goal come from the same authoritative nav data as every
        other route report, but the body, controller and agent are local objects.
        Nothing is added to the scene and the sim's replay hash stays untouched.
        """
        width, cell, origin = self._arena_layout()
        grid = self._nav_grid(0.0)
        spawn = self.sim.levels["player"]["spawn"]
        body = CharacterBody(
            position=Vec3(float(spawn[0]), float(spawn[1]), float(spawn[2])),
            half_extents=Vec3(0.35, 0.9, 0.35),
            velocity=Vec3(),
            on_ground=True,
        )
        agent = NavAgent(
            grid, CharacterController(gravity=24.0), body,
            cell_size=cell, origin=origin, speed=4.0,
        )
        goal = tuple(self.nav_plan_report()["pathfinding"]["goal"])
        planned = agent.set_goal(goal)
        before = nav_agent_report(agent)
        after = before
        for _ in range(max(0, int(frames))):
            after = agent.step(1.0 / 60.0)
        return {
            "schema": 1,
            "planned": planned,
            "goal": [goal[0], goal[1]],
            "blocked_cells": len(grid.blocked),
            "before": before,
            "after": after,
        }

    def data_error_report(self, error: KeystoneError) -> dict:
        """JSON-safe view of a structured data failure, on demand."""
        if not isinstance(error, KeystoneError):
            raise TypeError("data_error_report needs a KeystoneError")
        return {
            "schema": 1,
            "why": error.why,
            "fix": error.fix,
            "message": str(error),
        }

    def keystone_contract_report(self) -> dict:
        """The Keystone contract versions this build is running against.

        An on-demand query for AI/soak consumers: the values come from
        Keystone's schema_diff module, never from a copy that could go stale.
        """
        return {
            "schema": 1,
            "versions": dict(sorted(current_versions().items())),
        }

    def enemy_steering_report(self) -> dict:
        """AI-visible steering vectors for the first alive enemy, on demand.

        Built from the live positions, enemy-definition radii/speeds and the
        juice separation tuning. Pure query: no body is integrated and no sim
        state changes.
        """
        alive = [enemy for enemy in self.sim.enemies if enemy.alive]
        if not alive:
            return {
                "schema": 1, "subject": None, "neighbours": 0,
                "seek": [], "arrive": [], "separation": [0.0, 0.0, 0.0],
            }
        tuning = self.sim.juice.get("enemy_separation", {})
        strength = float(tuning.get("strength", 0.5))
        margin = float(tuning.get("clearance", 0.02))

        def as_agent(enemy) -> Agent:
            definition = self.sim.enemy_defs[enemy.etype]
            return Agent(
                position=enemy.pos, velocity=Vec3(),
                radius=float(definition["radius"]),
                max_speed=float(definition["speed"]),
            )

        subject = as_agent(alive[0])
        neighbours = [as_agent(enemy) for enemy in alive[1:]]
        wish = seek(subject.position, self.sim.player_pos, subject.max_speed)
        slowed = arrive(subject.position, self.sim.player_pos, subject.max_speed, 2.0)
        push = separation(
            subject.position, [(agent.position, agent.radius) for agent in neighbours],
            subject.radius, strength=strength, margin=margin,
        )
        steered = steer(
            subject, wish, neighbours, separation_weight=strength, margin=margin
        )
        return {
            "schema": 1,
            "subject": steering_report(subject, steered),
            "neighbours": len(neighbours),
            "seek": [wish.x, wish.y, wish.z],
            "arrive": [slowed.x, slowed.y, slowed.z],
            "separation": [push.x, push.y, push.z],
        }

    def enemy_state_preview(self, threat: float | None = None, frames: int = 30) -> dict:
        """Parameter-driven enemy animation states, as a JSON preview.

        The document is authored from shipped idle clips and a `threat` scalar;
        each call builds a fresh machine, so nothing leaks into the game's live
        animation controllers or the deterministic sim.
        """
        if threat is None:
            peak = max(float(defn["hp"]) for defn in self.sim.enemy_defs.values())
            threat = max(
                (float(getattr(enemy, "hp", 0)) / peak for enemy in self.sim.enemies
                 if getattr(enemy, "alive", True)),
                default=0.0,
            )
        value = max(0.0, min(1.0, float(threat)))
        clips = self._enemy_anim.clips
        document = {
            "schema": 1,
            "states": [
                {"name": "calm", "clip": clips["mite_idle"].to_dict()},
                {"name": "alert", "clip": clips["brute_idle"].to_dict()},
                {"name": "aggressive", "clip": clips["warden_idle"].to_dict()},
            ],
            "transitions": [
                {"source": "calm", "target": "alert", "parameter": "threat",
                 "operator": "greater", "value": 0.4, "duration": 0.1},
                {"source": "alert", "target": "aggressive", "parameter": "threat",
                 "operator": "greater", "value": 0.7, "duration": 0.1},
                {"source": "aggressive", "target": "calm", "parameter": "threat",
                 "operator": "less", "value": 0.3, "duration": 0.2},
            ],
            "parameters": {"threat": value},
            "current": "calm",
        }
        machine = AnimationStateMachine.from_dict(document)
        sampled: dict = {}
        for _ in range(max(0, int(frames))):
            sampled = machine.advance(1.0 / 60.0)
        pose = _pose_json(sampled)
        return {
            "schema": 1,
            "report": machine.report(),
            "parameter": value,
            "pose": pose,
        }

    def idle_root_motion_report(self, window: float = 0.3) -> dict:
        """Subject root deltas of the shipped idle clips, as a JSON report.

        Pure query: the extracted motion and the baked in-place pose are
        reported for AI/soak consumers but never applied to a scene node.
        """
        clips = self._enemy_anim.clips
        seconds = float(window)
        reported = {
            name: root_motion_report(
                extract_root_motion(clips[name], "subject", 0.0, seconds)
            )
            for name in CLIP_NAMES
        }
        baked = in_place_pose(clips["wisp_idle"].sample(seconds), "subject")["subject"]
        in_place = (
            baked.position.x == 0.0 and baked.position.y == 0.0 and baked.position.z == 0.0
            and baked.rotation.w == 1.0 and baked.scale.x == 1.0
        )
        return {
            "schema": 1,
            "window": seconds,
            "clips": reported,
            "in_place": in_place,
        }

    def enemy_blend_report(self, parameter: float | None = None, time: float = 0.0) -> dict:
        """Shipped enemy idle clips as a 1D blend space keyed by enemy HP.

        An on-demand AI/soak query: the pose is reported as JSON and never
        written back to a scene node, the sim or the snapshot.
        """
        clips = self._enemy_anim.clips
        samples = tuple(
            BlendSample(clip=clips[name], threshold=float(self.sim.enemy_defs[etype]["hp"]))
            for etype, name in TYPES.items()
        )
        blend = BlendSpace1D(samples)
        if parameter is None:
            parameter = max(
                (float(getattr(enemy, "hp", 0)) for enemy in self.sim.enemies
                 if getattr(enemy, "alive", True)),
                default=0.0,
            )
        pose = blend.sample(float(parameter), float(time))
        summary = _pose_json(pose)
        return {
            "schema": 1,
            "blend": blend.report(),
            "round_trip": BlendSpace1D.from_dict(blend.to_dict()) == blend,
            "parameter": float(parameter),
            "pose": summary,
        }

    def arena_tile_report(self) -> dict:
        """The shipped arena as a Keystone TileMap document, on demand.

        A pure authoring/AI query: the tile map's colliders and merged mesh are
        reported but never added to the scene, so rendering and the sim hash
        stay exactly as they were.
        """
        arena = self.sim.levels["arena"]
        width, cell, origin = self._arena_layout()
        solid: set[tuple[int, int]] = set()
        for box in arena["covers"]:
            cx, cz = float(box["x"]), float(box["z"])
            half_w, half_d = float(box["w"]) / 2.0, float(box["d"]) / 2.0
            x0 = max(0, int(math.floor((cx - half_w - origin.x) / cell)))
            x1 = min(width - 1, int(math.ceil((cx + half_w - origin.x) / cell)))
            z0 = max(0, int(math.floor((cz - half_d - origin.z) / cell)))
            z1 = min(width - 1, int(math.ceil((cz + half_d - origin.z) / cell)))
            solid.update((x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1))
        tiles = TileMap(
            width=width, height=width, tile_size=cell, origin=origin,
            solid=frozenset(solid), wall_height=float(arena["wall_height"]),
        )
        mesh = tiles.mesh()
        return {
            "schema": 1,
            "tiles": tilemap_report(tiles),
            "solid_cells": [[x, z] for x, z in sorted(solid)],
            "document": tiles.to_dict(),
            "colliders": len(tiles.colliders()),
            "mesh": {
                "vertices": len(mesh.positions),
                "triangles": len(mesh.indices) // 3,
            },
        }

    def _arena_layout(self) -> tuple[int, float, Vec3]:
        """The one grid layout shared by every arena-shaped report."""
        size = float(self.sim.levels["arena"]["size"])
        cell = 1.0
        return int(size / cell), cell, Vec3(-size / 2.0, 0.0, -size / 2.0)

    def _to_cell(self, x: float, z: float) -> tuple[int, int]:
        """Clamp a world XZ point to the shared arena grid cell."""
        width, cell, origin = self._arena_layout()
        return (
            max(0, min(width - 1, int(math.floor((x - origin.x) / cell)))),
            max(0, min(width - 1, int(math.floor((z - origin.z) / cell)))),
        )

    def _nav_grid(self, clearance: float = 0.0) -> NavGrid:
        """The authoritative arena nav grid, rasterized from collision boxes.

        The arena floor is a full-size AABB and grid_from_boxes ignores vertical
        extents, so floor-level boxes are excluded explicitly; otherwise every
        cell would be blocked. Both nav reports share this one derivation.
        """
        width, cell, origin = self._arena_layout()
        boxes = [
            box for box in self.sim.colliders
            if box.center.y + box.half_extents.y > 0.1
        ]
        return grid_from_boxes(
            width, width, boxes, cell_size=cell,
            origin=origin, clearance=float(clearance),
        )

    def nav_plan_report(self) -> dict:
        """Arena route from spawn to the surge pickup as Keystone nav data.

        An on-demand query for AI/soak consumers: the grid comes from the same
        collider-derived authority as nav_authoring_report, and neither the
        sim's movement nor its replay hash ever reads it.
        """
        levels = self.sim.levels
        width, cell, origin = self._arena_layout()
        grid = self._nav_grid(0.0)
        spawn = levels["player"]["spawn"]
        pickup = levels["pickup"]
        start = self._to_cell(float(spawn[0]), float(spawn[2]))
        goal = self._to_cell(float(pickup["x"]), float(pickup["z"]))
        result = find_path(grid, start, goal, diagonal=True)
        route = path_report(result)
        if result.found:
            points = grid_path_points(
                smooth_path(grid, result.path),
                cell_size=cell, origin=origin, height=0.0,
            )
        else:
            points = ()
        follower = PathFollower(points, speed=3.0)
        return {
            "schema": 1,
            "grid": {
                "width": width, "height": width, "cell_size": cell,
                "blocked_cells": len(grid.blocked),
            },
            "pathfinding": route,
            "waypoints": [[point.x, point.y, point.z] for point in points],
            "navigation": navigation_report(follower, self.sim.eye()),
        }

    def snapshot(self) -> dict:
        snap = self.sim.snapshot()
        snap["dropped_sfx"] = int(self.dropped_sfx)
        return snap

    def bind_input(self, mapping) -> None:
        """Bind every live button the actions() contract advertises.

        Mouse fire already arrives through ActionState.mouse_clicked; F is a
        keyboard alternative. Number keys need keystone's digit key table.
        """
        mapping.bind("fire", "f")
        mapping.bind("reload", "r")
        mapping.bind("slot1", "1")
        mapping.bind("slot2", "2")
        mapping.bind("slot3", "3")
        mapping.bind("overdrive", "j")
        mapping.bind("jump", "space")

    def actions(self) -> dict:
        return {
            "axes": ["forward", "right", "up", "look_yaw", "look_pitch"],
            "buttons": ["fire", "reload", "slot1", "slot2", "slot3", "overdrive", "jump", "sprint", "quit"],
            "notes": "fire=mouse_clicked or pressed.fire; hold fire key for auto; overdrive=voluntary 8s x2 (pulse-reserve cost, breaks on hurt)",
        }

    def status(self) -> str:
        # Short HP/ammo line only: "|" has no bitmap glyph (renders as "?"),
        # and WAVE/SCORE/KILLS already live in draw_shooter top-center.
        s = self.sim
        return f"HP {s.hp} - {s.weapon} {s.ammo.get(s.weapon,0)}/{s.reserve.get(s.weapon,0)}"

    def draw_ui(self, canvas, state) -> None:
        draw_shooter(canvas, state, self.sim)
        if self.sound_cue_t > 0.0 and self.sound_cue and self.sim.alive:
            text = self.sound_cue
            width = int(state.width)
            height = int(state.height)
            box_width = len(text) * 12 + 24
            left = max(8, (width - box_width) // 2)
            top = height - 106
            canvas.rect(left, top, box_width, 26, (0.03, 0.04, 0.06, 0.78))
            canvas.text(left + 12, top + 7, text, self.sound_cue_color, 2)
        for index, entry in enumerate(self.kill_feed):
            alpha = min(1.0, float(entry["t"]) / 0.6)
            if entry.get("critical"):
                color = (1.0, 0.62, 0.20, alpha)
            elif entry.get("danger"):
                color = (1.0, 0.35, 0.30, alpha)
            else:
                color = (0.95, 0.90, 0.80, alpha)
            canvas.text(16, 104 + index * 18, str(entry["text"]), color, 2)
        if self.score_pop is not None:
            alpha = min(1.0, max(0.0, float(self.score_pop["t"]) / 0.6))
            canvas.text(
                int(state.width) // 2 + 22, int(state.height) // 2 + 16,
                str(self.score_pop["text"]), (1.0, 0.62, 0.20, alpha), 2,
            )
        best = int(self.profile.get("best_score", 0))
        if best > 0:
            label = f"BEST {best}"
            canvas.text(
                int(state.width) // 2 - text_width(label, 2) // 2, 16,
                label, (0.55, 0.60, 0.68, 1.0), 2,
            )
        if self.sim.alive and self.campaign_clear_t > 0.0:
            width = int(state.width)
            cx = width // 2
            canvas.rect(cx - 180, 138, 360, 74, (0.03, 0.04, 0.06, 0.86))
            canvas.text(cx - 82, 146, "CAMPAIGN CLEAR", (1.0, 0.62, 0.20, 1.0), 2)
            canvas.text(
                cx - 96, 168,
                f"WAVE {int(self.sim.wave)}  SCORE {int(self.sim.score)}",
                (0.95, 0.95, 0.97, 1.0), 2,
            )
            canvas.text(
                cx - 82, 190,
                f"CAMPAIGNS WON {int(self.profile.get('wins', 0))}",
                (0.95, 0.90, 0.80, 1.0), 2,
            )
        elif self.sim.alive and bool(getattr(self.sim, "victory", False)):
            label = "CAMPAIGN COMPLETE"
            canvas.text(
                int(state.width) // 2 - text_width(label, 2) // 2, 116,
                label, (1.0, 0.62, 0.20, 1.0), 2,
            )
            prompt = "PRESS ENTER FOR A NEW RUN"
            canvas.text(
                int(state.width) // 2 - text_width(prompt, 2) // 2, 140,
                prompt, (0.95, 0.90, 0.80, 1.0), 2,
            )
        if not self.sim.alive and self.last_run is not None:
            run = self.last_run
            width = int(state.width)
            cx = width // 2
            top = int(state.height) // 2 - 8
            history = [
                f"{int(item.get('score', 0))}"
                f"{'W' if item.get('outcome') == 'win' else 'L'}"
                for item in list(self.profile.get("history", []))[:5]
            ]
            extras: list[tuple[str, tuple]] = []
            if self.profile_disabled:
                extras.append(("PROFILE DISABLED", (1.0, 0.30, 0.30, 1.0)))
            elif self.profile_recovered:
                label = ("PROFILE RECOVERED" if self.profile_recovered_from_backup
                         else "PROFILE RESET")
                color = ((1.0, 0.62, 0.20, 1.0) if self.profile_recovered_from_backup
                         else (1.0, 0.30, 0.30, 1.0))
                extras.append((label, color))
            elif self.profile_save_failed:
                extras.append(("PROFILE NOT SAVED", (1.0, 0.30, 0.30, 1.0)))
            if self.campaign_cleared:
                extras.append(("CAMPAIGN CLEARED", (1.0, 0.62, 0.20, 1.0)))
            if self.run_new_best:
                extras.append(("NEW BEST", (1.0, 0.62, 0.20, 1.0)))
            if history:
                extras.append((f"RECENT {' / '.join(history[:3])}", (0.55, 0.60, 0.68, 1.0)))
                if len(history) > 3:
                    extras.append((f"HISTORY {' / '.join(history[3:])}", (0.55, 0.60, 0.68, 1.0)))
            runs = int(self.profile.get("runs", 0))
            wins = int(self.profile.get("wins", 0))
            if runs > 0:
                extras.append((f"RUNS {runs}  WINS {wins}", (0.55, 0.60, 0.68, 1.0)))
            extras.append(("PRESS ENTER FOR A NEW RUN", (1.0, 0.62, 0.20, 1.0)))
            best_kills = int(self.profile.get("best_kills", 0))
            best_wave = int(self.profile.get("best_wave", 0))
            best_streak = int(self.profile.get("best_streak", 0))
            if best_kills or best_wave or best_streak:
                extras.append((
                    f"BEST KILLS {best_kills}  WAVE {best_wave}  STREAK {best_streak}",
                    (0.55, 0.60, 0.68, 1.0),
                ))
            widest = max([text_width(label, 2) for label, _color in extras] + [340])
            panel_width = max(380, widest + 40)
            panel_left = cx - panel_width // 2
            text_x = panel_left + 20
            panel_height = 100 + 22 * max(0, len(extras) - 1)
            canvas.rect(panel_left, top, panel_width, panel_height, (0.03, 0.04, 0.06, 0.86))
            canvas.text(text_x, top + 6, "RUN OVER", (1.0, 0.30, 0.30, 1.0), 2)
            canvas.text(
                text_x, top + 28,
                f"SCORE {run['score']}  KILLS {run['kills']}  WAVE {run['wave']}",
                (0.95, 0.95, 0.97, 1.0), 2,
            )
            canvas.text(
                text_x, top + 50,
                f"BEST STREAK {run['best_streak']}  TIME {run['time_s']}s",
                (0.55, 0.60, 0.68, 1.0), 2,
            )
            for index, (label, color) in enumerate(extras):
                canvas.text(text_x, top + 72 + index * 22, label, color, 2)
