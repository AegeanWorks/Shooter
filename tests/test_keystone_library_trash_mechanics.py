"""Keystone mechanics testbed: library soft delete and restore.

Deletes scenes and prefabs through their real libraries, checks the unique
trash naming, dotted entry names, suffix isolation and the refusal paths
(blank/path names, missing entries, wrong suffix, live collision).
"""

import pytest
from pathlib import Path

from keystone.library_trash import trash_entries
from keystone.prefab import Prefab
from keystone.prefab_library import PrefabLibrary
from keystone.scene import Node, Scene
from keystone.scene_library import SceneLibrary


def _scene(*names):
    scene = Scene()
    for name in names:
        scene.add(Node(name))
    return scene


def test_scene_library_delete_trash_and_restore(tmp_path):
    library = SceneLibrary(tmp_path / "scenes")
    library.save("arena", _scene("pad"))
    assert [entry.name for entry in library.entries()] == ["arena"]
    assert library.trash() == []

    path = library.delete("arena")
    assert path == library.path_for("arena")
    assert not path.exists()
    assert library.entries() == ()
    with pytest.raises(KeyError):
        library.load("arena")

    trash = library.trash()
    assert len(trash) == 1
    assert trash[0]["name"] == "arena"
    assert trash[0]["trash"].startswith("arena.")
    assert trash[0]["trash"].endswith(".kscene")
    assert Path(trash[0]["source"]).parent.name == ".trash"

    restored = library.restore(trash[0]["trash"])
    assert restored.name == "arena"
    assert [node.name for node in library.load("arena").traverse()] == ["", "pad"]
    assert library.trash() == []
    with pytest.raises(KeyError):
        library.delete("missing")


def test_prefab_library_delete_trash_and_restore(tmp_path):
    library = PrefabLibrary(tmp_path / "prefabs")
    prefab = Prefab.from_node(Node("pickup"), "pickup")
    library.save("pickup", prefab)
    assert [entry.name for entry in library.entries()] == ["pickup"]

    library.delete("pickup")
    assert not library.path_for("pickup").exists()
    trash = library.trash()
    assert len(trash) == 1
    assert trash[0]["name"] == "pickup"
    assert trash[0]["trash"].endswith(".kprefab")

    assert library.restore(trash[0]["trash"]).name == "pickup"
    assert library.load("pickup").node_count == 1
    assert library.trash() == []
    with pytest.raises(KeyError):
        library.delete("missing")


def test_trash_entries_are_unique_sorted_and_keep_dotted_names(tmp_path):
    library = SceneLibrary(tmp_path / "scenes")
    library.save("level.v2", _scene("pad"))
    library.delete("level.v2")
    library.save("level.v2", _scene("pad"))
    library.delete("level.v2")

    trash = library.trash()
    assert len(trash) == 2
    assert {item["name"] for item in trash} == {"level.v2"}
    names = [item["trash"] for item in trash]
    assert len(set(names)) == 2
    assert names == sorted(names)
    assert all(
        name.startswith("level.v2.") and name.endswith(".kscene")
        for name in names
    )
    assert trash_entries(tmp_path / "missing", ".kscene") == []


def test_restore_rejects_paths_wrong_suffix_and_collisions(tmp_path):
    directory = tmp_path / "scenes"
    library = SceneLibrary(directory)
    library.save("arena", _scene("old"))
    library.delete("arena")
    trash_name = library.trash()[0]["trash"]

    with pytest.raises(ValueError):
        library.restore("")
    with pytest.raises(ValueError):
        library.restore(f"../{trash_name}")
    with pytest.raises(KeyError):
        library.restore("missing.kscene")
    (directory / ".trash" / "legacy.kprefab").write_text(
        "{}", encoding="utf-8"
    )
    with pytest.raises(ValueError):
        library.restore("legacy.kprefab")

    library.save("arena", _scene("new"))
    with pytest.raises(FileExistsError):
        library.restore(trash_name)
    assert [node.name for node in library.load("arena").traverse()] == ["", "new"]
    assert len(library.trash()) == 1


def test_scene_and_prefab_trash_are_isolated_by_suffix(tmp_path):
    scenes = SceneLibrary(tmp_path / "library")
    prefabs = PrefabLibrary(tmp_path / "library")
    scenes.save("arena", _scene("pad"))
    prefabs.save("pickup", Prefab.from_node(Node("pickup"), "pickup"))
    scenes.delete("arena")
    prefabs.delete("pickup")

    assert [item["name"] for item in scenes.trash()] == ["arena"]
    assert [item["name"] for item in prefabs.trash()] == ["pickup"]

    scenes.restore(scenes.trash()[0]["trash"])
    prefabs.restore(prefabs.trash()[0]["trash"])
    assert [entry.name for entry in scenes.entries()] == ["arena"]
    assert [entry.name for entry in prefabs.entries()] == ["pickup"]
    assert scenes.trash() == [] and prefabs.trash() == []
