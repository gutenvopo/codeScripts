from __future__ import annotations

import logging
import threading
import tkinter as tk
import webbrowser
from tkinter import ttk

import customtkinter as ctk
import pyperclip

from qbsearch.core.magnet_resolver import MagnetResolver
from qbsearch.core.result_model import SearchResult, filter_results, sort_results
from qbsearch.ui import theme
from qbsearch.ui.toast import Toast
from qbsearch.utils import human_size

log = logging.getLogger(__name__)


class ResultsTable(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_add,
        magnet_resolver: MagnetResolver,
    ) -> None:
        super().__init__(master, fg_color=theme.BG, corner_radius=0)
        self.on_add = on_add
        self.magnet_resolver = magnet_resolver
        self.results: list[SearchResult] = []
        self.visible: list[SearchResult] = []
        self.sort_key = "seeders"
        self.sort_reverse = True
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        theme.style_treeview()
        columns = ("name", "size", "seeders", "leechers", "engine", "site_url", "action")
        self.action_column_id = f"#{len(columns)}"
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="extended")
        self.tree.grid(row=0, column=0, sticky="nsew")
        vscroll = ttk.Scrollbar(
            self, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar"
        )
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll = ttk.Scrollbar(
            self, orient="horizontal", command=self.tree.xview, style="Horizontal.TScrollbar"
        )
        hscroll.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        self._setup_columns()
        footer = ctk.CTkFrame(self, fg_color=theme.PANEL, corner_radius=0)
        footer.grid(row=2, column=0, columnspan=2, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)
        self.count = ctk.CTkLabel(footer, text="0 results", text_color=theme.MUTED)
        self.filter_var = ctk.StringVar()
        self.filter_entry = ctk.CTkEntry(
            footer, textvariable=self.filter_var, placeholder_text="Filter results..."
        )
        self.filter_regex = ctk.CTkSwitch(footer, text="Regex")
        self.count.grid(row=0, column=0, padx=12, pady=8)
        self.filter_entry.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        self.filter_regex.grid(row=0, column=2, padx=12, pady=8)
        self.filter_var.trace_add("write", lambda *_: self.refresh())
        self.tree.bind("<Double-1>", lambda _event: self.copy_selected())
        self.tree.bind("<Button-1>", self._on_left_click)
        self.tree.bind("<Button-3>", self._context_menu)
        self.tree.bind("<Motion>", self._on_motion)
        self.tree.bind(
            "<Shift-MouseWheel>",
            lambda event: self.tree.xview_scroll(int(-event.delta / 120), "units"),
        )

    def _setup_columns(self) -> None:
        specs = {
            "name": ("Name", 480, 240, "w", True),
            "size": ("Size", 90, 80, "e", False),
            "seeders": ("Seeders", 80, 70, "e", False),
            "leechers": ("Leechers", 80, 70, "e", False),
            "engine": ("Engine", 130, 100, "w", False),
            "site_url": ("Engine URL", 260, 160, "w", False),
            "action": ("Action", 160, 160, "center", False),
        }
        for key, (label, width, minwidth, anchor, stretch) in specs.items():
            if key == "action":
                self.tree.heading(key, text=label)
            else:
                self.tree.heading(key, text=label, command=lambda item=key: self.sort_by(item))
            self.tree.column(
                key,
                width=width,
                minwidth=minwidth,
                anchor=anchor,
                stretch=stretch,
            )
        self.tree.tag_configure("odd", background="#0F172A")
        self.tree.tag_configure("even", background=theme.BG)
        self.tree.tag_configure("low", foreground=theme.DANGER)
        self.tree.tag_configure("mid", foreground=theme.WARNING)
        self.tree.tag_configure("high", foreground=theme.SUCCESS)

    def clear(self) -> None:
        self.results.clear()
        self.visible.clear()
        self.refresh()

    def add_results(self, rows: list[SearchResult]) -> None:
        self.results.extend(rows)
        self.refresh()

    def sort_by(self, key: str) -> None:
        if self.sort_key == key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_key = key
            self.sort_reverse = key in {"size", "seeders", "leechers"}
        self.refresh()

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        filtered = filter_results(self.results, self.filter_var.get())
        self.visible = sort_results(filtered, self.sort_key, self.sort_reverse)
        for index, result in enumerate(self.visible):
            tags = ["odd" if index % 2 else "even", self._seed_tag(result.seeders)]
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    self._ellipsis(result.name, 96),
                    human_size(result.size),
                    result.seeders,
                    result.leechers,
                    result.engine,
                    result.site_url,
                    "Copy magnet link",
                ),
                tags=tags,
            )
        self.count.configure(text=f"{len(self.visible)} results")

    def selected_results(self) -> list[SearchResult]:
        rows: list[SearchResult] = []
        for item in self.tree.selection():
            try:
                rows.append(self.visible[int(item)])
            except (ValueError, IndexError):
                continue
        return rows

    def copy_selected(self) -> None:
        rows = self.selected_results()
        if rows:
            self.copy_result_link(rows[0])

    def copy_result_link(self, result: SearchResult) -> None:
        state, value = self.magnet_resolver.prepare(result)
        if state == "ready" and value:
            self._copy_to_clipboard(value)
            return
        if state == "inflight":
            return
        if state != "fetch" or not value:
            log.warning("could not resolve magnet target for result %s", result.name)
            Toast.error(self, "Could not extract magnet from detail page")
            return
        info = Toast.info(self, "Fetching magnet link…")
        thread = threading.Thread(
            target=self._resolve_and_copy_worker,
            args=(result, value, info),
            daemon=True,
        )
        thread.start()

    def _resolve_and_copy_worker(
        self,
        result: SearchResult,
        detail_url: str,
        info_toast: Toast,
    ) -> None:
        magnet = self.magnet_resolver.resolve_detail(detail_url, result.name)
        self.after(0, self._finish_resolve, result, detail_url, magnet, info_toast)

    def _finish_resolve(
        self,
        result: SearchResult,
        detail_url: str,
        magnet: str | None,
        info_toast: Toast,
    ) -> None:
        info_toast.dismiss()
        if not magnet:
            log.warning(
                "could not extract magnet from detail page %s for %s",
                detail_url,
                result.name,
            )
            Toast.error(self, "Could not extract magnet from detail page")
            return
        self._copy_to_clipboard(magnet)

    def _copy_to_clipboard(self, value: str) -> None:
        try:
            pyperclip.copy(value)
        except Exception:
            log.exception("failed to copy magnet link")
            Toast.error(self, "Failed to copy — see log")
            return
        Toast.success(self, "Magnet link copied")

    def focus_filter(self) -> None:
        self.filter_entry.focus_set()

    def _on_left_click(self, event: tk.Event) -> str | None:
        if self.tree.identify_region(event.x, event.y) != "cell":
            return None
        if self.tree.identify_column(event.x) != self.action_column_id:
            return None
        item = self.tree.identify_row(event.y)
        if not item:
            return None
        try:
            result = self.visible[int(item)]
        except (ValueError, IndexError):
            return "break"
        self.copy_result_link(result)
        return "break"

    def _on_motion(self, event: tk.Event) -> None:
        over_action = (
            self.tree.identify_region(event.x, event.y) == "cell"
            and self.tree.identify_column(event.x) == self.action_column_id
            and bool(self.tree.identify_row(event.y))
        )
        self.tree.configure(cursor="hand2" if over_action else "")

    def _context_menu(self, event: tk.Event) -> None:
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
        result = self.selected_results()[0] if self.selected_results() else None
        if not result:
            return
        menu = tk.Menu(self, tearoff=0, bg=theme.PANEL, fg=theme.TEXT)
        menu.add_command(label="Send to qBittorrent", command=lambda: self.on_add(result, False))
        menu.add_command(
            label="Send to qBittorrent (paused)", command=lambda: self.on_add(result, True)
        )
        menu.add_separator()
        menu.add_command(label="Copy magnet link", command=lambda: self.copy_result_link(result))
        menu.add_command(
            label="Copy description page URL",
            command=lambda: pyperclip.copy(result.description_url),
        )
        menu.add_command(
            label="Open description page", command=lambda: webbrowser.open(result.description_url)
        )
        menu.add_command(label="Open engine site", command=lambda: webbrowser.open(result.site_url))
        menu.tk_popup(event.x_root, event.y_root)

    @staticmethod
    def _ellipsis(value: str, limit: int) -> str:
        return value if len(value) <= limit else f"{value[: limit - 1]}..."

    @staticmethod
    def _seed_tag(seeders: int) -> str:
        if seeders >= 50:
            return "high"
        if seeders >= 10:
            return "mid"
        return "low"
