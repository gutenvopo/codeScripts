from __future__ import annotations

import time
import sys
from pathlib import Path
from typing import Any

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "seedrfetch"))

from core.downloader import Downloader


class FakeBackend:
    def __init__(self, file_url: str = "https://www.seedr.cc/rest/file/1",
                 folder_url: str = "https://www.seedr.cc/rest/folder/1/download") -> None:
        self.file_url = file_url
        self.folder_url = folder_url
        self.file_ids: list[int] = []
        self.folder_ids: list[int] = []

    def download_file_request(self, file_id: int) -> tuple[str, None]:
        self.file_ids.append(file_id)
        return self.file_url, None

    def download_folder_request(self, folder_id: int) -> tuple[str, None]:
        self.folder_ids.append(folder_id)
        return self.folder_url, None


class FakeResponse:
    def __init__(self, chunks: list[bytes], status_code: int = 200,
                 headers: dict[str, str] | None = None, body: dict[str, Any] | None = None) -> None:
        self.chunks = chunks
        self.status_code = status_code
        self.headers = headers or {}
        self.body = body or {}
        self.reason = "OK"
        self.url = ""

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError("HTTP %d" % self.status_code, response=self)

    def iter_content(self, _chunk_size: int):
        for chunk in self.chunks:
            yield chunk

    def json(self) -> dict[str, Any]:
        return self.body


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.requests: list[dict[str, Any]] = []

    def get(self, url: str, **kwargs):
        self.response.url = url
        self.requests.append({"url": url, **kwargs})
        return self.response


def wait_for_job(downloader: Downloader, job_id: str, *states: str):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        job = downloader.get(job_id)
        if job and job.state in states:
            return job
        time.sleep(0.01)
    raise AssertionError("job did not reach %s" % (states,))


def test_file_download_streams_api_redirect_request_and_renames(tmp_path: Path) -> None:
    session = FakeSession(FakeResponse([b"abc", b"def"], headers={"Content-Length": "6"}))
    backend = FakeBackend("https://www.seedr.cc/rest/file/12")
    events = []
    downloader = Downloader(backend, lambda: session, events.append)

    job_id = downloader.submit_file(12, "movie.mkv", tmp_path, "movie.mkv")
    job = wait_for_job(downloader, job_id, "completed")

    assert backend.file_ids == [12]
    assert (tmp_path / "movie.mkv").read_bytes() == b"abcdef"
    assert not (tmp_path / "movie.mkv.part").exists()
    assert session.requests[0]["url"] == "https://www.seedr.cc/rest/file/12"
    assert session.requests[0]["allow_redirects"] is True
    assert job.final_path == tmp_path / "movie.mkv"
    assert events[-1].state == "completed"


def test_unknown_content_length_download_completes_with_unknown_total(tmp_path: Path) -> None:
    session = FakeSession(FakeResponse([b"abc"], headers={}))
    downloader = Downloader(FakeBackend(), lambda: session)

    job_id = downloader.submit_file(1, "unknown.bin", tmp_path, "unknown.bin")
    job = wait_for_job(downloader, job_id, "completed")

    assert job.total_bytes == 0
    assert job.bytes == 3
    assert (tmp_path / "unknown.bin").read_bytes() == b"abc"


def test_folder_download_resolves_folder_zip_url(tmp_path: Path) -> None:
    session = FakeSession(FakeResponse([b"zip"], headers={"Content-Length": "3"}))
    backend = FakeBackend(folder_url="https://www.seedr.cc/rest/folder/44/download")
    downloader = Downloader(backend, lambda: session)

    job_id = downloader.submit_folder(44, "Season 1", tmp_path)
    job = wait_for_job(downloader, job_id, "completed")

    assert backend.folder_ids == [44]
    assert session.requests[0]["url"] == "https://www.seedr.cc/rest/folder/44/download"
    assert job.suggested_filename == "Season 1.zip"
    assert (tmp_path / "Season 1.zip").read_bytes() == b"zip"


def test_cancel_mid_stream_leaves_part_file(tmp_path: Path) -> None:
    session = FakeSession(FakeResponse([b"abc", b"def"], headers={"Content-Length": "6"}))
    downloader: Downloader

    def on_event(job) -> None:
        if job.state == "downloading" and job.bytes > 0:
            downloader.cancel(job.job_id)

    downloader = Downloader(FakeBackend(), lambda: session, on_event)
    job_id = downloader.submit_file(1, "cancel.bin", tmp_path, "cancel.bin")
    job = wait_for_job(downloader, job_id, "cancelled")

    assert job.state == "cancelled"
    assert not (tmp_path / "cancel.bin").exists()
    assert (tmp_path / "cancel.bin.part").read_bytes() == b"abc"


def test_resume_uses_range_and_appends_to_part_file(tmp_path: Path) -> None:
    part = tmp_path / "resume.bin.part"
    part.write_bytes(b"abc")
    session = FakeSession(FakeResponse([b"def"], status_code=206, headers={"Content-Length": "3"}))
    downloader = Downloader(FakeBackend(), lambda: session)

    job_id = downloader.submit_file(1, "resume.bin", tmp_path, "resume.bin")
    job = wait_for_job(downloader, job_id, "completed")

    assert session.requests[0]["headers"] == {"Range": "bytes=3-"}
    assert job.total_bytes == 6
    assert (tmp_path / "resume.bin").read_bytes() == b"abcdef"


def test_4xx_stream_failure_marks_job_failed(tmp_path: Path) -> None:
    response = FakeResponse([], status_code=403, body={"reason_phrase": "premium_required"})
    session = FakeSession(response)
    downloader = Downloader(FakeBackend(), lambda: session)

    job_id = downloader.submit_file(1, "blocked.bin", tmp_path, "blocked.bin")
    job = wait_for_job(downloader, job_id, "failed")

    assert "Access denied" in job.error
    assert not (tmp_path / "blocked.bin").exists()


def test_collision_adds_numeric_suffix(tmp_path: Path) -> None:
    (tmp_path / "movie.mkv").write_bytes(b"existing")
    downloader = Downloader(FakeBackend(), lambda: FakeSession(FakeResponse([b"x"])))

    first = downloader.submit_file(1, "movie.mkv", tmp_path, "movie.mkv")
    second = downloader.submit_file(2, "movie.mkv", tmp_path, "movie.mkv")

    assert downloader.get(first).suggested_filename == "movie (2).mkv"
    assert downloader.get(second).suggested_filename == "movie (3).mkv"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("foo/bar.mkv", "foo_bar.mkv"),
        ("NUL.txt", "NUL_.txt"),
    ],
)
def test_submit_sanitizes_unsafe_names(tmp_path: Path, raw: str, expected: str) -> None:
    downloader = Downloader(FakeBackend(), lambda: FakeSession(FakeResponse([b"x"])))

    job_id = downloader.submit_file(1, raw, tmp_path, raw)

    assert downloader.get(job_id).suggested_filename == expected
