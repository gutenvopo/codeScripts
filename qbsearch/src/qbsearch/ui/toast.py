from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from qbsearch.ui import theme


class Toast:
    _active: tk.Toplevel | None = None

    def __init__(self, window: tk.Toplevel) -> None:
        self.window = window

    @classmethod
    def success(cls, master: tk.Misc, message: str) -> Toast:
        return cls._show(master, f"✓ {message}", theme.SUCCESS, "#FFFFFF")

    @classmethod
    def error(cls, master: tk.Misc, message: str) -> Toast:
        return cls._show(master, f"✕ {message}", theme.DANGER, "#FFFFFF")

    @classmethod
    def info(cls, master: tk.Misc, message: str) -> Toast:
        return cls._show(master, f"⏳ {message}", theme.ACCENT, theme.ACCENT)

    def dismiss(self) -> None:
        if self.window.winfo_exists():
            self.window.destroy()

    @classmethod
    def _show(cls, master: tk.Misc, message: str, accent: str, text_color: str) -> Toast:
        root = master.winfo_toplevel()
        focused = root.focus_get()
        if cls._active and cls._active.winfo_exists():
            cls._active.destroy()
        toast = tk.Toplevel(root)
        cls._active = toast
        toast.overrideredirect(True)
        toast.configure(background=theme.ELEVATED)
        toast.attributes("-topmost", True)
        frame = ctk.CTkFrame(toast, fg_color=theme.ELEVATED, corner_radius=8)
        frame.pack(fill="both", expand=True)
        label = ctk.CTkLabel(
            frame,
            text=message,
            text_color=text_color,
            font=(theme.FONT, 12),
        )
        label.pack(side="left", padx=(12, 14), pady=9)
        ctk.CTkFrame(frame, width=4, fg_color=accent, corner_radius=3).pack(
            side="left",
            fill="y",
            padx=(0, 8),
            pady=8,
        )
        toast.update_idletasks()
        cls._place(root, toast)
        if focused:
            focused.focus_set()
        toast.after(1500, toast.destroy)
        return cls(toast)

    @staticmethod
    def _place(root: tk.Misc, toast: tk.Toplevel) -> None:
        width = toast.winfo_reqwidth()
        height = toast.winfo_reqheight()
        x = root.winfo_rootx() + root.winfo_width() - width - 16
        y = root.winfo_rooty() + root.winfo_height() - height - 16
        toast.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")
