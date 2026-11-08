"""Keystone mechanics testbed: typed component codecs and lifecycle.

Covers dataclass/custom to_dict components, node attach/remove,
scene-snapshot and prefab round trips with component_types, and the
codec's lifecycle fields under ComponentRuntime.
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from keystone.component_codec import (
    component_from_dict,
    component_to_dict,
    validate_component_types,
)
from keystone.lifecycle import ComponentRuntime
from keystone.prefab import Prefab
from keystone.scene import Node, Scene
from keystone.scene_snapshot import scene_from_dict, scene_to_dict


@dataclass
class Health:
    value: int = 0


class Counter:
    def __init__(self, value: int = 0) -> None:
        self.value = value

    def to_dict(self) -> dict:
        return {"value": self.value}

    @classmethod
    def from_dict(cls, data: dict) -> "Counter":
        return cls(int(data["value"]))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Counter) and other.value == self.value


@dataclass
class Ticker:
    ticks: int = 0
    started: int = 0
    stopped: int = 0

    def start(self, context) -> None:
        self.started += 1

    def update(self, context) -> None:
        self.ticks += 1

    def stop(self, context) -> None:
        self.stopped += 1


def test_component_codec_round_trips_dataclass_and_custom():
    health = Health(7)
    document = component_to_dict(health)
    assert document == {"type": "Health", "data": {"value": 7}}
    assert component_from_dict(document, {"Health": Health}) == health

    counter = Counter(9)
    document = component_to_dict(counter)
    assert document == {"type": "Counter", "data": {"value": 9}}
    assert component_from_dict(document, {"Counter": Counter}) == counter

    with pytest.raises(ValueError):
        component_from_dict(document, None)
    with pytest.raises(ValueError):
        component_from_dict({"type": "Missing", "data": {}}, {"Health": Health})
    with pytest.raises(ValueError):
        validate_component_types({"": Health})
    with pytest.raises(TypeError):
        validate_component_types({"Health": "not a type"})


def test_node_component_attach_require_remove():
    node = Node("probe", id="probe")
    health = node.add_component(Health(3))
    assert node.has_component(Health) is True
    assert node.get_component(Health) is health
    assert node.require_component(Health) is health
    assert node.remove_component(Health) is health
    assert node.has_component(Health) is False
    with pytest.raises(KeyError):
        node.require_component(Health)
    with pytest.raises(TypeError):
        node.add_component(None)


def test_scene_snapshot_components_round_trip():
    scene = Scene()
    node = Node("probe", id="probe")
    node.add_component(Health(5))
    node.add_component(Counter(9))
    scene.add(node)

    document = scene_to_dict(scene)
    raw = next(item for item in document["nodes"] if item["id"] == "probe")
    components = {item["type"]: item["data"] for item in raw["components"]}
    assert components == {"Health": {"value": 5}, "Counter": {"value": 9}}

    loaded = scene_from_dict(
        document, component_types={"Health": Health, "Counter": Counter}
    )
    loaded_node = loaded.find_by_id("probe")
    assert loaded_node is not None
    assert loaded_node.require_component(Health) == Health(5)
    assert loaded_node.require_component(Counter) == Counter(9)

    with pytest.raises(ValueError):
        scene_from_dict(document)
    with pytest.raises(ValueError):
        scene_from_dict(document, component_types={"Health": Health})


def test_prefab_components_round_trip():
    root = Node("probe", id="probe")
    root.add_component(Health(4))
    root.add_component(Counter(2))
    prefab = Prefab.from_node(root, name="component_probe")
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "probe.kprefab"
        prefab.save(path)
        loaded = Prefab.load(
            path, component_types={"Health": Health, "Counter": Counter}
        )
        scene = Scene()
        roots = loaded.instantiate(scene, instance="p")
        node = scene.find_by_id("p:probe")
        assert node is not None
        assert node.require_component(Health) == Health(4)
        assert node.require_component(Counter) == Counter(2)
        assert roots[0] is node
        with pytest.raises(ValueError):
            Prefab.load(path)


def test_component_runtime_runs_a_codec_component():
    scene = Scene()
    node = Node("probe", id="probe")
    ticker = node.add_component(Ticker())
    scene.add(node)
    runtime = ComponentRuntime(scene)
    assert runtime.start() == 1
    assert ticker.started == 1
    assert runtime.update(1.0 / 60.0) == 1
    assert runtime.update(1.0 / 60.0) == 1
    assert ticker.ticks == 2
    assert runtime.stop() == 1
    assert ticker.stopped == 1

    document = component_to_dict(ticker)
    assert document["type"] == "Ticker"
    assert document["data"]["ticks"] == 2
    restored = component_from_dict(document, {"Ticker": Ticker})
    assert restored == Ticker(ticks=2, started=1, stopped=1)
