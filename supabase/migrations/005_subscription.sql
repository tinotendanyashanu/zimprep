-- ============================================================
-- Migration 005: Subscription & Paywall
-- Run in Supabase SQL Editor (Dashboard → SQL → New Query)
-- ============================================================

-- 1. Update subscription_tier check constraint on student table
--    Original constraint only had ('starter', 'standard', 'prestige')
ALTER TABLE student
  DROP CONSTRAINT IF EXISTS student_subscription_tier_check;

ALTER TABLE student
  ADD CONSTRAINT student_subscription_tier_check
  CHECK (subscription_tier IN ('starter', 'standard', 'bundle', 'all_subjects'));

-- Ensure the column has a default
ALTER TABLE student
  ALTER COLUMN subscription_tier SET DEFAULT 'starter';


-- 2. Create subscription table
CREATE TABLE IF NOT EXISTS subscription (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id                UUID NOT NULL REFERENCES student(id) ON DELETE CASCADE,
  tier                      TEXT NOT NULL CHECK (tier IN ('standard', 'bundle', 'all_subjects')),
  status                    TEXT NOT NULL DEFAULT 'active'
                              CHECK (status IN ('active', 'cancelled', 'past_due', 'expired')),
  subject_ids               UUID[] NOT NULL DEFAULT '{}',
  paystack_customer_code    TEXT,
  paystack_subscription_code TEXT,
  paystack_plan_code        TEXT,
  paystack_email_token      TEXT,
  amount_usd                NUMERIC(10, 2) NOT NULL,
  period_start              TIMESTAMPTZ NOT NULL,
  period_end                TIMESTAMPTZ NOT NULL,
  created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- Only one active/cancelled/past_due subscription per student at a time
  UNIQUE (student_id)
);

-- Index for webhook lookups by subscription code
CREATE INDEX IF NOT EXISTS idx_subscription_paystack_code
  ON subscription (paystack_subscription_code)
  WHERE paystack_subscription_code IS NOT NULL;

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_subscription_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS subscription_updated_at ON subscription;
CREATE TRIGGER subscription_updated_at
  BEFORE UPDATE ON subscription
  FOR EACH ROW EXECUTE FUNCTION update_subscription_updated_at();


-- 3. RLS policies for subscription table
ALTER TABLE subscription ENABLE ROW LEVEL SECURITY;

-- Students can read their own subscription
DROP POLICY IF EXISTS "Students can read own subscription" ON subscription;
CREATE POLICY "Students can read own subscription"
  ON subscription FOR SELECT
  USING (auth.uid() = student_id);

-- Only service role can insert/update/delete (backend uses service key)
-- No INSERT/UPDATE/DELETE policies needed for anon/authenticated — service role bypasses RLS


-- 4. DB function: count a student's marked written attempts today (UTC)
--    Used for starter-tier quota enforcement
CREATE OR REPLACE FUNCTION count_student_attempts_today(p_student_id UUID)
RETURNS INTEGER LANGUAGE sql STABLE AS $$
  SELECT COUNT(*)::INTEGER
  FROM attempt a
  JOIN session s ON s.id = a.session_id
  JOIN question q ON q.id = a.question_id
  WHERE s.student_id = p_student_id
    AND q.question_type = 'written'
    AND a.marked_at IS NOT NULL
    AND a.marked_at >= DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC')
    AND a.marked_at <  DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC') + INTERVAL '1 day';
$$;


-- 5. DB function: count ALL attempts submitted today (including MCQ)
--    Used as a looser quota check at submission time (before marking)
CREATE OR REPLACE FUNCTION count_student_submissions_today(p_student_id UUID)
RETURNS INTEGER LANGUAGE sql STABLE AS $$
  SELECT COUNT(*)::INTEGER
  FROM attempt a
  JOIN session s ON s.id = a.session_id
  WHERE s.student_id = p_student_id
    AND a.created_at >= DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC')
    AND a.created_at <  DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC') + INTERVAL '1 day';
$$;


-- 6. Paystack plan codes table (populated by POST /admin/paystack/create-plans)
CREATE TABLE IF NOT EXISTS paystack_plan (
  tier      TEXT PRIMARY KEY CHECK (tier IN ('standard', 'bundle', 'all_subjects')),
  plan_code TEXT NOT NULL,
  name      TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. Add created_at to attempt if not present (needed by count function)
ALTER TABLE attempt ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();


-- 7. Cron functions for expiring subscriptions
--    Enable pg_cron extension first:
--      Dashboard → Extensions → pg_cron → Enable
--    Then schedule these jobs.

-- Function: expire cancelled subscriptions whose period_end has passed
CREATE OR REPLACE FUNCTION expire_cancelled_subscriptions()
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  UPDATE subscription
  SET status = 'expired'
  WHERE status = 'cancelled'
    AND period_end < NOW();

  -- Downgrade student tier for expired subscriptions
  UPDATE student s
  SET subscription_tier = 'starter'
  FROM subscription sub
  WHERE sub.student_id = s.id
    AND sub.status = 'expired'
    AND s.subscription_tier != 'starter';
END;
$$;

-- Function: expire past_due subscriptions after 7-day grace period
CREATE OR REPLACE FUNCTION expire_pastdue_subscriptions()
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  UPDATE subscription
  SET status = 'expired'
  WHERE status = 'past_due'
    AND period_end < NOW() - INTERVAL '7 days';

  UPDATE student s
  SET subscription_tier = 'starter'
  FROM subscription sub
  WHERE sub.student_id = s.id
    AND sub.status = 'expired'
    AND s.subscription_tier != 'starter';
END;
$$;

-- ── Schedule cron jobs (run once after enabling pg_cron) ─────────────────────
-- Uncomment and run after enabling pg_cron extension:
--
-- SELECT cron.schedule(
--   'expire-cancelled-subs',
--   '0 * * * *',  -- every hour
--   'SELECT expire_cancelled_subscriptions()'
-- );
--
-- SELECT cron.schedule(
--   'expire-pastdue-subs',
--   '0 2 * * *',  -- daily at 02:00 UTC
--   'SELECT expire_pastdue_subscriptions()'
-- );
