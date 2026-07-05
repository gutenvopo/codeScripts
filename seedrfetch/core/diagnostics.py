"""Network and TLS diagnostics."""
from __future__ import annotations

import socket
import ssl
import time
from typing import Any

INTERCEPTORS = ("Norton", "Symantec Endpoint", "Kaspersky", "Bitdefender",
                "ESET", "Sophos", "Trend Micro", "Zscaler", "Netskope", "Fortinet")


def check_dns_resolution(host: str) -> tuple[bool, str]:
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(host, 443)})
        return True, ", ".join(addresses[:4])
    except OSError as exc:
        return False, str(exc)


def check_tcp_connect(host: str, port: int) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=10) as sock:
            return True, f"Connected to {sock.getpeername()[0]}:{port}"
    except OSError as exc:
        return False, str(exc)


def _name(parts: Any) -> str:
    return ", ".join(f"{key}={value}" for group in parts for key, value in group)


def check_tls_handshake(host: str, port: int) -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False, "peer_cert_issuer": "",
                              "peer_cert_subject": "", "error_class": "", "error_msg": ""}
    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=10) as raw:
            with context.wrap_socket(raw, server_hostname=host) as tls:
                cert = tls.getpeercert()
                result.update(ok=True, peer_cert_issuer=_name(cert.get("issuer", ())),
                              peer_cert_subject=_name(cert.get("subject", ())))
        result["interception_detected"] = any(
            name.lower() in result["peer_cert_issuer"].lower() for name in INTERCEPTORS)
    except Exception as exc:
        result.update(error_class=type(exc).__name__, error_msg=str(exc))
    return result


def check_seedr_api(session, auth: Any = None) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        response = session.get("https://www.seedr.cc/rest/user", auth=auth, timeout=(10, 60))
        return {"ok": response.ok, "status_code": response.status_code,
                "elapsed_ms": round((time.perf_counter() - started) * 1000),
                "detail": response.reason}
    except Exception as exc:
        return {"ok": False, "status_code": None,
                "elapsed_ms": round((time.perf_counter() - started) * 1000),
                "detail": f"{type(exc).__name__}: {exc}"}


def run_all(session, auth: Any = None) -> list[tuple[str, dict[str, Any]]]:
    dns_ok, dns_msg = check_dns_resolution("www.seedr.cc")
    tcp_ok, tcp_msg = check_tcp_connect("www.seedr.cc", 443)
    return [("DNS resolution", {"ok": dns_ok, "detail": dns_msg}),
            ("TCP connection", {"ok": tcp_ok, "detail": tcp_msg}),
            ("TLS handshake", check_tls_handshake("www.seedr.cc", 443)),
            ("Seedr API", check_seedr_api(session, auth))]
