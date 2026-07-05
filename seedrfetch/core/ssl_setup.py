"""OS trust-store setup and the sole HTTP session factory."""
from __future__ import annotations

import json
import hashlib
import http.client
import logging
import os
import socket
import ssl
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

try:
    import truststore
    truststore.inject_into_ssl()
    TRUSTSTORE_ACTIVE = True
except (ImportError, RuntimeError):
    TRUSTSTORE_ACTIVE = False

CONFIG_PATH = Path.home() / ".seedrfetch" / "config.json"


def _settings() -> dict[str, Any]:
    try:
        value = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def apply_environment(settings: dict[str, Any] | None = None) -> dict[str, Any]:
    settings = settings or _settings()
    ca = Path(str(settings.get("custom_ca_bundle", ""))).expanduser()
    if str(ca) not in ("", ".") and ca.is_file():
        os.environ["REQUESTS_CA_BUNDLE"] = str(ca)
        os.environ["SSL_CERT_FILE"] = str(ca)
    for key in ("http_proxy", "https_proxy"):
        value = str(settings.get(key, "")).strip()
        if value:
            os.environ[key.upper()] = value
        else:
            os.environ.pop(key.upper(), None)
    return settings


_ACTIVE = apply_environment()

HTTP_LOG = logging.getLogger("seedrfetch.http")
TLS_LOG = logging.getLogger("seedrfetch.tls")
INTERCEPTORS = ("Norton", "NortonLifeLock", "Symantec Endpoint", "Kaspersky",
                "Bitdefender", "ESET", "Sophos", "Avast", "AVG", "Trend Micro",
                "McAfee", "Webroot", "Zscaler", "Netskope", "Fortinet", "Forcepoint",
                "Cisco Umbrella", "Palo Alto", "Check Point", "BlueCoat", "Cloudflare WARP")
_HTTPS_INSPECTION_ISSUER = ""


def https_inspection_warning() -> str:
    if not _HTTPS_INSPECTION_ISSUER:
        return ""
    return ("HTTPS inspection detected (%s). Download performance may be degraded; "
            "consider adding *.seedr.cc to antivirus HTTPS exceptions.") % _HTTPS_INSPECTION_ISSUER


def _safe_url(url: str) -> str:
    parsed = urlparse(url)
    query = [(key, "***REDACTED***" if "token" in key.lower() else value)
             for key, value in parse_qsl(parsed.query, keep_blank_values=True)]
    return urlunparse(parsed._replace(query=urlencode(query)))


def _cert_name(parts: Any) -> str:
    return ",".join("%s=%s" % (key, value) for group in parts for key, value in group)


def _log_socket_tls(sock: Any, host: str, insecure: bool = False) -> None:
    if not sock:
        TLS_LOG.debug("TLS_EVENT host=%s socket_metadata=unavailable", host)
        return
    cert = sock.getpeercert() or {}
    binary = sock.getpeercert(binary_form=True) or b""
    issuer, subject = _cert_name(cert.get("issuer", ())), _cert_name(cert.get("subject", ()))
    not_before, not_after = cert.get("notBefore"), cert.get("notAfter")
    if binary and not cert:
        try:
            from cryptography import x509
            parsed = x509.load_der_x509_certificate(binary)
            issuer, subject = parsed.issuer.rfc4514_string(), parsed.subject.rfc4514_string()
            not_before = parsed.not_valid_before_utc.isoformat()
            not_after = parsed.not_valid_after_utc.isoformat()
        except (ImportError, ValueError):
            pass
    suspected = any(item.lower() in issuer.lower() for item in INTERCEPTORS)
    global _HTTPS_INSPECTION_ISSUER
    if suspected and host.endswith("seedr.cc") and _HTTPS_INSPECTION_ISSUER != issuer:
        _HTTPS_INSPECTION_ISSUER = issuer
        TLS_LOG.warning("HTTPS inspection detected (issuer=%s). Download performance may be "
                        "degraded; consider adding *.seedr.cc to your antivirus HTTPS exceptions.",
                        issuer)
    chain_length = 1
    for method_name in ("get_verified_chain", "get_unverified_chain"):
        method = getattr(sock, method_name, None)
        if callable(method):
            try:
                chain_length = len(method())
                break
            except Exception:
                pass
    TLS_LOG.info("TLS_EVENT host=%s version=%s cipher=%s subject=%s issuer=%s "
                 "notBefore=%s notAfter=%s sha256=%s chain_length=%d "
                 "TLS_INTERCEPTION_SUSPECTED=%s INSECURE_DIAGNOSTIC_FETCH=%s",
                 host, sock.version(), sock.cipher(), subject, issuer, not_before,
                 not_after, hashlib.sha256(binary).hexdigest(), chain_length,
                 str(suspected).lower(), str(insecure).lower())


def _log_intercepted_chain(netloc: str) -> None:
    parsed_host, separator, parsed_port = netloc.partition(":")
    host, port = parsed_host, int(parsed_port) if separator and parsed_port.isdigit() else 443
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    try:
        with socket.create_connection((host, port), timeout=10) as raw:
            with context.wrap_socket(raw, server_hostname=host) as tls:
                _log_socket_tls(tls, netloc, insecure=True)
    except Exception as exc:
        TLS_LOG.error("INSECURE_DIAGNOSTIC_FETCH=true host=%s failed=%r", netloc, exc)


def _find_tls_exception(exc: BaseException, seen: set[int] | None = None) -> BaseException:
    seen = seen or set()
    if id(exc) in seen:
        return exc
    seen.add(id(exc))
    if isinstance(exc, (ssl.SSLError, ssl.SSLCertVerificationError)) and (
            getattr(exc, "verify_code", None) is not None or getattr(exc, "reason", None)):
        return exc
    candidates = [getattr(exc, "__cause__", None), getattr(exc, "__context__", None)]
    candidates.extend(value for value in getattr(exc, "args", ()) if isinstance(value, BaseException))
    for candidate in candidates:
        if isinstance(candidate, BaseException):
            found = _find_tls_exception(candidate, seen)
            if found is not candidate or isinstance(found, ssl.SSLError):
                return found
    return exc


def _log_tls_failure(netloc: str, exc: BaseException) -> None:
    cause = _find_tls_exception(exc)
    TLS_LOG.error("TLS_FAILURE host=%s class=%s errno=%s strerror=%s reason=%s "
                  "verify_code=%s verify_message=%s library=%s func=%s args=%r",
                  netloc, type(cause).__name__, getattr(cause, "errno", None),
                  getattr(cause, "strerror", None), getattr(cause, "reason", None),
                  getattr(cause, "verify_code", None), getattr(cause, "verify_message", None),
                  getattr(cause, "library", None), getattr(cause, "func", None),
                  getattr(cause, "args", None), exc_info=exc)


def _response_hook(response, *args: Any, **kwargs: Any):
    request = response.request
    headers = dict(request.headers)
    elapsed = round(response.elapsed.total_seconds() * 1000)
    HTTP_LOG.debug("HTTP_REQUEST method=%s url=%s headers=%s", request.method,
                   _safe_url(request.url), headers)
    HTTP_LOG.debug("HTTP_RESPONSE status=%d reason=%s headers=%s elapsed_ms=%d size=%s",
                   response.status_code, response.reason, dict(response.headers), elapsed,
                   response.headers.get("Content-Length", "unknown"))
    content_type = response.headers.get("Content-Type", "").lower()
    try:
        from core import logging_setup
        log_body = logging_setup.TRACE_WIRE or response.status_code >= 400
        textual = content_type.startswith("text/") or "application/json" in content_type
        if log_body and textual and not kwargs.get("stream", False):
            HTTP_LOG.debug("HTTP_RESPONSE_BODY first_512=%r", response.content[:512])
    except Exception:
        HTTP_LOG.exception("Could not capture HTTP response body")
    connection = getattr(response.raw, "connection", None) or getattr(response.raw, "_connection", None)
    _log_socket_tls(getattr(connection, "sock", None), urlparse(request.url).netloc)
    return response


def make_session(settings: dict[str, Any] | None = None):
    import requests
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry

    class LoggingRetry(Retry):
        def increment(self, *args: Any, **kwargs: Any):
            result = super().increment(*args, **kwargs)
            HTTP_LOG.warning("HTTP_RETRY attempt_num=%d backoff_ms=%d last_error=%r",
                             len(result.history), result.get_backoff_time() * 1000,
                             kwargs.get("error"))
            return result

    class TLSDiagnosticAdapter(HTTPAdapter):
        def send(self, request, **kwargs: Any):
            try:
                return super().send(request, **kwargs)
            except requests.exceptions.SSLError as exc:
                netloc = urlparse(request.url).netloc
                _log_tls_failure(netloc, exc)
                _log_intercepted_chain(netloc)
                raise

    current = apply_environment(settings)
    # http.client's built-in debug printer bypasses logging filters and can expose
    # Authorization headers. The response hook below provides redacted wire evidence.
    http.client.HTTPConnection.debuglevel = 0
    logging.getLogger("urllib3").setLevel(logging.DEBUG)
    session = requests.Session()
    retry = LoggingRetry(total=3, backoff_factor=1.0,
                         status_forcelist=[502, 503, 504],
                         allowed_methods=frozenset(["GET", "POST"]))
    session.mount("https://", TLSDiagnosticAdapter(max_retries=retry))
    session.mount("http://", TLSDiagnosticAdapter(max_retries=retry))
    session.hooks["response"].append(_response_hook)
    if current.get("disable_ssl_verify", False):
        session.verify = False
        from requests.packages import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    ca = str(current.get("custom_ca_bundle", "")).strip()
    if ca and Path(ca).is_file():
        session.verify = ca
    for scheme in ("http", "https"):
        value = str(current.get(f"{scheme}_proxy", "")).strip()
        if value:
            session.proxies[scheme] = value
    return session


if __name__ == "__main__":
    response = make_session().get("https://www.seedr.cc/", timeout=(10, 60))
    print(response.status_code, response.url)
