# SeedrFetch Agent Guide

## Project overview
SeedrFetch is a Windows 11 desktop client for Seedr Premium users running Python 3.13. It provides REST and device-code authentication, cloud torrent management, resumable local downloads, diagnostics, and a dark CustomTkinter interface. It deliberately does not provide FTP, WebDAV, streaming or playback, system-tray integration, or automatic updates.

## Tech stack (authoritative)
| Component | Version Floor | Why pinned |
| --- | --- | --- |
| customtkinter | 5.2.2 | Provides the themed Windows desktop UI and stable CTk widget APIs. |
| requests | 2.32 | Provides synchronous sessions, authentication, streaming, hooks, and adapter support. |
| truststore | 0.10 | Injects the Windows certificate store for antivirus and corporate TLS interception. |
| certifi | Compatible release | Provides a portable fallback CA bundle when native trust is unavailable. |
| cryptography | Compatible release | Encrypts remembered credentials and decodes diagnostic certificates. |
| seedrcc | Compatible release | Provides the Seedr device-code authentication path. |
| Pillow | Compatible release | Supports application icon and image asset handling. |

Any agent adding a dependency must update this table, `seedrfetch/requirements.txt`, and `CHANGELOG.md` in the same change.

## Project structure
```text
seedrfetch/
|-- .gitignore                       # Ignores bytecode and local smoke-test output.
|-- main.py                          # Entry point, interpreter guard, and startup ordering.
|-- README.md                        # User, troubleshooting, verification, and development guide.
|-- requirements.txt                 # Authoritative runtime dependency list.
|-- core/
|   |-- __init__.py                  # Application version and core package marker.
|   |-- backend.py                   # Authentication-agnostic SeedrBackend ABC.
|   |-- config.py                    # Settings paths and encrypted credential persistence.
|   |-- device_token_backend.py      # seedrcc device-code backend adapter.
|   |-- diagnostics.py               # DNS, TCP, TLS, and Seedr API checks.
|   |-- downloader.py                # Threaded resumable HTTP streaming downloads.
|   |-- errors.py                    # Correlated UserError translation and guidance.
|   |-- logging_setup.py             # Structured logs, redaction, correlation, and crash reports.
|   |-- rest_v1_backend.py           # Email/password Seedr REST v1 backend.
|   `-- ssl_setup.py                 # Native trust injection and shared diagnostic HTTP sessions.
|-- scripts/
|   `-- log_smoke_test.py            # Live HTTP/TLS/error logging reproduction check.
`-- ui/
    |-- __init__.py                  # UI package marker.
    |-- app.py                       # CTk root, navigation, queue drain, and worker tracking.
    |-- dashboard_view.py            # Cloud drive, torrent actions, and local downloads.
    |-- help_view.py                 # Collapsible in-app usage and troubleshooting help.
    |-- login_view.py                # Email/password and device-code login tabs.
    |-- onboarding.py                # Four-slide first-run walkthrough.
    |-- settings_view.py             # Network, diagnostics, account, and log controls.
    |-- theme.py                     # Authoritative palette and typography constants.
    `-- widgets.py                   # Shared buttons, frames, tooltips, toasts, and banners.
```

Generated `__pycache__` directories and `.smoke-data` output are not source files and are intentionally omitted.

## Architecture rules (non-negotiable)
- All network calls go through `core/ssl_setup.make_session()`. Bare `requests.get()` or `requests.post()` calls are forbidden and fail code review.
- Tk is single-threaded: network and IO work runs in daemon threads, and results marshal back through `queue.Queue` plus `app.after(100, drain)`. Worker threads never touch CTk widgets.
- All operations wrap in `with log_operation("name"):` so every action receives a correlation ID.
- Every third-party import must appear in `seedrfetch/requirements.txt`. `scripts/check_requirements.py` enforces this.
- Credentials and tokens are never logged. `core/logging_setup.py` is the redaction source of truth; extend it instead of scattering redaction logic.
- Backend implementations conform to the `SeedrBackend` ABC. The UI never branches on authentication type.
- Link classification (magnet vs torrent URL) lives in `core/rest_v1_backend.classify_link`. The UI calls `backend.add_link()` and never inspects the link itself.
- Local downloads go through `core/downloader.Downloader`. The UI submits file/folder jobs and consumes events; it never streams bytes directly.
- Seedr file/folder downloads use a single `requests.get()` with `allow_redirects=True` and a `_ScopedAuth` wrapper that only signs the primary `www.seedr.cc` host. Two-step resolve-then-stream is forbidden because it races signed-URL expiry.
- The downloader's streaming session has no retry adapter. CDN signed URLs must not be retried on any status.
- All errors raised from download worker threads are translated inside the `log_operation` block so `corr_id` is preserved.
- Download filenames pass through `core/downloader._sanitize_filename`; Seedr-supplied names are not trusted as filesystem-safe.
- Treeview items use explicit iids built via `_make_iid(kind, seedr_id)` in `ui/dashboard_view.py`. `self.items` is keyed by the same iid. Never rely on Treeview's auto-generated `I001` iids.
- All Tk callback exceptions route through `App.report_callback_exception`, which logs to `seedrfetch.log` and raises a user-facing toast. Silent stderr-only failures are bugs.
- The uncaught-exception hook ignores `KeyboardInterrupt` and `SystemExit`; these are user-initiated and must not produce crash dumps.
- Tree item labels come from `_folder_label` / `_file_label` in `ui/dashboard_view.py`. Never build labels from IDs directly.
- Navigation state (current folder, back stack) lives on `DashboardView`. All folder loads go through `navigate_to` / `navigate_up` / `navigate_back`; do not add ad-hoc `backend.get_folder` calls in the UI.

## Coding conventions
- Use Python 3.13 and type hints throughout, including parameters and return values.
- Keep functions under roughly 40 lines where reasonable.
- Logging uses `%` formatting with arguments, never f-strings: `log.debug("got %d items", n)` is correct; `log.debug(f"got {n} items")` is not.
- Do not use emoji in UI text or code comments. UI glyphs are geometric only, such as `▸`, `▾`, `●`, and `◇`.
- Surface errors through `core/errors.translate()`. Never raise raw exceptions into the UI layer.
- Tests live beside the tested module as `test_<name>.py` and run with `python -m pytest`.

## UI / theme reference
The authoritative palette lives in `seedrfetch/ui/theme.py`: `BG_DEEP #0A0E1A`, `BG_PANEL #111827`, `BG_ELEVATED #1A2233`, `BG_DANGER #30151B`, `ACCENT #00E5FF`, `ACCENT_DIM #0891B2`, `ACCENT_2 #A855F7`, `SUCCESS #22D3EE`, `WARNING #F59E0B`, `DANGER #EF4444`, `TEXT_PRIMARY #E5E7EB`, `TEXT_MUTED #6B7280`, and `BORDER #1F2937`. Typography uses Segoe UI and Cascadia Mono. Reference these constants; never hardcode hex values elsewhere. Adding a color requires updating both `theme.py` and this section.

## Commands an agent will commonly run
```bash
# Install deps
python -m pip install -r seedrfetch/requirements.txt
# Run the app
python seedrfetch/main.py
# Run with verbose logging
python seedrfetch/main.py --debug
# Self-check the requirements file
python scripts/check_requirements.py
# Verify logging + SSL stack
python seedrfetch/scripts/log_smoke_test.py
# Compile-check every file
python -m compileall seedrfetch
# Run tests
python -m pytest -v
# Run focused dashboard navigation/label tests
python -m pytest tests/test_navigation.py tests/test_folder_labels.py
```

The workspace selects `rwakiDev_v3`; `seedrfetch/main.py` also relaunches itself with that interpreter when available.

## File-modification protocol (CRITICAL)
Every time an agent modifies code in this repo, it MUST:
1. Make the code change.
2. Update `AGENTS.md` if the tech stack, project structure, architecture rules, or commands changed.
3. Append an entry under `[Unreleased]` in `CHANGELOG.md`.
4. Run `python scripts/check_requirements.py` and `python -m compileall seedrfetch` before declaring the change complete.

Skipping step 3 is an incomplete change.

## Known environment quirks
- Windows with Norton 360 or Norton VPN may intercept TLS. `truststore` handles the common case, and Settings diagnostics expose the rest. Never disable SSL verification by default.
- The user runs Python 3.13. Do not regress to 3.12-only patterns.
- Some Seedr endpoints return 4xx responses with `{"reason_phrase": "..."}`. `core/errors.translate()` owns user-facing parsing; do not bypass it.

## What to ask the user before doing
- Ask before adding a third-party dependency beyond `seedrfetch/requirements.txt`.
- Ask before changing authentication flow or credential storage.
- Refuse requests to disable SSL verification anywhere.
- Ask before removing or replacing the logging system.

## Sibling project: Kazi Tracker

`kazi-tracker/` is an isolated React 19 + Vite + TypeScript task-management web
app deployed with Firebase Hosting, Authentication, Firestore, and a scheduled
Node.js 22 Cloud Function. Task sorting uses the official `@dnd-kit` core,
sortable, utilities, and modifiers packages. Its frontend commands run from `kazi-tracker/`:
`npm run dev`, `npm run build`, and `npm run lint`; validate Firestore rules
with `npm run test:rules` (Firebase CLI and Java required), and build the
function with `npm run functions:build`. Its fixed-account, one-time Google Doc task importer
runs manually with `npm run import:tasks`; the fixed-account Kirwa profile
repair runs with `npm run fix:kirwa-profile`. Firebase deployment configuration,
security rules, environment setup, shared phone-app schema, import setup, and
archival behavior are documented in `kazi-tracker/README.md`. Parent/child task
completion rules are centralized in `kazi-tracker/src/lib/taskHierarchy.ts`;
display numbering and reorder calculations live in
`kazi-tracker/src/lib/taskOrdering.ts`. Structured, phone-readable account
profiles live at `users/{uid}/profile/main`, and Nairobi calendar formatting is
centralized in `kazi-tracker/src/lib/nairobiDate.ts`. Daily recurring tasks keep
their normal priority and are reset by the Nairobi nightly function only after
that day's late-task report has been generated; pure deadline/reset helpers
live in `kazi-tracker/functions/src/nightly.ts`. Main-task step checklists are
embedded in the task document, remain separate from `parentId` subtasks, and
use `kazi-tracker/src/components/StepTaskBoard.tsx` plus
`kazi-tracker/src/lib/stepTasks.ts` for numbered drag ordering. A task can
complete only when both its child subtasks and embedded step tasks are complete.
Browser-side application failures are captured by
`kazi-tracker/src/lib/errorLog.ts`, redacted, capped at 200 entries, retained
only in local storage, and displayed through the authenticated `/errors` tab.

## Sibling project: Maintenant

`maintenant/` is an isolated React 19 + Vite + strict TypeScript industrial
maintenance web app. It uses Tailwind CSS, React Router, Supabase email/password
authentication, and a row-level-secured Postgres `readings` table. Frontend
commands run from `maintenant/`: `npm run dev`, `npm run lint`, and
`npm run build`. Environment, Supabase SQL, Vercel deployment, architecture,
and verification instructions live in `maintenant/README.md` and
`maintenant/AGENTS.md`.

## Sibling project: Kalenjin Learning Guide

`kalenjin-learning-guide/` is an isolated, dependency-free static web app for
the 12-week Kalenjin language teacher guide. It includes fillable translation
fields, device-local auto-save, lesson checklists, progress tracking, search,
printing, assessments, translator notes, and JSON backup/restore. It is
configured for Firebase Hosting with `kalenjin-learning-guide/firebase.json`.
Preview it from that directory with `python -m http.server 4173`, and deploy it
with `firebase deploy --only hosting` after selecting a Firebase project.

## Sibling project: qbSearch

`qbsearch/` is an isolated Python 3.13 CustomTkinter desktop front-end for
qBittorrent search plugins and its Web API. Search polling and magnet
detail-page resolution run in worker threads, while Tk updates are marshalled
onto the UI thread. Magnet-link requests open a live verbose activity window
whose logging handler writes only to a thread-safe queue; the window reports
HTTP status and extraction failures while redacting detail-page query strings.
Run its checks from `qbsearch/` with `.venv\Scripts\ruff.exe check .` and
`.venv\Scripts\python.exe -m pytest -v`. Its full architecture and packaging
rules live in `qbsearch/AGENTS.md`.
