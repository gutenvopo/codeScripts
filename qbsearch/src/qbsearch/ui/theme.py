from __future__ import annotations

from tkinter import ttk

import customtkinter as ctk

BG = "#0B1120"
PANEL = "#111827"
ELEVATED = "#1F2937"
BORDER = "#374151"
TEXT = "#E5E7EB"
MUTED = "#9CA3AF"
ACCENT = "#3B82F6"
HIGHLIGHT = "#F97316"
SUCCESS = "#22C55E"
WARNING = "#F59E0B"
DANGER = "#EF4444"

FONT = "Segoe UI"
MONO = "Cascadia Mono"


def apply_theme(mode: str = "Dark") -> None:
    ctk.set_appearance_mode(mode)
    ctk.set_default_color_theme("blue")


def style_treeview() -> None:
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Treeview",
        background=BG,
        fieldbackground=BG,
        foreground=TEXT,
        bordercolor=BORDER,
        rowheight=28,
        font=(FONT, 10),
    )
    style.configure(
        "Treeview.Heading",
        background=PANEL,
        foreground=TEXT,
        bordercolor=BORDER,
        relief="flat",
        font=(FONT, 10, "bold"),
    )
    style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "#FFFFFF")])
    for name in ("Horizontal.TScrollbar", "Vertical.TScrollbar"):
        style.configure(
            name,
            background=ELEVATED,
            troughcolor=PANEL,
            bordercolor=BORDER,
            arrowcolor=TEXT,
            relief="flat",
        )
        style.map(name, background=[("active", ACCENT), ("pressed", ACCENT)])
