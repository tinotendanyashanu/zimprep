-- Migration 009: Add exam_board support to subject and student tables,
-- and extend the subject.level check constraint to include Cambridge levels.

-- ── 1. subject: add exam_board column ────────────────────────────────────────
ALTER TABLE subject
  ADD COLUMN IF NOT EXISTS exam_board TEXT NOT NULL DEFAULT 'zimsec';

-- Backfill any existing rows (all existing subjects are ZIMSEC)
UPDATE subject SET exam_board = 'zimsec' WHERE exam_board IS NULL OR exam_board = '';

ALTER TABLE subject
  DROP CONSTRAINT IF EXISTS subject_exam_board_check;

ALTER TABLE subject
  ADD CONSTRAINT subject_exam_board_check
  CHECK (exam_board IN ('zimsec', 'cambridge'));


-- ── 2. subject: extend level check constraint to include Cambridge levels ─────
ALTER TABLE subject
  DROP CONSTRAINT IF EXISTS subject_level_check;

ALTER TABLE subject
  ADD CONSTRAINT subject_level_check
  CHECK (level IN ('Grade7', 'O', 'A', 'IGCSE', 'AS_Level', 'A_Level'));


-- ── 3. student: add exam_board column (used by exam-select filter) ────────────
ALTER TABLE student
  ADD COLUMN IF NOT EXISTS exam_board TEXT DEFAULT 'zimsec';

-- Backfill existing rows
UPDATE student SET exam_board = 'zimsec' WHERE exam_board IS NULL;

ALTER TABLE student
  DROP CONSTRAINT IF EXISTS student_exam_board_check;

ALTER TABLE student
  ADD CONSTRAINT student_exam_board_check
  CHECK (exam_board IN ('zimsec', 'cambridge'));
