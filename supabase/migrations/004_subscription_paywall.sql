-- Migration 004: Subscription & Paywall
-- Aligns schema with backend subscription routes and Paystack integration.

-- 1. Update subscription_tier on student
-- Keep data valid before tightening the check constraint.
update student
set subscription_tier = 'all_subjects'
where subscription_tier = 'prestige';

alter table student
  drop constraint if exists student_subscription_tier_check;

alter table student
  add constraint student_subscription_tier_check
  check (subscription_tier in ('starter', 'standard', 'bundle', 'all_subjects'));

alter table student
  alter column subscription_tier set default 'starter';


-- 2. Subscription table
create table if not exists subscription (
  id                         uuid primary key default gen_random_uuid(),
  student_id                 uuid not null references student(id) on delete cascade,
  tier                       text not null check (tier in ('standard', 'bundle', 'all_subjects')),
  status                     text not null default 'active'
                               check (status in ('active', 'cancelled', 'past_due', 'expired')),
  subject_ids                uuid[] not null default '{}',
  paystack_customer_code     text,
  paystack_subscription_code text,
  paystack_plan_code         text,
  paystack_email_token       text,
  amount_usd                 numeric(10, 2) not null,
  period_start               timestamptz not null,
  period_end                 timestamptz not null,
  created_at                 timestamptz not null default now(),
  updated_at                 timestamptz not null default now(),
  unique (student_id)
);

create index if not exists idx_subscription_paystack_code
  on subscription (paystack_subscription_code)
  where paystack_subscription_code is not null;

create or replace function update_subscription_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists subscription_updated_at on subscription;
create trigger subscription_updated_at
  before update on subscription
  for each row execute function update_subscription_updated_at();


-- 3. RLS policy
alter table subscription enable row level security;

drop policy if exists "Students can read own subscription" on subscription;
create policy "Students can read own subscription"
  on subscription for select
  using (auth.uid() = student_id);


-- Ensure attempt.created_at exists before quota helper functions reference it.
alter table attempt
  add column if not exists created_at timestamptz default now();


-- 4. Quota helper functions
create or replace function count_student_attempts_today(p_student_id uuid)
returns integer language sql stable as $$
  select count(*)::integer
  from attempt a
  join session s on s.id = a.session_id
  join question q on q.id = a.question_id
  where s.student_id = p_student_id
    and q.question_type = 'written'
    and a.marked_at is not null
    and a.marked_at >= date_trunc('day', now() at time zone 'UTC')
    and a.marked_at <  date_trunc('day', now() at time zone 'UTC') + interval '1 day';
$$;

create or replace function count_student_submissions_today(p_student_id uuid)
returns integer language sql stable as $$
  select count(*)::integer
  from attempt a
  join session s on s.id = a.session_id
  where s.student_id = p_student_id
    and a.created_at >= date_trunc('day', now() at time zone 'UTC')
    and a.created_at <  date_trunc('day', now() at time zone 'UTC') + interval '1 day';
$$;


-- 5. Paystack plan codes
create table if not exists paystack_plan (
  tier       text primary key check (tier in ('standard', 'bundle', 'all_subjects')),
  plan_code  text not null,
  name       text not null,
  created_at timestamptz not null default now()
);


-- 6. Expiry jobs functions (to be scheduled with pg_cron)
create or replace function expire_cancelled_subscriptions()
returns void language plpgsql as $$
begin
  update subscription
  set status = 'expired'
  where status = 'cancelled'
    and period_end < now();

  update student s
  set subscription_tier = 'starter'
  from subscription sub
  where sub.student_id = s.id
    and sub.status = 'expired'
    and s.subscription_tier != 'starter';
end;
$$;

create or replace function expire_pastdue_subscriptions()
returns void language plpgsql as $$
begin
  update subscription
  set status = 'expired'
  where status = 'past_due'
    and period_end < now() - interval '7 days';

  update student s
  set subscription_tier = 'starter'
  from subscription sub
  where sub.student_id = s.id
    and sub.status = 'expired'
    and s.subscription_tier != 'starter';
end;
$$;

-- Optional schedule examples after enabling pg_cron:
-- select cron.schedule('expire-cancelled-subs', '0 * * * *', 'select expire_cancelled_subscriptions()');
-- select cron.schedule('expire-pastdue-subs', '0 2 * * *', 'select expire_pastdue_subscriptions()');
