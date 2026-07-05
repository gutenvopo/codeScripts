"""User preference loading and saving for Student Data Extractor."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


APP_DIR = Path.home() / ".student_data_extractor"
CONFIG_PATH = APP_DIR / "config.json"
LOG_PATH = APP_DIR / "student_data_extractor.log"


@dataclass(slots=True)
class AppSettings:
    """Persistent application settings."""

    conflict_mode: str = "Skip"
    after_extraction: str = "Keep"
    recurse: bool = False
    include_root: bool = False
    theme: str = "System"


def ensure_app_dir() -> None:
    """Create the application data directory if needed."""

    APP_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> AppSettings:
    """Load settings from disk, falling back to defaults on errors."""

    ensure_app_dir()
    if not CONFIG_PATH.exists():
        return AppSettings()

    try:
        raw: dict[str, Any] = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logging.getLogger(__name__).warning("Could not load config: %s", exc)
        return AppSettings()

    defaults = asdict(AppSettings())
    defaults.update({key: value for key, value in raw.items() if key in defaults})
    return AppSettings(**defaults)


def save_settings(settings: AppSettings) -> None:
    """Persist settings to the user config file."""

    ensure_app_dir()
    CONFIG_PATH.write_text(
        json.dumps(asdict(settings), indent=2),
        encoding="utf-8",
    )
