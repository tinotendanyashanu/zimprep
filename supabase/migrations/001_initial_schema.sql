-- ZimPrep Initial Schema
-- Migration 001: Core tables with RLS policies

-- ============================================================
-- EXTENSIONS
-- ============================================================
create extension if not exists "uuid-ossp";

-- ============================================================
-- TABLES
-- ============================================================

-- Subject
create table if not exists subject (
  id         uuid primary key default uuid_generate_v4(),
  name       text not null,
  level      text not null check (level in ('Grade7', 'O', 'A')),
  created_at timestamptz not null default now()
);

-- Paper
create table if not exists paper (
  id           uuid primary key default uuid_generate_v4(),
  subject_id   uuid not null references subject(id) on delete cascade,
  year         int  not null,
  paper_number int  not null,
  pdf_url      text not null,
  status       text not null default 'processing' check (status in ('processing', 'ready', 'error')),
  created_at   timestamptz not null default now()
);

-- Question
create table if not exists question (
  id              uuid primary key default uuid_generate_v4(),
  paper_id        uuid not null references paper(id) on delete cascade,
  subject_id      uuid not null references subject(id) on delete cascade,
  question_number text not null,
  sub_question    text,
  section         text,
  marks           int  not null default 0,
  text            text not null,
  has_image       boolean not null default false,
  image_url       text,
  topic_tags      text[] not null default '{}',
  question_type   text not null check (question_type in ('written', 'mcq')),
  created_at      timestamptz not null default now()
);

-- MCQAnswer
create table if not exists mcq_answer (
  id             uuid primary key default uuid_generate_v4(),
  question_id    uuid not null references question(id) on delete cascade,
  correct_option text not null check (correct_option in ('A', 'B', 'C', 'D'))
);

-- SyllabusChunk
create table if not exists syllabus_chunk (
  id         uuid primary key default uuid_generate_v4(),
  subject_id uuid not null references subject(id) on delete cascade,
  topic_name text not null,
  content    text not null,
  level      text not null,
  created_at timestamptz not null default now()
);

-- Student (linked to auth.users)
create table if not exists student (
  id                uuid primary key references auth.users(id) on delete cascade,
  email             text not null,
  name              text not null,
  level             text not null,
  subscription_tier text not null default 'starter' check (subscription_tier in ('starter', 'standard', 'prestige')),
  created_at        timestamptz not null default now()
);

-- Parent (linked to auth.users)
create table if not exists parent (
  id         uuid primary key references auth.users(id) on delete cascade,
  email      text not null,
  name       text not null,
  created_at timestamptz not null default now()
);

-- Session
create table if not exists session (
  id           uuid primary key default uuid_generate_v4(),
  student_id   uuid not null references student(id) on delete cascade,
  paper_id     uuid not null references paper(id) on delete cascade,
  mode         text not null check (mode in ('exam', 'practice')),
  started_at   timestamptz not null default now(),
  completed_at timestamptz,
  status       text not null default 'active'
);

-- Attempt
create table if not exists attempt (
  id                uuid primary key default uuid_generate_v4(),
  session_id        uuid not null references session(id) on delete cascade,
  question_id       uuid not null references question(id) on delete cascade,
  student_answer    text,
  answer_image_url  text,
  extracted_text    text,
  ai_score          int,
  ai_feedback       jsonb,
  ai_references     jsonb,
  marked_at         timestamptz,
  flagged           boolean not null default false,
  flag_resolved     boolean not null default false
);

-- WeakTopic
create table if not exists weak_topic (
  id            uuid primary key default uuid_generate_v4(),
  student_id    uuid not null references student(id) on delete cascade,
  subject_id    uuid not null references subject(id) on delete cascade,
  topic_name    text not null,
  attempt_count int not null default 0,
  fail_count    int not null default 0,
  last_attempted timestamptz not null default now()
);

-- SyllabusCoverage
create table if not exists syllabus_coverage (
  id             uuid primary key default uuid_generate_v4(),
  student_id     uuid not null references student(id) on delete cascade,
  subject_id     uuid not null references subject(id) on delete cascade,
  topic_name     text not null,
  attempted      boolean not null default false,
  last_attempted timestamptz
);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

alter table subject          enable row level security;
alter table paper            enable row level security;
alter table question         enable row level security;
alter table mcq_answer       enable row level security;
alter table syllabus_chunk   enable row level security;
alter table student          enable row level security;
alter table parent           enable row level security;
alter table session          enable row level security;
alter table attempt          enable row level security;
alter table weak_topic       enable row level security;
alter table syllabus_coverage enable row level security;

-- Drop policies if they already exist so this migration can be re-run safely.
drop policy if exists "Authenticated users can read subjects" on subject;
drop policy if exists "Authenticated users can read papers" on paper;
drop policy if exists "Authenticated users can read questions" on question;
drop policy if exists "Authenticated users can read mcq answers" on mcq_answer;
drop policy if exists "Authenticated users can read syllabus chunks" on syllabus_chunk;
drop policy if exists "Students can read own profile" on student;
drop policy if exists "Students can update own profile" on student;
drop policy if exists "Students can insert own profile" on student;
drop policy if exists "Parents can read own profile" on parent;
drop policy if exists "Parents can update own profile" on parent;
drop policy if exists "Parents can insert own profile" on parent;
drop policy if exists "Students can read own sessions" on session;
drop policy if exists "Students can insert own sessions" on session;
drop policy if exists "Students can update own sessions" on session;
drop policy if exists "Students can read own attempts" on attempt;
drop policy if exists "Students can insert own attempts" on attempt;
drop policy if exists "Students can update own attempts" on attempt;
drop policy if exists "Students can read own weak topics" on weak_topic;
drop policy if exists "Students can insert own weak topics" on weak_topic;
drop policy if exists "Students can update own weak topics" on weak_topic;
drop policy if exists "Students can read own syllabus coverage" on syllabus_coverage;
drop policy if exists "Students can insert own syllabus coverage" on syllabus_coverage;
drop policy if exists "Students can update own syllabus coverage" on syllabus_coverage;

-- Public content: readable by all authenticated users
create policy "Authenticated users can read subjects"
  on subject for select
  using (auth.role() = 'authenticated');

create policy "Authenticated users can read papers"
  on paper for select
  using (auth.role() = 'authenticated');

create policy "Authenticated users can read questions"
  on question for select
  using (auth.role() = 'authenticated');

create policy "Authenticated users can read mcq answers"
  on mcq_answer for select
  using (auth.role() = 'authenticated');

create policy "Authenticated users can read syllabus chunks"
  on syllabus_chunk for select
  using (auth.role() = 'authenticated');

-- Student: own row only
create policy "Students can read own profile"
  on student for select
  using (auth.uid() = id);

create policy "Students can update own profile"
  on student for update
  using (auth.uid() = id);

create policy "Students can insert own profile"
  on student for insert
  with check (auth.uid() = id);

-- Parent: own row only
create policy "Parents can read own profile"
  on parent for select
  using (auth.uid() = id);

create policy "Parents can update own profile"
  on parent for update
  using (auth.uid() = id);

create policy "Parents can insert own profile"
  on parent for insert
  with check (auth.uid() = id);

-- Session: student's own sessions
create policy "Students can read own sessions"
  on session for select
  using (auth.uid() = student_id);

create policy "Students can insert own sessions"
  on session for insert
  with check (auth.uid() = student_id);

create policy "Students can update own sessions"
  on session for update
  using (auth.uid() = student_id);

-- Attempt: via session ownership
create policy "Students can read own attempts"
  on attempt for select
  using (
    exists (
      select 1 from session s
      where s.id = attempt.session_id and s.student_id = auth.uid()
    )
  );

create policy "Students can insert own attempts"
  on attempt for insert
  with check (
    exists (
      select 1 from session s
      where s.id = attempt.session_id and s.student_id = auth.uid()
    )
  );

create policy "Students can update own attempts"
  on attempt for update
  using (
    exists (
      select 1 from session s
      where s.id = attempt.session_id and s.student_id = auth.uid()
    )
  );

-- WeakTopic: student's own records
create policy "Students can read own weak topics"
  on weak_topic for select
  using (auth.uid() = student_id);

create policy "Students can insert own weak topics"
  on weak_topic for insert
  with check (auth.uid() = student_id);

create policy "Students can update own weak topics"
  on weak_topic for update
  using (auth.uid() = student_id);

-- SyllabusCoverage: student's own records
create policy "Students can read own syllabus coverage"
  on syllabus_coverage for select
  using (auth.uid() = student_id);

create policy "Students can insert own syllabus coverage"
  on syllabus_coverage for insert
  with check (auth.uid() = student_id);

create policy "Students can update own syllabus coverage"
  on syllabus_coverage for update
  using (auth.uid() = student_id);
