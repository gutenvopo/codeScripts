from __future__ import annotations

from qbsearch.core.magnet_resolver import extract_magnet


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
