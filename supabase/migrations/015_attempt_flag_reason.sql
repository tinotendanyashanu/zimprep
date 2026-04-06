-- Migration 015: Add flag_reason to attempt
-- 'question_issue'  — student reports the question text/image is wrong or unclear
-- 'marking_issue'   — student believes their answer was marked incorrectly

alter table attempt
  add column if not exists flag_reason text
    check (flag_reason in ('question_issue', 'marking_issue'));
