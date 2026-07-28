from __future__ import annotations

import logging
from dataclasses import dataclass, field

import requests

from qbsearch.core.magnet_resolver import MagnetResolver, extract_magnet


def test_extract_magnet_single_match() -> None:
    html = '<a href="magnet:?xt=urn:btih:ABC123&dn=Ubuntu">Magnet</a>'
    assert extract_magnet(html) == "magnet:?xt=urn:btih:ABC123&dn=Ubuntu"


def test_extract_magnet_prefers_closest_name_match() -> None:
    html = """
    <a href="magnet:?xt=urn:btih:AAA111&dn=Some+Other+Movie">A</a>
    <a href="magnet:?xt=urn:btih:BBB222&dn=Ubuntu+Desktop+24.04">B</a>
    """
    assert (
        extract_magnet(html, "Ubuntu Desktop 24.04")
        == "magnet:?xt=urn:btih:BBB222&dn=Ubuntu+Desktop+24.04"
    )


def test_extract_magnet_unescapes_html_entities() -> None:
    html = '<a href="magnet:?xt=urn:btih:ABC123&amp;dn=Ubuntu">Magnet</a>'
    assert extract_magnet(html) == "magnet:?xt=urn:btih:ABC123&dn=Ubuntu"


def test_extract_magnet_returns_none_when_missing() -> None:
    assert extract_magnet("<html>No magnet here</html>") is None


@dataclass
class FakeResponse:
    status_code: int
    text: str
    reason: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)


class FakeSession:
    def __init__(self, response: FakeResponse | requests.RequestException) -> None:
        self.response = response
        self.headers: dict[str, str] = {}

    def get(self, url: str, timeout: int, allow_redirects: bool) -> FakeResponse:
        if isinstance(self.response, requests.RequestException):
            raise self.response
        return self.response


def test_resolve_detail_logs_http_failure_code(caplog) -> None:
    url = "https://example.test/item/123"
    response = FakeResponse(
        status_code=503,
        text="Temporarily unavailable",
        reason="Service Unavailable",
        url=url,
    )
    resolver = MagnetResolver(session=FakeSession(response))  # type: ignore[arg-type]
    resolver.in_flight.add(url)

    with caplog.at_level(logging.DEBUG, logger="qbsearch.core.magnet_resolver"):
        assert resolver.resolve_detail(url, "Example") is None

    assert "HTTP 503 Service Unavailable" in caplog.text
    assert "Cannot scan this page" in caplog.text
    assert url not in resolver.in_flight


def test_resolve_detail_logs_steps_without_query_secrets(caplog) -> None:
    url = "https://example.test/item/123?passkey=private-secret"
    response = FakeResponse(
        status_code=200,
        text='<a href="magnet:?xt=urn:btih:ABC123&dn=Example">Get</a>',
        reason="OK",
        url=url,
        headers={"Content-Type": "text/html"},
    )
    resolver = MagnetResolver(session=FakeSession(response))  # type: ignore[arg-type]

    with caplog.at_level(logging.DEBUG, logger="qbsearch.core.magnet_resolver"):
        magnet = resolver.resolve_detail(url, "Example")

    assert magnet == "magnet:?xt=urn:btih:ABC123&dn=Example"
    assert "Step 2/4" in caplog.text
    assert "Step 3/4" in caplog.text
    assert "Magnet found" in caplog.text
    assert "private-secret" not in caplog.text
    assert "?<query redacted>" in caplog.text


def test_resolve_detail_logs_network_exception_type(caplog) -> None:
    url = "https://example.test/item/123"
    resolver = MagnetResolver(  # type: ignore[arg-type]
        session=FakeSession(requests.Timeout("request timed out"))
    )
    resolver.in_flight.add(url)

    with caplog.at_level(logging.DEBUG, logger="qbsearch.core.magnet_resolver"):
        assert resolver.resolve_detail(url) is None

    assert "Timeout" in caplog.text
    assert "before an HTTP response was received" in caplog.text
    assert url not in resolver.in_flight
