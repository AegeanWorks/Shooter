"""Boltshooter: Keystone plug-in shooter. Engine owns loop/render/input.

Game owns state/rules/scene. Five ops + optional draw_ui. All tuning in
shooter/data/*.json, never hardcoded one-offs.
"""

from __future__ import annotations

import math
from dataclasses import replace

from keystone.assets import AssetRegistry
from keystone.audio import Mixer, noise, sine, square
from keystone.geometry import Material, MeshData
from keystone.math3d import Quat, Vec3
from keystone.primitives import cone, cube, plane, sphere
from keystone.scene import BloomSettings, ColorSettings, DirectionalLight, Node, PointLight, PostSettings, Scene, ShadowSettings, Transform
from keystone.texture import TextureData
from keystone.ui.font import text_width

from .profile import ProfileStore, default_profile
from .sim import Sim
from .ui import draw_shooter

MAX_ENEMIES = 24
MAX_TRACERS = 16
MAX_SPAWN_MARKS = 4
MAX_CACHES = 4


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
        self._pickup: Node | None = None
        self._pickup_beam: Node | None = None
        self._pickup_orb: Node | None = None
        self._boss_core: Node | None = None
        self._built = False

    # ---- five-operation contract --------------------------------------
    def build_scene(self) -> Scene:
        self.sim.reset()
        self.scene = Scene()
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
        self.assets.register("material.warden", Material(color=Vec3(0.62, 0.09, 0.10), specular=0.35, shininess=32.0, emissive=Vec3(0.38, 0.02, 0.02), metallic=0.15, roughness=0.65))
        self.assets.register("material.enemy_hit", Material(color=Vec3(1.0, 0.96, 0.86), specular=0.8, shininess=64.0, emissive=Vec3(1.0, 0.62, 0.28)))
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
        self.assets.register("material.cache", Material(color=Vec3(1.0, 0.68, 0.22), specular=0.5, shininess=48.0, emissive=Vec3(0.82, 0.38, 0.04)))
        self.assets.register("material.boss_core", Material(color=Vec3(1.0, 0.78, 0.24), specular=0.8, shininess=64.0, emissive=Vec3(1.0, 0.48, 0.08)))

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
            pad = Node(
                "platform-pad", id="platform-pad",
                transform=Transform(
                    position=Vec3(px, 0.02, pz - pd / 2.0 - 0.8),
                    scale=Vec3(1.4, 0.02, 1.4),
                ),
                mesh=wall_mesh, material=trim_mat,
            )
            self.scene.add(pad)
            self._approach_pad = pad

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
        # First-person viewmodel: two shared cubes follow the camera and tint
        # with the active weapon; purely visual until _sync_scene moves them.
        gun_mesh = self.assets.require("mesh.wall").payload
        gun_mat = self.assets.require("material.gun_pulse").payload
        self._view_body = Node("viewmodel-body", id="viewmodel-body", visible=True,
                               mesh=gun_mesh, material=gun_mat)
        self._view_barrel = Node("viewmodel-barrel", id="viewmodel-barrel", visible=True,
                                 mesh=gun_mesh, material=gun_mat)
        self.scene.add(self._view_body)
        self.scene.add(self._view_barrel)
        pickup_mesh = self.assets.require("mesh.pickup").payload
        pickup_mat = self.assets.require("material.pickup").payload
        self._pickup_spot = self.sim.levels.get("pickup", {"x": 0.0, "y": 0.5, "z": -6.0})
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
        # Ammo-cache pool: shared glowing cubes mark sim-dropped caches.
        # Presentation only; lifetime, pickup and reward RNG stay in sim.
        self._cache_nodes = []
        cache_mat = self.assets.require("material.cache").payload
        for index in range(MAX_CACHES):
            node = Node(
                f"ammo-cache-{index}", id=f"ammo-cache-{index}", visible=False,
                mesh=pickup_mesh, material=cache_mat,
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
        for i in range(MAX_SPAWN_MARKS):
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
        self._built = True
        self._sync_scene()
        return self.scene

    def set_clip_hook(self, hook) -> None:
        """Attach an optional (clip, gain) observer for evidence tooling."""
        self._clip_hook = hook

    def _play_clip(self, clip, gain: float) -> None:
        """Play one SFX clip, counting (never hiding) a mixer refusal.

        Audio must never crash gameplay, but a refusal used to vanish into
        `except ValueError: pass`. Counting drops keeps the failure visible
        to soak reports without changing the deterministic sim.
        """
        if self._clip_hook is not None:
            self._clip_hook(clip, gain)
        try:
            self.mixer.play(clip, bus="sfx", gain=gain)
        except ValueError:
            self.dropped_sfx += 1

    def update(self, dt: float, actions) -> None:
        if not self._built:
            self.build_scene()
        events = self.sim.step(float(dt), actions)
        self._forfeit_cue_pending = False
        self._clutch_cue_pending = False
        self._critical_kill_pending = False
        for e in events:
            self._play_event(e)
        if "died" in events:
            self._finish_run()
        elif "wave" in events:
            self._record_progress()
        if (
            not self.campaign_cleared
            and self.sim.alive
            and int(self.sim.wave) >= int(self.sim.levels.get("win_wave", 4))
        ):
            self.campaign_cleared = True
            self.campaign_clear_t = 4.0
            self.sim.seal_campaign()
            self._record_campaign_clear()
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
        self._sync_scene()

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

    def _record_campaign_clear(self) -> None:
        if self.profile_disabled:
            return
        self.profile["wins"] = int(self.profile.get("wins", 0)) + 1
        self._record_run("win")

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
        if changed:
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
                cap = max(1, int(cfg.get("max", MAX_SPAWN_MARKS)))
                self.spawn_marks = self.spawn_marks[:cap]
            self._play_clip(self._clips["spawn"], 0.30)
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
            self._play_clip(clip, 0.7)
        elif event == "hit":
            self._play_clip(self._clips["hit"], 0.5)
        elif event == "kill":
            self._play_clip(self._clips["kill"], 0.8)
        elif event == "critical":
            self._play_clip(self._clips["critical"], 0.55)
            self._cue("CRITICAL")
            self._critical_kill_pending = True
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
        elif event == "wisp_bolt":
            self._play_clip(self._clips["wisp_bolt"], 0.65)
            self._cue("WISP BOLT", danger=True)
        elif event == "boss_summon":
            self._play_clip(self._clips["boss_summon"], 0.7)
            self._cue("WARDEN SUMMON", danger=True)
            cfg = dict(self.sim.juice.get("spawn_mark", {}))
            for pos in list(getattr(self.sim, "summon_positions", []))[:MAX_SPAWN_MARKS]:
                self.spawn_marks.insert(0, {
                    "x": float(pos.x), "z": float(pos.z),
                    "t": float(cfg.get("life_s", 0.7)),
                })
            self.spawn_marks = self.spawn_marks[:MAX_SPAWN_MARKS]
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

    def _sync_scene(self) -> None:
        sim = self.sim
        cam = self.scene.camera
        eye = sim.eye()
        hurt = float(getattr(sim, "hurt_t", 0.0))
        if hurt > 0.0:
            # Short deterministic jolt while the damage cue is live; the
            # aim ray still starts at the sim eye, so this is presentation.
            amp = min(1.0, hurt / 0.3) * 0.035
            cam.position = Vec3(
                eye.x + math.sin(sim.time * 55.0) * amp,
                eye.y + math.cos(sim.time * 47.0) * amp * 0.6,
                eye.z,
            )
        else:
            cam.position = eye
        cam.yaw = sim.yaw
        cam.pitch = max(-1.55, min(1.55, sim.pitch + sim.kick))
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
        hit_span = max(1e-6, float(self.sim.juice.get("hit_flinch_s", 0.25)))
        death_span = max(1e-6, float(self.sim.juice.get("death_fx_s", 0.15)))
        ordered = sorted(sim.enemies, key=lambda e: (0 if e.alive else 1, e.etype))
        for i, node in enumerate(self._enemy_nodes):
            if i < len(ordered) and (ordered[i].alive or ordered[i].death_t > 0.0):
                e = ordered[i]
                mesh, mat, _ = mesh_by_type[e.etype]
                node.mesh = mesh
                node.visible = True
                if not e.alive:
                    # Brief white-hot shrink so the kill has a body exit.
                    k = max(0.0, min(1.0, e.death_t / death_span))
                    node.material = hit_mat
                    node.transform = Transform(
                        position=e.pos, scale=Vec3(k, k, k)
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
                node.transform = Transform(
                    position=Vec3(e.pos.x + ux * push, e.pos.y, e.pos.z + uz * push),
                    scale=Vec3(s * (1.0 + flinch), s * (1.0 - flinch), s * (1.0 + flinch)),
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
            boss = next(
                (e for e in sim.enemies if e.alive and e.etype == "warden"),
                None,
            )
            self._boss_core.visible = boss is not None
            if boss is not None:
                # Glowing core on the face turned toward the player. Purely
                # visual: it follows the boss and swells during the windup.
                dx = sim.player_pos.x - boss.pos.x
                dz = sim.player_pos.z - boss.pos.z
                length = math.hypot(dx, dz)
                ux, uz = (dx / length, dz / length) if length > 1e-6 else (0.0, -1.0)
                pulse = 1.0 + (0.18 if boss.windup_t > 0.0 else 0.0)
                self._boss_core.transform = Transform(
                    position=Vec3(boss.pos.x + ux * 1.25, boss.pos.y + 0.35, boss.pos.z + uz * 1.25),
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
            cfg = self.sim.juice.get("viewmodel", {})
            forward = sim.forward()
            right = Vec3(math.cos(sim.yaw), 0.0, math.sin(sim.yaw))
            up = right.cross(forward)
            eye = sim.eye()
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
            rotation = (
                Quat.from_axis_angle(Vec3(0.0, 1.0, 0.0), sim.yaw)
                * Quat.from_axis_angle(Vec3(1.0, 0.0, 0.0), sim.pitch)
            )

            def gun_pos(forward_d: float, right_d: float, down_d: float) -> Vec3:
                return Vec3(
                    eye.x + forward.x * forward_d + right.x * right_d - up.x * down_d,
                    eye.y + forward.y * forward_d + right.y * right_d - up.y * down_d,
                    eye.z + forward.z * forward_d + right.z * right_d - up.z * down_d,
                )

            self._view_body.visible = bool(sim.alive)
            self._view_barrel.visible = bool(sim.alive)
            if sim.alive:
                self._view_body.transform = Transform(
                    position=gun_pos(
                        float(cfg.get("forward", 0.40)) - recoil_back - reload_back,
                        float(cfg.get("right", 0.18)) + bob_right,
                        float(cfg.get("down", 0.16)) - recoil_up + reload_drop - bob_up,
                    ),
                    rotation=rotation,
                    scale=Vec3(
                        float(cfg.get("body_width", 0.07)),
                        float(cfg.get("body_height", 0.07)),
                        float(cfg.get("body_length", 0.30)),
                    ),
                )
                self._view_barrel.transform = Transform(
                    position=gun_pos(
                        float(cfg.get("barrel_forward", 0.62)) - recoil_back - reload_back,
                        float(cfg.get("right", 0.18)) + bob_right,
                        float(cfg.get("barrel_down", 0.20)) - recoil_up + reload_drop - bob_up,
                    ),
                    rotation=rotation,
                    scale=Vec3(
                        float(cfg.get("barrel_size", 0.035)),
                        float(cfg.get("barrel_size", 0.035)),
                        float(cfg.get("barrel_length", 0.32)),
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
        if self._approach_pad is not None:
            pulse = 1.0 + 0.08 * math.sin(sim.time * 3.0)
            self._approach_pad.transform = Transform(
                position=self._approach_pad.transform.position,
                scale=Vec3(1.4 * pulse, 0.02, 1.4 * pulse),
            )
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
                size = 1.0 + float(sim.juice.get("pickup_fx_scale", 3.0)) * k
                rise = float(sim.juice.get("pickup_fx_rise", 1.2)) * k
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

    def snapshot(self) -> dict:
        snap = self.sim.snapshot()
        snap["dropped_sfx"] = int(self.dropped_sfx)
        return snap

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
            elif self.profile_save_errors > 0:
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
