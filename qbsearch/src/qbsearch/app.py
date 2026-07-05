from __future__ import annotations

import queue
import re
import tkinter as tk
from pathlib import Path
from tkinter import simpledialog

import customtkinter as ctk

from qbsearch.api.qbittorrent import QbtAuthError, QbtClient
from qbsearch.config import AppSettings, load_password, load_settings, save_settings
from qbsearch.core.magnet_resolver import MagnetResolver
from qbsearch.core.regex_filter import compile_pattern, longest_alphanumeric_token
from qbsearch.core.result_model import SearchResult
from qbsearch.core.search_controller import SearchController, SearchRequest
from qbsearch.ui import theme
from qbsearch.ui.engine_panel import EnginePanel
from qbsearch.ui.results_table import ResultsTable
from qbsearch.ui.search_bar import SearchBar
from qbsearch.ui.settings_dialog import SettingsDialog
from qbsearch.ui.status_bar import StatusBar


class QbSearchApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.settings = load_settings()
        theme.apply_theme(self.settings.theme)
        self.client = QbtClient()
        self.magnet_resolver = MagnetResolver()
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.controller = SearchController(self.client, self.events)
        self.last_request: SearchRequest | None = None
        self.title("qbSearch - qBittorrent Search Client")
        self.minsize(1280, 720)
        self.geometry(self.settings.geometry or "1280x720")
        self._center_if_new()
        self._set_icon()
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.search_bar = SearchBar(self, self.start_search, self.stop_search, self.open_settings)
        self.search_bar.grid(row=0, column=0, sticky="ew")
        body = ctk.CTkFrame(self, fg_color=theme.BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)
        self.engines = EnginePanel(body)
        self.engines.grid(row=0, column=0, sticky="nsw")
        self.results = ResultsTable(body, self.add_torrent, self.magnet_resolver)
        self.results.grid(row=0, column=1, sticky="nsew")
        self.status = StatusBar(self)
        self.status.grid(row=2, column=0, sticky="ew")
        self._bind_keys()
        self.after(100, self.drain_events)
        self.after(300, self.connect_on_startup)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def connect_on_startup(self) -> None:
        password = load_password(self.settings)
        if not password:
            self.open_settings(welcome=True)
            return
        try:
            self.client.login(
                self.settings.host, self.settings.port, self.settings.username, password
            )
            plugins = self.client.list_plugins()
        except Exception as exc:  # noqa: BLE001
            self.status.set_connected("Disconnected", False)
            self.status.set_status(str(exc))
            self.open_settings(welcome=True)
            return
        self.engines.set_plugins(plugins)
        self.status.set_connected(
            f"Connected to qBittorrent @ {self.settings.host}:{self.settings.port}", True
        )

    def start_search(self) -> None:
        query = self.search_bar.query()
        if not query:
            self.status.set_status("Enter a search query.")
            return
        regex = None
        broad_query = query
        if self.search_bar.regex_var.get():
            try:
                regex = compile_pattern(query)
            except re.error as exc:
                self.status.set_status(f"Regex error: {exc}")
                return
            broad_query = longest_alphanumeric_token(query)
        request = SearchRequest(
            pattern=broad_query,
            plugins=self.engines.selected_plugins(),
            category=self.search_bar.category_value(),
            regex=regex,
        )
        self.last_request = request
        self.results.clear()
        self.search_bar.set_running(True)
        self.status.set_running(True)
        self.controller.start(request)

    def stop_search(self) -> None:
        self.controller.stop()
        self.search_bar.set_running(False)
        self.status.set_running(False)
        self.status.set_status("Stopping search...")

    def add_torrent(self, result: SearchResult, paused: bool) -> None:
        savepath = self.settings.default_save_path
        category = self.settings.default_category
        if not savepath:
            savepath = (
                simpledialog.askstring("Save path", "Optional qBittorrent save path:", parent=self)
                or ""
            )
        if not category:
            category = (
                simpledialog.askstring("Category", "Optional qBittorrent category:", parent=self)
                or ""
            )
        try:
            self.client.add_torrent(
                result.copy_url,
                savepath=savepath or None,
                category=category or None,
                paused=paused or self.settings.add_paused_by_default,
            )
        except QbtAuthError:
            self.status.set_status("Please log in again before adding torrents.")
            self.open_settings()
            return
        except Exception as exc:  # noqa: BLE001
            self.status.set_status(str(exc))
            return
        self.status.set_status("Sent to qBittorrent.")

    def open_settings(self, welcome: bool = False) -> None:
        SettingsDialog(
            self, self.settings, load_password(self.settings), self._settings_saved, welcome=welcome
        )

    def drain_events(self) -> None:
        processed = 0
        while processed < 200:
            try:
                kind, payload = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "results":
                self.results.add_results(payload)  # type: ignore[arg-type]
            elif kind == "status":
                self.status.set_status(str(payload))
            elif kind == "error" or kind == "complete":
                self.status.set_status(str(payload))
                self.search_bar.set_running(False)
                self.status.set_running(False)
            processed += 1
        self.after(100, self.drain_events)

    def on_close(self) -> None:
        self.settings.geometry = self.geometry()
        save_settings(self.settings)
        self.controller.close()
        self.client.close()
        self.destroy()

    def _settings_saved(self, settings: AppSettings) -> None:
        self.settings = settings
        theme.apply_theme(settings.theme)
        self.connect_on_startup()

    def _bind_keys(self) -> None:
        self.bind("<Return>", lambda _event: self.start_search())
        self.bind("<Escape>", lambda _event: self.stop_search())
        self.bind(
            "<F5>",
            lambda _event: self.controller.start(self.last_request) if self.last_request else None,
        )
        self.bind("<Control-f>", lambda _event: self.results.focus_filter())
        self.bind("<Control-l>", lambda _event: self.search_bar.entry.focus_set())

    def _center_if_new(self) -> None:
        if self.settings.geometry:
            return
        self.update_idletasks()
        width, height = 1280, 720
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _set_icon(self) -> None:
        icon = Path(__file__).with_name("assets") / "qbsearch.png"
        if icon.exists():
            self.iconphoto(True, tk.PhotoImage(file=str(icon)))
