-- ============================================================
-- Migration 012: Waitlist entries
-- Run in Supabase SQL Editor (Dashboard -> SQL -> New Query)
-- ============================================================

CREATE TABLE IF NOT EXISTS waitlist_entry (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email        TEXT NOT NULL UNIQUE,
  phone_number TEXT NOT NULL,
  source_page  TEXT NOT NULL DEFAULT '/',
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_waitlist_entry_source_page
  ON waitlist_entry (source_page);

CREATE OR REPLACE FUNCTION update_waitlist_entry_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS waitlist_entry_updated_at ON waitlist_entry;
CREATE TRIGGER waitlist_entry_updated_at
  BEFORE UPDATE ON waitlist_entry
  FOR EACH ROW EXECUTE FUNCTION update_waitlist_entry_updated_at();

ALTER TABLE waitlist_entry ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role manages waitlist entries"
  ON waitlist_entry
  FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');
