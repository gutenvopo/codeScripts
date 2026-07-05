from __future__ import annotations

import logging
import sys
from pathlib import Path
from types import MethodType, SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "seedrfetch"))

from ui.dashboard_view import DashboardView, _make_iid


class FakeTree:
    def __init__(self) -> None:
        self.nodes: dict[str, dict] = {}

    def get_children(self, _parent: str = "") -> list[str]:
        return list(self.nodes)

    def delete(self, iid: str) -> None:
        self.nodes.pop(iid, None)

    def insert(self, _parent: str, _index: str, **kwargs) -> str:
        iid = kwargs["iid"]
        self.nodes[iid] = kwargs
        return iid


class FakeWidget:
    def pack(self, *_args, **_kwargs) -> None:
        return None

    def pack_forget(self) -> None:
        return None

    def configure(self, **_kwargs) -> None:
        return None


class FakeConfig:
    def __init__(self, dest: Path) -> None:
        self.dest = dest

    def get(self, key: str) -> str:
        assert key == "download_destination"
        return str(self.dest)


class FakeApp:
    def __init__(self, dest: Path) -> None:
        self.config = FakeConfig(dest)
        self.toasts: list[tuple[object, bool]] = []
        self.logger = logging.getLogger("test")

    def toast(self, message, danger: bool = False, **_kwargs) -> None:
        self.toasts.append((message, danger))


class FakeDownloader:
    def __init__(self) -> None:
        self.files: list[dict] = []
        self.folders: list[dict] = []

    def submit_file(self, file_id: int, display_name: str, dest_dir: Path, suggested_filename: str) -> str:
        self.files.append({
            "file_id": file_id,
            "display_name": display_name,
            "dest_dir": dest_dir,
            "suggested_filename": suggested_filename,
        })
        return "job-file"

    def submit_folder(self, folder_id: int, display_name: str, dest_dir: Path, suggested_filename: str) -> str:
        self.folders.append({
            "folder_id": folder_id,
            "display_name": display_name,
            "dest_dir": dest_dir,
            "suggested_filename": suggested_filename,
        })
        return "job-folder"


def make_view(tmp_path: Path) -> SimpleNamespace:
    view = SimpleNamespace()
    view.tree = FakeTree()
    view.items = {}
    view.empty = FakeWidget()
    view.transfer_text = FakeWidget()
    view.storage = FakeWidget()
    view._refresh_job = None
    view.app = FakeApp(tmp_path)
    view.downloader = FakeDownloader()
    view.after_cancel = lambda _job: None
    view.after = lambda _delay, _callback: "refresh-job"
    view.refresh = lambda: None
    view._size = DashboardView._size
    for name in ("_render_tree", "download", "_submit_download", "_lookup_item"):
        setattr(view, name, MethodType(getattr(DashboardView, name), view))
    return view


def test_render_tree_uses_explicit_iids_as_item_keys(tmp_path: Path) -> None:
    view = make_view(tmp_path)
    payload = {
        "folders": [{"id": 11, "name": "Movies"}, {"folder_id": 12, "name": "Shows"}],
        "files": [
            {"folder_file_id": 99887, "name": "one.mkv"},
            {"id": 99888, "name": "two.mkv"},
            {"folder_file_id": 99889, "name": "three.mkv"},
        ],
    }

    view._render_tree(payload)

    assert set(view.tree.get_children("")) == set(view.items)
    assert _make_iid("file", 99887) in view.items
    assert all(not iid.startswith("I") for iid in view.tree.get_children(""))


def test_download_known_file_iid_submits_file_job(tmp_path: Path) -> None:
    view = make_view(tmp_path)
    view._render_tree({"files": [{"folder_file_id": 99887, "name": "one.mkv"}]})

    view.download(_make_iid("file", 99887))

    assert view.downloader.files == [{
        "file_id": 99887,
        "display_name": "one.mkv",
        "dest_dir": tmp_path,
        "suggested_filename": "one.mkv",
    }]


def test_download_known_folder_iid_submits_folder_job(tmp_path: Path) -> None:
    view = make_view(tmp_path)
    view._render_tree({"folders": [{"id": 44, "name": "Season"}]})

    view.download(_make_iid("folder", 44))

    assert view.downloader.folders == [{
        "folder_id": 44,
        "display_name": "Season",
        "dest_dir": tmp_path,
        "suggested_filename": "Season.zip",
    }]


def test_download_unknown_iid_warns_and_toasts_without_exception(tmp_path: Path, caplog) -> None:
    view = make_view(tmp_path)

    with caplog.at_level(logging.WARNING):
        view.download("bogus-iid")

    assert "unknown iid=bogus-iid" in caplog.text
    assert view.app.toasts == [("Couldn't find that item - try refreshing the folder.", True)]
