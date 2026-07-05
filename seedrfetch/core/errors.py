"""Detailed user-facing error translation with correlated evidence."""
from __future__ import annotations

import logging
import socket
import ssl
from dataclasses import dataclass
from urllib.parse import urlparse

from core.config import LOG_PATH
from core.logging_setup import correlated_tail, current_corr_id, mark_operation_failed


@dataclass
class UserError:
    title: str
    detail: str
    guidance: str
    corr_id: str
    log_excerpt: str


def _response_reason(response) -> str:
    try:
        body = response.json()
        if isinstance(body, dict):
            reason = body.get("reason_phrase") or body.get("reason") or body.get("message")
            if reason:
                return str(reason)
    except (ValueError, AttributeError):
        pass
    return ""


def translate(exc: BaseException, corr_id: str | None = None) -> UserError:
    mark_operation_failed()
    cid = corr_id or current_corr_id()
    title, detail = "Unexpected error", repr(exc)
    guidance = "Try again. If it repeats, copy diagnostics from Settings and include correlation ID %s." % cid
    try:
        import requests
        if isinstance(exc, socket.gaierror):
            title, detail = "Can't reach seedr.cc", "DNS lookup failed: %s" % exc
            guidance = "Check your connection and DNS settings, then run Settings > Diagnostics."
        elif isinstance(exc, ConnectionRefusedError):
            title, detail = "Connection refused", str(exc)
            guidance = "Check firewall, VPN, and proxy settings."
        elif isinstance(exc, requests.ConnectTimeout):
            title, detail, guidance = "Connection timed out", str(exc), "Check your network, proxy, and firewall."
        elif isinstance(exc, requests.ReadTimeout):
            title, detail, guidance = "Server too slow to respond", str(exc), "Wait briefly and retry."
        elif isinstance(exc, (ssl.SSLCertVerificationError, requests.exceptions.SSLError)):
            from core.ssl_setup import _find_tls_exception
            cause = _find_tls_exception(exc)
            reason = (getattr(cause, "verify_message", None) or getattr(cause, "reason", None)
                      or getattr(exc, "reason", None) or str(exc))
            code = getattr(cause, "verify_code", None) or getattr(exc, "verify_code", None)
            title = "Secure connection failed"
            detail = "Certificate verification failed (code=%s): %s" % (code, reason)
            guidance = ("Your network or antivirus may be inspecting HTTPS traffic. "
                        "Open Settings > Run Diagnostics for details.")
        elif isinstance(exc, requests.ConnectionError):
            title, detail = "Can't reach seedr.cc", str(exc)
            guidance = "Check your internet connection, DNS, proxy, and firewall, then run Diagnostics."
        elif isinstance(exc, requests.HTTPError) and exc.response is not None:
            status = exc.response.status_code
            reason = _response_reason(exc.response)
            url = getattr(exc.response, "url", "") or ""
            host = urlparse(url).hostname or ""
            is_seedr_cdn = host.endswith(".seedr.cc") and host != "www.seedr.cc"
            if status == 404 and is_seedr_cdn:
                title = "Download link expired"
                detail = "Seedr's download link expired before the file could be fetched."
                guidance = (
                    "This usually means HTTPS inspection from antivirus, VPN, or a corporate "
                    "proxy delayed the request long enough to invalidate the link. Try again; "
                    "if it keeps failing, add an exception for *.seedr.cc in HTTPS scanning."
                )
            elif status == 401:
                title = "Sign-in failed"
                detail = reason or "Seedr returned HTTP 401."
                guidance = "Check your credentials or use Device Code."
            elif status == 403:
                title = "Access denied"
                detail = reason or "Seedr returned HTTP 403."
                guidance = "Confirm your Seedr Premium plan is active."
            elif reason == "not_a_torrent":
                title = "That link isn't a torrent"
                detail = "Seedr returned not_a_torrent for the submitted link."
                guidance = (
                    "Paste a magnet link or a direct .torrent URL. If this came from a torrent "
                    "site, copy the magnet link instead of the page URL."
                )
            elif status >= 500:
                title = "Seedr is having a problem"
                detail = reason or "Seedr returned HTTP %d." % status
                guidance = "Try again in a minute."
        elif type(exc).__module__.startswith("seedrcc"):
            title, detail = "Seedr device authorization failed", repr(exc)
            guidance = "Generate a new device code, authorize it in the browser, and retry."
    except ImportError:
        pass
    logging.getLogger("errors").error("USER_ERROR corr_id=%s title=%s detail=%s guidance=%s",
                                      cid, title, detail, guidance, exc_info=exc)
    return UserError(title, detail, guidance, cid, correlated_tail(LOG_PATH, cid, 20))
