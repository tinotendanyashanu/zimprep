-- Migration 014: Question quality review queue
-- Auto-flagged by the extraction pipeline when questions fail quality checks.
-- Flagged questions are hidden from students until an admin approves them.

alter table question
  add column if not exists needs_review  boolean  not null default false,
  add column if not exists review_reasons text[]   not null default '{}';

create index if not exists question_needs_review_idx on question (needs_review) where needs_review = true;
