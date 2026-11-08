"""Enemy presentation animation: file-backed .kanim idle clips.

Keystone owns sampling, looping and crossfade; this module binds one
AnimationController to each enemy node slot and returns the sampled idle
Transform. The game layers that rotation/scale onto the sim-driven node
position, so animation can never move a hitbox or change the sim hash.
"""

from __future__ import annotations

from pathlib import Path

from keystone.animation import AnimationClip, AnimationController
from keystone.animation_library import AnimationLibrary
from keystone.scene import Transform

ANIM_DIR = Path(__file__).parent / "data" / "anim"
CLIP_NAMES = ("mite_idle", "brute_idle", "wisp_idle", "warden_idle")
TYPES = {
    "mite": "mite_idle",
    "brute": "brute_idle",
    "wisp": "wisp_idle",
    "warden": "warden_idle",
}


class EnemyAnimations:
    """One deterministic idle controller per enemy node slot."""

    def __init__(self, directory: str | Path | None = None) -> None:
        self.library = AnimationLibrary(directory or ANIM_DIR)
        self.clips: dict[str, AnimationClip] = {
            name: self.library.load(name) for name in CLIP_NAMES
        }
        self._controllers: dict[int, AnimationController] = {}
        self._active: dict[int, str] = {}

    def _controller(self, slot: int, name: str) -> AnimationController:
        controller = self._controllers.get(slot)
        if controller is None:
            controller = AnimationController()
            for clip in self.clips.values():
                controller.add(clip)
            controller.play(name)
            self._controllers[slot] = controller
            self._active[slot] = name
        elif self._active[slot] != name:
            controller.crossfade(name, 0.15)
            self._active[slot] = name
        return controller

    def offset(self, slot: int, etype: str, dt: float) -> Transform:
        """Advance one slot's idle clip and return its sampled Transform."""
        name = TYPES[etype]
        controller = self._controller(slot, name)
        pose = controller.advance(float(dt))
        return pose.get("subject", Transform())
