"""Audio-cue evidence: render the new voices to WAV + a spectrogram PNG.

The game itself only uses stdlib + Keystone; this dev probe uses numpy and
Pillow (both already in the Keystone pinned stack) to make inspectable audio
evidence. It writes the report JSON, the mixed WAV and the spectrogram beside
the path given; nothing is loaded by the game at runtime.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "keystone"))

from keystone.audio import AudioClip, audio_report, write_wav  # noqa: E402

from shooter.game import ShooterGame  # noqa: E402

CUES = (
    "boss_windup",
    "boss_slam",
    "boss_summon",
    "boss_down",
    "overdrive",
    "overdrive_end",
    "overdrive_denied",
    "dry_fire",
    "critical",
    "cache",
    "cache_drop",
    "clutch",
    "near_miss",
    "reload",
    "reloaded",
    "surge_forfeit",
    "streak_break",
    "pickup",
    "death",
)
VISUAL_CUES = (
    "boss_windup",
    "boss_slam",
    "boss_down",
    "overdrive",
    "critical",
    "cache",
    "cache_drop",
    "clutch",
    "pickup",
    "surge_forfeit",
    "death",
)


def _join(clips: list[AudioClip], gap: float = 0.25) -> tuple[AudioClip, list[dict]]:
    rate = clips[0].sample_rate if clips else 22050
    samples: list[float] = []
    marks: list[dict] = []
    silence = [0.0] * int(gap * rate)
    for clip in clips:
        marks.append({"name": clip.name, "start_s": round(len(samples) / rate, 3)})
        samples.extend(clip.samples)
        samples.extend(silence)
    return AudioClip(tuple(samples), rate, "cue-sequence"), marks


def _spectrogram(clip: AudioClip, path: Path, marks: list[dict]) -> dict:
    import numpy as np
    from PIL import Image, ImageDraw

    samples = np.asarray(clip.samples, dtype=np.float32)
    window = 1024
    hop = 256
    count = max(1, 1 + max(0, len(samples) - window) // hop)
    frames = np.zeros((count, window), dtype=np.float32)
    for index in range(count):
        start = index * hop
        chunk = samples[start : start + window]
        frames[index, : len(chunk)] = chunk
    taper = np.hanning(window).astype(np.float32)
    spectrum = np.abs(np.fft.rfft(frames * taper, axis=1))
    db = 20.0 * np.log10(spectrum + 1e-6)
    top = float(db.max())
    value = np.clip((db - (top - 60.0)) / 60.0, 0.0, 1.0)
    bins = min(value.shape[1], int(5000 / (clip.sample_rate / window)))
    value = value[:, :bins][::-1]
    # Three-stop heat ramp, readable on a dark evidence sheet.
    red = np.clip(value * 2.0 - 0.55, 0, 1)
    green = np.clip(value * 1.8 - 0.15, 0, 1)
    blue = np.clip(0.15 + value * 0.9, 0, 1) * np.clip(1.4 - value, 0, 1)
    rgb = np.stack([red, green, blue], axis=2)
    spec = Image.fromarray((rgb * 255).astype(np.uint8), mode="RGB")
    width = 960
    spec = spec.resize((width, 300), Image.Resampling.BILINEAR)

    sheet = Image.new("RGB", (width, 420), (10, 12, 18))
    draw = ImageDraw.Draw(sheet)
    # waveform strip
    mid = 70
    amplitude = 60
    peak = max(1e-6, float(np.abs(samples).max()))
    columns = np.array_split(samples, width)
    for x, column in enumerate(columns):
        if len(column) == 0:
            continue
        low = int(mid - amplitude * float(column.min()) / peak)
        high = int(mid - amplitude * float(column.max()) / peak)
        draw.line((x, low, x, high), fill=(80, 210, 220))
    draw.line((0, mid, width, mid), fill=(35, 45, 55))
    sheet.paste(spec, (0, 120))
    duration = max(1e-6, clip.duration())
    for index, mark in enumerate(marks):
        x = int(width * mark["start_s"] / duration)
        draw.line((x, 116, x, 420), fill=(255, 190, 70), width=1)
        label = mark["name"].replace("boss_", "").replace("_", " ").upper()
        draw.text((min(width - 80, x + 3), 84 if index % 2 else 100), label, fill=(230, 230, 240))
    draw.text((6, 4), "SHOOTER AUDIO CUES - WAVEFORM + 0-5 KHZ SPECTROGRAM", fill=(230, 230, 240))
    sheet.save(path)
    return {"width": width, "height": 420, "duration_s": round(clip.duration(), 3)}


def main(out_dir: str) -> dict:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    game = ShooterGame(profile_path=Path(tempfile.mkdtemp(prefix="shooter-audio-")) / "profile.json")
    game.build_scene()
    reports = {}
    for name in CUES:
        reports[name] = audio_report(game._clips[name])
    sequence, marks = _join([game._clips[name] for name in VISUAL_CUES])
    wav_path = target / "cues.wav"
    write_wav(wav_path, sequence)
    png_path = target / "cues_spectrogram.png"
    image_info = _spectrogram(sequence, png_path, marks)
    payload = {
        "cues": reports,
        "sequence": {"duration_s": round(sequence.duration(), 3), "marks": marks},
        "wav": str(wav_path),
        "spectrogram": {"path": str(png_path), **image_info},
    }
    (target / "audio_probe.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(
        "audio cues=%d sequence_s=%.2f wav=%s spectrogram=%s"
        % (len(reports), sequence.duration(), wav_path.name, png_path.name)
    )
    for name in ("boss_windup", "boss_slam", "boss_down", "overdrive", "pickup"):
        r = reports[name]
        print(f"  {name}: {r['duration']}s peak={r['peak']} rms={r['rms']}")
    return payload


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "audio_probe")
