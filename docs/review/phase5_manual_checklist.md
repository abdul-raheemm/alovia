# Phase 5 manual checklist — Doctor Dashboard + Admin

For the owner, once, before Phase 5 is merged into `main` (DEC-104). Every item has automated
tests already (mocked Supabase services). This list proves the **real** Supabase setup works and
lets you see each screen. Use test data only: no real people.

Tick each box. If a step fails, copy the error message (or a screenshot) and send it.

## 0. Start everything (once)

1. Backend: `cd backend` → `.venv\Scripts\python -m uvicorn app.main:create_app --factory --reload`
2. Doctor app: `cd frontend` → `npm run dev:doctor` → http://localhost:5174
3. Patient app (for steps 6–7): `cd frontend` → `npm run dev:patient` → http://localhost:5173

## 1. A doctor login for you

- [ ] Supabase dashboard → Authentication → Users → **Add user** → Create new user → an email you
      control, a password, tick **Auto confirm user** → copy the **User UID**.
- [ ] From `backend/`:
      `.venv\Scripts\python scripts\make_doctor.py --user-id <UID> --email <email> --name "Test Doctor" --assign-seed-patients`
      It prints `doctor account created` (and `assigned N seed patients` if the seed was run).
- [ ] Sign in at http://localhost:5174 with that email and password → accept the consent once →
      **Home** shows "Needs attention" and the patient list.

## 2. Patients and invites

- [ ] **New patient** → name "Test Patient Manual", age 29 → Save → the patient page opens; you are
      listed as the primary doctor.
- [ ] Overview → **Invite patient** → a link appears → **Copy** works.
- [ ] **Edit details** → change the age → Save → the new age shows.

## 3. Predictions (Fetal and Maternal tabs)

- [ ] Maternal → enter values (HbA1c in %, glucose in mg/dL, temperature in °C); the preview line
      (for example "7 % = 53.01 mmol/mol") shows under each switched field.
- [ ] Enter an age outside 15–48 → the range warning shows (pending text) → **Run prediction** still
      gives a result with class, probabilities, top factors and limitations.
- [ ] **Share with patient** → the preview shows the (pending) patient text → add a message →
      **Confirm and share** → "Shared with the patient on …".
- [ ] Enter a second result → **Trends** shows charts with a point per reading.

## 4. Medical records (real private bucket)

- [ ] Records → **File**: `alovia-test-record.pdf` (the synthetic PDF from the chat, or any
      no-data PDF) → type → **Upload** → it is listed.
- [ ] **Download** → the file opens in a new tab.
- [ ] Supabase dashboard → Storage → `medical-records` → the file is under `patients/<patient id>/`.
- [ ] Try a `.txt` file renamed to `.pdf` → refused with "Only PDF, JPG, PNG".

## 5. Notes, appointments, pregnancy, genetic, symptoms

- [ ] Notes → a private note, then **Share with patient**.
- [ ] Appointments → add one; edit it; patient-added ones have no Edit button.
- [ ] Pregnancy → set a clinician-confirmed due date → Overview shows "(Clinician confirmed)".
- [ ] Genetic / Symptoms tabs show "nothing yet" for the new patient (data comes from the patient app).

## 6. The patient side of sharing (patient app)

- [ ] Open the invite link from step 2 in a private window → sign up → accept the consent.
- [ ] More → **My results** shows the shared result as text plus your message — no numbers.
- [ ] Doctor notes shows the shared note; notifications show "A new result is available" and
      "Your doctor updated your pregnancy dates".
- [ ] Log a symptom (any warning sign) → back in the doctor app the inbox shows it; **Mark as seen**.
- [ ] Do a genetic check → doctor app → **Genetic review** → open it → **Confirm with note** →
      the patient app shows the note and "Reviewed by your doctor".

## 7. Admin and doctor invites

- [ ] Supabase dashboard → Authentication → URL Configuration → **Redirect URLs** → add
      `http://localhost:5174/set-password` (DEC-101).
- [ ] Make yourself an admin with a second Supabase user (ENVIRONMENT.md §3a, `make_admin.py`),
      sign in → **Admin**.
- [ ] Doctors → **Send invite** to a second email you control → the email arrives → its link opens
      **Set your password** → save → Home.
- [ ] Assignments → search "Test Patient Manual" → add the new doctor → **Make primary** → try to
      remove the last doctor → refused.
- [ ] Activity log → filter by action "patient created" → your entry shows, with no clinical values.

## 8. Rule review

- [ ] **Rule review** → tick one row with a comment → Save → "Checked by …" shows.
- [ ] **Export sign-off** downloads `rule_review_signoff_genetic.md`.

## 9. Look and accessibility (quick)

- [ ] Phone width (browser dev tools, 375 px) and laptop width: nothing overflows sideways except the
      wide tables, which scroll inside their own box.
- [ ] Theme switch: light and dark both readable.
- [ ] No screen shows a combined or overall risk score (§25 test 15).

When every box is ticked, reply **"checklist done"** (or send what failed).
