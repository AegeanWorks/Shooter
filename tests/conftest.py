import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
KEYSTONE = ROOT.parent / "keystone"
for candidate in (str(ROOT), str(KEYSTONE)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)


@pytest.fixture(autouse=True)
def _isolate_default_profile(tmp_path, monkeypatch):
    """Never let the suite read or write the player's real save file."""
    import shooter.profile as profile_module

    monkeypatch.setattr(profile_module, "DEFAULT_PATH", tmp_path / "profile.json")
