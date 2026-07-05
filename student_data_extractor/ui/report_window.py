"""Completion report window."""

from __future__ import annotations

from tkinter import messagebox, ttk

import customtkinter as ctk

from report import ExtractionReport


class ReportWindow(ctk.CTkToplevel):
    """Modal report view with export support."""

    def __init__(self, master: ctk.CTkBaseClass, report: ExtractionReport) -> None:
        super().__init__(master)
        self.report = report
        self.title("Extraction Report")
        self.geometry("860x500")
        self.minsize(760, 420)
        self.transient(master)
        self.grab_set()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        summary = (
            f"Found: {report.total_found}    Extracted: {report.extracted}    "
            f"Skipped: {report.skipped}    Failed: {report.failed}    "
            f"Files: {report.total_files}    Elapsed: {report.elapsed_label}"
        )
        ctk.CTkLabel(
            self,
            text=summary,
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=14)

        columns = ("Folder", "Archive", "Status", "Files extracted", "Notes")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for column in columns:
            self.tree.heading(column, text=column)
        self.tree.column("Folder", width=240)
        self.tree.column("Archive", width=170)
        self.tree.column("Status", width=90, anchor="center")
        self.tree.column("Files extracted", width=110, anchor="center")
        self.tree.column("Notes", width=250)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 10))

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=(0, 10))
        self.tree.configure(yscrollcommand=scrollbar.set)

        for row in report.rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    str(row.folder),
                    row.archive.name,
                    row.status,
                    row.files_extracted,
                    row.notes,
                ),
            )

        ctk.CTkButton(self, text="Export Report", command=self.export_report).grid(
            row=2,
            column=0,
            sticky="e",
            padx=16,
            pady=(0, 16),
        )

    def export_report(self) -> None:
        """Export the report to txt and csv files."""

        txt_path, csv_path = self.report.export()
        messagebox.showinfo(
            "Report exported",
            f"Wrote:\n{txt_path}\n{csv_path}",
            parent=self,
        )
