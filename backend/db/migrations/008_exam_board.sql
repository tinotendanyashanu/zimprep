-- Migration 008: Add exam_board to student and subject tables
-- Supports ZIMSEC and Cambridge exam boards

-- Add exam_board to subject table
ALTER TABLE subject
  ADD COLUMN IF NOT EXISTS exam_board TEXT NOT NULL DEFAULT 'zimsec'
    CHECK (exam_board IN ('zimsec', 'cambridge'));

-- Add exam_board to student table
ALTER TABLE student
  ADD COLUMN IF NOT EXISTS exam_board TEXT NOT NULL DEFAULT 'zimsec'
    CHECK (exam_board IN ('zimsec', 'cambridge'));

-- Update existing level check to allow Cambridge levels
-- Cambridge levels: IGCSE (O-equiv), AS_Level, A_Level
-- ZIMSEC levels: Grade7, O, A (existing)

-- Index for fast filtering
CREATE INDEX IF NOT EXISTS idx_subject_exam_board ON subject(exam_board);
CREATE INDEX IF NOT EXISTS idx_student_exam_board ON student(exam_board);
