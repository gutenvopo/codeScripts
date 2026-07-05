# qbSearch

qbSearch is a polished Windows desktop front-end for qBittorrent's installed search plugins. It uses qBittorrent's Web API, so your existing plugins stay managed by qBittorrent.

![Screenshot placeholder](docs/screenshot-placeholder.png)

## Features
- Fast threaded searches that keep the UI responsive.
- Live engine list from qBittorrent.
- Regex mode with client-side filtering.
- Sortable, filterable dark results table.
- Copy, open, and send results back to qBittorrent.
- Password storage through Windows keyring.
- Rotating logs under `%LOCALAPPDATA%\qbsearch\logs\`.

## Install And Run
Install `uv`, then from this folder run:

```bash
uv sync
uv run python -m qbsearch
```

qBittorrent must have Web UI enabled. The default connection is `http://localhost:8080` with username `admin`.

If `uv sync` reports an `UnknownIssuer` certificate error on Windows, rerun it with native certificates:

```bash
uv sync --system-certs
```

## Development
```bash
uv run pytest -v
uv run ruff check .
uv run ruff format .
```

## Packaging Notes
Create the self-contained onedir build and Inno Setup installer with:

```powershell
.\scripts\build.ps1
```

See [docs/PACKAGING.md](docs/PACKAGING.md) for prerequisites, clean-VM checks,
version bumps, certificate notes, and signing guidance.

## Constraints
qbSearch does not download torrents directly, install qBittorrent plugins, provide a web UI, or authenticate to tracker/indexer services. Regex is implemented client-side because qBittorrent's search API does not support native regex queries.
