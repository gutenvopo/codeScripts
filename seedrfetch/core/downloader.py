"""Resumable signed-URL downloads running outside the Tk thread."""
from __future__ import annotations

import logging
import os
import re
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from itertools import count
from pathlib import Path
from typing import Any, Callable, Deque
from urllib.parse import urlparse, urlunparse

import requests

from core.backend import SeedrBackend
from core.errors import translate
from core.logging_setup import log_operation
from core.ssl_setup import make_session

LOG = logging.getLogger(__name__)
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                  *(f"LPT{i}" for i in range(1, 10))}
TERMINAL_STATES = {"completed", "failed", "cancelled"}
CHUNK_SIZE = 256 * 1024


class DownloadCancelled(RuntimeError):
    """Raised when the user cancels a local download."""


@dataclass
class DownloadJob:
    job_id: str
    kind: str
    seedr_id: int
    display_name: str
    dest_dir: Path
    suggested_filename: str
    state: str = "queued"
    bytes: int = 0
    total_bytes: int = 0
    speed: float = 0.0
    started_at: float | None = None
    finished_at: float | None = None
    error: str = ""
    final_path: Path | None = None
    corr_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "kind": self.kind,
            "seedr_id": self.seedr_id,
            "display_name": self.display_name,
            "dest_dir": self.dest_dir,
            "suggested_filename": self.suggested_filename,
            "state": self.state,
            "bytes": self.bytes,
            "total_bytes": self.total_bytes,
            "speed": self.speed,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
            "final_path": self.final_path,
            "corr_id": self.corr_id,
        }


class Downloader:
    def __init__(
        self,
        backend: SeedrBackend,
        session_factory: Callable[[], Any] = make_session,
        on_event: Callable[[DownloadJob], None] | None = None,
        max_workers: int = 2,
    ) -> None:
        self.backend = backend
        self.session_factory = session_factory
        self.on_event = on_event or (lambda _job: None)
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="downloader")
        self._lock = threading.RLock()
        self._jobs: dict[str, DownloadJob] = {}
        self._cancel_events: dict[str, threading.Event] = {}
        self._reserved_paths: set[Path] = set()
        self._counter = count(1)

    def submit_file(
        self,
        file_id: int,
        display_name: str,
        dest_dir: Path,
        suggested_filename: str | None = None,
    ) -> str:
        return self._submit("file", file_id, display_name, dest_dir, suggested_filename or display_name)

    def submit_folder(
        self,
        folder_id: int,
        display_name: str,
        dest_dir: Path,
        suggested_filename: str | None = None,
    ) -> str:
        filename = suggested_filename or f"{display_name}.zip"
        if not filename.lower().endswith(".zip"):
            filename = f"{filename}.zip"
        return self._submit("folder", folder_id, display_name, dest_dir, filename)

    def cancel(self, job_id: str) -> None:
        with self._lock:
            cancel_event = self._cancel_events.get(job_id)
            job = self._jobs.get(job_id)
        if cancel_event:
            cancel_event.set()
        if job and job.state == "queued":
            self._finish(job, "cancelled")

    def get(self, job_id: str) -> DownloadJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def all_jobs(self) -> list[DownloadJob]:
        with self._lock:
            return list(self._jobs.values())

    def _submit(self, kind: str, seedr_id: int, display_name: str, dest_dir: Path,
                suggested_filename: str) -> str:
        filename = _sanitize_filename(suggested_filename)
        final_path = self._reserve_path(dest_dir, filename)
        with self._lock:
            job_id = "dl-%d-%d" % (int(time.time() * 1000), next(self._counter))
            job = DownloadJob(job_id, kind, int(seedr_id), display_name, dest_dir,
                              final_path.name, final_path=final_path)
            self._jobs[job_id] = job
            self._cancel_events[job_id] = threading.Event()
        self._emit(job, force=True)
        self._pool.submit(self._run, job_id)
        return job_id

    def _run(self, job_id: str) -> None:
        job = self.get(job_id)
        if not job:
            return
        cancel_event = self._cancel_events[job_id]
        try:
            with log_operation("download-%s" % job.kind, item_id=job.seedr_id,
                               filename=job.suggested_filename) as cid:
                job.corr_id = cid
                self._emit(job, force=True)
                try:
                    if cancel_event.is_set():
                        raise DownloadCancelled()
                    self._set_state(job, "resolving")
                    self._set_state(job, "downloading")
                    self._stream(job, cancel_event)
                    self._finish(job, "completed")
                except DownloadCancelled:
                    self._finish(job, "cancelled")
                except Exception as exc:
                    LOG.exception("download failed job_id=%s", job.job_id)
                    user_error = translate(exc, corr_id=cid)
                    job.error = ("%s: %s" % (user_error.title, user_error.detail))[:200]
                    self._finish(job, "failed")
        finally:
            with self._lock:
                if job.final_path:
                    self._reserved_paths.discard(job.final_path)

    def _download_request(self, job: DownloadJob) -> tuple[str, Any]:
        if job.kind == "folder":
            return self.backend.download_folder_request(job.seedr_id)
        return self.backend.download_file_request(job.seedr_id)

    def _stream(self, job: DownloadJob, cancel_event: threading.Event) -> None:
        if job.final_path is None:
            raise RuntimeError("Download job missing final path")
        job.dest_dir.mkdir(parents=True, exist_ok=True)
        part_path = job.final_path.with_name(job.final_path.name + ".part")
        existing = part_path.stat().st_size if part_path.exists() else 0
        headers = {"Range": "bytes=%d-" % existing} if existing else {}
        api_url, auth = self._download_request(job)
        scoped_auth = _ScopedAuth(auth, urlparse(api_url).hostname or "")
        session = self._build_stream_session()
        try:
            response = session.get(api_url, headers=headers, auth=scoped_auth, stream=True,
                                   allow_redirects=True, timeout=(10, 120))
            with response:
                response.raise_for_status()
                LOG.info("streaming download url=%s", _redact_signed_url(response.url))
                LOG.debug("streaming download full_url=%s", response.url)
                append = existing > 0 and getattr(response, "status_code", None) == 206
                if not append:
                    existing = 0
                self._stream_response(response, part_path, existing, append, job, cancel_event)
        finally:
            close = getattr(session, "close", None)
            if callable(close):
                close()
        os.replace(part_path, job.final_path)

    def _build_stream_session(self):
        session = self.session_factory()
        no_retry = requests.adapters.HTTPAdapter(max_retries=0)
        mount = getattr(session, "mount", None)
        if callable(mount):
            mount("http://", no_retry)
            mount("https://", no_retry)
        try:
            session.auth = None
        except AttributeError:
            pass
        headers = getattr(session, "headers", None)
        if headers is not None:
            headers.pop("Authorization", None)
        return session

    def _stream_response(self, response: Any, part_path: Path, existing: int, append: bool,
                         job: DownloadJob, cancel_event: threading.Event) -> None:
        length = _content_length(response)
        job.bytes = existing
        job.total_bytes = existing + length if length and (append or existing) else length
        window: Deque[tuple[float, int]] = deque()
        last_emit = 0.0
        next_percent = 0
        with part_path.open("ab" if append else "wb") as output:
            for chunk in response.iter_content(CHUNK_SIZE):
                if cancel_event.is_set():
                    output.flush()
                    raise DownloadCancelled()
                if not chunk:
                    continue
                output.write(chunk)
                job.bytes += len(chunk)
                now = time.monotonic()
                window.append((now, job.bytes))
                while window and now - window[0][0] > 2.0:
                    window.popleft()
                if len(window) > 1:
                    elapsed = max(now - window[0][0], 0.01)
                    job.speed = (job.bytes - window[0][1]) / elapsed
                percent = int((job.bytes / job.total_bytes) * 100) if job.total_bytes else 0
                if now - last_emit >= 0.25 or (job.total_bytes and percent >= next_percent):
                    last_emit = now
                    next_percent = percent + 1
                    LOG.debug("download progress bytes=%d total=%d speed_bps=%d",
                              job.bytes, job.total_bytes, job.speed)
                    self._emit(job)
            output.flush()
            os.fsync(output.fileno())

    def _set_state(self, job: DownloadJob, state: str) -> None:
        job.state = state
        if state == "downloading" and job.started_at is None:
            job.started_at = time.time()
        self._emit(job, force=True)

    def _finish(self, job: DownloadJob, state: str) -> None:
        job.state = state
        job.finished_at = time.time()
        if state in TERMINAL_STATES:
            job.speed = 0.0
        self._emit(job, force=True)

    def _emit(self, job: DownloadJob, force: bool = False) -> None:
        try:
            self.on_event(job)
        except Exception:
            if force:
                LOG.exception("download event callback failed job_id=%s", job.job_id)

    def _reserve_path(self, dest_dir: Path, filename: str) -> Path:
        dest_dir = Path(dest_dir)
        stem = Path(filename).stem
        suffix = "".join(Path(filename).suffixes)
        with self._lock:
            candidate = dest_dir / filename
            index = 2
            while candidate.exists() or candidate in self._reserved_paths:
                candidate = dest_dir / ("%s (%d)%s" % (stem, index, suffix))
                index += 1
            self._reserved_paths.add(candidate)
            return candidate


def _sanitize_filename(raw: str, max_stem_length: int = 240) -> str:
    name = INVALID_FILENAME_CHARS.sub("_", (raw or "").strip())
    name = name.strip(" .")
    if not name:
        name = "download"
    path = Path(name)
    stem = path.stem.strip(" .") or "download"
    suffix = "".join(path.suffixes)
    if stem.upper() in RESERVED_NAMES:
        stem = f"{stem}_"
    name = stem + suffix
    if len(stem) > max_stem_length:
        name = (stem[:max_stem_length].strip(" .") or "download") + suffix
    return name


def _content_length(response: Any) -> int:
    try:
        return int(response.headers.get("Content-Length") or 0)
    except (AttributeError, TypeError, ValueError):
        return 0


class _ScopedAuth(requests.auth.AuthBase):
    def __init__(self, auth: Any, allowed_host: str) -> None:
        self.auth = auth
        self.allowed_host = allowed_host.lower()

    def __call__(self, request):
        host = (urlparse(request.url).hostname or "").lower()
        if host == self.allowed_host and callable(self.auth):
            return self.auth(request)
        request.headers.pop("Authorization", None)
        return request


def _redact_signed_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.query:
        return urlunparse(parsed._replace(query="<redacted>", fragment=""))
    return urlunparse(parsed._replace(fragment=""))
