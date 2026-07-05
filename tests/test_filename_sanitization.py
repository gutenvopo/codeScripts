from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "seedrfetch"))

from core.downloader import _sanitize_filename


def test_reserved_windows_name_gets_safe_suffix() -> None:
    assert _sanitize_filename("CON") == "CON_"


def test_path_separators_are_replaced() -> None:
    assert _sanitize_filename("foo/bar.mkv") == "foo_bar.mkv"


def test_trailing_dot_is_removed() -> None:
    assert _sanitize_filename("trailing.") == "trailing"


def test_long_stem_is_truncated_and_extension_is_preserved() -> None:
    value = _sanitize_filename("%s.txt" % ("a" * 300))

    assert value.endswith(".txt")
    assert len(Path(value).stem) == 240
