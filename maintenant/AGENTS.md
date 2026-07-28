# Maintenant Agent Guide

## Purpose

Maintenant is an industrial preventative-maintenance web app. It records Pump
House 1 instrument readings under an authenticated operator and leaves clear
extension points for additional facilities and historic reporting.

## Architecture

- React 19 + Vite + strict TypeScript; npm is the package manager.
- Tailwind CSS owns styling. Keep the deep navy surfaces, Maintenant blue
  primary actions, and orange focus/attention accent defined in
  `tailwind.config.js`.
- React Router owns navigation. All operational routes must remain beneath
  `ProtectedRoute`; `/login` is the only public workflow route.
- `AuthProvider` owns Supabase session state and auth actions.
- `src/lib/supabase.ts` is the only Supabase client constructor. Credentials
  come only from `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.
- Database access must respect the user-owned RLS model in
  `supabase/schema.sql`. Never put a service-role key in frontend code.
- Reusable controls and layouts belong in `src/components`; route screens
  belong in `src/pages`.
- The supplied logo is preserved at `src/assets/logo.png` and is used for the
  login brand, application header, and favicon. Keep its white field intact;
  `BrandLogo` controls the presentation crop without modifying the asset.

## Conventions

- Do not introduce `any`; keep TypeScript strict and resolve lint warnings.
- Keep field labels programmatically associated with inputs and preserve clear
  keyboard focus states and touch targets of at least 48 pixels.
- Surface authentication and database errors inline. Successful writes require
  an accessible status confirmation.
- A Pump House save is atomic from the UI perspective: submit PT1 and FM1 in a
  single Supabase insert call.
- Update `CHANGELOG.md` whenever behavior changes and update `README.md` when
  setup or deployment changes.

## Commands

```powershell
npm install
npm run dev
npm run lint
npm run build
npm run preview
```

## Environment

Copy `.env.example` to `.env` and supply the Supabase project URL and anon key.
The local `.env` must remain untracked. Run `supabase/schema.sql` in the target
Supabase project's SQL Editor before testing writes.
