-- ZimPrep Migration 003: Parent-Student Link
-- Adds parent_id FK to student table for parent dashboard access

alter table student
  add column if not exists parent_id uuid references parent(id) on delete set null;

drop policy if exists "Parents can read linked children" on student;
drop policy if exists "Parents can read linked children sessions" on session;
drop policy if exists "Parents can read linked children attempts" on attempt;
drop policy if exists "Parents can read linked children weak topics" on weak_topic;
drop policy if exists "Parents can read linked children syllabus coverage" on syllabus_coverage;

-- Allow parents to read their linked children's profiles
create policy "Parents can read linked children"
  on student for select
  using (auth.uid() = parent_id);

-- Allow parents to read sessions belonging to their linked children
create policy "Parents can read linked children sessions"
  on session for select
  using (
    exists (
      select 1 from student s
      where s.id = session.student_id and s.parent_id = auth.uid()
    )
  );

-- Allow parents to read attempts belonging to their linked children
create policy "Parents can read linked children attempts"
  on attempt for select
  using (
    exists (
      select 1 from session se
      join student s on s.id = se.student_id
      where se.id = attempt.session_id and s.parent_id = auth.uid()
    )
  );

-- Allow parents to read weak_topic for their linked children
create policy "Parents can read linked children weak topics"
  on weak_topic for select
  using (
    exists (
      select 1 from student s
      where s.id = weak_topic.student_id and s.parent_id = auth.uid()
    )
  );

-- Allow parents to read syllabus_coverage for their linked children
create policy "Parents can read linked children syllabus coverage"
  on syllabus_coverage for select
  using (
    exists (
      select 1 from student s
      where s.id = syllabus_coverage.student_id and s.parent_id = auth.uid()
    )
  );
