-- Migration 010: Store MCQ option texts on the question row
-- mcq_options: [{"letter": "A", "text": "..."}, ...] — null for written questions

alter table question
  add column if not exists mcq_options jsonb;
