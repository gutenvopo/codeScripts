"""Seedr REST v1 email/password backend."""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from requests.auth import HTTPBasicAuth

from core.backend import SeedrBackend
from core.ssl_setup import make_session

BASE = "https://www.seedr.cc/rest"
_MAGNET_RE = re.compile(r"^\s*magnet:\?", re.IGNORECASE)


def classify_link(raw: str) -> str:
    """Return 'magnet' or 'torrent_url', or raise ValueError."""
    if not raw or not raw.strip():
        raise ValueError("Link is empty. Paste a magnet or .torrent URL.")
    s = raw.strip()
    if _MAGNET_RE.match(s):
        return "magnet"
    parsed = urlparse(s)
    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError(
            "Link must start with 'magnet:' or 'http(s)://'. "
            f"Got scheme: {parsed.scheme or '(none)'}"
        )
    path = parsed.path.lower()
    if path.endswith(".torrent") or "/download.php" in path or "/torrent/download" in path:
        return "torrent_url"
    raise ValueError(
        "Link doesn't look like a magnet link or a direct .torrent URL. "
        "On torrent sites, look for the magnet icon (a horseshoe magnet) "
        "and copy that link. Direct .torrent URLs end in .torrent."
    )


class RestV1Backend(SeedrBackend):
    def __init__(self, email: str, password: str, settings: dict[str, Any] | None = None) -> None:
        self.auth = HTTPBasicAuth(email, password)
        self.session = make_session(settings)

    def _request(self, method: str, path: str, **kwargs: Any):
        response = self.session.request(method, BASE + path, auth=self.auth,
                                        timeout=kwargs.pop("timeout", (10, 60)), **kwargs)
        response.raise_for_status()
        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError:
            return {"text": response.text}

    def user_info(self) -> dict[str, Any]: return self._request("GET", "/user")
    def get_drive(self) -> dict[str, Any]: return self._request("GET", "/folder")
    def get_folder(self, folder_id: int) -> dict[str, Any]: return self._request("GET", f"/folder/{folder_id}")
    def add_magnet(self, link: str) -> dict[str, Any]: return self._request("POST", "/torrent/magnet", data={"magnet": link})
    def add_torrent_url(self, url: str) -> dict[str, Any]: return self._request("POST", "/torrent/url", data={"torrent_url": url})
    def add_link(self, raw: str) -> dict[str, Any]:
        s = raw.strip()
        kind = classify_link(s)
        if kind == "magnet":
            return self.add_magnet(s)
        return self.add_torrent_url(s)

    def _redirect(self, path: str) -> str:
        response = self.session.get(BASE + path, auth=self.auth, timeout=(10, 60),
                                    allow_redirects=False)
        response.raise_for_status()
        return response.headers.get("Location", response.url)

    def download_file_request(self, file_id: int) -> tuple[str, Any]:
        return BASE + f"/file/{file_id}", self.auth

    def download_folder_request(self, folder_id: int) -> tuple[str, Any]:
        return BASE + f"/folder/{folder_id}/download", self.auth

    def get_file_url(self, file_id: int) -> str: return self._redirect(f"/file/{file_id}")
    def get_folder_zip_url(self, folder_id: int) -> str: return self._redirect(f"/folder/{folder_id}/download")
    def delete_file(self, file_id: int) -> Any: return self._request("DELETE", f"/file/{file_id}")
    def delete_folder(self, folder_id: int) -> Any: return self._request("DELETE", f"/folder/{folder_id}")
    def delete_torrent(self, torrent_id: int) -> Any: return self._request("DELETE", f"/torrent/{torrent_id}")


if __name__ == "__main__":
    import getpass
    print(RestV1Backend(input("Email: "), getpass.getpass()).user_info())
