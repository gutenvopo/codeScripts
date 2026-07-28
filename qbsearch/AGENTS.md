# qbSearch Agent Guide

## Project Overview
qbSearch is a Windows desktop front-end for qBittorrent's installed search engine plugins. It talks only to the qBittorrent Web API and never imports, modifies, installs, or calls qBittorrent's Python search plugins directly.

## Tech Stack
| Component | Version Floor | Purpose |
| --- | --- | --- |
| Python | 3.11 | Desktop runtime, packaged with `uv`. |
| customtkinter | 5.2.2 | Modern dark UI shell and controls. |
| tkinter.ttk.Treeview | stdlib | Native high-density results table, restyled for the app theme. |
| requests | 2.32 | Session-based qBittorrent Web API calls. |
| truststore | 0.10 | Native certificate store support for Norton and corporate TLS inspection. |
| keyring | 25.0 | Stores the qBittorrent WebUI password outside JSON settings. |
| pyperclip | 1.9 | Copies magnet and page URLs to the clipboard. |
| PyInstaller | 6.14 | Creates the self-contained Windows onedir application bundle (development only). |
| pytest | 8.0 | Unit tests. |
| ruff | 0.8 | Linting and formatting. |

## Project Structure
```text
qbsearch/
|-- AGENTS.md
|-- CHANGELOG.md
|-- pyproject.toml
|-- README.md
|-- build/qbsearch.spec
|-- installer/qbsearch.iss
|-- scripts/build.ps1
|-- docs/PACKAGING.md
|-- src/qbsearch/
|   |-- __init__.py
|   |-- __main__.py
|   |-- version.py
|   |-- app.py
|   |-- config.py
|   |-- logging_setup.py
|   |-- utils.py
|   |-- api/qbittorrent.py
|   |-- core/regex_filter.py
|   |-- core/result_model.py
|   |-- core/search_controller.py
|   |-- core/magnet_resolver.py
|   `-- ui/
|       |-- engine_panel.py
|       |-- log_window.py
|       |-- results_table.py
|       |-- search_bar.py
|       |-- settings_dialog.py
|       |-- status_bar.py
|       |-- toast.py
|       `-- theme.py
`-- tests/
```

## API Client Contract
- `QbtClient` owns exactly one persistent `requests.Session`.
- `login()` calls `POST /api/v2/auth/login` and relies on the Web API `SID` cookie stored in the session.
- Search methods map one-to-one to `/api/v2/search/*` endpoints.
- `add_torrent()` always hands magnet/file URLs to qBittorrent through `/api/v2/torrents/add`; qbSearch never downloads torrent payloads itself.
- On HTTP 403, callers should surface a re-login flow.
- All network exceptions are converted to `QbtError` with user-readable messages.

## Threading Model
- The Tk/CustomTkinter thread owns all widgets.
- `SearchController` runs Web API search polling in a daemon thread.
- Worker events are marshalled through `queue.Queue`.
- The UI drains at `after(100, drain)` and inserts table rows in batches.
- Worker threads must never touch CTk or ttk widgets directly.
- `VerboseLogHandler` only writes records into a thread-safe queue; the
  `VerboseLogWindow` drains that queue with `after()` on the Tk thread.

## Known Constraints
- qBittorrent search has no native regex support. Regex mode sends a broad token query to qBittorrent, then filters loaded results client-side.
- Plugin behavior and result fields vary by provider. Treat missing sizes, URLs, seeders, and leechers as normal.
- Some plugins put detail-page HTML URLs in `fileUrl` instead of real magnets. `core/magnet_resolver.py` resolves magnets on demand, caches successful detail-page lookups in memory, and tracks in-flight URLs so the UI never starts duplicate fetch threads.
- Every magnet-link request opens a reusable verbose activity window. Resolver
  logs include HTTP status and diagnostic metadata but redact detail-page query
  strings because they may contain private tracker tokens.
- Norton, VPN, and corporate TLS products can intercept HTTPS traffic. `truststore.inject_into_ssl()` must run on startup.
- The app does not install plugins, modify qBittorrent plugin settings, download torrents directly, provide a web UI, or authenticate to anything other than qBittorrent itself.

## Common Commands
```bash
uv sync
uv run python -m qbsearch
uv run pytest -v
uv run ruff check .
uv run ruff format .
.\scripts\build.ps1
```

If `uv` hits `UnknownIssuer` on Windows, rerun sync/check commands with `--system-certs`.

## Packaging Contract
- `src/qbsearch/version.py` is the only source for the app name, AppId, company,
  and version. The package, PyInstaller spec, and Inno build import or receive
  those values; never duplicate the version in `pyproject.toml` or the `.iss`.
- `build/qbsearch.spec` must remain a windowed `--onedir` build. It explicitly
  bundles CustomTkinter, truststore, certifi, the app PNG, and keyring backends.
- `assets/app.ico` is optional. When present, both PyInstaller and Inno Setup use
  it without requiring an absolute path.
- `scripts/build.ps1` preserves the committed spec while cleaning generated
  `build/pyinstaller` and `dist` output, requires Python 3.13, and emits the
  installer under `dist/installer`.
- Keep `truststore.inject_into_ssl()` before networking during frozen startup;
  Norton and corporate HTTPS inspection rely on the Windows certificate store.
- Settings and logs live under `%LOCALAPPDATA%\qbsearch`. The installer
  uninstaller must preserve this directory unless the user explicitly opts in
  to deleting it.
