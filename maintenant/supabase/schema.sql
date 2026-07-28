create extension if not exists pgcrypto;

create table if not exists public.readings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  location text not null,
  instrument_tag text not null,
  value numeric not null,
  created_at timestamptz not null default now()
);

create index if not exists readings_user_created_at_idx
  on public.readings (user_id, created_at desc);

alter table public.readings enable row level security;

drop policy if exists "Users can insert their own readings" on public.readings;
create policy "Users can insert their own readings"
  on public.readings
  for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists "Users can read their own readings" on public.readings;
create policy "Users can read their own readings"
  on public.readings
  for select
  to authenticated
  using ((select auth.uid()) = user_id);

grant usage on schema public to authenticated;
grant select, insert on table public.readings to authenticated;
