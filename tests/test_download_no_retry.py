from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "seedrfetch"))

from core.downloader import Downloader


class Backend:
    def download_file_request(self, _file_id: int) -> tuple[str, None]:
        return "https://www.seedr.cc/rest/file/7", None

    def download_folder_request(self, _folder_id: int) -> tuple[str, None]:
        return "https://www.seedr.cc/rest/folder/7/download", None


class Response:
    def __init__(self, status_code: int, chunks: list[bytes] | None = None) -> None:
        self.status_code = status_code
        self.chunks = chunks or []
        self.headers = {"Content-Length": str(sum(len(chunk) for chunk in self.chunks))}
        self.url = "https://nw33.seedr.cc/ff_get_premium/file?st=expired"

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError("HTTP %d" % self.status_code, response=self)

    def iter_content(self, _chunk_size: int):
        yield from self.chunks

    def json(self) -> dict[str, Any]:
        return {}


class NoRetrySession:
    def __init__(self) -> None:
        self.calls = 0
        self.headers = {}
        self.auth = None

    def mount(self, *_args) -> None:
        return None

    def get(self, *_args, **_kwargs):
        self.calls += 1
        if self.calls == 1:
            return Response(404)
        return Response(200, [b"should-not-be-used"])

    def close(self) -> None:
        return None


def wait_for_job(downloader: Downloader, job_id: str, *states: str):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        job = downloader.get(job_id)
        if job and job.state in states:
            return job
        time.sleep(0.01)
    raise AssertionError("job did not reach %s" % (states,))


def test_seedr_cdn_404_is_not_retried_and_reports_expired_link(tmp_path: Path) -> None:
    session = NoRetrySession()
    downloader = Downloader(Backend(), lambda: session, max_workers=1)

    job_id = downloader.submit_file(7, "movie.mkv", tmp_path, "movie.mkv")
    job = wait_for_job(downloader, job_id, "failed")

    assert session.calls == 1
    assert "Download link expired" in job.error
    assert not (tmp_path / "movie.mkv").exists()
