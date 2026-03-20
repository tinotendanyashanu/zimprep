-- Migration 006: Answer hash cache for zero-cost repeated marking

create table if not exists marking_cache (
  id          uuid primary key default uuid_generate_v4(),
  answer_hash text not null unique,
  result      jsonb not null,
  created_at  timestamptz not null default now()
);

create index if not exists idx_marking_cache_hash on marking_cache (answer_hash);

-- Cache is readable/writable by service role only (no RLS needed — backend-only table)
