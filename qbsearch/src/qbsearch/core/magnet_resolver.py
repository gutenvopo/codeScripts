from __future__ import annotations

import html
import logging
import re
import threading
from difflib import SequenceMatcher
from typing import Literal
from urllib.parse import parse_qs, unquote_plus, urlparse

import requests

from qbsearch.core.result_model import SearchResult

log = logging.getLogger(__name__)

MAGNET_RE = re.compile(
    r"magnet:\?xt=urn:btih:[A-Za-z0-9]+(?:&[^\s\"'<>]*)?",
    re.IGNORECASE,
)

ResolveState = Literal["ready", "fetch", "inflight", "missing"]


def extract_magnet(html_text: str, prefer_name: str | None = None) -> str | None:
    matches = MAGNET_RE.findall(html.unescape(html_text))
    if not matches:
        return None
    if not prefer_name:
        return matches[0]
    scored = []
    target = prefer_name.casefold()
    for magnet in matches:
        try:
            name = parse_qs(urlparse(magnet).query).get("dn", [""])[0]
            decoded = unquote_plus(name).casefold()
            scored.append((SequenceMatcher(None, target, decoded).ratio(), magnet))
        except (AttributeError, ValueError):
            continue
    if not scored:
        return matches[0]
    return max(scored, key=lambda item: item[0])[1]


class MagnetResolver:
    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml",
            }
        )
        self.cache: dict[str, str] = {}
        self.in_flight: set[str] = set()
        self._lock = threading.Lock()

    def prepare(self, result: SearchResult) -> tuple[ResolveState, str | None]:
        direct = self._direct_url(result)
        if direct:
            return "ready", direct
        detail_url = self.detail_url(result)
        if not detail_url:
            return "missing", None
        with self._lock:
            cached = self.cache.get(detail_url)
            if cached:
                log.debug("magnet resolver cache hit for %s", detail_url)
                return "ready", cached
            if detail_url in self.in_flight:
                return "inflight", detail_url
            self.in_flight.add(detail_url)
        return "fetch", detail_url

    def resolve_detail(self, detail_url: str, prefer_name: str | None = None) -> str | None:
        try:
            response = self.session.get(detail_url, timeout=10, allow_redirects=True)
        except requests.RequestException as exc:
            log.warning("failed to fetch magnet detail page %s: %s", detail_url, exc)
            return None
        try:
            if response.status_code != 200:
                log.warning(
                    "magnet detail page returned HTTP %s for %s",
                    response.status_code,
                    detail_url,
                )
                return None
            magnet = extract_magnet(response.text, prefer_name)
            if not magnet:
                log.warning("magnet not found on detail page %s", detail_url)
                return None
            with self._lock:
                self.cache[detail_url] = magnet
            return magnet
        finally:
            with self._lock:
                self.in_flight.discard(detail_url)

    def detail_url(self, result: SearchResult) -> str:
        candidate = result.file_url.strip() or result.description_url.strip()
        parsed = urlparse(candidate)
        if parsed.scheme.lower() in {"http", "https"}:
            return candidate
        fallback = result.description_url.strip()
        parsed_fallback = urlparse(fallback)
        if parsed_fallback.scheme.lower() in {"http", "https"}:
            return fallback
        return ""

    @staticmethod
    def _direct_url(result: SearchResult) -> str:
        file_url = result.file_url.strip()
        if file_url.lower().startswith("magnet:?"):
            return file_url
        parsed = urlparse(file_url)
        if parsed.scheme.lower() in {"http", "https"} and parsed.path.lower().endswith(".torrent"):
            log.debug("using direct .torrent URL as copy target: %s", file_url)
            return file_url
        return ""
