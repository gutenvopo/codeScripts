from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "seedrfetch"))

from core.rest_v1_backend import classify_link


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("magnet:?xt=urn:btih:abc", "magnet"),
        ("  magnet:?xt=urn:btih:abc  ", "magnet"),
        ("MAGNET:?xt=urn:btih:abc", "magnet"),
        ("https://example.com/file.torrent", "torrent_url"),
        ("https://tracker.example.com/download.php?id=123", "torrent_url"),
    ],
)
def test_classify_link_accepts_supported_links(raw: str, expected: str) -> None:
    assert classify_link(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "https://somesite.com/page",
        "ftp://example.com/file.torrent",
        "",
        "   ",
    ],
)
def test_classify_link_rejects_unsupported_links(raw: str) -> None:
    with pytest.raises(ValueError):
        classify_link(raw)
