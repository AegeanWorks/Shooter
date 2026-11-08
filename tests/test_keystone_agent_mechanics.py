"""Keystone mechanics testbed: AI actions, observations and audit trails.

Covers LLM-style action JSON validation and clamping, deterministic
observations with random-state restoration, report summaries, and the
hash-chained append-only audit trail in memory and on disk.
"""

import json
import random

import pytest

from keystone.agents import AuditTrail, observe, parse_actions, summarize_report
from keystone.analysis import analyze_frame
from keystone.geometry import Material
from keystone.input import ActionState
from keystone.math3d import Vec3
from keystone.primitives import cube
from keystone.replay import stable_hash
from keystone.scene import Node, Scene, Transform

from shooter.game import ShooterGame


def test_parse_actions_clamps_axes_and_accepts_wrappers():
    actions = parse_actions(
        [
            {
                "forward": 5,
                "right": -9,
                "up": 0.5,
                "look_yaw": -2,
                "look_pitch": 2,
                "pressed": ["jump"],
                "held": ["fire"],
                "pointer": [1, 2],
                "mouse_clicked": True,
            }
        ]
    )
    assert len(actions) == 1
    action = actions[0]
    assert action.forward == 1.0
    assert action.right == -1.0
    assert action.up == 0.5
    assert action.look_yaw == -1.0
    assert action.look_pitch == 1.0
    assert action.pressed == frozenset({"jump"})
    assert action.held == frozenset({"fire"})
    assert action.pointer == (1.0, 2.0)
    assert action.mouse_clicked is True

    assert parse_actions({"actions": [{"up": 2}]})[0].up == 1.0
    assert parse_actions({"frames": [{"look_yaw": -2}]})[0].look_yaw == -1.0

    with pytest.raises(ValueError, match="at least one"):
        parse_actions([])
    with pytest.raises(TypeError):
        parse_actions({"actions": {"bad": 1}})
    with pytest.raises(TypeError):
        parse_actions([1])
    with pytest.raises(ValueError, match="unknown keys"):
        parse_actions([{"bogus": 1}])
    with pytest.raises(ValueError, match="must be numeric"):
        parse_actions([{"forward": "fast"}])
    with pytest.raises(ValueError, match="must be finite"):
        parse_actions([{"forward": float("nan")}])


def test_observe_is_deterministic_and_auditable():
    before = random.getstate()
    first = observe(
        ShooterGame(), frames=4, actions=[ActionState(forward=1.0)]
    )
    assert random.getstate() == before
    second = observe(
        ShooterGame(), frames=4, actions=[ActionState(forward=1.0)]
    )
    assert first["schema"] == 1
    assert first["game"] == "shooter"
    assert first["hash"] == second["hash"]
    assert first["description"]["capabilities"]["agents"] is True
    assert "fire" in first["description"]["actions"]["buttons"]
    simulation = first["simulation"]
    assert simulation["frames"] == 4
    assert len(simulation["actions"]) == 4
    assert simulation["actions"][0]["forward"] == 1.0
    assert first["hash"] == stable_hash(
        {
            "game": first["game"],
            "actions": simulation["actions"],
            "final": simulation["final"],
        }
    )

    with pytest.raises(ValueError, match="positive"):
        observe(ShooterGame(), frames=0)

    class Bare:
        pass

    with pytest.raises(TypeError, match="build_scene"):
        observe(Bare())


def test_summarize_report_truncates_and_keeps_material():
    scene = Scene()
    for index in range(4):
        scene.add(
            Node(
                f"n{index}",
                transform=Transform(position=Vec3(index, 0.0, -5.0)),
                mesh=cube(1.0),
                material=Material(color=Vec3(1.0, 0.0, 0.0)),
            )
        )
    report = analyze_frame(scene, bytes((0, 0, 0, 255)) * 16, 4, 4)
    summary = summarize_report(report, max_nodes=2)
    assert summary["schema"] == 1
    assert summary["truncated"] is True
    assert summary["node_count"] == 5
    assert len(summary["nodes"]) == 2
    assert summary["hash"] == report["hash"]
    assert summary["image_sha"] == report["image"]["rgba_sha256"]
    assert summary["mean_luma"] == report["stats"]["mean_luma"]
    assert summary["content_ratio"] == report["stats"]["content_ratio"]
    assert summary["ui"] is None
    materials = [node["material"] for node in summary["nodes"] if node["material"]]
    assert materials == [
        {"color": [1.0, 0.0, 0.0], "metallic": 0.0, "roughness": 0.7}
    ]
    assert all(node["id"] and node["world"] for node in summary["nodes"])

    full = summarize_report(report)
    assert full["truncated"] is False
    assert len(full["nodes"]) == 5

    with pytest.raises(TypeError):
        summarize_report({})


def test_audit_trail_chains_and_detects_tampering():
    trail = AuditTrail()
    first = trail.record("simulate", {"frames": 4})
    second = trail.record("render", {"nodes": 6})
    assert first["index"] == 0
    assert first["previous"] == "genesis"
    assert first["hash"] == stable_hash(
        {"previous": "genesis", "kind": "simulate", "payload": {"frames": 4}}
    )
    assert second["index"] == 1
    assert second["previous"] == first["hash"]
    assert trail.verify() is True

    trail.entries[0]["payload"] = {"frames": 999}
    assert trail.verify() is False

    broken = AuditTrail()
    broken.record("a", {"x": 1})
    broken.record("b", {"x": 2})
    broken.entries[1]["previous"] = "wrong"
    assert broken.verify() is False
    broken.entries[1]["previous"] = broken.entries[0]["hash"]
    broken.entries[1]["index"] = 7
    assert broken.verify() is False

    with pytest.raises(ValueError, match="kind"):
        trail.record(" ", {})
    with pytest.raises(TypeError, match="payload"):
        trail.record("simulate", [])


def test_audit_trail_persists_reloads_and_rejects_bad_documents(tmp_path):
    path = tmp_path / "audit.json"
    trail = AuditTrail(path)
    trail.record("simulate", {"frames": 4})
    trail.record("render", {"nodes": 6})
    assert path.is_file()
    assert not path.with_name("audit.json.bak").exists()
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["schema"] == 1
    assert [entry["kind"] for entry in document["entries"]] == [
        "simulate",
        "render",
    ]

    reloaded = AuditTrail(path)
    assert len(reloaded.entries) == 2
    assert reloaded.verify() is True
    reloaded.entries.pop()
    assert reloaded.verify() is False

    appended = AuditTrail(path)
    third = appended.record("analyze", {"nodes": 2})
    assert third["index"] == 2
    assert third["previous"] == appended.entries[1]["hash"]
    assert appended.verify() is True

    for bad in (
        {"schema": 0, "entries": []},
        {"schema": 1, "entries": {}},
        {"schema": 1, "entries": [1]},
        [],
    ):
        path.write_text(json.dumps(bad), encoding="utf-8")
        with pytest.raises(ValueError):
            AuditTrail(path)
