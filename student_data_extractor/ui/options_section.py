"""Options section view."""

from __future__ import annotations

import customtkinter as ctk

from settings import AppSettings


class OptionsSection(ctk.CTkFrame):
    """Extraction settings controls."""

    def __init__(self, master: ctk.CTkBaseClass, on_destructive_change) -> None:
        super().__init__(master, corner_radius=10)
        self.on_destructive_change = on_destructive_change
        self.expanded = True

        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.header = ctk.CTkButton(
            self,
            text="Options",
            command=self.toggle,
            anchor="w",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray82", "gray25"),
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=12, pady=(10, 4))

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 12))
        self.body.grid_columnconfigure((0, 1, 2), weight=1)

        self.conflict_menu = self._labeled_menu(
            0,
            0,
            "On conflict",
            ["Skip", "Overwrite", "Rename with suffix"],
        )
        self.after_menu = self._labeled_menu(
            0,
            1,
            "After extraction",
            ["Keep", "Delete", "Move to _extracted/"],
            command=self._after_changed,
        )

        self.recurse_var = ctk.BooleanVar(value=False)
        self.include_root_var = ctk.BooleanVar(value=False)
        self.recurse_check = ctk.CTkCheckBox(
            self.body,
            text="Recurse into all subfolders",
            variable=self.recurse_var,
        )
        self.recurse_check.grid(row=2, column=0, sticky="w", padx=8, pady=8)
        self.include_root_check = ctk.CTkCheckBox(
            self.body,
            text="Include archives at root level",
            variable=self.include_root_var,
        )
        self.include_root_check.grid(row=2, column=1, sticky="w", padx=8, pady=8)

    def _labeled_menu(
        self,
        row: int,
        column: int,
        label: str,
        values: list[str],
        command=None,
    ) -> ctk.CTkOptionMenu:
        ctk.CTkLabel(self.body, text=label).grid(
            row=row,
            column=column,
            sticky="w",
            padx=8,
            pady=(4, 2),
        )
        menu = ctk.CTkOptionMenu(self.body, values=values, command=command, width=190)
        menu.grid(row=row + 1, column=column, sticky="w", padx=8, pady=(0, 8))
        return menu

    def toggle(self) -> None:
        """Collapse or expand options."""

        self.expanded = not self.expanded
        if self.expanded:
            self.body.grid()
        else:
            self.body.grid_remove()

    def _after_changed(self, value: str) -> None:
        if value == "Delete":
            self.on_destructive_change()

    def load_settings(self, settings: AppSettings) -> None:
        """Populate controls from settings."""

        self.conflict_menu.set(settings.conflict_mode)
        self.after_menu.set(settings.after_extraction)
        self.recurse_var.set(settings.recurse)
        self.include_root_var.set(settings.include_root)

    def to_settings(self, theme: str) -> AppSettings:
        """Read settings from controls."""

        return AppSettings(
            conflict_mode=self.conflict_menu.get(),
            after_extraction=self.after_menu.get(),
            recurse=self.recurse_var.get(),
            include_root=self.include_root_var.get(),
            theme=theme,
        )

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable option controls."""

        state = "normal" if enabled else "disabled"
        for widget in (
            self.conflict_menu,
            self.after_menu,
            self.recurse_check,
            self.include_root_check,
            self.header,
        ):
            widget.configure(state=state)
