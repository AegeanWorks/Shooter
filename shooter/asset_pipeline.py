"""File-backed gameplay assets registered through Keystone's asset pipeline.

AssetRegistry.register_file infers the kind from the suffix, loads with
keystone.asset_io/obj_loader and fingerprints the source, so the registry's
refresh() can hot-reload a changed file without a restart.
"""

from __future__ import annotations

from pathlib import Path

from keystone.assets import AssetRegistry
from keystone.geometry import MeshData

CACHE_CRATE = "mesh.cache_crate"
CACHE_CRATE_FILE = "cache_crate.obj"


def register_cache_crate(
    assets: AssetRegistry, directory: str | Path, fallback: MeshData
) -> bool:
    """Register the cache crate from disk, or the fallback mesh when absent."""
    path = Path(directory) / CACHE_CRATE_FILE
    try:
        assets.register_file(CACHE_CRATE, path)
    except (OSError, TypeError, ValueError):
        assets.register(CACHE_CRATE, fallback)
        return False
    return True
