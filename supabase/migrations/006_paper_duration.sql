-- Migration 006: Add duration_minutes to paper table
-- Run in Supabase SQL Editor (Dashboard → SQL → New Query)

ALTER TABLE paper
  ADD COLUMN IF NOT EXISTS duration_minutes INTEGER NOT NULL DEFAULT 120;

COMMENT ON COLUMN paper.duration_minutes IS
  'Exam duration in minutes. Common values: 90 (1.5h), 120 (2h), 150 (2.5h), 180 (3h).';
