-- Reset ALL users and app data before running backend/scripts/seed_dev.py (owner 2026-11-22).
-- Run in the Supabase dashboard: SQL Editor -> New query -> paste -> Run.
-- IRREVERSIBLE: deletes every login (admin, doctors, patients) and every app record.
-- Kept: database structure (tables, migrations), rule files, models, the storage bucket itself.
-- Synthetic data only in this project; never run this on a database with real people.

begin;

-- every app table (users and everything linked to them); alembic_version is not touched
truncate table
  public.result_shares,
  public.fetal_results,
  public.maternal_results,
  public.symptom_logs,
  public.symptom_checkins,
  public.genetic_assessments,
  public.doctor_notes,
  public.inbox_items,
  public.medical_records,
  public.rule_signoffs,
  public.appointments,
  public.notifications,
  public.pregnancy_date_history,
  public.patient_invites,
  public.doctor_patient_assignments,
  public.consents,
  public.audit_log,
  public.patients,
  public.doctors,
  public.users
restart identity cascade;

-- every Supabase login (their sessions and identities go with them)
delete from auth.users;

commit;

-- Check (both should be 0):
--   select count(*) from public.users;
--   select count(*) from auth.users;
--
-- Uploaded record files: Supabase does not allow deleting storage files with SQL.
-- Dashboard -> Storage -> medical-records -> select all -> Delete (or leave them: no row
-- points at them any more).
