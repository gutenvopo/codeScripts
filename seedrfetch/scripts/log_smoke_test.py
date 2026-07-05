"""Single-command logging and error-translation verification."""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.logging_setup import log_operation, setup_logging

setup_logging(debug=True)

from core import ssl_setup  # noqa: E402,F401
from core.config import HTTP_LOG_PATH, LOG_PATH, TLS_LOG_PATH  # noqa: E402
from core.errors import translate  # noqa: E402
from core.ssl_setup import make_session  # noqa: E402


def assert_contains(path: Path, needle: str) -> None:
    content = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    if needle not in content:
        raise AssertionError("%s does not contain %r" % (path, needle))


def main() -> int:
    try:
        with log_operation("log-smoke-test") as cid:
            import logging
            logging.getLogger("smoke").info("smoke test start")
            try:
                response = make_session().get(
                    "https://www.seedr.cc/rest/user",
                    auth=(os.environ.get("SEEDR_SMOKE_EMAIL", "wrong@example.invalid"),
                          os.environ.get("SEEDR_SMOKE_PASSWORD", "deliberately-wrong")),
                    timeout=(5, 10),
                )
                response.raise_for_status()
                raise AssertionError("Expected Seedr to reject deliberately wrong credentials")
            except AssertionError:
                raise
            except Exception as exc:
                error = translate(exc, cid)
                print(error)
        assert_contains(LOG_PATH, cid)
        assert_contains(HTTP_LOG_PATH, cid)
        assert_contains(TLS_LOG_PATH, cid)
        print("OK")
        return 0
    except Exception as exc:
        print("FAILED: %s" % exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
