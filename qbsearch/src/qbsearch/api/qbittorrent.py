from __future__ import annotations

import logging
from typing import Any

import requests

log = logging.getLogger(__name__)


class QbtError(RuntimeError):
    """User-facing qBittorrent API error."""


class QbtAuthError(QbtError):
    """Raised when qBittorrent asks the user to log in again."""


class QbtClient:
    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self.base_url = "http://localhost:8080"

    def close(self) -> None:
        self.session.close()

    def login(self, host: str, port: int, username: str, password: str) -> None:
        self.base_url = self._build_base_url(host, port)
        response = self._request(
            "POST",
            "/api/v2/auth/login",
            data={"username": username, "password": password},
        )
        if response.text.strip() != "Ok.":
            raise QbtAuthError("qBittorrent rejected the username or password.")

    def list_plugins(self) -> list[dict[str, Any]]:
        return self._json("GET", "/api/v2/search/plugins")

    def start_search(self, pattern: str, plugins: str, category: str = "all") -> int:
        response = self._json(
            "POST",
            "/api/v2/search/start",
            data={"pattern": pattern, "plugins": plugins, "category": category},
        )
        search_id = response.get("id")
        if not isinstance(search_id, int):
            raise QbtError("qBittorrent did not return a search id.")
        return search_id

    def search_status(self, search_id: int) -> list[dict[str, Any]]:
        return self._json("GET", "/api/v2/search/status", params={"id": search_id})

    def search_results(
        self, search_id: int, limit: int = 0, offset: int = 0
    ) -> list[dict[str, Any]]:
        response = self._json(
            "GET",
            "/api/v2/search/results",
            params={"id": search_id, "limit": limit, "offset": offset},
        )
        results = response.get("results", [])
        if not isinstance(results, list):
            raise QbtError("qBittorrent returned malformed search results.")
        return results

    def stop_search(self, search_id: int) -> None:
        self._request("POST", "/api/v2/search/stop", data={"id": search_id})

    def delete_search(self, search_id: int) -> None:
        self._request("POST", "/api/v2/search/delete", data={"id": search_id})

    def add_torrent(
        self,
        url_or_magnet: str,
        savepath: str | None = None,
        category: str | None = None,
        paused: bool = False,
    ) -> None:
        fields: dict[str, tuple[None, str]] = {"urls": (None, url_or_magnet)}
        if savepath:
            fields["savepath"] = (None, savepath)
        if category:
            fields["category"] = (None, category)
        fields["paused"] = (None, "true" if paused else "false")
        self._request("POST", "/api/v2/torrents/add", files=fields)

    def _json(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self._request(method, path, **kwargs)
        try:
            return response.json()
        except ValueError as exc:
            raise QbtError("qBittorrent returned a non-JSON response.") from exc

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(method, url, timeout=20, **kwargs)
        except requests.RequestException as exc:
            log.warning("qBittorrent request failed: %s", exc)
            raise QbtError(f"Could not reach qBittorrent: {exc}") from exc
        if response.status_code == 403:
            raise QbtAuthError("qBittorrent session expired. Please log in again.")
        if response.status_code >= 400:
            detail = response.text.strip() or response.reason
            raise QbtError(f"qBittorrent returned HTTP {response.status_code}: {detail}")
        return response

    @staticmethod
    def _build_base_url(host: str, port: int) -> str:
        value = host.strip().rstrip("/")
        if value.startswith(("http://", "https://")):
            tail = value.rsplit("/", 1)[-1]
            return value if ":" in tail else f"{value}:{port}"
        return f"http://{value}:{port}"
