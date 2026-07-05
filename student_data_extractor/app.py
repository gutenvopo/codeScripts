"""Main CustomTkinter application."""

from __future__ import annotations

import logging
import logging.handlers
import queue
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from extractor import ProgressMessage, extract_archives_worker, scan_archives
from report import ExtractionReport
from settings import AppSettings, LOG_PATH, ensure_app_dir, load_settings, save_settings
from ui.action_bar import ActionBar
from ui.header import Header
from ui.log_view import LogView
from ui.options_section import OptionsSection
from ui.progress_section import ProgressSection
from ui.report_window import ReportWindow
from ui.source_section import SourceSection


class StudentDataExtractorApp(ctk.CTk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Student Data Extractor")
        self.geometry("900x650")
        self.minsize(900, 650)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        ensure_app_dir()
        self.logger = self._configure_logging()
        self.settings = load_settings()
        self.selected_root: Path | None = None
        self.worker: threading.Thread | None = None
        self.cancel_event = threading.Event()
        self.messages: queue.Queue[ProgressMessage] = queue.Queue()
        self.latest_report: ExtractionReport | None = None

        ctk.set_default_color_theme("blue")
        self._apply_theme(self.settings.theme)

        self.header = Header(self, self.on_theme_change)
        self.header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 10))
        self.header.set_theme(self.settings.theme)

        self.source = SourceSection(self, self.select_folder)
        self.source.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        self.options = OptionsSection(self, self.confirm_delete_archives)
        self.options.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 10))
        self.options.load_settings(self.settings)

        self.action_bar = ActionBar(self, self.start_extraction, self.cancel_extraction)
        self.action_bar.grid(row=3, column=0, sticky="w", padx=16, pady=(0, 4))

        self.progress = ProgressSection(self)
        self.progress.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 10))

        self.log_view = LogView(self)
        self.log_view.grid(row=5, column=0, sticky="nsew", padx=16, pady=(0, 10))

        self.footer = ctk.CTkLabel(
            self,
            text="Idle",
            corner_radius=999,
            fg_color=("#e5e7eb", "#374151"),
            width=120,
            height=28,
        )
        self.footer.grid(row=6, column=0, sticky="w", padx=16, pady=(0, 16))

        self.bind("<Control-o>", lambda _event: self.select_folder())
        self.bind("<Escape>", lambda _event: self.cancel_extraction())
        self.bind("<Control-q>", lambda _event: self.destroy())
        self.after(120, self.consume_worker_messages)

    def _configure_logging(self) -> logging.Logger:
        logger = logging.getLogger("student_data_extractor")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

        file_handler = logging.handlers.RotatingFileHandler(
            LOG_PATH,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        logger.info("Application started")
        return logger

    def select_folder(self) -> None:
        """Open the native folder picker."""

        chosen = filedialog.askdirectory(title="Select root folder")
        if not chosen:
            return
        root = Path(chosen)
        self.selected_root = root
        self.logger.info("Selected source folder: %s", root)
        self.source.set_path(str(root))
        self.validate_root()

    def validate_root(self) -> bool:
        """Validate the selected source folder."""

        if self.selected_root is None:
            self.source.set_error("Choose a folder before starting.")
            return False
        if not self.selected_root.exists() or not self.selected_root.is_dir():
            self.source.set_error("Selected path is not a valid folder.")
            return False
        try:
            next(self.selected_root.iterdir(), None)
        except OSError as exc:
            self.source.set_error(f"Folder is not readable: {exc}")
            return False
        self.source.set_error("")
        return True

    def start_extraction(self) -> None:
        """Scan and start extraction after the user confirms the summary."""

        if self.worker and self.worker.is_alive():
            return
        if not self.validate_root() or self.selected_root is None:
            return

        settings = self.options.to_settings(self.header.theme_menu.get())
        save_settings(settings)
        self.settings = settings
        self.set_status("Scanning")
        self.log_view.clear()
        self.progress.reset()
        self.logger.info(
            "Scanning %s (recurse=%s, include_root=%s)",
            self.selected_root,
            settings.recurse,
            settings.include_root,
        )

        try:
            archives = scan_archives(self.selected_root, settings)
        except OSError as exc:
            self.set_status("Error")
            self.source.set_error(f"Could not scan folder: {exc}")
            self.logger.exception("Scan failed")
            return

        folder_count = len({archive.parent for archive in archives})
        summary = f"Found {len(archives)} archives across {folder_count} folders"
        self.logger.info(summary)
        self.log_view.append(summary, "info")
        self.progress.update_progress(0, len(archives), summary)
        self.set_status("Idle")

        if not archives:
            self.logger.info("Extraction not started because no archives were found")
            messagebox.showinfo("No archives found", summary, parent=self)
            return
        if not messagebox.askyesno("Start extraction?", f"{summary}\n\nContinue?", parent=self):
            self.logger.info("Extraction cancelled before start")
            return

        self.cancel_event.clear()
        self.latest_report = None
        self.set_running(True)
        self.set_status("Extracting")
        self.logger.info("Starting extraction for %d archives", len(archives))
        self.worker = threading.Thread(
            target=extract_archives_worker,
            args=(
                self.selected_root,
                archives,
                settings,
                self.messages,
                self.cancel_event,
                self.logger,
            ),
            daemon=True,
        )
        self.worker.start()

    def cancel_extraction(self) -> None:
        """Request cancellation after the current archive finishes."""

        if self.worker and self.worker.is_alive():
            self.cancel_event.set()
            self.set_status("Cancelled")
            self.logger.info("Cancel requested")
            self.log_view.append("Cancel requested. Waiting for current archive to finish.", "warning")

    def consume_worker_messages(self) -> None:
        """Process worker thread messages on the UI thread."""

        try:
            while True:
                message = self.messages.get_nowait()
                self.handle_worker_message(message)
        except queue.Empty:
            pass
        self.after(120, self.consume_worker_messages)

    def handle_worker_message(self, message: ProgressMessage) -> None:
        """Apply a worker message to widgets."""

        if message.kind == "log":
            self.log_view.append(message.text, message.level)
        elif message.kind == "progress":
            self.progress.update_progress(message.current, message.total, message.text)
        elif message.kind == "done":
            self.set_running(False)
            self.set_status("Done")
            self.latest_report = message.report
            if message.report:
                self.logger.info(
                    "Extraction complete: %d archives processed in %.2f seconds",
                    message.report.total_found,
                    message.report.elapsed_seconds,
                )
            self.log_view.append("✅ Extraction complete.", "info")
            if message.report:
                ReportWindow(self, message.report)
        elif message.kind == "cancelled":
            self.set_running(False)
            self.set_status("Cancelled")
            self.latest_report = message.report
            if message.report:
                self.logger.info(
                    "Extraction cancelled: %d of %d archives processed in %.2f seconds",
                    len(message.report.rows),
                    message.report.total_found,
                    message.report.elapsed_seconds,
                )
            self.log_view.append("⚠ Extraction cancelled.", "warning")
            if message.report:
                ReportWindow(self, message.report)

    def on_theme_change(self, value: str) -> None:
        """Apply and persist theme changes."""

        self._apply_theme(value)
        self.settings = self.options.to_settings(value)
        save_settings(self.settings)

    def _apply_theme(self, value: str) -> None:
        appearance = "system" if value == "System" else value.lower()
        ctk.set_appearance_mode(appearance)

    def confirm_delete_archives(self) -> None:
        """Confirm destructive archive deletion."""

        if not messagebox.askyesno(
            "Delete archives?",
            "Delete archive after extraction removes the original archive files. Continue?",
            parent=self,
        ):
            self.options.after_menu.set("Keep")

    def set_running(self, running: bool) -> None:
        """Enable or disable controls while a worker is running."""

        self.action_bar.set_running(running)
        self.source.set_enabled(not running)
        self.options.set_enabled(not running)

    def set_status(self, value: str) -> None:
        """Set footer status pill text."""

        self.footer.configure(text=value)
