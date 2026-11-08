"""Keystone mechanics testbed: versioned scene snapshots.

Covers node/transform/tag/parent round trips, camera/light/environment
settings, registry-backed assets, malformed snapshot validation and
in-place restore replacement semantics.
"""

import json

import pytest

from keystone.assets import AssetRegistry
from keystone.camera import MAX_PITCH
from keystone.geometry import Material
from keystone.math3d import Quat, Vec3
from keystone.primitives import cube
from keystone.scene import (
    BloomSettings,
    ColorSettings,
    CullingSettings,
    DirectionalLight,
    Node,
    PointLight,
    PostSettings,
    Scene,
    ShadowSettings,
    SpriteSettings,
    Transform,
)
from keystone.scene_snapshot import (
    SCENE_SNAPSHOT_VERSION,
    restore_scene,
    scene_from_dict,
    scene_to_dict,
)


def _source_scene():
    scene = Scene()
    scene.camera.position = Vec3(1.0, 2.0, 3.0)
    scene.camera.yaw = 0.5
    scene.camera.pitch = 0.75
    scene.camera.fov_y = 55.0
    scene.camera.near = 0.2
    scene.camera.far = 500.0
    scene.ambient = Vec3(0.1, 0.2, 0.3)
    scene.background = Vec3(0.01, 0.02, 0.03)
    scene.sky = Vec3(0.4, 0.5, 0.6)
    scene.fog_density = 0.05
    scene.light = DirectionalLight(
        direction=Vec3(0.0, -1.0, -1.0),
        color=Vec3(1.0, 0.9, 0.8),
        intensity=0.8,
    )
    scene.point_light = PointLight(
        position=Vec3(1.0, 2.0, 3.0),
        color=Vec3(0.5, 0.6, 0.7),
        intensity=2.0,
        radius=5.0,
    )
    scene.shadow = ShadowSettings(enabled=False)
    scene.color = ColorSettings(enabled=False)
    scene.post = PostSettings(enabled=False)
    scene.bloom = BloomSettings(enabled=False)
    scene.sprite = SpriteSettings(enabled=False)
    scene.culling = CullingSettings(enabled=False)
    scene.root.transform = Transform(position=Vec3(0.0, 0.0, 1.0))
    scene.root.visible = False
    parent = scene.add(Node("parent", id="parent", tags={"a"}, layer="gameplay"))
    child = Node("child", id="child", tags={"b"}, visible=False)
    child.transform = Transform(
        position=Vec3(1.0, 2.0, 3.0),
        rotation=Quat.from_axis_angle(Vec3.UP, 0.5),
        scale=Vec3(2.0, 2.0, 2.0),
    )
    parent.add_child(child)
    return scene


def test_scene_snapshot_round_trip_nodes_and_transforms():
    scene = _source_scene()
    data = scene_to_dict(scene)
    assert data["schema"] == SCENE_SNAPSHOT_VERSION == 6
    assert len(data["nodes"]) == 2
    assert json.loads(json.dumps(data)) == data

    by_name = {node["name"]: node for node in data["nodes"]}
    parent = by_name["parent"]
    child = by_name["child"]
    assert parent["id"] == "parent"
    assert parent["parent_id"] is None
    assert parent["tags"] == ["a"]
    assert parent["layer"] == "gameplay"
    assert parent["visible"] is True
    assert parent["transform"] == {
        "position": [0.0, 0.0, 0.0],
        "rotation": [0.0, 0.0, 0.0, 1.0],
        "scale": [1.0, 1.0, 1.0],
    }
    assert child["parent_id"] == "parent"
    assert child["tags"] == ["b"]
    assert child["visible"] is False
    assert child["transform"]["position"] == [1.0, 2.0, 3.0]
    assert child["transform"]["scale"] == [2.0, 2.0, 2.0]

    restored = scene_from_dict(data)
    assert restored.root.transform.position == Vec3(0.0, 0.0, 1.0)
    assert restored.root.visible is False
    assert restored.camera.position == Vec3(1.0, 2.0, 3.0)
    names = [node.name for node in restored.traverse()]
    assert names == ["", "parent", "child"]
    restored_parent = restored.find_by_id("parent")
    restored_child = restored.find_by_id("child")
    assert restored_child.parent is restored_parent
    assert restored_parent.tags == {"a"}
    assert restored_child.tags == {"b"}
    assert restored_child.layer == "default"
    assert restored_child.visible is False
    assert restored_child.transform.position == Vec3(1.0, 2.0, 3.0)
    assert restored_child.transform.scale == Vec3(2.0, 2.0, 2.0)
    rotation = restored_child.transform.rotation
    assert (rotation.w, rotation.x, rotation.y, rotation.z) == pytest.approx(
        (0.9689124, 0.0, 0.2474039, 0.0), abs=1e-6
    )
    assert scene_to_dict(restored) == data
    assert restored._next_id == data["next_id"]


def test_scene_snapshot_camera_environment_and_settings():
    data = scene_to_dict(_source_scene())
    restored = scene_from_dict(data)
    assert restored.camera.fov_y == 55.0
    assert restored.camera.near == 0.2
    assert restored.camera.far == 500.0
    assert restored.ambient == Vec3(0.1, 0.2, 0.3)
    assert restored.background == Vec3(0.01, 0.02, 0.03)
    assert restored.sky == Vec3(0.4, 0.5, 0.6)
    assert restored.fog_density == 0.05
    assert restored.light == DirectionalLight(
        direction=Vec3(0.0, -1.0, -1.0),
        color=Vec3(1.0, 0.9, 0.8),
        intensity=0.8,
    )
    assert restored.point_light == PointLight(
        position=Vec3(1.0, 2.0, 3.0),
        color=Vec3(0.5, 0.6, 0.7),
        intensity=2.0,
        radius=5.0,
    )
    assert restored.shadow.enabled is False
    assert restored.color.enabled is False
    assert restored.post.enabled is False
    assert restored.bloom.enabled is False
    assert restored.sprite.enabled is False
    assert restored.culling.enabled is False

    clamped = scene_from_dict(
        {"schema": 6, "nodes": [], "camera": {"pitch": 2.0}}
    )
    assert clamped.camera.pitch == MAX_PITCH

    with pytest.raises(ValueError, match="fog_density"):
        scene_from_dict(
            {"schema": 6, "nodes": [], "environment": {"fog_density": -1.0}}
        )
    with pytest.raises(ValueError, match="three values"):
        scene_from_dict(
            {"schema": 6, "nodes": [], "environment": {"ambient": [1.0, 2.0]}}
        )
    with pytest.raises(ValueError, match="finite"):
        scene_from_dict(
            {"schema": 6, "nodes": [], "camera": {"yaw": float("nan")}}
        )
    with pytest.raises(TypeError, match="shadow"):
        scene_from_dict(
            {"schema": 6, "nodes": [], "environment": {"shadow": 3}}
        )
    with pytest.raises(TypeError, match="camera"):
        scene_from_dict({"schema": 6, "nodes": [], "camera": []})


def test_scene_snapshot_assets_round_trip():
    mesh = cube(1.0)
    material = Material()
    registry = AssetRegistry()
    registry.register("mesh.cube", mesh, kind="mesh")
    registry.register("mat.gold", material, kind="material")
    scene = Scene()
    scene.add(
        Node("mesh-node", id="mesh-node", mesh=mesh, material=material)
    )
    data = scene_to_dict(scene, registry)
    entry = next(node for node in data["nodes"] if node["id"] == "mesh-node")
    assert entry["mesh"] == "mesh.cube"
    assert entry["material"] == "mat.gold"

    restored = scene_from_dict(data, registry)
    node = restored.find_by_id("mesh-node")
    assert node.mesh is mesh
    assert node.material is material

    plain = scene_from_dict(data)
    assert plain.find_by_id("mesh-node").mesh is None
    assert plain.find_by_id("mesh-node").material is None

    missing = json.loads(json.dumps(data))
    next(node for node in missing["nodes"] if node["id"] == "mesh-node")[
        "mesh"
    ] = "mesh.missing"
    assert scene_from_dict(missing, registry).find_by_id("mesh-node").mesh is None

    wrong_kind = json.loads(json.dumps(data))
    next(node for node in wrong_kind["nodes"] if node["id"] == "mesh-node")[
        "mesh"
    ] = "mat.gold"
    with pytest.raises(ValueError, match="not a mesh"):
        scene_from_dict(wrong_kind, registry)


def test_scene_snapshot_validation_errors():
    with pytest.raises(TypeError):
        scene_from_dict([])
    with pytest.raises(ValueError, match="unsupported"):
        scene_from_dict({"schema": 0, "nodes": []})
    with pytest.raises(ValueError, match="unsupported"):
        scene_from_dict({"schema": 7, "nodes": []})
    with pytest.raises(ValueError, match="nodes list"):
        scene_from_dict({"schema": 6})
    with pytest.raises(TypeError, match="nodes must be a list"):
        scene_from_dict({"schema": 6, "nodes": {}})
    with pytest.raises(ValueError, match="duplicate"):
        scene_from_dict(
            {"schema": 6, "nodes": [{"id": "a"}, {"id": "a"}]}
        )
    with pytest.raises(TypeError, match="node id"):
        scene_from_dict({"schema": 6, "nodes": [{}]})
    with pytest.raises(ValueError, match="non-blank"):
        scene_from_dict({"schema": 6, "nodes": [{"id": " "}]})
    with pytest.raises(ValueError, match="unknown parent"):
        scene_from_dict(
            {"schema": 6, "nodes": [{"id": "a", "parent_id": "missing"}]}
        )
    with pytest.raises(ValueError, match="own parent"):
        scene_from_dict(
            {"schema": 6, "nodes": [{"id": "a", "parent_id": "a"}]}
        )
    with pytest.raises(TypeError, match="parent_id"):
        scene_from_dict(
            {"schema": 6, "nodes": [{"id": "a", "parent_id": 3}]}
        )
    with pytest.raises(ValueError, match="three values"):
        scene_from_dict(
            {
                "schema": 6,
                "nodes": [{"id": "a", "transform": {"position": [1.0, 2.0]}}],
            }
        )
    with pytest.raises(TypeError, match="tags must be a list"):
        scene_from_dict({"schema": 6, "nodes": [{"id": "a", "tags": "x"}]})
    with pytest.raises(TypeError, match="visible"):
        scene_from_dict({"schema": 6, "nodes": [{"id": "a", "visible": 1}]})
    with pytest.raises(ValueError, match="layer"):
        scene_from_dict({"schema": 6, "nodes": [{"id": "a", "layer": ""}]})
    with pytest.raises(ValueError, match="next_id"):
        scene_from_dict({"schema": 6, "nodes": [], "next_id": 0})
    with pytest.raises(TypeError, match="root"):
        scene_from_dict({"schema": 6, "nodes": [], "root": []})


def test_restore_scene_replaces_contents_in_place():
    source = _source_scene()
    data = scene_to_dict(source)
    target = Scene()
    old = target.add(Node("old"))
    root_id = id(target.root)
    returned = restore_scene(target, data)
    assert returned is target
    assert id(target.root) == root_id
    assert old.parent is None
    assert [node.name for node in target.traverse()] == ["", "parent", "child"]
    assert target.camera.position == Vec3(1.0, 2.0, 3.0)
    assert target.culling.enabled is False
    assert target.root.visible is False
    assert target._next_id >= source._next_id
    assert target.add(Node("new")).id == "node-2"
    assert [node.name for node in source.traverse()] == ["", "parent", "child"]

    with pytest.raises(TypeError, match="Scene"):
        restore_scene(object(), data)
