"""Report data structures and exporters."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ArchiveResult:
    """Per-archive extraction outcome."""

    folder: Path
    archive: Path
    status: str
    files_extracted: int = 0
    notes: str = ""


@dataclass(slots=True)
class ExtractionReport:
    """Aggregated extraction report."""

    root: Path
    total_found: int
    rows: list[ArchiveResult] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    @property
    def extracted(self) -> int:
        """Count archives that extracted at least one file successfully."""

        return sum(1 for row in self.rows if row.status == "Extracted")

    @property
    def skipped(self) -> int:
        """Count skipped archives."""

        return sum(1 for row in self.rows if row.status == "Skipped")

    @property
    def failed(self) -> int:
        """Count failed archives."""

        return sum(1 for row in self.rows if row.status == "Failed")

    @property
    def total_files(self) -> int:
        """Count total files extracted."""

        return sum(row.files_extracted for row in self.rows)

    @property
    def elapsed_label(self) -> str:
        """Return elapsed time as mm:ss."""

        minutes, seconds = divmod(int(self.elapsed_seconds), 60)
        return f"{minutes:02d}:{seconds:02d}"

    def export(self) -> tuple[Path, Path]:
        """Write text and CSV reports into the selected root folder."""

        txt_path = self.root / "report.txt"
        csv_path = self.root / "report.csv"
        txt_path.write_text(self.to_text(), encoding="utf-8")

        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Folder", "Archive", "Status", "Files extracted", "Notes"])
            for row in self.rows:
                writer.writerow(
                    [
                        str(row.folder),
                        row.archive.name,
                        row.status,
                        row.files_extracted,
                        row.notes,
                    ]
                )

        return txt_path, csv_path

    def to_text(self) -> str:
        """Build a human-readable report."""

        lines = [
            "Student Data Extractor Report",
            "=" * 29,
            f"Root: {self.root}",
            f"Elapsed: {self.elapsed_label}",
            f"Archives found: {self.total_found}",
            f"Extracted: {self.extracted}",
            f"Skipped: {self.skipped}",
            f"Failed: {self.failed}",
            f"Files extracted: {self.total_files}",
            "",
            "Rows:",
        ]
        for row in self.rows:
            lines.append(
                f"- {row.folder} | {row.archive.name} | {row.status} | "
                f"{row.files_extracted} files | {row.notes}"
            )
        return "\n".join(lines) + "\n"
