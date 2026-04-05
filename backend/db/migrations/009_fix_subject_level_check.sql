-- Migration 009: Fix subject level check constraint to include Cambridge levels
-- The 008 migration added exam_board but forgot to update the level constraint

ALTER TABLE subject
  DROP CONSTRAINT IF EXISTS subject_level_check;

ALTER TABLE subject
  ADD CONSTRAINT subject_level_check
    CHECK (level IN ('Grade7', 'O', 'A', 'IGCSE', 'AS_Level', 'A_Level'));
