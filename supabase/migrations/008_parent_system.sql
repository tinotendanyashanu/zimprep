-- 008_parent_system.sql
-- Tables for parent goals, alerts, and weekly reports.

-- ── Parent Goals ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS parent_goals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id uuid NOT NULL REFERENCES parent(id) ON DELETE CASCADE,
    student_id uuid NOT NULL REFERENCES student(id) ON DELETE CASCADE,
    weekly_hours_target numeric(4,1) NOT NULL DEFAULT 5,
    target_grade_percent integer NOT NULL DEFAULT 70,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(parent_id, student_id)
);

-- ── Parent Alerts ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS parent_alert (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id uuid NOT NULL REFERENCES parent(id) ON DELETE CASCADE,
    student_id uuid NOT NULL REFERENCES student(id) ON DELETE CASCADE,
    alert_type text NOT NULL,   -- 'inactivity' | 'performance_drop' | 'goal_not_met' | 'improving'
    message text NOT NULL,
    is_read boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- ── Parent Weekly Reports ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS parent_report (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id uuid NOT NULL REFERENCES parent(id) ON DELETE CASCADE,
    report_data jsonb NOT NULL,
    generated_at timestamptz NOT NULL DEFAULT now()
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS parent_goals_parent_idx ON parent_goals(parent_id);
CREATE INDEX IF NOT EXISTS parent_alert_parent_idx ON parent_alert(parent_id, is_read);
CREATE INDEX IF NOT EXISTS parent_report_parent_idx ON parent_report(parent_id, generated_at DESC);

-- ── Row Level Security ────────────────────────────────────────────────────────
ALTER TABLE parent_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE parent_alert ENABLE ROW LEVEL SECURITY;
ALTER TABLE parent_report ENABLE ROW LEVEL SECURITY;

CREATE POLICY "parent_goals_owner" ON parent_goals
    FOR ALL USING (auth.uid() = parent_id);

CREATE POLICY "parent_alert_owner" ON parent_alert
    FOR ALL USING (auth.uid() = parent_id);

CREATE POLICY "parent_report_owner" ON parent_report
    FOR ALL USING (auth.uid() = parent_id);

-- ── updated_at trigger for goals ─────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_parent_goals_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER parent_goals_updated_at
    BEFORE UPDATE ON parent_goals
    FOR EACH ROW EXECUTE FUNCTION update_parent_goals_updated_at();
