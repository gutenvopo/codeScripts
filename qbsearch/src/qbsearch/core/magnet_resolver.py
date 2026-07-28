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
    # match a magnet URI and allow an arbitrary query string after the infohash
    r"magnet:\?xt=urn:btih:[A-Za-z0-9%]+(?:[^\s\"'<>]*)?",
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
        log.info("Step 1/4: Inspecting the search result for a downloadable link")
        direct = self._direct_url(result)
        if direct:
            log.info("The search engine supplied a direct %s", _target_kind(direct))
            return "ready", direct
        detail_url = self.detail_url(result)
        if not detail_url:
            log.error("The result contains no usable HTTP or HTTPS detail-page URL")
            return "missing", None
        log.debug("Detail page selected: %s", _safe_url(detail_url))
        with self._lock:
            cached = self.cache.get(detail_url)
            if cached:
                log.info("A previously resolved magnet was found in the in-memory cache")
                return "ready", cached
            if detail_url in self.in_flight:
                log.warning("The same detail page is already being requested")
                return "inflight", detail_url
            self.in_flight.add(detail_url)
        return "fetch", detail_url

    def resolve_detail(self, detail_url: str, prefer_name: str | None = None) -> str | None:
        safe_url = _safe_url(detail_url)
        log.info("Step 2/4: Requesting the search engine detail page")
        log.debug("GET %s (timeout=10s, redirects=enabled)", safe_url)
        try:
            try:
                response = self.session.get(detail_url, timeout=10, allow_redirects=True)
            except requests.RequestException as exc:
                log.error(
                    "Network request failed before an HTTP response was received: %s: %s",
                    type(exc).__name__,
                    exc,
                )
                return None
            reason = getattr(response, "reason", "") or "no reason phrase"
            log.info("Response received: HTTP %s %s", response.status_code, reason)
            final_url = getattr(response, "url", detail_url)
            if final_url != detail_url:
                log.debug("Redirected to: %s", _safe_url(final_url))
            headers = getattr(response, "headers", {})
            content_type = headers.get("Content-Type", "unknown") if headers else "unknown"
            log.debug(
                "Response content: %s; %s characters",
                content_type,
                len(response.text),
            )
            if response.status_code != 200:
                log.error(
                    "Cannot scan this page because the server returned HTTP %s %s",
                    response.status_code,
                    reason,
                )
                return None
            log.info("Step 3/4: Scanning the returned HTML for magnet URIs")
            magnet = extract_magnet(response.text, prefer_name)
            if not magnet:
                log.error("The page loaded successfully, but no magnet URI was found in its HTML")
                return None
            log.info("Magnet found: %s", _magnet_summary(magnet))
            with self._lock:
                self.cache[detail_url] = magnet
            return magnet
        finally:
            with self._lock:
                self.in_flight.discard(detail_url)
            log.debug("Detail-page request marked as finished")

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
            return file_url
        return ""


def _safe_url(value: str) -> str:
    parsed = urlparse(value)
    path = parsed.path or "/"
    query_note = "?<query redacted>" if parsed.query else ""
    return f"{parsed.scheme}://{parsed.netloc}{path}{query_note}"


def _target_kind(value: str) -> str:
    return "magnet URI" if value.lower().startswith("magnet:?") else ".torrent URL"


def _magnet_summary(value: str) -> str:
    query = parse_qs(urlparse(value).query)
    info_hash = query.get("xt", ["unknown"])[0].rsplit(":", 1)[-1]
    display_name = query.get("dn", ["not supplied"])[0]
    tracker_count = len(query.get("tr", []))
    short_hash = f"{info_hash[:12]}…" if len(info_hash) > 12 else info_hash
    return (
        f"info hash {short_hash}; name {display_name!r}; "
        f"{tracker_count} tracker{'s' if tracker_count != 1 else ''}"
    )
