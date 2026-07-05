"""Persistent settings and encrypted credential storage."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
from pathlib import Path
from typing import Any

APP_DIR = Path(os.environ.get("SEEDRFETCH_HOME", str(Path.home() / ".seedrfetch")))
CONFIG_PATH = APP_DIR / "config.json"
LOG_DIR = APP_DIR / "logs"
CRASH_DIR = APP_DIR / "crashes"
LOG_PATH = LOG_DIR / "seedrfetch.log"
HTTP_LOG_PATH = LOG_DIR / "http.log"
TLS_LOG_PATH = LOG_DIR / "tls-events.log"
DEFAULTS: dict[str, Any] = {
    "download_destination": str(Path.home() / "Downloads"),
    "custom_ca_bundle": "",
    "http_proxy": "",
    "https_proxy": "",
    "disable_ssl_verify": False,
    "onboarded": False,
}


class Config:
    def __init__(self) -> None:
        self.existed = CONFIG_PATH.exists()
        self.data = dict(DEFAULTS)
        self.load()

    def load(self) -> None:
        if CONFIG_PATH.exists():
            try:
                loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    self.data.update(loaded)
            except (OSError, ValueError):
                pass

    def save(self) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        try:
            os.chmod(CONFIG_PATH, 0o600)
        except OSError:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()

    def delete(self, *keys: str) -> None:
        for key in keys:
            self.data.pop(key, None)
        self.save()

    def _fernet(self):
        from cryptography.fernet import Fernet
        salt = self.data.get("install_salt")
        if not salt:
            salt = base64.urlsafe_b64encode(os.urandom(16)).decode("ascii")
            self.data["install_salt"] = salt
            self.save()
        material = f"{platform.node()}:{salt}:SeedrFetch".encode()
        key = base64.urlsafe_b64encode(hashlib.sha256(material).digest())
        return Fernet(key)

    def remember_credentials(self, email: str, password: str) -> None:
        encrypted = self._fernet().encrypt(password.encode()).decode("ascii")
        self.data.update({"auth_method": "rest", "email": email, "password_enc": encrypted})
        self.save()

    def credentials(self) -> tuple[str, str] | None:
        email, encrypted = self.get("email"), self.get("password_enc")
        if not email or not encrypted:
            return None
        try:
            return str(email), self._fernet().decrypt(encrypted.encode()).decode()
        except Exception:
            return None

    def sign_out(self) -> None:
        self.delete("auth_method", "email", "password_enc", "device_token")
