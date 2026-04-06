-- Migration 012: Add exam_session to paper table
-- ZIMSEC runs two exam sittings per year: June and November

alter table paper
  add column if not exists exam_session text
    check (exam_session in ('june', 'november'));
