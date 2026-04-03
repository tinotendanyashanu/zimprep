-- Migration 007: Make student.name and student.level nullable
-- Auth-only signups won't have a name/level until they complete their profile.
ALTER TABLE student ALTER COLUMN name DROP NOT NULL;
ALTER TABLE student ALTER COLUMN level DROP NOT NULL;
