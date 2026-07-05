from __future__ import annotations

import json
import os
from contextlib import suppress
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import keyring

SERVICE_NAME = "qbsearch"


def settings_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    path = Path(base) / "qbsearch"
    path.mkdir(parents=True, exist_ok=True)
    return path


def settings_path() -> Path:
    return settings_dir() / "settings.json"


def _legacy_settings_path() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return Path(base) / "qbSearch" / "settings.json"


@dataclass(slots=True)
class AppSettings:
    host: str = "localhost"
    port: int = 8080
    username: str = "admin"
    default_save_path: str = ""
    default_category: str = ""
    add_paused_by_default: bool = False
    theme: str = "Dark"
    geometry: str = ""

    @property
    def base_url(self) -> str:
        host = self.host.strip()
        if host.startswith(("http://", "https://")):
            return (
                f"{host.rstrip('/')}:{self.port}"
                if ":" not in host.rsplit("/", 1)[-1]
                else host.rstrip("/")
            )
        return f"http://{host}:{self.port}"

    @property
    def keyring_username(self) -> str:
        return f"{self.host}:{self.port}"


def load_settings() -> AppSettings:
    path = settings_path()
    source = path if path.exists() else _legacy_settings_path()
    if not source.exists():
        return AppSettings()
    try:
        text = source.read_text(encoding="utf-8")
        data = json.loads(text)
    except (OSError, json.JSONDecodeError):
        return AppSettings()
    if source != path:
        with suppress(OSError):
            path.write_text(text, encoding="utf-8")
    allowed = {field: data[field] for field in AppSettings.__dataclass_fields__ if field in data}
    return AppSettings(**allowed)


def save_settings(settings: AppSettings) -> None:
    data: dict[str, Any] = asdict(settings)
    settings_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_password(settings: AppSettings) -> str:
    return keyring.get_password(SERVICE_NAME, settings.keyring_username) or ""


def save_password(settings: AppSettings, password: str) -> None:
    if password:
        keyring.set_password(SERVICE_NAME, settings.keyring_username, password)
