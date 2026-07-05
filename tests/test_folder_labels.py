from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "seedrfetch"))

from ui.dashboard_view import _file_label, _folder_label


def test_folder_label_uses_name() -> None:
    assert _folder_label({"name": "X", "id": 1}) == "X"


def test_folder_label_falls_back_for_empty_name() -> None:
    assert _folder_label({"name": "", "id": 1}) == "(unnamed folder 1)"


def test_folder_label_falls_back_for_missing_name() -> None:
    assert _folder_label({"id": 1}) == "(unnamed folder 1)"


def test_file_label_uses_name() -> None:
    assert _file_label({"name": "movie.mkv", "folder_file_id": 7}) == "movie.mkv"


def test_file_label_falls_back_for_empty_name() -> None:
    assert _file_label({"name": "", "folder_file_id": 7}) == "(unnamed file 7)"


def test_file_label_falls_back_for_missing_name() -> None:
    assert _file_label({"id": 7}) == "(unnamed file 7)"
