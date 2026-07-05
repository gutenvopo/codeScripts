# Student Data Extractor

A CustomTkinter desktop app for batch-extracting student submission archives from folders.

## Install

```powershell
cd student_data_extractor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

## Supported archives

- `.zip`
- `.7z`
- `.rar`
- `.tar.gz`
- `.tgz`
- `.tar.bz2`

RAR support uses the Python `rarfile` package and also requires the `unrar` system binary on your PATH. If `unrar` is missing, `.rar` files are skipped with a clear warning instead of crashing the app.

## Workflow

1. Select the root folder.
2. Pick extraction options.
3. Click **Start Extraction**.
4. Review the scan summary.
5. Confirm to run extraction.
6. Export the report when complete.

## Settings and logs

Settings are saved to:

```text
~/.student_data_extractor/config.json
```

Rolling logs are written to:

```text
~/.student_data_extractor/student_data_extractor.log
```

## Screenshots

Screenshots placeholder:

```text
docs/screenshots/main-window.png
docs/screenshots/report-window.png
```

## Troubleshooting

- If `.rar` files fail with a missing binary message, install `unrar` and ensure it is on PATH.
- If an archive is password-protected, v1 skips it and records the reason in the report.
- If extraction fails with an OS error, check disk space, permissions, and long path settings.
- If the UI cannot scan a folder, verify the selected root exists and is readable.
