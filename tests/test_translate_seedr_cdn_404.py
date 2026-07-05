from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "seedrfetch"))

from core.errors import translate


class Response:
    status_code = 404
    url = "https://nw33.seedr.cc/ff_get_premium/file?st=expired"

    def json(self) -> dict[str, Any]:
        return {}


def test_seedr_cdn_404_translates_to_download_link_expired() -> None:
    error = requests.HTTPError("HTTP 404", response=Response())

    user_error = translate(error, corr_id="abc123")

    assert user_error.title == "Download link expired"
    assert "expired before the file could be fetched" in user_error.detail
    assert user_error.corr_id == "abc123"
