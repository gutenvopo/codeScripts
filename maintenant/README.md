# Maintenant

Maintenant is a responsive dark-mode maintenance readings app for industrial
facilities. It uses Supabase email/password authentication, protected React
routes, and row-level-secured readings storage.

## Stack

- React 19, Vite, and strict TypeScript
- Tailwind CSS
- React Router
- Supabase Auth and Postgres
- Vercel for static frontend hosting

## Local Setup

Use Node.js 20.19+ or 22.12+ and npm. From this directory:

```powershell
npm install
Copy-Item .env.example .env
```

Edit `.env` with the values from Supabase, then start the app:

```powershell
npm run dev
```

Vite prints the local URL, normally `http://localhost:5173`. The app displays a
configuration notice and disables sign-in until both environment variables are
present. `.env` is ignored by Git.

## Supabase Setup

### 1. Create The Project

1. Sign in at the Supabase dashboard and select **New project**.
2. Choose an organization, name the project `maintenant`, create a strong
   database password, and select the closest suitable region.
3. Wait for provisioning to finish.

Project creation requires account and billing choices in the dashboard, so it
is intentionally not automated by this repository.

### 2. Configure Authentication

1. Open **Authentication > Providers > Email**.
2. Enable the Email provider. Leave password sign-in enabled and save.
3. Open **Authentication > Users**, select **Add user > Create new user**, and
   enter the first operator's email and password.
4. Enable automatic email confirmation for this dashboard-created user, or
   confirm the invitation before trying to sign in.

### 3. Create The Readings Table And Policies

Open **SQL Editor**, create a query, paste the complete contents of
[`supabase/schema.sql`](supabase/schema.sql), and select **Run**. The script:

- creates the `readings` table and supporting index;
- enables Row Level Security;
- permits authenticated users to insert rows carrying their own user ID; and
- permits authenticated users to read only their own rows.

The app creates one row for PT1 and one row for FM1 each time **Save Readings**
is selected. `created_at` is assigned by Postgres.

### 4. Add Environment Variables

In Supabase, open **Project Settings > API**. Copy the **Project URL** and the
publishable **anon** key. Depending on the dashboard version, the key may be
labelled **Publishable key** or **anon public**. Put them in `.env`:

```dotenv
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-publishable-anon-key
```

The anon key is intended for browser clients; Row Level Security is the actual
data boundary. Never place a service-role key in a Vite variable or frontend.

## Production Build

Run both checks before deployment:

```powershell
npm run lint
npm run build
```

The production files are generated in `dist/`.

## Deploy To Vercel

1. Push the repository to a Git provider supported by Vercel.
2. In Vercel, select **Add New > Project** and import the repository.
3. If this app is inside the shared repository, set **Root Directory** to
   `maintenant`.
4. Confirm **Framework Preset: Vite**, **Build Command: `npm run build`**, and
   **Output Directory: `dist`**.
5. Under **Environment Variables**, add `VITE_SUPABASE_URL` and
   `VITE_SUPABASE_ANON_KEY` for Production and Preview.
6. Deploy. `vercel.json` rewrites client-side routes to `index.html`, so direct
   visits to protected pages work.

After deployment, open Supabase **Authentication > URL Configuration**:

1. Set **Site URL** to the production Vercel URL, such as
   `https://maintenant.example.vercel.app`.
2. Add the production URL and any intentional Vercel preview pattern to
   **Redirect URLs**.
3. Keep `http://localhost:5173` as an allowed redirect while developing.

## End-To-End Verification

1. Visit `/login` and sign in with the dashboard-created user.
2. Open **Location**, visit both location options, and confirm each Back button.
3. Open **Historic Data** and confirm its placeholder view.
4. Open **Pump House 1**, enter values for PT1 and FM1, and save.
5. Confirm the success message, then open Supabase **Table Editor > readings**.
6. Verify two rows have the correct user ID, location, tags, values, and
   timestamps.
7. Select **Back** on Preventative Maintenance and confirm the session signs
   out and protected URLs redirect to `/login`.

## Project Structure

```text
src/components/       Shared layout, controls, route guards, and branding
src/context/          Supabase session state and auth actions
src/lib/supabase.ts   Environment-backed Supabase browser client
src/pages/            Login and maintenance workflow screens
supabase/schema.sql   Readings table, index, grants, and RLS policies
vercel.json           SPA route fallback for Vercel
```
