"""Reusable themed widgets."""
from __future__ import annotations

import customtkinter as ctk

from ui.theme import *


class NeonButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", ACCENT_DIM)
        kwargs.setdefault("hover_color", ACCENT)
        kwargs.setdefault("text_color", BG_DEEP)
        kwargs.setdefault("corner_radius", 8)
        super().__init__(master, **kwargs)


class GlowFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", BG_PANEL)
        kwargs.setdefault("border_color", BORDER)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("corner_radius", 12)
        super().__init__(master, **kwargs)


class Tooltip:
    def __init__(self, widget, text: str, delay: int = 600) -> None:
        self.widget, self.text, self.delay = widget, text, delay
        self.tip = None
        self.job = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self.hide, add="+")

    def _schedule(self, _event=None) -> None:
        self.job = self.widget.after(self.delay, self.show)

    def show(self) -> None:
        if self.tip or not self.widget.winfo_exists():
            return
        x, y = self.widget.winfo_rootx() + 12, self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self.tip = ctk.CTkToplevel(self.widget)
        self.tip.overrideredirect(True)
        self.tip.geometry(f"+{x}+{y}")
        self.tip.attributes("-alpha", 0.0)
        ctk.CTkLabel(self.tip, text=self.text, fg_color=BG_ELEVATED, text_color=TEXT_PRIMARY,
                     corner_radius=7, padx=10, pady=6).pack()
        self._fade(0.0)

    def _fade(self, alpha: float) -> None:
        if not self.tip:
            return
        self.tip.attributes("-alpha", min(alpha, 0.96))
        if alpha < 0.96:
            self.tip.after(25, self._fade, alpha + 0.16)

    def hide(self, _event=None) -> None:
        if self.job:
            self.widget.after_cancel(self.job)
            self.job = None
        if self.tip:
            self.tip.destroy()
            self.tip = None


class Toast(ctk.CTkFrame):
    def __init__(self, master, message, danger: bool = False, duration: int = 5000):
        from core.errors import UserError
        user_error = message if isinstance(message, UserError) else None
        display = user_error.title if user_error else str(message)
        super().__init__(master, fg_color=BG_ELEVATED, border_width=1,
                         border_color=DANGER if danger or user_error else ACCENT, corner_radius=10)
        ctk.CTkLabel(self, text=display, wraplength=360, justify="left").pack(padx=16, pady=(12, 6 if user_error else 12))
        if user_error:
            ctk.CTkButton(self, text="Show details", height=26, fg_color="transparent",
                          text_color=ACCENT, command=lambda: ErrorDetails(master, user_error)).pack(pady=(0, 8))
        self.place(relx=1, rely=1, x=-24, y=-24, anchor="se")
        self.lift()
        self.after(duration, self.destroy)


class ErrorDetails(ctk.CTkToplevel):
    def __init__(self, master, error):
        super().__init__(master)
        self.title(error.title); self.geometry("720x560"); self.configure(fg_color=BG_DEEP)
        self.transient(master)
        ctk.CTkLabel(self, text=error.title, font=(FONT, 22, "bold"), text_color=DANGER).pack(anchor="w", padx=22, pady=(20, 6))
        ctk.CTkLabel(self, text=error.detail, wraplength=670, justify="left").pack(anchor="w", padx=22, pady=5)
        ctk.CTkLabel(self, text=error.guidance, wraplength=670, justify="left", text_color=TEXT_MUTED).pack(anchor="w", padx=22, pady=5)
        ctk.CTkLabel(self, text="Correlation ID: " + error.corr_id, font=(MONO, 13), text_color=ACCENT).pack(anchor="w", padx=22, pady=8)
        box = ctk.CTkTextbox(self, font=(MONO, 11)); box.pack(fill="both", expand=True, padx=22, pady=8)
        content = error.log_excerpt or "No correlated log lines were available yet."
        box.insert("1.0", content); box.configure(state="disabled")
        def copy() -> None:
            self.clipboard_clear(); self.clipboard_append("%s\n%s\n%s\nCorrelation: %s\n\n%s" %
                                                         (error.title, error.detail, error.guidance,
                                                          error.corr_id, content))
        NeonButton(self, text="Copy", command=copy).pack(anchor="e", padx=22, pady=(0, 18))


class InfoBanner(ctk.CTkFrame):
    def __init__(self, master, text: str, danger: bool = False, **kwargs):
        super().__init__(master, fg_color=BG_DANGER if danger else BG_ELEVATED,
                         border_color=DANGER if danger else ACCENT_DIM, border_width=1,
                         corner_radius=8, **kwargs)
        ctk.CTkLabel(self, text=text, text_color=DANGER if danger else TEXT_PRIMARY,
                     wraplength=800).pack(padx=14, pady=9)


class ProgressRow(GlowFrame):
    def __init__(self, master, name: str, cancel_command=None):
        super().__init__(master)
        self.label = ctk.CTkLabel(self, text=name, anchor="w")
        self.label.grid(row=0, column=0, padx=10, pady=(8, 2), sticky="ew")
        self.status = ctk.CTkLabel(self, text="Queued", text_color=TEXT_MUTED)
        self.status.grid(row=0, column=1, padx=8)
        self.bar = ctk.CTkProgressBar(self, progress_color=ACCENT)
        self.bar.grid(row=1, column=0, padx=10, pady=(2, 8), sticky="ew")
        self.bar.set(0)
        ctk.CTkButton(self, text="X", width=30, fg_color="transparent", hover_color=DANGER,
                      command=cancel_command).grid(row=1, column=1, padx=8)
        self.grid_columnconfigure(0, weight=1)

    def update_progress(self, progress) -> None:
        ratio = progress.downloaded / progress.total if progress.total else 0
        self.bar.set(min(ratio, 1))
        speed = progress.speed / (1024 * 1024)
        self.status.configure(text=f"{progress.state.title()}  {speed:.1f} MB/s")
