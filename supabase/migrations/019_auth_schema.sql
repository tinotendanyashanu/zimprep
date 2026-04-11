-- ============================================================
-- 019_auth_schema.sql
-- Clean role-based access control foundation.
-- Adds: users, roles, user_roles tables.
-- The student/parent/employee tables remain as profile stores.
-- ============================================================

-- ── Core auth identity table ─────────────────────────────────────────────────
-- One row per Supabase auth user. Created automatically via trigger below.
CREATE TABLE IF NOT EXISTS public.users (
  id         uuid        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email      text        NOT NULL,
  status     text        NOT NULL DEFAULT 'active'
               CHECK (status IN ('active', 'suspended', 'deleted')),
  created_at timestamptz NOT NULL DEFAULT now()
);

-- ── Roles lookup table ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.roles (
  id   smallserial PRIMARY KEY,
  name text        UNIQUE NOT NULL
);

-- Seed the four roles (idempotent)
INSERT INTO public.roles (name)
VALUES ('admin'), ('employee'), ('parent'), ('student')
ON CONFLICT (name) DO NOTHING;

-- ── User ↔ Role junction ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.user_roles (
  user_id     uuid        NOT NULL REFERENCES public.users(id)  ON DELETE CASCADE,
  role_id     smallint    NOT NULL REFERENCES public.roles(id)  ON DELETE CASCADE,
  assigned_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, role_id)
);

CREATE INDEX IF NOT EXISTS user_roles_user_id_idx ON public.user_roles (user_id);

-- ── Auto-create users row whenever Supabase creates an auth user ─────────────
-- This covers: email signup, invite, OAuth, magic link.
CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.users (id, email)
  VALUES (NEW.id, NEW.email)
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_auth_user();

-- ── RLS ───────────────────────────────────────────────────────────────────────
ALTER TABLE public.users      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.roles      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

-- users: each user sees only their own row
DROP POLICY IF EXISTS "users_select_own"  ON public.users;
DROP POLICY IF EXISTS "users_update_own"  ON public.users;
CREATE POLICY "users_select_own" ON public.users
  FOR SELECT USING (auth.uid() = id);
CREATE POLICY "users_update_own" ON public.users
  FOR UPDATE USING (auth.uid() = id);

-- roles: public read-only reference table
DROP POLICY IF EXISTS "roles_select_all" ON public.roles;
CREATE POLICY "roles_select_all" ON public.roles
  FOR SELECT USING (true);

-- user_roles: each user reads their own assignments;
-- inserts go through service-role key (backend/API routes bypass RLS)
DROP POLICY IF EXISTS "user_roles_select_own" ON public.user_roles;
CREATE POLICY "user_roles_select_own" ON public.user_roles
  FOR SELECT USING (auth.uid() = user_id);
