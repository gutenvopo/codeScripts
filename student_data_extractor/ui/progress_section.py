"""Progress display view."""

from __future__ import annotations

import customtkinter as ctk


class ProgressSection(ctk.CTkFrame):
    """Determinate progress bar and current file labels."""

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, corner_radius=10)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="Progress",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        self.progress.set(0)

        self.status_var = ctk.StringVar(value="No archive selected")
        self.counter_var = ctk.StringVar(value="0 / 0")
        ctk.CTkLabel(self, textvariable=self.status_var).grid(
            row=2,
            column=0,
            sticky="w",
            padx=16,
            pady=(0, 12),
        )
        ctk.CTkLabel(self, textvariable=self.counter_var).grid(
            row=2,
            column=0,
            sticky="e",
            padx=16,
            pady=(0, 12),
        )

    def reset(self) -> None:
        """Reset progress state."""

        self.update_progress(0, 0, "No archive selected")

    def update_progress(self, current: int, total: int, current_file: str) -> None:
        """Update progress controls."""

        value = 0 if total == 0 else current / total
        self.progress.set(value)
        self.status_var.set(current_file or "Working...")
        self.counter_var.set(f"{current} / {total}")
