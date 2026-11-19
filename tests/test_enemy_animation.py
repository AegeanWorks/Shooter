"""Gameplay proof: enemies animate from Keystone .kanim clips.

The testbed proved AnimationLibrary/AnimationController sampling, but the
game never loaded a clip and animated enemies with ad-hoc sine math. Enemy
presentation now samples file-backed idle clips; the sim hash stays untouched.
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.anim import CLIP_NAMES, EnemyAnimations
from shooter.game import ShooterGame
from shooter.sim import Sim, _Enemy


def _game() -> ShooterGame:
    game = ShooterGame()
    game.build_scene()
    return game


def test_library_loads_every_enemy_idle_clip():
    anim = EnemyAnimations()
    assert set(anim.clips) == set(CLIP_NAMES)
    for name in CLIP_NAMES:
        clip = anim.clips[name]
        assert clip.name == name
        assert clip.duration() > 0.0
        assert clip.node_ids() == ["subject"]
        assert clip.rotation_tracks or clip.scale_tracks


def test_idle_sampling_is_deterministic_and_uniform():
    first = EnemyAnimations()
    second = EnemyAnimations()
    poses = [first.offset(0, "wisp", 1.0 / 60.0) for _ in range(36)]
    mirror = [second.offset(0, "wisp", 1.0 / 60.0) for _ in range(36)]
    assert [pose.rotation for pose in poses] == [pose.rotation for pose in mirror]
    assert len({round(pose.rotation.y, 6) for pose in poses}) > 1
    for pose in poses:
        assert pose.scale.x == pose.scale.y == pose.scale.z


def test_shipped_idle_clips_stay_inside_their_presentation_bands():
    """A mistyped keyframe must fail a test, not silently change enemy feel."""
    anim = EnemyAnimations()
    scales = []
    for name in CLIP_NAMES:
        pose = anim.clips[name].sample(0.5)["subject"]
        scale = pose.scale.x
        assert pose.scale.x == pose.scale.y == pose.scale.z, name
        assert 1.0 <= scale <= 1.12, (name, scale)
        assert abs(pose.rotation.y) <= 1.0, (name, pose.rotation.y)
        scales.append(scale)
    assert max(scales) > 1.02, "the idle clips must keep a visible breathe"


def test_sync_scene_rotates_a_live_enemy_without_moving_it():
    game = _game()
    game.sim.enemies = [
        _Enemy(etype="wisp", pos=Vec3(0.0, 0.7, 2.0), hp=30, max_hp=30)
    ]
    game._sync_scene(0.0)
    node = game._enemy_nodes[0]
    start = node.transform.rotation
    assert node.transform.position == Vec3(0.0, 0.7, 2.0)
    for _ in range(24):
        game._sync_scene(1.0 / 60.0)
    assert node.transform.rotation != start
    assert node.transform.position == Vec3(0.0, 0.7, 2.0)
    assert node.transform.scale.x == node.transform.scale.y


def test_idle_scale_keeps_the_flinch_squash_invariant():
    game = _game()
    game.sim.enemies = [
        _Enemy(etype="mite", pos=Vec3(0.0, 0.5, 2.0), hp=18, max_hp=30, hit_t=0.25)
    ]
    game._sync_scene(0.0)
    node = game._enemy_nodes[0]
    assert node.transform.scale.x > node.transform.scale.y
    assert node.transform.position.z < 2.0


def test_animation_never_changes_the_sim_snapshot():
    plain = Sim(seed=1)
    game = ShooterGame()
    game.sim = Sim(seed=1)
    game.build_scene()
    for _ in range(30):
        plain.step(1.0 / 60.0, ActionState())
        game.update(1.0 / 60.0, ActionState())
    assert plain.snapshot() == game.sim.snapshot()
