-- Migration 018: Add permissions column to student table
-- Stores a set of permission flags for each student.
-- Default is '{"student"}'. Admins can grant extra flags (e.g. 'beta').
-- Employee/admin access is still governed by the employee table.

alter table student
  add column if not exists permissions text[] not null default '{"student"}';

comment on column student.permissions is
  'Set of permission flags for this student (e.g. student, beta). Admin access is managed via the employee table.';
