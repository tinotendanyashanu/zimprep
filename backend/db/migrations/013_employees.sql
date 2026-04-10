-- ============================================================
-- Migration 013: Employees
-- Run in Supabase SQL Editor (Dashboard -> SQL -> New Query)
-- ============================================================

CREATE TABLE IF NOT EXISTS employee (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  email        TEXT NOT NULL UNIQUE,
  name         TEXT NOT NULL,
  role         TEXT NOT NULL DEFAULT 'employee'
                 CHECK (role IN ('admin', 'employee')),
  is_active    BOOLEAN NOT NULL DEFAULT true,
  invited_by   UUID REFERENCES employee(id) ON DELETE SET NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_employee_user_id  ON employee (user_id);
CREATE INDEX IF NOT EXISTS idx_employee_email     ON employee (email);
CREATE INDEX IF NOT EXISTS idx_employee_role      ON employee (role);

ALTER TABLE employee ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role manages employees"
  ON employee
  FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');
