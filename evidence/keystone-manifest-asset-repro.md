# Keystone defect: `validate_project` re-imports manifest assets

**Status**: reproducible on keystone `c31f935` (shooter testbed `c2de9fa`).
**Area**: project validation / export.
**Impact**: `export_project` rejects any project whose `keystone.json` lists an
asset (PNG/OBJ/prefab); a game with manifest assets cannot be exported.

## Minimal reproducer

```powershell
python projects/shooter/scripts/keystone_manifest_asset_repro.py
```

The script scaffolds a temp project, adds `assets/swatch.png`, saves it in the
manifest, loads the game, then calls `validate_project`.

Expected:

```json
{"ok": true, "errors": []}
```

Actual:

```json
{
  "ok": false,
  "errors": [
    {
      "kind": "assets",
      "message": "ValueError: asset 'project:assets/swatch.png' is already registered; pass replace=True to replace it"
    }
  ]
}
```

## Root cause

`load_project_game(context)` calls `attach_project_assets`, which registers the
manifest assets in `game.assets`. `validate_project(context, game)` then:

1. copies the game assets into a fresh registry with `replace=True`, then
2. calls `import_project_assets(context, registry)`, which registers the same
   `project:assets/...` IDs again without `replace=True`.

The second registration raises. `validate_project` catches it as an `assets`
error, so `ok` is false; `export_project` turns any reported error into a
validation failure and refuses to build the bundle.

## Suggested fix

In `validate_project`, either skip manifest asset IDs already present in the
registry, or register them with `replace=True` (matching the game-asset copy
above). The smallest change is in `import_project_assets`:

```python
# keystone/keystone/project.py, import_project_assets
records[identifier] = registry.register_file(
    identifier,
    target,
    kind=kind,
    component_types=component_types if kind == "prefab" else None,
    replace=True,
)
```

`replace=True` keeps the existing `attach_project_assets` refresh behaviour and
lets validation overwrite the temporary copies it makes of `game.assets`.
Skipping instead is also correct, but would leave the temporary copy rather
than the project file as the validated payload.

A regression test could assert:

```python
context = ...  # manifest with a PNG asset
report = validate_project(context, load_project_game(context))
assert report["ok"] is True, report["errors"]
```

## Upstream issue draft

**Title**: `validate_project` rejects manifest assets after `load_project_game`

**Environment**: keystone `c31f935`, Python 3.12, Windows 11.

**Steps**:

1. `create_project` a temp project and add `assets/swatch.png`.
2. Save a manifest whose `assets` lists `assets/swatch.png`.
3. `context = load_project(root)`; `game = load_project_game(context)`.
4. `validate_project(context, game)`.

**Expected**: `{"ok": true, "errors": []}`.
**Actual**: `ok` is false with
`"asset 'project:assets/swatch.png' is already registered; pass replace=True to replace it"`.
**Impact**: `export_project` calls the same pair, so any project with a
manifest asset cannot be exported.

**Fix**: pass `replace=True` in `import_project_assets`, or skip IDs already
in the registry. Add the regression test above.

This report is the upstream handoff while no issue-tracker credentials or push
authorization are available in the testbed environment; the reproducer and
tests are committed here so the fix can be verified locally.

## Testbed evidence

- `projects/shooter/tests/test_keystone_project_export_mechanics.py`:
  `test_manifest_asset_validation_after_load_game_duplicates` fails as
  expected while the defect exists and passes automatically after a fix.
- `test_cli_export_with_manifest_asset_self_clears` covers the CLI path and
  self-clears the same way.
- `test_cli_validate_project_reports_clean_and_broken_content` and
  `test_cli_export_builds_bundle_and_refuses_non_empty_target` cover the
  unaffected `--validate-project`/`--export` CLI branches.
- The export-bundle test deliberately uses an unlisted asset so the passing
  export path stays covered.
- Reproducer exits 1 while the defect exists and 0 after a fix.

