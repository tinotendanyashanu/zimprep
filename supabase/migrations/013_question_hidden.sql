-- Migration 013: Add hidden flag to question table
-- Allows admins to hide incorrectly extracted questions from students
-- without deleting them (so they can be fixed and re-shown later).

alter table question
  add column if not exists hidden boolean not null default false;

create index if not exists question_hidden_idx on question (hidden);
