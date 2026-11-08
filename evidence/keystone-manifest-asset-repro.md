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
above). A regression test could assert:

```python
context = ...  # manifest with a PNG asset
report = validate_project(context, load_project_game(context))
assert report["ok"] is True, report["errors"]
```

## Testbed evidence

- `projects/shooter/tests/test_keystone_project_export_mechanics.py`:
  `test_manifest_asset_validation_after_load_game_duplicates` is a strict
  xfail that calls the minimal path above.
- The export-bundle test deliberately uses an unlisted asset so the passing
  export path stays covered.
- Reproducer exits 1 while the defect exists and 0 after a fix.
