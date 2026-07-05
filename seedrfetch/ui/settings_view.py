"""Settings, diagnostics, account, and logs."""
from __future__ import annotations

import json
import os
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk

from core.config import CRASH_DIR, HTTP_LOG_PATH, LOG_DIR, LOG_PATH, TLS_LOG_PATH
from core.diagnostics import run_all
from core.logging_setup import RedactionFilter, build_snapshot, log_operation, set_log_level
from core.ssl_setup import TRUSTSTORE_ACTIVE, https_inspection_warning, make_session
from ui.theme import *
from ui.widgets import GlowFrame, NeonButton


def open_path(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.startfile(path)  # type: ignore[attr-defined]


class SettingsView(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=BG_DEEP)
        self.app = app
        ctk.CTkLabel(self, text="SETTINGS", font=(FONT, 28, "bold"), text_color=ACCENT).pack(anchor="w", padx=24, pady=(24, 10))
        self._destination(); self._network(); self._account(); self._logs(); self._about()

    def card(self, title: str) -> GlowFrame:
        frame = GlowFrame(self); frame.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(frame, text=title, font=(FONT, 16, "bold")).pack(anchor="w", padx=16, pady=(13, 7))
        return frame

    def _destination(self) -> None:
        card = self.card("Download destination")
        self.destination = ctk.CTkLabel(card, text=self.app.config.get("download_destination"), text_color=TEXT_MUTED)
        self.destination.pack(anchor="w", padx=16, pady=5)
        row = ctk.CTkFrame(card, fg_color="transparent"); row.pack(anchor="w", padx=12, pady=(3, 14))
        NeonButton(row, text="Change...", width=110, command=self.choose_destination).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Open folder", fg_color=BG_ELEVATED,
                      command=lambda: open_path(Path(self.app.config.get("download_destination")))).pack(side="left", padx=4)

    def _network(self) -> None:
        card = self.card("SSL & Network")
        status = "Using Windows certificate store  [OK]" if TRUSTSTORE_ACTIVE else "Using Python/certifi certificate store"
        ctk.CTkLabel(card, text=status, text_color=SUCCESS if TRUSTSTORE_ACTIVE else WARNING).pack(anchor="w", padx=16, pady=5)
        warning = https_inspection_warning()
        if warning:
            ctk.CTkLabel(card, text=warning, text_color=WARNING, wraplength=800,
                         justify="left").pack(anchor="w", padx=16, pady=5)
        self.ca = self._entry(card, "Custom CA bundle (.pem)", self.app.config.get("custom_ca_bundle", ""))
        row = ctk.CTkFrame(card, fg_color="transparent"); row.pack(anchor="w", padx=12)
        ctk.CTkButton(row, text="Browse", width=90, command=self.choose_ca).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Clear", width=70, fg_color=BG_ELEVATED, command=lambda: self.ca.delete(0, "end")).pack(side="left", padx=4)
        self.http = self._entry(card, "HTTP proxy", self.app.config.get("http_proxy", ""))
        self.https = self._entry(card, "HTTPS proxy", self.app.config.get("https_proxy", ""))
        self.insecure = ctk.CTkCheckBox(card, text="Disable SSL verification (NOT RECOMMENDED)", text_color=DANGER,
                                        command=self.confirm_insecure)
        self.insecure.pack(anchor="w", padx=16, pady=8)
        if self.app.config.get("disable_ssl_verify"): self.insecure.select()
        row = ctk.CTkFrame(card, fg_color="transparent"); row.pack(anchor="w", padx=12, pady=(3, 14))
        NeonButton(row, text="Save network settings", command=self.save_network).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Run Diagnostics", fg_color=ACCENT_2, command=self.run_diagnostics).pack(side="left", padx=4)

    @staticmethod
    def _entry(card, label: str, value: str):
        ctk.CTkLabel(card, text=label, text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(7, 2))
        entry = ctk.CTkEntry(card); entry.pack(fill="x", padx=16, pady=2); entry.insert(0, value)
        return entry

    def _account(self) -> None:
        card = self.card("Account")
        identity = self.app.identity or "Not signed in"
        ctk.CTkLabel(card, text=identity, text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=6)
        ctk.CTkButton(card, text="Sign out", fg_color=DANGER, command=self.app.sign_out).pack(anchor="w", padx=16, pady=(4, 14))

    def _logs(self) -> None:
        card = self.card("Logs")
        row = ctk.CTkFrame(card, fg_color="transparent"); row.pack(anchor="w", padx=12, pady=(3, 14))
        ctk.CTkButton(row, text="Open logs folder", fg_color=BG_ELEVATED, command=lambda: open_path(LOG_DIR)).pack(side="left", padx=4)
        crashes = sorted(CRASH_DIR.glob("crash-*.txt"), reverse=True) if CRASH_DIR.exists() else []
        ctk.CTkButton(row, text="Open latest crash", fg_color=BG_ELEVATED,
                      state="normal" if crashes else "disabled",
                      command=lambda: os.startfile(crashes[0]) if crashes else None).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Copy diagnostics", fg_color=BG_ELEVATED, command=self.copy_diagnostics).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Clear logs", fg_color=DANGER, command=self.clear_logs).pack(side="left", padx=4)
        levels = ctk.CTkFrame(card, fg_color="transparent"); levels.pack(anchor="w", padx=16, pady=(0, 14))
        ctk.CTkLabel(levels, text="Log level", text_color=TEXT_MUTED).pack(side="left", padx=(0, 8))
        self.log_level = ctk.CTkComboBox(levels, values=["INFO", "DEBUG", "TRACE-WIRE"],
                                         command=self.change_log_level, width=140)
        self.log_level.set(self.app.config.get("log_level", "DEBUG")); self.log_level.pack(side="left")

    def _about(self) -> None:
        card = self.card("About")
        ctk.CTkLabel(card, text="SeedrFetch 1.0.0", text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=5)
        NeonButton(card, text="Show walkthrough again", command=self.app.show_onboarding).pack(anchor="w", padx=16, pady=(4, 14))

    def choose_destination(self) -> None:
        value = filedialog.askdirectory(initialdir=self.app.config.get("download_destination"))
        if value: self.app.config.set("download_destination", value); self.destination.configure(text=value)

    def choose_ca(self) -> None:
        value = filedialog.askopenfilename(filetypes=[("PEM certificate", "*.pem"), ("All files", "*.*")])
        if value: self.ca.delete(0, "end"); self.ca.insert(0, value)

    def confirm_insecure(self) -> None:
        if self.insecure.get() and not messagebox.askyesno("Insecure setting", "This exposes HTTPS traffic to interception. Enable only temporarily to diagnose SSL inspection. Continue?", icon="warning"):
            self.insecure.deselect()

    def save_network(self) -> None:
        self.app.config.data.update(custom_ca_bundle=self.ca.get().strip(), http_proxy=self.http.get().strip(),
                                    https_proxy=self.https.get().strip(), disable_ssl_verify=bool(self.insecure.get()))
        self.app.config.save(); self.app.toast("Network settings saved. Restart active connections to apply them.")
        self.app.refresh_security_banner()

    def run_diagnostics(self) -> None:
        self.app.toast("Running diagnostics...")
        self.app.run_worker(self._diagnostics_worker)

    def _diagnostics_worker(self) -> None:
        results = run_all(make_session(self.app.config.data), getattr(self.app.backend, "auth", None))
        self.app.last_diagnostics = results
        self.app.post(self.show_diagnostics, results)

    def show_diagnostics(self, results) -> None:
        modal = ctk.CTkToplevel(self); modal.title("SeedrFetch Diagnostics"); modal.geometry("680x520"); modal.transient(self.app)
        scroll = ctk.CTkScrollableFrame(modal, fg_color=BG_DEEP); scroll.pack(fill="both", expand=True)
        ctk.CTkLabel(scroll, text="NETWORK DIAGNOSTICS", font=(FONT, 22, "bold"), text_color=ACCENT).pack(pady=18)
        for name, details in results:
            intercepted = details.get("interception_detected", False)
            color = WARNING if intercepted else (SUCCESS if details.get("ok") else DANGER)
            text = f"{name}  {'INTERCEPTION DETECTED' if intercepted else ('OK' if details.get('ok') else 'FAILED')}"
            box = GlowFrame(scroll); box.pack(fill="x", padx=18, pady=5)
            ctk.CTkLabel(box, text=text, text_color=color, font=(FONT, 14, "bold")).pack(anchor="w", padx=12, pady=(9, 2))
            detail = json.dumps(details, indent=2, default=str)
            if intercepted: detail += "\nYour security software is inspecting TLS. Add *.seedr.cc as an HTTPS-scanning exception."
            ctk.CTkLabel(box, text=detail, justify="left", wraplength=610, text_color=TEXT_MUTED).pack(anchor="w", padx=12, pady=(2, 9))

    def copy_diagnostics(self) -> None:
        self.app.toast("Building diagnostics...")
        self.app.run_worker(self._copy_diagnostics_worker)

    def _copy_diagnostics_worker(self) -> None:
        payload = ("Paste this when asking for help.\n\n" + build_snapshot() +
                   "\n----- Last diagnostics run -----\n" +
                   json.dumps(self.app.last_diagnostics, indent=2, default=str))
        payload = RedactionFilter.redact(payload[:50_000])
        self.app.post(self._set_diagnostics_clipboard, payload)

    def _set_diagnostics_clipboard(self, payload: str) -> None:
        self.clipboard_clear(); self.clipboard_append(payload); self.app.toast("Diagnostics copied to clipboard.")

    def change_log_level(self, value: str) -> None:
        set_log_level(value); self.app.config.set("log_level", value)
        self.app.toast("Log level changed to " + value + ".")

    def clear_logs(self) -> None:
        if not messagebox.askyesno("Clear logs", "Clear all current and rotated log files?"):
            return
        cleared = 0
        for base in (LOG_PATH, HTTP_LOG_PATH, TLS_LOG_PATH):
            for path in base.parent.glob(base.name + "*"):
                try:
                    path.write_text("", encoding="utf-8")
                    cleared += 1
                except OSError:
                    pass
        self.app.toast("Cleared %d log file(s)." % cleared)
