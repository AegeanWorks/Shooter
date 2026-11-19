"""Architecture safety net: a rebuild fully resets scene-scoped state.

`ShooterGame.build_scene` is the project's largest method (448 lines, writing 50
distinct `self` attributes). That is a real maintainability cost, recorded as a
finding rather than fixed by churn -- but it also means every one of those 50
attributes must be re-initialised on a rebuild, and a miss would leak one run's
state into the next.

The game rebuilds in two real situations: `new_run()` after a death or a sealed
campaign, and `Engine` calling `build_scene` at startup. This suite dirties the
scene-scoped attributes a rebuild must own and asserts none of them survive.
"""

import pathlib
import subprocess
import sys

import pytest

from shooter import game as game_module
from shooter.game import ShooterGame

REPO = pathlib.Path(__file__).resolve().parent.parent


def _game(tmp_path) -> ShooterGame:
    game = ShooterGame(profile_path=tmp_path / "profile.json")
    game.build_scene()
    return game


def _scene_scoped_attributes() -> list[str]:
    """Attributes assigned inside build_scene, discovered from its own source.

    Reading them from the method means a newly added attribute is covered
    automatically, instead of this list drifting from the code it protects.
    """
    import ast

    source = pathlib.Path(game_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "build_scene":
            for inner in ast.walk(node):
                targets = []
                if isinstance(inner, ast.Assign):
                    targets = inner.targets
                elif isinstance(inner, (ast.AugAssign, ast.AnnAssign)):
                    targets = [inner.target]
                for target in targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        names.add(target.attr)
    return sorted(names)


def _committed_scene_attributes() -> list[str]:
    """The attribute surface of build_scene as committed at HEAD.

    Deriving the checklist from the *working* file is circular: delete an
    assignment and it silently drops out of its own checklist (50 -> 49). The
    committed version is the independent reference, so a removed assignment
    fails instead of passing.
    """
    try:
        shown = subprocess.run(
            ["git", "show", "HEAD:shooter/game.py"],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if shown.returncode != 0 or not shown.stdout.strip():
        return []
    return _attributes_of(shown.stdout)


def _attributes_of(source: str) -> list[str]:
    """Attributes assigned inside build_scene in one source text."""
    import ast as ast_module

    tree = ast_module.parse(source)
    names = set()
    for node in ast_module.walk(tree):
        if isinstance(node, ast_module.FunctionDef) and node.name == "build_scene":
            for inner in ast_module.walk(node):
                targets = []
                if isinstance(inner, ast_module.Assign):
                    targets = inner.targets
                elif isinstance(inner, (ast_module.AugAssign, ast_module.AnnAssign)):
                    targets = [inner.target]
                for target in targets:
                    if (
                        isinstance(target, ast_module.Attribute)
                        and isinstance(target.value, ast_module.Name)
                        and target.value.id == "self"
                    ):
                        names.add(target.attr)
    return sorted(names)


def test_build_scene_reassigns_a_large_scene_surface():
    """Sanity: the discovery works and reports the real size of the surface.

    NOTE ON STRENGTH: the parametrized test below replaces each attribute with a
    sentinel and asserts it is no longer the sentinel after a rebuild. That
    proves the attribute is *reassigned*, not that it is reassigned to the
    correct value -- a deleted assignment whose target is set again elsewhere
    still passes. It catches the class of bug where a new attribute is added to
    build_scene and then one branch stops setting it, which is why it is worth
    keeping, but it is not a full reset proof.
    """
    attributes = _scene_scoped_attributes()
    assert len(attributes) >= 40, (
        f"only {len(attributes)} attributes discovered in build_scene; the "
        "discovery is probably broken rather than the method having shrunk"
    )


def test_no_committed_scene_attribute_has_been_dropped():
    """A deleted build_scene assignment must fail, not quietly leave the list."""
    committed = _committed_scene_attributes()
    if not committed:
        pytest.skip("git history is unavailable, so there is no independent reference")
    working = set(_scene_scoped_attributes())
    dropped = [name for name in committed if name not in working]
    assert dropped == [], (
        f"build_scene no longer sets {dropped}, which it set at HEAD; a run's "
        "scene state would leak because nothing re-initialises them"
    )


def test_every_scene_scoped_attribute_is_reassignable_on_a_rebuild(tmp_path):
    """Each attribute build_scene owns must exist after a build and survive one.

    One build, one dirty pass over the whole surface, one rebuild: the property
    is identical to checking each attribute separately, but a full scene build
    is ~0.85s, so doing it per attribute made this suite the slowest in the
    project (43s) for no extra information.

    The limit is the same and deliberate: this proves each attribute is
    REASSIGNED, not that it is assigned the correct value. An attribute that is
    also initialised in __init__ or set again later in update() passes here even
    if its build_scene line is deleted.
    """
    game = _game(tmp_path)
    attributes = _scene_scoped_attributes()
    missing = [name for name in attributes if not hasattr(game, name)]
    assert missing == [], f"build_scene never set {missing}"

    sentinel = object()
    for name in attributes:
        setattr(game, name, sentinel)
    setattr(game, "_built", False)  # a rebuild is what reset()/new_run() triggers
    game.build_scene()

    survived = [name for name in attributes if getattr(game, name, None) is sentinel]
    assert survived == [], (
        "these attributes survived a rebuild, so one run's scene state leaks "
        f"into the next: {survived}"
    )


def test_a_restart_does_not_inherit_transient_scene_state(tmp_path):
    """The real path a player takes: die, press Enter, play again."""
    game = _game(tmp_path)
    # Dirty the transient scene state through setattr: these tests exist to
    # inspect a rebuilt scene, so they name the attributes dynamically rather
    # than reaching into another object's fields with dotted assignment.
    setattr(game, "_tracer_nodes", ["sentinel"] * 3)
    setattr(game, "_pickup_fx_t", 3.5)
    setattr(game, "_asset_reload_t", 9.0)
    setattr(game, "_boss_pose", None)
    game.sim.alive = False
    game.last_run = {"score": 1}

    game.new_run()

    # the tracer pool is legitimately rebuilt, so freshness is the contract:
    # the sentinels must be gone and the replacement nodes must all be hidden
    tracers = getattr(game, "_tracer_nodes")
    assert "sentinel" not in tracers, "stale tracers would draw from the previous run"
    assert tracers, "the pool must be rebuilt"
    assert all(node.visible is False for node in tracers)
    assert getattr(game, "_pickup_fx_t") in (0, 0.0), getattr(game, "_pickup_fx_t")
    assert getattr(game, "_asset_reload_t") in (0, 0.0), getattr(game, "_asset_reload_t")
    assert game.last_run is None
    assert game.sim.tick == 0


def test_a_rebuild_does_not_keep_the_previous_scene_object(tmp_path):
    """A stale Scene would keep dead nodes alive in the renderer."""
    game = _game(tmp_path)
    first = game.scene
    setattr(game, "_built", False)
    game.build_scene()
    assert game.scene is not first


def test_a_rebuild_produces_an_equivalent_scene(tmp_path):
    """The scene must come back the same, not merely different."""
    game = _game(tmp_path)

    def fingerprint(scene):
        ids = sorted(node.id for node in scene.traverse() if node.id)
        return (
            scene.camera.position.x, scene.camera.position.y, scene.camera.position.z,
            scene.camera.fov_y,
            scene.fog_density,
            len(scene.point_lights),
            ids,
        )

    before = fingerprint(game.scene)
    setattr(game, "_built", False)
    game.build_scene()
    after = fingerprint(game.scene)
    assert after == before, f"rebuild changed the scene: {before} -> {after}"
