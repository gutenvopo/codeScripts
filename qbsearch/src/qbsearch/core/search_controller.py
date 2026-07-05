from __future__ import annotations

import logging
import queue
import re
import threading
import time
from dataclasses import dataclass

from qbsearch.api.qbittorrent import QbtClient
from qbsearch.core.regex_filter import regex_matches
from qbsearch.core.result_model import SearchResult

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SearchRequest:
    pattern: str
    plugins: str
    category: str
    regex: re.Pattern[str] | None = None


class SearchController:
    def __init__(self, client: QbtClient, events: queue.Queue[tuple[str, object]]) -> None:
        self.client = client
        self.events = events
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._search_id: int | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, request: SearchRequest) -> None:
        if self.running:
            self.stop()
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, args=(request,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        search_id = self._search_id
        if search_id is not None:
            try:
                self.client.stop_search(search_id)
            except Exception as exc:  # noqa: BLE001
                log.info("stop search failed: %s", exc)

    def close(self) -> None:
        self.stop()

    def _run(self, request: SearchRequest) -> None:
        last_count = 0
        total_seen = 0
        total_shown = 0
        try:
            self.events.put(("status", "Starting search..."))
            self._search_id = self.client.start_search(
                request.pattern,
                request.plugins,
                request.category,
            )
            while not self._stop.is_set():
                statuses = self.client.search_status(self._search_id)
                status = statuses[0] if statuses else {}
                raw_rows = self.client.search_results(self._search_id, offset=last_count)
                last_count += len(raw_rows)
                total_seen += len(raw_rows)
                rows = [SearchResult.from_api(row) for row in raw_rows]
                rows = [row for row in rows if regex_matches(request.regex, row.name)]
                total_shown += len(rows)
                if rows:
                    self.events.put(("results", rows))
                label = self._status_label(status, total_shown, total_seen, bool(request.regex))
                self.events.put(("status", label))
                if str(status.get("status", "")).lower() in {"stopped", "stopped.", "finished"}:
                    break
                time.sleep(0.6)
            self.events.put(("complete", "Search complete."))
        except Exception as exc:  # noqa: BLE001
            log.exception("search failed")
            self.events.put(("error", str(exc)))
        finally:
            if self._search_id is not None:
                try:
                    self.client.delete_search(self._search_id)
                except Exception as exc:  # noqa: BLE001
                    log.info("delete search failed: %s", exc)
            self._search_id = None

    @staticmethod
    def _status_label(status: dict[str, object], shown: int, seen: int, regex: bool) -> str:
        plugins = status.get("pluginsStatus")
        if regex:
            return f"Showing {shown} of {seen} results (regex filter)"
        if isinstance(plugins, list):
            done = sum(1 for item in plugins if str(item.get("status", "")).lower() != "running")
            return f"Searching... {shown} results from {done}/{len(plugins)} engines"
        return f"Searching... {shown} results"
