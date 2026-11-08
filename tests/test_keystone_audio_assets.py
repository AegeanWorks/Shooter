"""Keystone mechanics testbed: audio buses/mixdown and asset hot reload.

Covers the named-bus Mixer (gain scaling, mute, validation, game voice
cap) and the AssetRegistry (dependency tracking, duplicate digests,
file-backed hot reload and missing-source reporting).
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from keystone.assets import AssetRegistry
from keystone.audio import Mixer, audio_report, sine
from keystone.geometry import Material
from keystone.input import ActionState
from keystone.math3d import Vec3
from keystone.texture import TextureData

from shooter.game import ShooterGame

DATA = Path(__file__).parent.parent / "shooter" / "data"


def _clip():
    return sine(440.0, 0.05)


def test_mixer_bus_gain_scales_the_render():
    clip = _clip()
    mixer = Mixer(buses={"master": 1.0, "sfx": 1.0, "music": 1.0})
    mixer.play(clip, bus="sfx", gain=1.0)
    full = audio_report(mixer.render(), mixer.voice_count(), mixer.buses)
    assert full["peak"] > 0.0

    mixer.clear()
    mixer.set_bus("sfx", 0.25)
    mixer.play(clip, bus="sfx", gain=1.0)
    quarter = audio_report(mixer.render(), mixer.voice_count(), mixer.buses)
    assert abs(quarter["peak"] - full["peak"] * 0.25) < 1e-9

    mixer.clear()
    mixer.set_bus("sfx", 0.0)
    mixer.play(clip, bus="sfx", gain=1.0)
    muted = audio_report(mixer.render(), mixer.voice_count(), mixer.buses)
    assert muted["peak"] == 0.0
    assert muted["rms"] == 0.0


def test_mixer_validates_buses_and_gains():
    mixer = Mixer()
    with pytest.raises(ValueError):
        mixer.play(_clip(), bus="nope")
    with pytest.raises(ValueError):
        mixer.set_bus("sfx", -0.1)
    assert mixer.voice_count() == 0


def test_shooter_mixer_routes_sfx_and_caps_voices():
    g = ShooterGame()
    g.build_scene()
    g.mixer.set_bus("sfx", 0.0)
    g.mixer.clear()
    g._play_clip(g._clips["brute_slam"], 0.7)
    muted = audio_report(g.mixer.render(), g.mixer.voice_count(), g.mixer.buses)
    assert muted["peak"] == 0.0

    g.mixer.set_bus("sfx", 0.9)
    g.mixer.clear()
    for _ in range(12):
        g.mixer.play(g._clips["shoot"], bus="sfx", gain=0.7)
    assert g.mixer.voice_count() == 12
    g.update(1.0 / 60.0, ActionState())
    assert g.mixer.voice_count() <= 8


def test_registry_tracks_dependencies_and_duplicates():
    registry = AssetRegistry()
    texture = TextureData.checker(4, (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), 2, "checker")
    record = registry.register("texture.checker", texture)
    assert record.kind == "texture"
    duplicate = registry.register("texture.copy", texture)
    assert duplicate.sha256 == record.sha256
    groups = registry.duplicates()
    assert any(set(group) == {"texture.checker", "texture.copy"} for group in groups), groups

    material = Material(color=Vec3(1.0, 0.8, 0.2), texture=texture)
    mrecord = registry.register(
        "material.gold", material, dependencies=("texture.checker",)
    )
    assert mrecord.dependencies == ("texture.checker",)
    assert registry.missing_dependencies() == ()
    registry.remove("texture.checker")
    assert ("material.gold", "texture.checker") in registry.missing_dependencies()
    with pytest.raises(KeyError):
        registry.require("texture.checker")


def test_registry_replace_guard_and_digest():
    registry = AssetRegistry()
    first = TextureData.checker(4, (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), 2, "first")
    record = registry.register("texture.swap", first)
    with pytest.raises(ValueError):
        registry.register("texture.swap", first)
    second = TextureData.checker(8, (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), 2, "second")
    replaced = registry.register("texture.swap", second, replace=True)
    assert replaced.payload is second
    assert replaced.sha256 != record.sha256


def test_registry_register_file_hot_reloads_and_reports_missing():
    g = ShooterGame()
    g.build_scene()
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "pickup_beacon.kprefab"
        shutil.copyfile(DATA / "pickup_beacon.kprefab", source)
        record = g.assets.register_file("prefab.test", source)
        assert record.kind == "prefab"
        assert record.source == source
        old_sha = record.sha256

        document = json.loads(source.read_text(encoding="utf-8"))
        document["roots"][0]["name"] = "surge-pickup-v2"
        source.write_text(json.dumps(document), encoding="utf-8")

        report = g.assets.refresh()
        assert "prefab.test" in report.reloaded, report
        updated = g.assets.require("prefab.test")
        assert updated.sha256 != old_sha
        assert updated.payload.roots[0].name == "surge-pickup-v2"

        source.unlink()
        missing = g.assets.refresh()
        assert "prefab.test" in missing.missing, missing
