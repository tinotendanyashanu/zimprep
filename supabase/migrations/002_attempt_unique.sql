-- Migration 002: Add unique constraint to attempt(session_id, question_id)
-- Required for upsert-based autosave and submit in the exam session flow.

alter table attempt
  drop constraint if exists attempt_session_question_unique;

alter table attempt
  add constraint attempt_session_question_unique unique (session_id, question_id);
