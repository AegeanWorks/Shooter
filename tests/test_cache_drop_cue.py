"""Audio proof: an ammo cache announces its drop, not just its pickup.

The sim emits `cache_drop` when a 3% reward roll leaves a cache, but only
collection had a voice/caption. Cycle 70 made caches visible; the drop now
also needs to be audible at the kill that produced it.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import _Enemy


def _kill_game(cache: bool) -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.engagement["reward"] = {
        "standard_p": 0.0 if cache else 1.0,
        "critical_p": 0.0,
        "critical_mult": 2.0,
        "cache_p": 1.0 if cache else 0.0,
        "cache_reserve": 12,
        "cache_expire_s": 8.0,
    }
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = [
        _Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=1, max_hp=30)
    ]
    return g


def test_cache_drop_plays_a_distinct_cue_and_caption():
    g = _kill_game(True)
    clips: list[str] = []
    g.set_clip_hook(lambda clip, gain: clips.append(clip.name))
    g.update(1.0 / 60.0, ActionState(held=frozenset({"fire"})))
    assert len(g.sim.caches) == 1
    assert "cache_drop" in clips, clips
    assert g.sound_cue == "AMMO CACHE DROP"


def test_standard_kill_does_not_play_the_drop_cue():
    g = _kill_game(False)
    clips: list[str] = []
    g.set_clip_hook(lambda clip, gain: clips.append(clip.name))
    g.update(1.0 / 60.0, ActionState(held=frozenset({"fire"})))
    assert g.sim.caches == []
    assert "cache_drop" not in clips
    assert g.sound_cue != "AMMO CACHE DROP"


def test_drop_voice_differs_from_collection_and_kill():
    g = ShooterGame()
    g.build_scene()
    drop = g._clips["cache_drop"]
    pickup = g._clips["cache"]
    kill = g._clips["kill"]
    assert drop.samples != pickup.samples
    assert drop.samples != kill.samples
    assert drop.duration() < pickup.duration()
