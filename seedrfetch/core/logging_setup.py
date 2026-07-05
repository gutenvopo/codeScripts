"""Structured logging, correlation tracking, redaction, and crash reports."""
from __future__ import annotations

import contextvars
import locale
import logging
import os
import platform
import re
import secrets
import ssl
import subprocess
import sys
import threading
import time
import traceback
from contextlib import contextmanager
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Iterator

from core import APP_VERSION
from core.config import CRASH_DIR, HTTP_LOG_PATH, LOG_DIR, LOG_PATH, TLS_LOG_PATH

_corr_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("corr_id", default="--------")
_operation_failed_var: contextvars.ContextVar[bool] = contextvars.ContextVar("operation_failed", default=False)
TRACE_WIRE = False
_initialized = False


def current_corr_id() -> str:
    return _corr_id_var.get()


def mark_operation_failed() -> None:
    _operation_failed_var.set(True)


class RedactionFilter(logging.Filter):
    patterns = (
        (re.compile(r"(Basic\s+)[A-Za-z0-9+/=]+", re.I), r"\1***REDACTED***"),
        (re.compile(r"(?i)(password[\"'\s:=]+)[^\s\"',}]+"), r"\1***REDACTED***"),
        (re.compile(r"(?i)(authorization[\"'\s:=]+)[^\s\"',}]+"), r"\1***REDACTED***"),
        (re.compile(r"(?i)(token[\"'\s:=]+)[^\s\"',}]+"), r"\1***REDACTED***"),
        (re.compile(r"(?i)(api[_-]?key[\"'\s:=]+)[^\s\"',}]+"), r"\1***REDACTED***"),
        (re.compile(r"\b([\w.+-]{2})[\w.+-]*(@[\w.-]+\.[A-Za-z]{2,})\b"), r"\1***\2"),
    )

    @classmethod
    def redact(cls, value: str) -> str:
        for pattern, replacement in cls.patterns:
            value = pattern.sub(replacement, value)
        return value

    @classmethod
    def sanitize(cls, value: Any) -> Any:
        if isinstance(value, str):
            return cls.redact(value)
        if isinstance(value, dict):
            return {key: cls.sanitize(item) for key, item in value.items()}
        if isinstance(value, tuple):
            return tuple(cls.sanitize(item) for item in value)
        if isinstance(value, list):
            return [cls.sanitize(item) for item in value]
        return value

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self.redact(str(record.msg))
        record.args = self.sanitize(record.args)
        return True


class StructuredFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        return datetime.fromtimestamp(record.created).astimezone().isoformat(timespec="milliseconds")

    def format(self, record: logging.LogRecord) -> str:
        record.corr_id = current_corr_id()
        return super().format(record)


class ColorFormatter(StructuredFormatter):
    COLORS = {logging.DEBUG: "\033[90m", logging.WARNING: "\033[33m",
              logging.ERROR: "\033[31m", logging.CRITICAL: "\033[31m"}

    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        if not sys.stderr.isatty():
            return text
        return self.COLORS.get(record.levelno, "") + text + "\033[0m"


FORMAT = "%(asctime)s | %(levelname)-7s | %(name)-24s | %(threadName)-14s | %(corr_id)s | %(message)s"


def _file_handler(path: Path, logger_filter: str | None = None) -> RotatingFileHandler:
    handler = RotatingFileHandler(path, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(StructuredFormatter(FORMAT))
    handler.addFilter(RedactionFilter())
    if logger_filter:
        handler.addFilter(lambda record: record.name.startswith(logger_filter))
    return handler


def setup_logging(debug: bool = False) -> logging.Logger:
    global _initialized
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    CRASH_DIR.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    if not any(isinstance(item, RedactionFilter) for item in root.filters):
        root.addFilter(RedactionFilter())
    if not _initialized:
        main_handler = _file_handler(LOG_PATH)
        http_handler = _file_handler(HTTP_LOG_PATH)
        http_handler.addFilter(lambda record: record.name.startswith(("urllib3", "requests", "http.client", "seedrfetch.http")))
        tls_handler = _file_handler(TLS_LOG_PATH, "seedrfetch.tls")
        console = logging.StreamHandler(sys.stderr)
        console.setLevel(logging.DEBUG if debug else logging.INFO)
        console.setFormatter(ColorFormatter(FORMAT)); console.addFilter(RedactionFilter())
        root.addHandler(main_handler); root.addHandler(console)
        for name in ("urllib3", "requests", "http.client", "seedrfetch.http"):
            logging.getLogger(name).addHandler(http_handler)
        logging.getLogger("seedrfetch.tls").addHandler(tls_handler)
        _initialized = True
    install_exception_hooks()
    return logging.getLogger("seedrfetch")


@contextmanager
def log_operation(name: str, **fields: Any) -> Iterator[str]:
    cid = secrets.token_hex(4)
    token = _corr_id_var.set(cid)
    failed_token = _operation_failed_var.set(False)
    log = logging.getLogger("op")
    started = time.monotonic()
    log.info("BEGIN %s %s", name, fields)
    try:
        yield cid
        outcome = "FAILED" if _operation_failed_var.get() else "ok"
        log.info("END   %s %s elapsed_ms=%d", name, outcome, (time.monotonic() - started) * 1000)
    except Exception:
        log.exception("END   %s FAILED elapsed_ms=%d", name, (time.monotonic() - started) * 1000)
        raise
    finally:
        _corr_id_var.reset(token)
        _operation_failed_var.reset(failed_token)


def correlated_tail(path: Path, corr_id: str, limit: int) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        matching = [line for line in lines if corr_id in line]
        return "\n".join(matching[-limit:])
    except OSError:
        return ""


def file_tail(path: Path, limit: int) -> str:
    try:
        return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:])
    except OSError:
        return ""


def detected_security_software() -> list[str]:
    if os.name != "nt":
        return []
    command = ("Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct "
               "| Select-Object -ExpandProperty displayName")
    try:
        result = subprocess.run(["powershell", "-NoProfile", "-Command", command],
                                capture_output=True, text=True, timeout=12, check=False)
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        logging.getLogger(__name__).exception("Security software query failed")
        return []


def build_snapshot(exc_info: tuple | None = None, corr_id: str | None = None) -> str:
    from core.ssl_setup import TRUSTSTORE_ACTIVE
    cid = corr_id or current_corr_id()
    exception = "No exception - current session diagnostics"
    if exc_info:
        exception = "".join(traceback.format_exception(*exc_info))
    env_names = ("HTTP_PROXY", "HTTPS_PROXY", "REQUESTS_CA_BUNDLE", "SSL_CERT_FILE", "NO_PROXY")
    environment = "\n".join("%s=%s" % (name, os.environ.get(name, "")) for name in env_names)
    try:
        ca_count = len(ssl.create_default_context().get_ca_certs())
    except Exception:
        ca_count = -1
    security = "\n".join(detected_security_software()) or "None detected or query unavailable"
    return f"""===== SeedrFetch Crash Report =====
Time:        {datetime.now().astimezone().isoformat(timespec='milliseconds')}
Version:     {APP_VERSION}
Python:      {platform.python_version()} ({platform.python_implementation()})
Platform:    {platform.platform()}
Locale:      {locale.getlocale()}
Correlation: {cid}

----- Exception -----
{exception}
----- Last 200 log lines (this correlation ID) -----
{correlated_tail(LOG_PATH, cid, 200)}

----- Last 50 HTTP wire lines -----
{file_tail(HTTP_LOG_PATH, 50)}

----- Last 20 TLS events -----
{file_tail(TLS_LOG_PATH, 20)}

----- Environment (sanitized) -----
{environment}

----- Detected security software -----
{security}

----- truststore status -----
truststore_active={TRUSTSTORE_ACTIVE}
openssl={ssl.OPENSSL_VERSION}
ca_cert_count={ca_count}
"""


def write_crash_dump(exc_info: tuple) -> Path:
    CRASH_DIR.mkdir(parents=True, exist_ok=True)
    path = CRASH_DIR / ("crash-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".txt")
    path.write_text(RedactionFilter.redact(build_snapshot(exc_info)), encoding="utf-8")
    return path


def _uncaught(exc_type, exc_value, exc_tb, main_thread: bool) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        logging.getLogger("app").info("Interrupted by user (Ctrl+C). Exiting.")
        return
    if issubclass(exc_type, SystemExit):
        return
    logging.getLogger("crash").critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))
    path = write_crash_dump((exc_type, exc_value, exc_tb))
    if main_thread:
        try:
            import tkinter as tk
            dialog = tk.Tk(); dialog.title("SeedrFetch crashed"); dialog.geometry("620x190")
            tk.Label(dialog, text="SeedrFetch encountered an unexpected error.",
                     font=("Segoe UI", 12, "bold")).pack(pady=(20, 8))
            tk.Label(dialog, text=str(path), wraplength=570).pack(padx=20, pady=8)
            row = tk.Frame(dialog); row.pack(pady=10)
            tk.Button(row, text="Copy path", command=lambda: (dialog.clipboard_clear(),
                      dialog.clipboard_append(str(path)))).pack(side="left", padx=6)
            tk.Button(row, text="Close", command=dialog.destroy).pack(side="left", padx=6)
            dialog.mainloop()
        except Exception:
            pass


def install_exception_hooks() -> None:
    sys.excepthook = lambda kind, value, tb: _uncaught(kind, value, tb, True)
    threading.excepthook = lambda args: _uncaught(args.exc_type, args.exc_value, args.exc_traceback, False)


def set_log_level(level: str) -> None:
    global TRACE_WIRE
    TRACE_WIRE = level == "TRACE-WIRE"
    logging.getLogger().setLevel(logging.INFO if level == "INFO" else logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.DEBUG if level != "INFO" else logging.INFO)
    logging.getLogger("requests").setLevel(logging.DEBUG if level != "INFO" else logging.INFO)
