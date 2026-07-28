# Changelog
All notable changes to SeedrFetch are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
- Give every Kazi Tracker Error Log record its own Copy entry button with
  entry-specific success feedback. [kazi-tracker/src/pages/ErrorLogPage.tsx,
  kazi-tracker/src/styles/index.css]
- Normalize Kazi Tracker browser geolocation failures into readable
  `GeolocationError` records with permission, unavailable, and timeout
  messages, while preserving non-enumerable error properties and diagnostic
  codes in the local Error Log. [kazi-tracker/src/hooks/useWeather.ts,
  kazi-tracker/src/lib/errorLog.ts]
- Align Maintenant's dark interface and logo presentation with its navy-blue
  and orange industrial brand identity. [maintenant/src/]

### Added
- Add a browser-local, redacted Error Log tab to Kazi Tracker with verbose
  timestamps, sources, routes, messages, stack traces, diagnostic details,
  copy/clear controls, and capture for global, promise, React, resource,
  console, Firebase, weather, profile, and authentication failures.
  [kazi-tracker/src/lib/errorLog.ts,
  kazi-tracker/src/components/AppErrorBoundary.tsx,
  kazi-tracker/src/pages/ErrorLogPage.tsx, kazi-tracker/src/App.tsx,
  kazi-tracker/src/main.tsx, kazi-tracker/src/styles/index.css,
  kazi-tracker/README.md]
- Add a thread-safe, live verbose activity window to qbSearch magnet-link
  requests, covering direct/cache decisions, detail-page fetches, redirects,
  HTTP status and reason, response metadata, extraction failures, network
  exceptions, and clipboard completion while redacting URL query strings.
  [qbsearch/src/qbsearch/core/magnet_resolver.py,
  qbsearch/src/qbsearch/ui/results_table.py,
  qbsearch/src/qbsearch/ui/log_window.py, qbsearch/tests/]
- Add a colourful, fillable 12-week Kalenjin language teacher guide with all
  source lessons, auto-saving translation fields, lesson checklists, progress
  tracking, search, assessments, translator notes, print support, JSON
  backup/restore, responsive layouts, and Firebase Hosting configuration.
  [kalenjin-learning-guide/]
- Add bottom-corner Shopping and Task quick actions to Kazi Tracker. Shopping
  opens the active medium Shopping parent directly in subtask-entry mode,
  creating that parent on demand when absent, while Task opens the standard
  new-task dialog. [kazi-tracker/src/pages/TasksPage.tsx,
  kazi-tracker/src/components/AddTaskModal.tsx,
  kazi-tracker/src/hooks/useTasks.ts, kazi-tracker/src/styles/index.css]
- Remember each signed-in Kazi Tracker user's chosen forecast location in
  device-local browser storage, reuse it on later logins without prompting
  again, and request browser geolocation only after an explicit user action.
  [kazi-tracker/src/lib/locationPreference.ts,
  kazi-tracker/src/hooks/useWeather.ts,
  kazi-tracker/src/components/WeatherWidget.tsx,
  kazi-tracker/src/pages/TasksPage.tsx, kazi-tracker/README.md]
- Add the Maintenant industrial maintenance web app with protected Supabase
  authentication, facility navigation, Pump House readings persistence,
  database/RLS setup, and Vercel deployment documentation. [maintenant/]
- Add a Kazi Tracker TODO note for making Shopping easier to reach, easier to
  extend with subtasks, and persistent by default on starting lists.
  [kazi-tracker/TODO.md]
- Add a regular-task edit-modal shortcut for creating subtasks with a default
  23:59 Nairobi deadline, hidden from subtasks and step-task editors.
  [kazi-tracker/src/components/AddTaskModal.tsx,
  kazi-tracker/src/hooks/useTasks.ts, kazi-tracker/src/pages/TasksPage.tsx,
  kazi-tracker/src/styles/index.css]
- Add separate Kazi Tracker step-task checklists embedded in main tasks, with
  card-level completion indicators, click-to-open checklist dialogs,
  checkboxes, numbered drag-and-drop ordering, and full add/edit/remove
  controls in the task editor. Main-task completion now
  requires both subtasks and step tasks to be complete, and recurring nightly
  resets clear step completion for the next Nairobi day.
  [kazi-tracker/src/components/StepTaskBoard.tsx,
  kazi-tracker/src/components/StepTasksDialog.tsx,
  kazi-tracker/src/lib/stepTasks.ts, kazi-tracker/src/hooks/useTasks.ts,
  kazi-tracker/functions/src/, kazi-tracker/firestore.rules]
- Add Kazi Tracker daily recurring tasks with create/edit controls, visible
  task badges, schema-aware Firestore validation, Nairobi-time nightly resets,
  and daily-report late counts/lists captured before recurring completion and
  deadlines reset for the next day. Preserve that pre-reset report across
  scheduler retries while unfinished task rollovers continue safely.
  [kazi-tracker/src/, kazi-tracker/functions/src/,
  kazi-tracker/firestore.rules, kazi-tracker/test/,
  kazi-tracker/functions/test/, kazi-tracker/README.md]
- Add Kazi Tracker security hardening with schema-aware, default-deny Firestore
  rules; emulator owner-isolation tests; reCAPTCHA Enterprise App Check;
  bounded listeners; generic authentication failures; stronger signup
  passwords; scheduler runtime bounds; expanded secret ignores; and an
  operational security guide.
  [kazi-tracker/firestore.rules, kazi-tracker/test/firestore.rules.test.mjs,
  kazi-tracker/src/lib/firebase.ts, kazi-tracker/SECURITY.md]
- Add a concise dawn-to-dusk summary inside Kazi Tracker's Tasks weather
  widget, derived client-side from Open-Meteo sunrise, sunset, hourly
  conditions, daytime rain probability, and daily high/low data.
  [kazi-tracker/src/lib/weather.ts,
  kazi-tracker/src/components/WeatherWidget.tsx,
  kazi-tracker/src/styles/index.css]
- Add structured Kazi Tracker signup profiles, app-wide profile loading, a
  personalized Tasks greeting, a live Nairobi-local ordinal date, and a
  single-account admin repair command for `kirwaboit@gmail.com`.
  [kazi-tracker/src/hooks/useAuth.ts, kazi-tracker/src/hooks/useNairobiDate.ts,
  kazi-tracker/src/lib/nairobiDate.ts, kazi-tracker/src/types/profile.ts,
  kazi-tracker/scripts/fixKirwaProfile.ts, kazi-tracker/package.json,
  kazi-tracker/README.md]
- Add a compact inline-SVG rain indicator beside Kazi Tracker's mean
  precipitation probability, with data-driven drop intensity, staggered
  animation, cyan glow, and reduced-motion behavior.
  [kazi-tracker/src/components/WeatherWidget.tsx,
  kazi-tracker/src/styles/index.css]
- Add a guarded, single-account Kazi Tracker import command that parses the
  published Google Doc's list hierarchy, derives Nairobi-local deadlines,
  resolves `kirwaboit@gmail.com` through Firebase Admin Authentication, and
  batch-writes schema-compatible tasks with duplicate-date protection.
  [kazi-tracker/scripts/importTasks.ts, kazi-tracker/package.json,
  kazi-tracker/README.md]
- Add the complete Kazi Tracker Firebase web app with authenticated React and
  TypeScript task management, nested priority lists, cross-group drag and drop,
  animated completion feedback, Open-Meteo weather, daily summary history,
  owner-only Firestore rules, and a configurable Nairobi nightly summary and
  archival function. [kazi-tracker/]
- Add qbSearch's self-contained Windows release pipeline: a shared version and
  application identity source, windowed PyInstaller onedir build with required
  UI/TLS assets, Inno Setup per-user/all-users installer and shortcuts,
  opt-in uninstall data cleanup, an idempotent PowerShell build orchestrator,
  and clean-machine packaging guidance. [qbsearch/src/qbsearch/version.py,
  qbsearch/build/qbsearch.spec, qbsearch/installer/qbsearch.iss,
  qbsearch/scripts/build.ps1, qbsearch/docs/PACKAGING.md]
- Add authoritative agent memory, changelog enforcement, dependency checks, and local pre-commit hooks. [AGENTS.md, CHANGELOG.md, scripts/, .pre-commit-config.yaml]
- Add a clipboard-replacing Paste button to the link bar and a persistent Exit button. [seedrfetch/ui/dashboard_view.py, seedrfetch/ui/app.py]
- Add the standalone qbSearch qBittorrent search front-end scaffold. [qbsearch/]
- Add a qbSearch results-table Action column for copying magnet/torrent links, toast feedback, and horizontal table scrolling. [qbsearch/src/qbsearch/ui/results_table.py, qbsearch/src/qbsearch/ui/toast.py]
- Back and Up navigation buttons above the SeedrFetch file tree, plus a clickable breadcrumb built from Seedr's `fullname` field. Keyboard shortcuts: Alt+Left (back), Alt+Up (up), Backspace (back when no input is focused). [seedrfetch/ui/dashboard_view.py]
- Add focused dashboard navigation and file-tree label tests. [tests/test_navigation.py, tests/test_folder_labels.py]
- Add end-to-end local file/folder download jobs with signed-URL resolution, streamed CDN downloads without backend auth, resumable `.part` files, range requests, cancellation, retry/dismiss/open actions, and live progress rows in the dashboard. [seedrfetch/core/downloader.py, seedrfetch/ui/dashboard_view.py]
- Add filename sanitization coverage and downloader behavior tests for redirects, unknown content length, cancellation, resume, HTTP failures, collisions, and unsafe names. [tests/test_downloader.py, tests/test_filename_sanitization.py]
- Add a "Download link expired" UserError for Seedr CDN 404s with guidance pointing to HTTPS inspection as the likely cause. [seedrfetch/core/errors.py]
- Add a TLS warning path that records suspected HTTPS inspection on Seedr certificate chains and surfaces it in Settings > SSL & Network. [seedrfetch/core/ssl_setup.py, seedrfetch/ui/settings_view.py]

### Changed
- Give Kazi Tracker's Shopping and Task floating actions a glossy glass finish
  with translucent color layers, blurred backdrops, reflective highlights, and
  polished depth shadows. [kazi-tracker/src/styles/index.css]
- Simplify Kazi Tracker step tasks into one numbered, draggable checklist
  without High, Medium, or Low categories.
  [kazi-tracker/src/components/StepTaskBoard.tsx,
  kazi-tracker/src/lib/stepTasks.ts]
- Sort Kazi Tracker's parent-task selector alphabetically by task title in the
  new-task and edit-task forms.
  [kazi-tracker/src/components/AddTaskModal.tsx]
- Make Kazi Tracker App Check initialization optional: an absent or blank
  reCAPTCHA Enterprise site key now logs a warning and leaves the app usable
  instead of crashing during startup.
  [kazi-tracker/src/lib/firebase.ts, kazi-tracker/.env.example,
  kazi-tracker/SECURITY.md]
- Replace Kazi Tracker's generic checkmark brand mark with the faithfully
  converted Android adaptive icon, and use it for the SVG favicon, PNG browser
  fallbacks, Apple touch icon, and installable web-app icons.
  [kazi-tracker/assets/icon/kazi-icon.svg, kazi-tracker/public/,
  kazi-tracker/index.html, kazi-tracker/src/App.tsx,
  kazi-tracker/src/components/LoginScreen.tsx]
- Make Kazi Tracker's Logout action explicit and mobile-safe with a labeled
  exit icon, accessible tap target, and restrained danger styling; replace the
  generic main weather glyph with condition-specific animated SVGs for sun,
  partial cloud, overcast, fog, rain, thunder, and snow.
  [kazi-tracker/src/App.tsx, kazi-tracker/src/components/WeatherWidget.tsx,
  kazi-tracker/src/styles/index.css]
- Reorganize the Kazi Tracker Tasks weather widget into three balanced internal
  glass sub-panels for date/temperature, the day summary, and rain chance,
  stacking them cleanly on narrow screens without changing forecast behavior.
  [kazi-tracker/src/components/WeatherWidget.tsx,
  kazi-tracker/src/pages/TasksPage.tsx, kazi-tracker/src/styles/index.css]
- Increase the Kazi Tracker rain indicator's drop contrast with brighter cyan,
  stronger opacity, slightly thicker streaks, layered glow, and a gentler fade
  for dim or low-quality displays. [kazi-tracker/src/styles/index.css]
- Scale Kazi Tracker's animated rain indicator with its probability typography
  and show rounded Celsius and derived Fahrenheit temperatures side by side.
  [kazi-tracker/src/components/WeatherWidget.tsx,
  kazi-tracker/src/styles/index.css]
- Animate the Kazi Tracker login-page wordmark's existing white, cyan, and
  purple gradient as a seamless five-second light wave, with a static
  reduced-motion fallback. [kazi-tracker/src/styles/index.css]
- Default new Kazi Tracker deadlines to 23:59 on the current Nairobi calendar
  day while preserving each existing task's saved time when editing.
  [kazi-tracker/src/components/AddTaskModal.tsx,
  kazi-tracker/src/hooks/useTasks.ts, kazi-tracker/src/lib/nairobiDate.ts]
- Rework Kazi Tracker task sorting around stable parent-family and sibling-child
  sortable contexts, dedicated handles, keyboard/touch sensors, fixed-slot
  display numbering, drag overlays, optimistic local ordering, and one
  Firestore batch per drop. Parent moves retain their children, while children
  can only reorder inside their own family. [kazi-tracker/src/components/TaskItem.tsx,
  kazi-tracker/src/components/TaskList.tsx, kazi-tracker/src/hooks/useTasks.ts,
  kazi-tracker/src/lib/taskOrdering.ts, kazi-tracker/src/pages/TasksPage.tsx,
  kazi-tracker/src/styles/index.css, kazi-tracker/package.json]
- Wrap long Kazi Tracker task titles without clipping, gate parent completion
  on child status, atomically auto-complete or reopen parents as children
  change, and keep completed parent/child families visually grouped.
  [kazi-tracker/src/components/TaskItem.tsx,
  kazi-tracker/src/components/TaskList.tsx, kazi-tracker/src/hooks/useTasks.ts,
  kazi-tracker/src/lib/taskHierarchy.ts, kazi-tracker/src/pages/TasksPage.tsx,
  kazi-tracker/src/styles/index.css]
- Restore Kazi Tracker Hosting to the Vite `dist/` output after Firebase
  initialization replaced it with the starter `public/` directory.
  [kazi-tracker/firebase.json]
- Centralize the danger-banner background color in the UI theme. [seedrfetch/ui/theme.py, seedrfetch/ui/widgets.py]
- Organize every Internet Speed Test script version, its runtime logs, and project documentation under a dedicated folder. [internet_speed_test/]

### Fixed
- Fix Kazi Tracker's initial iPhone scale with a single
  `width=device-width`/`viewport-fit=cover` viewport declaration, remove the
  global fixed minimum width, add safe-area-aware mobile gutters, and keep
  mobile form controls at 16px to prevent Safari focus zoom.
  [kazi-tracker/index.html, kazi-tracker/src/styles/index.css]
- Fix Kazi Tracker's narrow-screen task cards and controls by constraining all
  task-family layers to fluid viewport-safe widths, reducing child indentation,
  restoring Add Task to normal flow, and moving navigation out of fixed
  positioning with 44px touch targets. [kazi-tracker/src/styles/index.css]
- Make Kazi Tracker's rain indicator read as continuous rainfall by rendering
  five to seven independently timed drops across the cloud, with varied
  durations, negative staggered phases, and linear infinite falls.
  [kazi-tracker/src/components/WeatherWidget.tsx,
  kazi-tracker/src/styles/index.css]
- Show Kazi Tracker's daily mean precipitation probability as its primary
  chance-of-rain value instead of the day's misleading hourly maximum, while
  retaining the peak in a tooltip. [kazi-tracker/src/lib/weather.ts,
  kazi-tracker/src/components/WeatherWidget.tsx]
- Fix the Kazi Tracker task importer crashing under `tsx` ESM execution because
  the Firebase Admin namespace import exposed `apps` as undefined.
  [kazi-tracker/scripts/importTasks.ts]
- File tree displayed generic "Folder {id}" labels instead of the real folder names returned by Seedr. Labels now use the API's `name` field via `_folder_label` / `_file_label` helpers, with a debug-logged fallback for genuinely unnamed items. [seedrfetch/ui/dashboard_view.py]
- Resolve qbSearch magnet copies from plugin detail pages when qBittorrent search results expose HTML URLs instead of real magnet URIs, with cached asynchronous lookups. [qbsearch/src/qbsearch/core/magnet_resolver.py, qbsearch/src/qbsearch/ui/results_table.py]
- Magnet links no longer route to /rest/torrent/url and produce 422 not_a_torrent. Classification centralised in core/rest_v1_backend.classify_link(); dashboard now calls backend.add_link(). [ui/dashboard_view.py, core/rest_v1_backend.py, core/backend.py] [3361c4b9]
- Parse Seedr `reason_phrase`, `reason`, and `message` response fields when translating HTTP errors. [seedrfetch/core/errors.py]
- Access urllib3 through Requests' compatibility namespace so every direct third-party import remains declared. [seedrfetch/core/ssl_setup.py]
- Isolate each speed-test diagnostic run in its own window and replace stale results in the error log. [internet_speed_test/speedtest_gui_v1.07.py]
- Fix right-click Download on files and folders so it queues a visible local download job instead of silently resolving a URL with no dashboard progress. [seedrfetch/ui/dashboard_view.py, seedrfetch/core/downloader.py]
- Fix downloads failing with 404 on Seedr CDN signed URLs by resolving and streaming through a single `allow_redirects=True` request scoped with `_ScopedAuth`; Basic auth is applied only to `www.seedr.cc` and stripped from CDN hops, and the streaming session disables retries so signed URLs are not burned by retry attempts. [seedrfetch/core/downloader.py, seedrfetch/core/rest_v1_backend.py, seedrfetch/core/backend.py]
- Fix the first-click download race by replacing ad-hoc thread-per-job execution with a `ThreadPoolExecutor` and emitting the `queued` event synchronously before pool submission so the dashboard row appears on the first click. [seedrfetch/core/downloader.py]
- Fix download error logs showing correlation ID `--------` by translating worker-thread exceptions inside the `log_operation` block with the explicit download `corr_id`. [seedrfetch/core/downloader.py, seedrfetch/core/errors.py]
- Fix right-click Download silently doing nothing with `KeyError: 'I004'` by making Treeview iids explicit via `_make_iid(kind, seedr_id)` and using the same iid keys in `DashboardView.items`; unknown iids now warn and show a refresh toast instead of raising. [seedrfetch/ui/dashboard_view.py, tests/test_dashboard_iid.py]
- Fix Tk callback exceptions only printing to stderr by installing `App.report_callback_exception`, which logs callback failures and shows a danger toast. [seedrfetch/ui/app.py]
- Fix Ctrl+C exits producing spurious uncaught-exception crash dumps by ignoring `KeyboardInterrupt` and `SystemExit` in the exception hooks and wrapping the Tk mainloop for graceful shutdown. [seedrfetch/core/logging_setup.py, seedrfetch/main.py, tests/test_excepthook_filter.py]

## [0.1.0] - 2026-06-21
### Added
- Initial scaffold: project structure, AGENTS.md, CHANGELOG.md.
- REST v1 backend with HTTP Basic auth (email + password).
- Device-code backend via seedrcc.
- CustomTkinter dark futuristic UI with cyan accent.
- In-app onboarding modal, Help view, Settings view.
- Resumable threaded downloads with `.part` files, HTTP Range requests, progress, speed, and cancellation.
- Encrypted remembered credentials and account sign-out cleanup.
- `core/ssl_setup` with `truststore.inject_into_ssl()` and `TLSDiagnosticAdapter` for intercepted-certificate visibility.
- Structured logging with correlation IDs, credential redaction, crash reports, and dedicated `http.log` / `tls-events.log` streams.
- `core/errors.translate()` with instructional user errors and correlated log excerpts.
- DNS, TCP, TLS-interception, and Seedr API diagnostics with support-bundle copying.
- First-run walkthrough, contextual help, tooltips, persistent navigation, and SSL warning banner.
- README installation, Norton/antivirus guidance, usage instructions, and logging smoke-test documentation.
- VS Code and entry-point selection of the `rwakiDev_v3` Python 3.13 environment.

### Security
- Route outbound Requests traffic through the shared session factory with native trust, CA overrides, proxies, retries, and TLS evidence capture.
- Redact credentials, Basic authorization values, tokens, API keys, and email local parts before log formatting.
