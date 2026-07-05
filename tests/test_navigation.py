from __future__ import annotations

import logging
import sys
from pathlib import Path
from types import MethodType, SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "seedrfetch"))

from ui.dashboard_view import DashboardView


PAYLOADS = {
    None: {"folder_id": None, "name": "", "fullname": "/", "parent": -1, "folders": []},
    1: {"folder_id": 1, "name": "A", "fullname": "/A", "parent": -1, "folders": []},
    2: {"folder_id": 2, "name": "B", "fullname": "/A/B", "parent": 1, "folders": []},
    3: {"folder_id": 3, "name": "C", "fullname": "/C", "parent": -1, "folders": []},
}


class FakeBackend:
    def get_drive(self) -> dict:
        return PAYLOADS[None]

    def get_folder(self, folder_id: int) -> dict:
        return PAYLOADS[folder_id]


class FakeApp:
    def __init__(self) -> None:
        self.backend = FakeBackend()
        self.logger = logging.getLogger("test")

    def run_worker(self, function, *args) -> None:
        function(*args)

    def post(self, function, *args, **kwargs) -> None:
        function(*args, **kwargs)

    def toast(self, *_args, **_kwargs) -> None:
        pass


def make_view() -> SimpleNamespace:
    view = SimpleNamespace()
    view.app = FakeApp()
    view._nav_stack = []
    view._current_folder_id = None
    view._current_folder_payload = None
    view._fullname_folder_ids = {"/": None}
    view._render_tree = lambda _payload: None
    view._render_breadcrumb = lambda _payload: None
    view._update_nav_buttons = lambda: None
    for name in (
        "navigate_to",
        "navigate_up",
        "navigate_back",
        "_start_folder_load",
        "_folder_load_worker",
        "_on_folder_loaded",
        "_cache_folder_ids",
    ):
        setattr(view, name, MethodType(getattr(DashboardView, name), view))
    return view


def test_navigate_to_child_then_back_returns_to_root() -> None:
    view = make_view()
    view.navigate_to(1)
    view.navigate_back()
    assert view._current_folder_id is None


def test_multiple_back_steps_return_through_history() -> None:
    view = make_view()
    view.navigate_to(1)
    view.navigate_to(2)
    view.navigate_back()
    assert view._current_folder_id == 1
    view.navigate_back()
    assert view._current_folder_id is None


def test_navigate_up_from_root_is_noop() -> None:
    view = make_view()
    view.navigate_to(None, push_history=False)
    view.navigate_up()
    assert view._current_folder_id is None
    assert view._nav_stack == []


def test_navigate_up_from_child_uses_parent() -> None:
    view = make_view()
    view.navigate_to(2)
    view.navigate_up()
    assert view._current_folder_id == 1


def test_navigate_up_parent_minus_one_routes_to_root() -> None:
    view = make_view()
    view.navigate_to(3)
    view.navigate_up()
    assert view._current_folder_id is None


def test_push_history_false_does_not_modify_back_stack() -> None:
    view = make_view()
    view.navigate_to(1, push_history=False)
    assert view._current_folder_id == 1
    assert view._nav_stack == []
