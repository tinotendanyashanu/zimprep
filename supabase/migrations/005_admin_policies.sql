-- Migration 005: Admin policies, QA workflow, and storage buckets
-- Adds admin role, PDF ingestion workflow, QA status, and storage RLS.

-- ============================================================
-- ADMIN HELPER
-- Admin status is stored in auth.users app_metadata by the backend
-- (set server-side via service_role key — never by the client).
-- Usage in policies: is_admin()
-- ============================================================
create or replace function is_admin()
returns boolean language sql stable as $$
  select coalesce(
    (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin',
    false
  );
$$;


-- ============================================================
-- QA STATUS on question
-- Tracks admin approval state for extracted questions.
-- pending  → just extracted, awaiting admin review
-- approved → live and visible to students
-- rejected → excluded from student-facing queries
-- ============================================================
alter table question
  add column if not exists qa_status text not null default 'pending'
    check (qa_status in ('pending', 'approved', 'rejected'));

-- Students only see approved questions
drop policy if exists "Authenticated users can read questions" on question;
create policy "Authenticated users can read questions"
  on question for select
  using (
    auth.role() = 'authenticated'
    and (qa_status = 'approved' or is_admin())
  );

-- MCQ answers follow the same visibility: only for approved questions
drop policy if exists "Authenticated users can read mcq answers" on mcq_answer;
create policy "Authenticated users can read mcq answers"
  on mcq_answer for select
  using (
    auth.role() = 'authenticated'
    and (
      is_admin()
      or exists (
        select 1 from question q
        where q.id = mcq_answer.question_id
          and q.qa_status = 'approved'
      )
    )
  );


-- ============================================================
-- ADMIN WRITE POLICIES — subject, paper, question, mcq_answer,
--                        syllabus_chunk
-- ============================================================

-- subject
drop policy if exists "Admin can manage subjects" on subject;
create policy "Admin can manage subjects"
  on subject for all
  using (is_admin())
  with check (is_admin());

-- paper
drop policy if exists "Admin can manage papers" on paper;
create policy "Admin can manage papers"
  on paper for all
  using (is_admin())
  with check (is_admin());

-- question
drop policy if exists "Admin can manage questions" on question;
create policy "Admin can manage questions"
  on question for all
  using (is_admin())
  with check (is_admin());

-- mcq_answer
drop policy if exists "Admin can manage mcq answers" on mcq_answer;
create policy "Admin can manage mcq answers"
  on mcq_answer for all
  using (is_admin())
  with check (is_admin());

-- syllabus_chunk
drop policy if exists "Admin can manage syllabus chunks" on syllabus_chunk;
create policy "Admin can manage syllabus chunks"
  on syllabus_chunk for all
  using (is_admin())
  with check (is_admin());


-- ============================================================
-- STORAGE BUCKETS
-- Created via storage schema (available in Supabase hosted + local).
-- ============================================================

-- past-papers: admin upload only, no public read
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'past-papers',
  'past-papers',
  false,
  52428800,  -- 50 MB
  array['application/pdf']
)
on conflict (id) do nothing;

-- question-images: public read (served to students), admin write
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'question-images',
  'question-images',
  true,
  5242880,   -- 5 MB
  array['image/png', 'image/jpeg', 'image/webp']
)
on conflict (id) do nothing;

-- syllabus: admin upload only, no public read
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'syllabus',
  'syllabus',
  false,
  52428800,  -- 50 MB
  array['application/pdf']
)
on conflict (id) do nothing;

-- Storage RLS: past-papers — admin only
drop policy if exists "Admin upload past papers" on storage.objects;
create policy "Admin upload past papers"
  on storage.objects for insert
  with check (bucket_id = 'past-papers' and is_admin());

drop policy if exists "Admin read past papers" on storage.objects;
create policy "Admin read past papers"
  on storage.objects for select
  using (bucket_id = 'past-papers' and is_admin());

drop policy if exists "Admin delete past papers" on storage.objects;
create policy "Admin delete past papers"
  on storage.objects for delete
  using (bucket_id = 'past-papers' and is_admin());

-- Storage RLS: question-images — public read, admin write
drop policy if exists "Public read question images" on storage.objects;
create policy "Public read question images"
  on storage.objects for select
  using (bucket_id = 'question-images' and auth.role() = 'authenticated');

drop policy if exists "Admin upload question images" on storage.objects;
create policy "Admin upload question images"
  on storage.objects for insert
  with check (bucket_id = 'question-images' and is_admin());

drop policy if exists "Admin delete question images" on storage.objects;
create policy "Admin delete question images"
  on storage.objects for delete
  using (bucket_id = 'question-images' and is_admin());

-- Storage RLS: syllabus — admin only
drop policy if exists "Admin upload syllabus" on storage.objects;
create policy "Admin upload syllabus"
  on storage.objects for insert
  with check (bucket_id = 'syllabus' and is_admin());

drop policy if exists "Admin read syllabus" on storage.objects;
create policy "Admin read syllabus"
  on storage.objects for select
  using (bucket_id = 'syllabus' and is_admin());

drop policy if exists "Admin delete syllabus" on storage.objects;
create policy "Admin delete syllabus"
  on storage.objects for delete
  using (bucket_id = 'syllabus' and is_admin());
