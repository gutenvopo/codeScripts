# Kazi Tracker

Kazi Tracker is a responsive, dark-mode task manager built with React,
TypeScript, Tailwind CSS, and Firebase. It supports nested tasks, private
step-task checklists, priority-aware drag and drop, deadlines, completion
celebrations, local weather, Firebase Authentication, nightly summaries, and a
Firestore schema shared cleanly with future Android and iOS clients.

## Local setup

1. Install Node.js 22 or newer and the Firebase CLI:

   ```bash
   npm install -g firebase-tools
   ```

2. Create a Firebase project, then enable:

   - Authentication: Email/Password and Google providers
   - Cloud Firestore in production mode
   - Firebase Hosting
   - Cloud Functions (the scheduled function requires the Blaze plan)

3. Register a Web app in Firebase. Copy `.env.example` to `.env` and replace
   each placeholder with the Web app configuration. Register the web app for
   App Check with reCAPTCHA Enterprise and add its public site key. Never
   commit `.env`.

4. Install both dependency sets and start Vite:

   ```bash
   npm install
   npm --prefix functions install
   npm run dev
   ```

5. Add `localhost` and your Hosting domain under Authentication > Settings >
   Authorized domains.

## Firebase project initialization

The required Firebase files are already included. Associate the folder with
your own project:

```bash
firebase login
firebase use --add
```

Alternatively, copy `.firebaserc.example` to `.firebaserc` and replace the
project ID. Do not run `firebase init` over the existing files. If starting from
an empty copy, choose Firestore, Functions (TypeScript), and Hosting; use
`dist` as the Hosting public directory and enable SPA rewrites.

## Build and deployment

Verify both TypeScript projects and create the deployable `dist/` directory:

```bash
npm run build
npm run functions:build
```

Deploy everything:

```bash
firebase deploy
```

Or deploy parts independently:

```bash
firebase deploy --only firestore:rules
firebase deploy --only hosting
firebase deploy --only functions:generateNightlySummaries
```

`firebase.json` serves `dist` and rewrites unknown routes to `index.html`, so
`/summary` and `/errors` work when opened directly.

## Error Log

The authenticated app includes an **Error Log** tab beside Tasks and Summary.
It captures verbose diagnostics for global JavaScript errors, unhandled promise
rejections, React render failures, resource-load failures, `console.error`
calls, and handled task, summary, weather, profile, and authentication errors.
Each entry includes its timestamp, source, route, message, stack trace, and
available diagnostic details.

The newest 200 entries are stored only in that browser's local storage until
cleared. Passwords, authorization values, tokens, secrets, credentials, and API
keys are redacted before an entry is retained. The log can be copied as JSON
for troubleshooting or cleared from the tab.

## One-time task import

`scripts/importTasks.ts` imports the published Google Doc into today's task
collection. It is a manual utility and never runs during app startup. The
destination is deliberately fixed to `kirwaboit@gmail.com`; the script resolves
that account's UID with Firebase Authentication and accepts no UID override.

In Firebase Console, open **Project settings > Service accounts > Firebase
Admin SDK**, select **Generate new private key**, and store the downloaded JSON
outside this repository. In PowerShell, point Application Default Credentials
at that file and run the import:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\secure\kazi-service-account.json"
npm run import:tasks
```

The service account must belong to the same Firebase project as the target
account and have access to Firebase Authentication and Firestore. If the target
already has tasks dated today in `Africa/Nairobi`, the script aborts without
writing. After reviewing the warning, an intentional repeat can be run with:

```powershell
npm run import:tasks -- --force
```

Never commit the service account key or place its contents in `.env`.

## One-time Kirwa profile correction

The fixed-account repair utility resolves `kirwaboit@gmail.com` through
Firebase Authentication, updates its Auth display name to `Kirwa Boit`, and
creates or merges `users/{resolvedUid}/profile/main` with the structured name.
It accepts no UID or email override. With `GOOGLE_APPLICATION_CREDENTIALS`
configured as above, run:

```powershell
npm run fix:kirwa-profile
```

## Firestore schema

The browser client and any phone client use the same flat documents. Mobile
clients should use their platform's native Firestore timestamp type for
timestamp fields and ISO 8601 strings for deadlines.

### `users/{uid}/tasks/{taskId}`

```ts
{
  id: string,
  title: string,
  priority: "high" | "medium" | "low",
  deadline: string | null,       // ISO 8601, including offset or Z
  order: number,                 // ordering within its priority group
  completed: boolean,
  completedAt: Timestamp | null,
  createdAt: Timestamp,
  date: string,                  // YYYY-MM-DD in the user's active day
  parentId: string | null,       // another task ID; null means top-level
  recurring: boolean,            // true for a task that resets every Nairobi day
  steps: [
    {
      id: string,
      title: string,
      order: number,
      completed: boolean
    }
  ]
}
```

Tasks remain ordinary documents—there are no React-specific fields. A phone
app can query the current `date`, sort by `order`, and connect children using
`parentId`. Task IDs are duplicated in `id` for convenient serialization and
cross-platform model parity.

Step tasks are distinct from parent/child subtasks and are embedded in their
main task document. The task card shows only a step count; selecting the card
opens the interactive checklist. Steps use one numbered drag-and-drop order. A
main task cannot be completed while either a child subtask or an embedded step
remains incomplete. Existing documents without `steps` are treated as having
an empty checklist.

### `users/{uid}/profile/main`

```ts
{
  firstName: string,
  lastName: string,
  email: string,
  createdAt: Timestamp
}
```

The structured profile is shared with phone clients. The lightweight
`users/{uid}` document remains available for compatibility with existing
account metadata.

### `users/{uid}/summaries/{YYYY-MM-DD}`

```ts
{
  date: string,
  totalTasks: number,
  completedTasks: number,
  completionRate: number,        // 0–100
  byPriority: {
    high: { total: number, completed: number },
    medium: { total: number, completed: number },
    low: { total: number, completed: number }
  },
  completedList: [
    { title: string, priority: "high" | "medium" | "low", completedAt: Timestamp | null }
  ],
  lateTasks: number,
  lateList: [
    {
      title: string,
      priority: "high" | "medium" | "low",
      deadline: string,
      recurring: boolean
    }
  ],
  generatedAt: Timestamp
}
```

When archival is enabled, completed source documents are copied to
`users/{uid}/taskArchive/{taskId}` with `archivedAt` and `sourceDate`, then
removed from `tasks`. Archives preserve the original task schema and are not
required by the UI.

## Nightly summary behavior

`generateNightlySummaries` runs at `00:05` in `Africa/Nairobi`. It:

1. Summarizes the previous Nairobi calendar day for every Firebase Auth user.
2. Writes that day's summary once, preserving the pre-reset snapshot during
   scheduler retries.
3. Records incomplete tasks whose deadline passed, plus tasks completed after
   their deadline, in the report's late count and list.
4. Resets every recurring task for the new day, preserving its deadline time,
   priority, and order while clearing both task and step-task completion state.
5. Rolls incomplete non-recurring tasks forward by changing their `date`.
6. Archives and removes completed non-recurring tasks when
   `ARCHIVE_COMPLETED_TASKS` is true.

Archival defaults to true. To retain completed task documents instead, set the
Cloud Functions parameter during deployment when prompted:

```text
ARCHIVE_COMPLETED_TASKS=false
```

With archival disabled, completed non-recurring documents remain on their
original date and therefore do not appear in the new day's task query.
Recurring tasks are never archived by this function. Summary generation and
task rollover are retry-safe: rerunning preserves the first pre-reset report
and finishes processing any task documents that remain on the previous day.

## Weather and location privacy

The browser asks for location only after the signed-in user selects **Use
current location**. The browser remains the authority for granting or denying
that permission. After a current or manually searched location is chosen, Kazi
Tracker remembers the forecast location for that account in this browser so it
does not ask again on every login. Stored coordinates are rounded to three
decimal places, kept in browser local storage under the account UID, and never
written to Firebase. Coordinates are sent to Open-Meteo and BigDataCloud for
forecast and reverse geocoding. The user can select **Change location** at any
time or search for a city manually through Open-Meteo's geocoding API.

## Security

`firestore.rules` defaults to deny, enforces owner-only access under
`users/{uid}`, validates known schemas, and protects server-generated summaries
and archives from client writes. Run the emulator evidence with:

```bash
npm run test:rules
```

App Check, Authentication console settings, billing alerts, secrets handling,
and the Cloud Functions trust model are documented in [SECURITY.md](SECURITY.md).
The Admin SDK used by the scheduled function runs in trusted Cloud Functions
infrastructure and is not governed by client security rules.
