"""Keystone testbed: the spawn warning voice consumes audio_spatial.

`keystone.audio_spatial` was one of the Keystone modules the shooter had never
imported. The sim already publishes `spawn_pos` as presentation telemetry, so
the HOSTILE INBOUND voice can now attenuate with listener distance while the
game's single Mixer keeps owning buses, pitch and the voice cap.
"""

from keystone.audio_spatial import SoundSource, distance_gain
from keystone.math3d import Vec3
from keystone.replay import stable_hash

from shooter.game import ShooterGame


def _game() -> ShooterGame:
    g = ShooterGame()
    g.build_scene()
    g.sim.spawn_queue = ["mite", "mite"]
    g.sim.spawn_t = 999.0
    g.sim.enemies = []
    return g


def _played_gain(g: ShooterGame, position: Vec3) -> float:
    seen: list[float] = []
    g.set_clip_hook(lambda clip, gain: seen.append(float(gain)))
    g.sim.spawn_pos = position
    g._play_event("spawn")
    assert len(seen) == 1, seen
    return seen[0]


def _at(eye: Vec3, dx: float) -> Vec3:
    return Vec3(eye.x + dx, eye.y, eye.z)


def test_spawn_voice_gain_falls_off_with_distance():
    eye = _game().sim.eye()
    near = _played_gain(_game(), _at(eye, 2.0))
    far = _played_gain(_game(), _at(eye, 18.0))
    silent = _played_gain(_game(), _at(eye, 40.0))
    assert 0.0 < far < near <= 0.30, (near, far)
    assert silent == 0.0, silent


def test_spatial_report_describes_the_same_geometry():
    g = _game()
    eye = g.sim.eye()
    position = _at(eye, 8.0)
    g.sim.spawn_pos = position
    g._play_event("spawn")
    report = g.spatial_audio_report
    assert report is not None
    assert report["schema"] == 1
    assert len(report["sources"]) == 1
    entry = report["sources"][0]
    source = SoundSource(position=position, clip=g._clips["spawn"], gain=0.30)
    assert entry["distance"] == round((position - eye).length(), 6)
    assert entry["attenuation"] == round(distance_gain(eye, source), 6)
    assert entry["audible"] is True
    assert report["audible"] == 1 and report["silent"] == 0


def test_a_bad_position_falls_back_without_crashing_the_frame():
    g = _game()
    seen: list[float] = []
    g.set_clip_hook(lambda clip, gain: seen.append(float(gain)))
    g.sim.spawn_pos = Vec3(float("nan"), 0.0, 0.0)
    g._play_event("spawn")
    assert seen == [0.30], seen
    assert g.spatial_audio_report is None
    assert g.dropped_sfx == 0


def test_a_rebuild_clears_the_spatial_report():
    g = _game()
    g.sim.spawn_pos = _at(g.sim.eye(), 4.0)
    g._play_event("spawn")
    assert g.spatial_audio_report is not None
    g.build_scene()
    assert g.spatial_audio_report is None


def test_spatial_audio_does_not_touch_the_deterministic_state():
    g = _game()
    g.sim.spawn_pos = _at(g.sim.eye(), 4.0)
    before = stable_hash(g.snapshot())
    g._play_event("spawn")
    assert stable_hash(g.snapshot()) == before
