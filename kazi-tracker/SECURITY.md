# Kazi Tracker security

## Security boundary

Firebase Authentication identifies the user, Firestore Security Rules enforce
document ownership, and App Check attests that browser requests came from the
registered Kazi Tracker web app. These controls are complementary: App Check
does not replace Authentication or Security Rules.

`firestore.rules` defaults to deny and grants access only inside
`users/{request.auth.uid}`:

- User metadata and structured profiles are owner-only and schema validated.
- Tasks are owner-only, have an exact field allowlist, and validate IDs, title
  length, priority, completion state, timestamps, date, order, and parent IDs.
- Summaries and task archives are owner-readable but client-write-protected;
  only trusted Admin SDK code creates them.
- Future user subcollections inherit owner-only access. Known collections are
  explicitly excluded from that fallback so it cannot bypass stricter rules.
- Collection queries require a bounded `limit`.
- Every path outside `users/{uid}` is denied.

The Admin SDK bypasses Firestore rules. Admin scripts therefore resolve their
fixed target through Firebase Authentication and keep credentials outside the
repository.

## Verify Firestore rules

The test suite uses `@firebase/rules-unit-testing` against the local Firestore
Emulator. It proves same-user access, cross-user read/write denial,
unauthenticated denial, schema rejection, bounded queries, and read-only
server-generated summaries.

Prerequisites are Node.js, Firebase CLI, and Java 21 or another emulator-
supported Java runtime. Run:

```bash
npm run test:rules
```

The test library connects only to the emulator and never production Firestore.

## Firebase App Check

When its optional site key is configured, the web client initializes App Check
before Authentication or Firestore using the reCAPTCHA Enterprise provider and
enables automatic token refresh. Without the key, initialization is skipped
with a console warning so Authentication and Firestore remain available.

### Console setup and enforcement

1. In Google Cloud Console, create a website reCAPTCHA Enterprise key and add
   the Firebase Hosting domain and any custom production domains.
2. In Firebase Console, open **Security > App Check**, select the registered web
   app, and register the reCAPTCHA Enterprise key.
3. Set the public site key in the deployment environment:

   ```text
   VITE_FIREBASE_APPCHECK_RECAPTCHA_ENTERPRISE_SITE_KEY=...
   ```

4. Build and deploy the updated client. Confirm valid requests appear in App
   Check metrics before enabling enforcement.
5. In **Security > App Check**, enable enforcement for **Cloud Firestore**.
   Enable enforcement for **Authentication** as well after confirming metrics.
   Unverified requests are rejected after enforcement propagates.

App Check product enforcement is a Firebase Console project setting and is not
represented by `firebase.json`. Keep it enabled in every production project.
See the official
[web setup](https://firebase.google.com/docs/app-check/web/recaptcha-enterprise-provider)
and [enforcement guide](https://firebase.google.com/docs/app-check/enable-enforcement).

### Local development

Set `VITE_FIREBASE_APPCHECK_DEBUG=true` only in a local `.env`. Open the browser
console once, copy the generated debug token, and register it under **Security
> App Check > Apps > Manage debug tokens**. Never commit or share a debug
token, and never enable debug mode in a production build.

## Authentication hardening

- Email/password sign-up requires at least 12 characters containing uppercase,
  lowercase, and numeric characters. Login requirements are unchanged for
  existing accounts.
- Configure the matching server-side policy in **Firebase Console > Security >
  Authentication > Settings > Password policy**, using **Require** mode.
- Enable **Email enumeration protection** under **Authentication > Settings >
  User actions**. Projects created after September 15, 2023 generally have it
  enabled by default, but verify it explicitly.
- Enable Authentication App Check enforcement after monitoring valid traffic.
- Firebase Authentication applies built-in IP-based signup throttling. Do not
  replace it with client-only rate limiting.
- The UI maps failures to generic sign-in/sign-up messages. It never reveals
  whether a submitted email is registered.

See Firebase's
[password authentication guidance](https://firebase.google.com/docs/auth/web/password-auth)
and Google's
[email enumeration protection guide](https://cloud.google.com/identity-platform/docs/admin/email-enumeration-protection).

## Cloud Functions

The project exposes no callable or public HTTP functions. The only function,
`generateNightlySummaries`, is invoked by Cloud Scheduler through IAM, accepts
no user-controlled parameters, derives UIDs from Firebase Authentication, and
constructs every path beneath that UID. Runtime concurrency and instance count
are capped at one to prevent overlapping jobs.

App Check is designed for requests from app clients and does not apply to the
IAM-authenticated scheduler invocation. Any future callable function must:

```ts
onCall(
  { enforceAppCheck: true },
  (request) => {
    if (!request.auth) throw new HttpsError("unauthenticated", "Sign in required.");
    // Validate request.data with explicit type, length, and allowlist checks.
    // Derive the Firestore UID only from request.auth.uid.
  },
);
```

Sensitive or replay-prone callables should additionally use
`consumeAppCheckToken: true`. See the official
[Cloud Functions App Check guide](https://firebase.google.com/docs/app-check/cloud-functions).

## Secrets and sensitive data

- `.env*`, private keys, service-account JSON patterns, runtime config, build
  output, and Firebase debug logs are ignored. `.env.example` contains
  placeholders only.
- Service-account keys belong outside this repository and are referenced only
  through `GOOGLE_APPLICATION_CREDENTIALS`.
- Firebase web configuration and the reCAPTCHA site key are public client
  identifiers, not server secrets. No Admin credential is bundled into the
  client.
- Firestore stores task data, account email/name metadata, and generated
  summaries only. It stores no passwords, tokens, weather coordinates, or
  service credentials.
- No credentials, tokens, task content, or user identity are placed in URL
  query parameters. The weather feature necessarily sends a user-approved
  location/city to the disclosed Open-Meteo and BigDataCloud endpoints and
  never stores it in Firebase.
- Firebase Hosting serves production traffic over HTTPS. Do not create
  alternate plaintext origins.

If a credential is ever committed, remove it from history, revoke it
immediately, and issue a replacement. Deleting the file alone is insufficient.

## Cost and abuse controls

- App Check rejects unattested scripted Firestore/Auth traffic after console
  enforcement. It raises the cost of automated abuse but is not a complete DDoS
  service or a substitute for rules and quotas.
- Task listeners are restricted to the active Nairobi date and 500 documents.
  Summary listeners are ordered and capped at 180 documents. No client code
  recursively opens listeners or retries writes in a loop.
- Firestore rules require query limits, preventing unbounded collection reads
  through the browser client.
- In **Google Cloud Console > Billing > Budgets & alerts**, create a monthly
  budget scoped to this project and configure actual-spend alerts such as 50%,
  90%, and 100%, plus forecast alerts appropriate to the expected spend.
- Budget alerts notify; they do not automatically cap charges. Review Firestore,
  Authentication, Functions, Scheduler, and reCAPTCHA usage alongside billing.

See Firebase's
[avoid surprise bills](https://firebase.google.com/docs/projects/billing/avoid-surprise-bills)
guidance.
