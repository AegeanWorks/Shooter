"""Audio-cue proofs: boss/engagement events own a voice and a caption.

The audio layer is presentation-only; the same events, HP and snapshot hash
must hold with or without the new voices. Captions are the visible half of
the cue (accessibility + screenshot evidence).
"""

from keystone.input import ActionState
from keystone.math3d import Vec3

from shooter.game import ShooterGame
from shooter.sim import _Enemy


class _Canvas:
    def __init__(self) -> None:
        self.rects: list[tuple] = []
        self.texts: list[tuple] = []

    def rect(self, *args) -> None:
        self.rects.append(args)

    def text(self, *args) -> None:
        self.texts.append(args)


class _Hud:
    width = 960
    height = 540


def _close_boss_game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = []
    g.sim.spawn_t = 999.0
    g.sim.wave = 3
    g.sim.enemies = [
        _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 5.0), hp=600, max_hp=600,
               summon_cd=999.0)
    ]
    return g


def test_boss_windup_and_slam_get_audio_and_caption():
    g = _close_boss_game()
    g.update(1.0 / 60.0, ActionState())
    assert g.sound_cue == "WARDEN WINDUP", g.sound_cue
    assert g.sound_cue_t > 0.0
    assert g.mixer.voice_count() >= 1
    assert g._clips["boss_windup"].duration() > 0.2
    for _ in range(60):
        g.update(1.0 / 60.0, ActionState())
        if g.sim.hp < 100:
            break
    assert g.sim.hp == 70
    assert g.sound_cue == "WARDEN SLAM", g.sound_cue
    assert g._clips["boss_slam"].duration() > 0.2
    assert g.dropped_sfx == 0


def test_pickup_gets_audio_and_caption():
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    g.sim.pickup_active = True
    rest_y = float(g.sim.player_pos.y)
    g.sim.player_pos = Vec3(0.0, rest_y, -6.0)
    g.sim.body = g.sim.body.__class__(
        position=Vec3(0.0, rest_y, -6.0), half_extents=g.sim.body.half_extents,
        velocity=Vec3(), on_ground=True,
    )
    g.update(1.0 / 60.0, ActionState())
    assert g.sim.weapon == "surge"
    assert g.sound_cue == "SURGE ACQUIRED", g.sound_cue
    assert g._clips["pickup"].duration() > 0.0


def test_the_shipped_audio_cue_manifest_is_complete():
    """Every voice the event layer can request must exist and be non-empty."""
    game = ShooterGame()
    game.build_scene()
    clips = game._clips
    expected = {
        "boss_down", "boss_slam", "boss_summon", "boss_windup",
        "brute_slam", "brute_windup", "cache", "cache_drop",
        "clutch", "critical", "death", "dry_fire", "hit", "hurt",
        "kill", "lance", "near_miss", "overdrive", "overdrive_denied",
        "overdrive_end", "overdrive_hit", "pickup", "reload", "reloaded",
        "scatter", "shoot", "spawn", "streak_break", "surge_forfeit",
        "switch_lance", "switch_pulse", "switch_scatter", "wave", "wisp_bolt",
    }
    assert set(clips) == expected
    assert all(clip.duration() > 0.0 for clip in clips.values())


def test_clip_hook_observes_play_without_owning_mixer():
    g = _close_boss_game()
    seen: list[tuple[str, float]] = []
    g.set_clip_hook(lambda clip, gain: seen.append((clip.name, float(gain))))
    g.update(1.0 / 60.0, ActionState())
    assert ("boss_windup", 0.8) in seen, seen
    assert g.mixer.voice_count() == 1


def test_boss_down_event_and_clip():
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = [
        _Enemy(etype="warden", pos=Vec3(0.0, 1.1, 2.0), hp=12, max_hp=600,
               summon_cd=999.0)
    ]
    g.sim.pitch = 0.0
    events: list[str] = []
    for _ in range(12):
        if not any(e.alive for e in g.sim.enemies):
            break
        g.sim._fire(g.sim.weapons["pulse"], events)
    assert "boss_down" in events, events
    g._play_event("boss_down")
    assert g.sound_cue == "WARDEN DOWN", g.sound_cue
    assert g._clips["boss_down"].duration() > 0.3


def test_caption_draws_and_expires():
    g = ShooterGame()
    g.build_scene()
    g.sound_cue = "WARDEN WINDUP"
    g.sound_cue_t = 0.5
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    assert any("WARDEN WINDUP" in str(t[2]) for t in canvas.texts), canvas.texts
    g.sound_cue_t = 0.0
    canvas = _Canvas()
    g.draw_ui(canvas, _Hud())
    assert not any("WARDEN WINDUP" in str(t[2]) for t in canvas.texts), canvas.texts
