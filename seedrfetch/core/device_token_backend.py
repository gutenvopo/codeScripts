"""Device-code authentication adapter using seedrcc when available."""
from __future__ import annotations

from typing import Any

from core.backend import SeedrBackend
from core.rest_v1_backend import BASE, classify_link
from core.ssl_setup import make_session


class _BearerTokenAuth:
    def __init__(self, token: str) -> None:
        self.token = token

    def __call__(self, request):
        request.headers["Authorization"] = "Bearer %s" % self.token
        return request


class DeviceTokenBackend(SeedrBackend):
    def __init__(self, token: str | None = None, client: Any = None,
                 settings: dict[str, Any] | None = None) -> None:
        self.session = make_session(settings)
        self.token = token
        self.client = client or self._new_client(token)
        for attribute in ("session", "_session"):
            if hasattr(self.client, attribute):
                setattr(self.client, attribute, self.session)

    @staticmethod
    def _new_client(token: str | None):
        try:
            from seedrcc import Seedr
        except ImportError as exc:
            raise RuntimeError("Install seedrcc to use Device Code authentication.") from exc
        for kwargs in ({"token": token}, {"access_token": token}, {}):
            try:
                return Seedr(**{k: v for k, v in kwargs.items() if v})
            except TypeError:
                continue
        return Seedr()

    @classmethod
    def generate_code(cls) -> tuple["DeviceTokenBackend", dict[str, Any]]:
        backend = cls()
        for name in ("get_device_code", "device_code", "authorize_device"):
            method = getattr(backend.client, name, None)
            if callable(method):
                value = method()
                return backend, value if isinstance(value, dict) else {"code": str(value)}
        raise RuntimeError("This seedrcc version does not expose device-code authentication.")

    def poll_authorization(self) -> str | None:
        for name in ("poll_authorization", "authorize", "get_token"):
            method = getattr(self.client, name, None)
            if callable(method):
                value = method()
                if isinstance(value, dict):
                    token = value.get("access_token") or value.get("token")
                    self.token = token
                    return token
                self.token = str(value) if value else None
                return self.token
        return None

    def _call(self, names: tuple[str, ...], *args: Any, **kwargs: Any) -> Any:
        for name in names:
            method = getattr(self.client, name, None)
            if callable(method):
                value = method(*args, **kwargs)
                return value if isinstance(value, dict) else {"result": value}
        raise RuntimeError(f"Installed seedrcc lacks required operation: {names[0]}")

    def user_info(self) -> dict[str, Any]: return self._call(("user_info", "get_user"))
    def get_drive(self) -> dict[str, Any]: return self._call(("get_drive", "list_contents", "get_folder"))
    def get_folder(self, folder_id: int) -> dict[str, Any]: return self._call(("get_folder",), folder_id)
    def add_magnet(self, link: str) -> dict[str, Any]: return self._call(("add_magnet", "add_torrent"), link)
    def add_torrent_url(self, url: str) -> dict[str, Any]: return self._call(("add_torrent_url", "add_torrent"), url)
    def add_link(self, raw: str) -> dict[str, Any]:
        s = raw.strip()
        kind = classify_link(s)
        if kind == "magnet":
            return self.add_magnet(s)
        return self.add_torrent_url(s)
    def download_file_request(self, file_id: int) -> tuple[str, Any]:
        if not self.token:
            raise RuntimeError("Device-code download requires an access token.")
        return BASE + f"/file/{file_id}", _BearerTokenAuth(self.token)
    def download_folder_request(self, folder_id: int) -> tuple[str, Any]:
        if not self.token:
            raise RuntimeError("Device-code download requires an access token.")
        return BASE + f"/folder/{folder_id}/download", _BearerTokenAuth(self.token)
    def get_file_url(self, file_id: int) -> str: return str(self._call(("get_file_url", "download_file"), file_id).get("result", ""))
    def get_folder_zip_url(self, folder_id: int) -> str: return str(self._call(("get_folder_zip_url", "download_folder"), folder_id).get("result", ""))
    def delete_file(self, file_id: int) -> Any: return self._call(("delete_file",), file_id)
    def delete_folder(self, folder_id: int) -> Any: return self._call(("delete_folder",), folder_id)
    def delete_torrent(self, torrent_id: int) -> Any: return self._call(("delete_torrent",), torrent_id)


if __name__ == "__main__":
    print(DeviceTokenBackend().user_info())
