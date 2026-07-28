from __future__ import annotations

import logging
import queue
import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from qbsearch.ui import theme


class VerboseLogHandler(logging.Handler):
    """Send selected log records to a thread-safe queue.

    Logging can happen in resolver worker threads, so this handler must never
    call Tk directly.
    """

    def __init__(
        self,
        messages: queue.SimpleQueue[tuple[int, str]],
        include_names: tuple[str, ...],
    ) -> None:
        super().__init__()
        self.messages = messages
        self.include_names = include_names

    def emit(self, record: logging.LogRecord) -> None:
        if not any(record.name.startswith(name) for name in self.include_names):
            return
        try:
            message = self.format(record)
        except Exception:
            self.handleError(record)
            return
        self.messages.put((record.levelno, message))


class VerboseLogWindow:
    LOGGER_NAMES = (
        "qbsearch.core.magnet_resolver",
        "qbsearch.ui.results_table",
    )

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        title: str = "Magnet link activity",
    ) -> None:
        root = master.winfo_toplevel()
        self.window = tk.Toplevel(root)
        self.window.title(title)
        self.window.geometry("840x440")
        self.window.minsize(640, 320)
        self.window.configure(bg=theme.PANEL)
        self.window.transient(root)
        self.window.attributes("-topmost", True)
        self.window.after(900, self._drop_topmost)

        frame = ctk.CTkFrame(self.window, fg_color=theme.BG, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 6))
        header.grid_columnconfigure(0, weight=1)
        self.title_label = ctk.CTkLabel(
            header,
            text=title,
            text_color=theme.TEXT,
            font=(theme.FONT, 15, "bold"),
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        self.status_label = ctk.CTkLabel(
            header,
            text="LIVE",
            text_color=theme.SUCCESS,
            font=(theme.MONO, 10, "bold"),
        )
        self.status_label.grid(row=0, column=1, padx=(8, 0))

        text_frame = tk.Frame(frame, bg=theme.BG)
        text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.text = tk.Text(
            text_frame,
            wrap="word",
            state="disabled",
            bg=theme.BG,
            fg=theme.TEXT,
            insertbackground=theme.TEXT,
            selectbackground=theme.ACCENT,
            font=(theme.MONO, 10),
            relief="flat",
            padx=8,
            pady=8,
        )
        self.text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        scrollbar.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.tag_configure("debug", foreground=theme.MUTED)
        self.text.tag_configure("info", foreground=theme.TEXT)
        self.text.tag_configure("warning", foreground=theme.WARNING)
        self.text.tag_configure("error", foreground=theme.DANGER)
        self.text.tag_configure("system", foreground=theme.ACCENT)

        actions = ctk.CTkFrame(frame, fg_color="transparent")
        actions.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(
            actions,
            text="Copy log",
            width=92,
            command=self.copy_log,
        ).pack(side="left")
        ctk.CTkButton(
            actions,
            text="Clear",
            width=76,
            fg_color=theme.ELEVATED,
            hover_color=theme.BORDER,
            command=self.clear,
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            actions,
            text="Close",
            width=76,
            fg_color=theme.ELEVATED,
            hover_color=theme.BORDER,
            command=self._on_close,
        ).pack(side="right")

        self.messages: queue.SimpleQueue[tuple[int, str]] = queue.SimpleQueue()
        self.handler = VerboseLogHandler(
            self.messages,
            include_names=self.LOGGER_NAMES,
        )
        self.handler.setLevel(logging.DEBUG)
        self.handler.setFormatter(
            logging.Formatter(
                "%(asctime)s  %(levelname)-7s  %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        self.logger: logging.Logger | None = None
        self.previous_levels: dict[str, int] = {}

        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        self.window.after(80, self._drain_messages)

    def attach(self, logger: logging.Logger | None = None) -> None:
        if self.logger:
            return
        self.logger = logger or logging.getLogger()
        self.logger.addHandler(self.handler)
        for name in self.LOGGER_NAMES:
            child = logging.getLogger(name)
            self.previous_levels[name] = child.level
            child.setLevel(logging.DEBUG)

    def detach(self) -> None:
        if self.logger:
            self.logger.removeHandler(self.handler)
            self.logger = None
        for name, level in self.previous_levels.items():
            logging.getLogger(name).setLevel(level)
        self.previous_levels.clear()

    def start_session(self, result_name: str, engine: str) -> None:
        self._discard_messages()
        self.clear()
        self.title_label.configure(text="Magnet link activity")
        self.status_label.configure(text="LIVE", text_color=theme.SUCCESS)
        self._append(
            f"New request: {result_name}\nSearch engine: {engine or 'unknown'}",
            "system",
        )
        self.window.deiconify()
        self.window.lift()

    def finish(self, success: bool) -> None:
        text = "COMPLETE" if success else "FAILED"
        color = theme.SUCCESS if success else theme.DANGER
        self.status_label.configure(text=text, text_color=color)

    def clear(self) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")

    def copy_log(self) -> None:
        value = self.text.get("1.0", "end-1c")
        self.window.clipboard_clear()
        self.window.clipboard_append(value)
        self.window.update_idletasks()

    def is_open(self) -> bool:
        return bool(self.window.winfo_exists())

    def _drain_messages(self) -> None:
        if not self.window.winfo_exists():
            return
        drained = 0
        while drained < 200:
            try:
                level, message = self.messages.get_nowait()
            except queue.Empty:
                break
            self._append(message, self._tag_for_level(level))
            drained += 1
        self.window.after(80, self._drain_messages)

    def _discard_messages(self) -> None:
        while True:
            try:
                self.messages.get_nowait()
            except queue.Empty:
                return

    def _append(self, message: str, tag: str) -> None:
        self.text.configure(state="normal")
        self.text.insert("end", f"{message}\n", tag)
        self.text.see("end")
        self.text.configure(state="disabled")

    def _on_close(self) -> None:
        self.detach()
        self.window.destroy()

    def _drop_topmost(self) -> None:
        if self.is_open():
            self.window.attributes("-topmost", False)

    @staticmethod
    def _tag_for_level(level: int) -> str:
        if level >= logging.ERROR:
            return "error"
        if level >= logging.WARNING:
            return "warning"
        if level <= logging.DEBUG:
            return "debug"
        return "info"
