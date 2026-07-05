from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from qbsearch.api.qbittorrent import QbtAuthError, QbtClient


@dataclass
class FakeResponse:
    status_code: int = 200
    text: str = "Ok."
    reason: str = "OK"
    payload: Any = None

    def json(self) -> Any:
        return self.payload


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def request(self, method: str, url: str, timeout: int, **kwargs: Any) -> FakeResponse:
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)

    def close(self) -> None:
        pass


def test_login_posts_credentials() -> None:
    session = FakeSession([FakeResponse()])
    client = QbtClient(session=session)  # type: ignore[arg-type]
    client.login("localhost", 8080, "admin", "secret")
    method, url, kwargs = session.calls[0]
    assert method == "POST"
    assert url == "http://localhost:8080/api/v2/auth/login"
    assert kwargs["data"]["username"] == "admin"


def test_start_search_returns_id() -> None:
    session = FakeSession([FakeResponse(payload={"id": 42})])
    client = QbtClient(session=session)  # type: ignore[arg-type]
    assert client.start_search("ubuntu", "enabled") == 42


def test_403_raises_auth_error() -> None:
    session = FakeSession([FakeResponse(status_code=403, text="Forbidden", reason="Forbidden")])
    client = QbtClient(session=session)  # type: ignore[arg-type]
    with pytest.raises(QbtAuthError):
        client.list_plugins()
