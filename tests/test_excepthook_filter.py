from __future__ import annotations

import sys
import threading
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "seedrfetch"))

from core import logging_setup


def test_keyboard_interrupt_does_not_write_crash_dump(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(logging_setup, "CRASH_DIR", tmp_path)
    old_hook = sys.excepthook
    try:
        logging_setup.install_exception_hooks()
        sys.excepthook(KeyboardInterrupt, KeyboardInterrupt(), None)
    finally:
        sys.excepthook = old_hook

    assert list(tmp_path.glob("crash-*.txt")) == []


def test_thread_value_error_writes_crash_dump(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(logging_setup, "CRASH_DIR", tmp_path)
    old_thread_hook = threading.excepthook
    try:
        logging_setup.install_exception_hooks()
        threading.excepthook(SimpleNamespace(
            exc_type=ValueError,
            exc_value=ValueError("boom"),
            exc_traceback=None,
            thread=SimpleNamespace(name="worker"),
        ))
    finally:
        threading.excepthook = old_thread_hook

    assert len(list(tmp_path.glob("crash-*.txt"))) == 1
