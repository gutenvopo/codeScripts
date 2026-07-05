"""Archive scanning and extraction helpers."""

from __future__ import annotations

import logging
import queue
import rarfile
import shutil
import inspect
import tarfile
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Literal

import py7zr

from report import ArchiveResult, ExtractionReport
from settings import AppSettings


ARCHIVE_SUFFIXES = (".zip", ".7z", ".rar", ".tar.gz", ".tgz", ".tar.bz2")
ProgressKind = Literal["log", "scan_done", "progress", "done", "cancelled"]


@dataclass(slots=True)
class ProgressMessage:
    """Message sent from worker thread to the UI queue."""

    kind: ProgressKind
    text: str = ""
    level: str = "info"
    current: int = 0
    total: int = 0
    report: ExtractionReport | None = None


def is_archive(path: Path) -> bool:
    """Return True when a path has a supported archive suffix."""

    lowered = path.name.lower()
    return any(lowered.endswith(suffix) for suffix in ARCHIVE_SUFFIXES)


def scan_archives(root: Path, settings: AppSettings) -> list[Path]:
    """Find supported archives using the selected scan depth settings."""

    archives: list[Path] = []
    if settings.recurse:
        candidates = root.rglob("*")
    else:
        folders = [item for item in root.iterdir() if item.is_dir()]
        if settings.include_root:
            folders.append(root)
        candidates = (file for folder in folders for file in folder.iterdir())

    for candidate in candidates:
        if candidate.parent == root and not settings.include_root:
            continue
        if candidate.is_file() and is_archive(candidate):
            archives.append(candidate)
    return sorted(archives, key=lambda item: str(item).lower())


def extract_archives_worker(
    root: Path,
    archives: list[Path],
    settings: AppSettings,
    output: queue.Queue[ProgressMessage],
    cancel_event: Event,
    logger: logging.Logger,
) -> None:
    """Extract archives on a background thread and report progress via queue."""

    start = time.monotonic()
    rows: list[ArchiveResult] = []
    total = len(archives)

    for index, archive in enumerate(archives, start=1):
        output.put(ProgressMessage("progress", archive.name, current=index - 1, total=total))
        if cancel_event.is_set():
            report = ExtractionReport(root, total, rows, time.monotonic() - start)
            output.put(ProgressMessage("cancelled", "Cancelled", report=report))
            return

        logger.info("Extracting %s", archive)
        output.put(ProgressMessage("log", f"Extracting {archive.name}", "info"))
        result = extract_one_archive(archive, settings, logger)
        rows.append(result)
        output.put(
            ProgressMessage(
                "log",
                f"{result.status}: {archive.name} - {result.notes}",
                _level_for_status(result.status),
            )
        )
        output.put(ProgressMessage("progress", archive.name, current=index, total=total))

    report = ExtractionReport(root, total, rows, time.monotonic() - start)
    output.put(ProgressMessage("done", "Done", report=report))


def extract_one_archive(
    archive: Path,
    settings: AppSettings,
    logger: logging.Logger,
) -> ArchiveResult:
    """Extract a single archive to its containing folder."""

    target = archive.parent
    with tempfile.TemporaryDirectory(prefix=".student_extract_", dir=target) as temp_name:
        temp_dir = Path(temp_name)
        try:
            _extract_to_temp(archive, temp_dir)
            files_extracted = _merge_extracted_files(temp_dir, target, settings.conflict_mode)
            _handle_archive_afterward(archive, settings.after_extraction)
        except rarfile.RarCannotExec as exc:
            note = "Missing unrar binary on PATH; install unrar to process .rar files."
            logger.warning("%s: %s", note, exc)
            return ArchiveResult(target, archive, "Failed", 0, note)
        except (RuntimeError, py7zr.exceptions.PasswordRequired) as exc:
            note = f"Password-protected archive skipped: {exc}"
            logger.warning("%s: %s", archive, note)
            return ArchiveResult(target, archive, "Skipped", 0, note)
        except (
            zipfile.BadZipFile,
            tarfile.TarError,
            py7zr.exceptions.Bad7zFile,
            rarfile.Error,
        ) as exc:
            note = f"Invalid or corrupt archive: {exc}"
            logger.exception("%s: %s", archive, note)
            return ArchiveResult(target, archive, "Failed", 0, note)
        except PermissionError as exc:
            note = f"Permission denied: {exc}"
            logger.exception("%s: %s", archive, note)
            return ArchiveResult(target, archive, "Failed", 0, note)
        except OSError as exc:
            note = f"OS error, possibly path-too-long or disk-full: {exc}"
            logger.exception("%s: %s", archive, note)
            return ArchiveResult(target, archive, "Failed", 0, note)

    if files_extracted == 0:
        return ArchiveResult(target, archive, "Skipped", 0, "No new files extracted.")
    return ArchiveResult(target, archive, "Extracted", files_extracted, "Completed.")


def _extract_to_temp(archive: Path, temp_dir: Path) -> None:
    lowered = archive.name.lower()
    if lowered.endswith(".zip"):
        with zipfile.ZipFile(archive) as handle:
            if any(info.flag_bits & 0x1 for info in handle.infolist()):
                raise RuntimeError("zip file is encrypted")
            handle.extractall(temp_dir)
    elif lowered.endswith(".7z"):
        with py7zr.SevenZipFile(archive, mode="r") as handle:
            handle.extractall(temp_dir)
    elif lowered.endswith(".rar"):
        with rarfile.RarFile(archive) as handle:
            if handle.needs_password():
                raise RuntimeError("rar file is encrypted")
            handle.extractall(temp_dir)
    elif lowered.endswith((".tar.gz", ".tgz", ".tar.bz2")):
        with tarfile.open(archive) as handle:
            if "filter" in inspect.signature(handle.extractall).parameters:
                handle.extractall(temp_dir, filter="data")
            else:
                handle.extractall(temp_dir)
    else:
        raise ValueError(f"Unsupported archive type: {archive.name}")


def _merge_extracted_files(temp_dir: Path, target: Path, conflict_mode: str) -> int:
    extracted = 0
    for source in sorted((item for item in temp_dir.rglob("*") if item.is_file()), key=str):
        relative = source.relative_to(temp_dir)
        destination = target / relative

        if destination.exists():
            if conflict_mode == "Skip":
                continue
            if conflict_mode == "Rename with suffix":
                destination = _unique_destination(destination)

        destination.parent.mkdir(parents=True, exist_ok=True)
        if conflict_mode == "Overwrite" and destination.exists():
            destination.unlink()
        shutil.move(str(source), str(destination))
        extracted += 1
    return extracted


def _unique_destination(destination: Path) -> Path:
    counter = 1
    candidate = destination
    while candidate.exists():
        candidate = destination.with_name(
            f"{destination.stem}_{counter}{destination.suffix}"
        )
        counter += 1
    return candidate


def _handle_archive_afterward(archive: Path, mode: str) -> None:
    if mode == "Delete":
        archive.unlink()
    elif mode == "Move to _extracted/":
        destination_dir = archive.parent / "_extracted"
        destination_dir.mkdir(exist_ok=True)
        shutil.move(str(archive), str(_unique_destination(destination_dir / archive.name)))


def _level_for_status(status: str) -> str:
    if status == "Extracted":
        return "info"
    if status == "Skipped":
        return "warning"
    return "error"
