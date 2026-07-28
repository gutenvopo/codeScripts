# Changelog
All notable changes to qbSearch are documented here.

## [Unreleased]
### Added
- Open a live, copyable verbose activity window whenever a user requests a
  magnet link. It reports direct-link and cache decisions, background detail
  page requests, redirects, HTTP status and reason, response metadata, magnet
  extraction, clipboard completion, and network failures while redacting URL
  query strings. [src/qbsearch/core/magnet_resolver.py,
  src/qbsearch/ui/results_table.py, src/qbsearch/ui/log_window.py,
  tests/test_magnet_resolver.py, tests/test_log_window.py]
- Add a reproducible Python 3.13 Windows packaging pipeline with a windowed
  PyInstaller onedir spec, bundled CustomTkinter/truststore/certifi assets,
  embedded executable version metadata, an Inno Setup per-user/all-users
  installer, Start Menu and optional desktop shortcuts, opt-in user-data
  cleanup, and clean-VM packaging documentation. The app, package metadata,
  executable, and installer now share `src/qbsearch/version.py` as their
  identity and version source. [src/qbsearch/version.py, build/qbsearch.spec,
  installer/qbsearch.iss, scripts/build.ps1, docs/PACKAGING.md, pyproject.toml]
- Add a rightmost results-table Action column for copying magnet or torrent links, plus toast feedback and horizontal table scrolling. [src/qbsearch/ui/results_table.py, src/qbsearch/ui/toast.py]
- Scaffold the qbSearch desktop app with qBittorrent Web API integration, threaded search orchestration, CustomTkinter UI shell, settings persistence, logging, docs, tests, and placeholder PNG icon.

### Fixed
- Store settings alongside logs under `%LOCALAPPDATA%\qbsearch` so installer
  cleanup targets the app's real user-data directory, while automatically
  copying valid legacy `%APPDATA%\qbSearch\settings.json` settings on first
  launch. [src/qbsearch/config.py, src/qbsearch/logging_setup.py,
  tests/test_config.py]
- Resolve real magnet URIs on demand from plugin detail pages when qBittorrent search results expose HTML URLs instead of magnets, with in-memory caching and duplicate-fetch suppression. [src/qbsearch/core/magnet_resolver.py, src/qbsearch/ui/results_table.py]

## [0.1.0] - 2026-06-25
### Added
- Initial project version.
