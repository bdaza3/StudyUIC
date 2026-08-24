-- Run this in a Supabase migration. Spatial data requires PostGIS.
create extension if not exists postgis with schema extensions;

create table if not exists public.study_spots (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  building text not null,
  outlet_density text not null check (outlet_density in ('High', 'Med', 'Low')),
  coordinates extensions.geometry(Point, 4326) not null
);

create table if not exists public.study_beacons (
  id uuid primary key default gen_random_uuid(),
  spot_id uuid not null references public.study_spots(id) on delete cascade,
  course_code text not null check (char_length(trim(course_code)) between 2 and 32),
  description text not null check (char_length(trim(description)) between 1 and 280),
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default (now() + interval '2 hours'),
  check (expires_at > created_at)
);

create index if not exists study_spots_coordinates_gix on public.study_spots using gist (coordinates);
create index if not exists study_beacons_active_idx on public.study_beacons (spot_id, expires_at);

alter table public.study_spots enable row level security;
alter table public.study_beacons enable row level security;

create policy "Anyone can view study spots"
  on public.study_spots for select using (true);
create policy "Anyone can view active study beacons"
  on public.study_beacons for select using (true);
-- Anonymous insert is deliberately enabled for this MVP. Add auth/rate limiting before production launch.
create policy "Anyone can create a beacon"
  on public.study_beacons for insert with check (expires_at > now() and expires_at <= now() + interval '24 hours');

-- Makes postgres_changes subscriptions available for these tables in Supabase Realtime.
alter publication supabase_realtime add table public.study_beacons;
