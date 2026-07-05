from __future__ import annotations

import json
from pathlib import Path

from qbsearch.config import load_settings, settings_path


def test_settings_use_local_app_data(monkeypatch, tmp_path: Path) -> None:
    local = tmp_path / "local"
    monkeypatch.setenv("LOCALAPPDATA", str(local))

    assert settings_path() == local / "qbsearch" / "settings.json"


def test_roaming_settings_are_migrated(monkeypatch, tmp_path: Path) -> None:
    local = tmp_path / "local"
    roaming = tmp_path / "roaming"
    legacy = roaming / "qbSearch" / "settings.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text(json.dumps({"host": "legacy-host", "port": 9090}), encoding="utf-8")
    monkeypatch.setenv("LOCALAPPDATA", str(local))
    monkeypatch.setenv("APPDATA", str(roaming))

    settings = load_settings()

    assert settings.host == "legacy-host"
    assert settings.port == 9090
    assert json.loads(settings_path().read_text(encoding="utf-8"))["host"] == "legacy-host"
