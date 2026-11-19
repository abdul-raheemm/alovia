# Symptom Tracking — rule review sign-off (Symptom spec §16)

**Status:** not signed off. The module must not be released before this sign-off (spec §15 "Do not").

## How to review
1. Open `symptom_rule_review.csv` in this folder (Excel opens it). It is generated from the live rule
   files by `backend/scripts/export_symptom_rule_review.py`, so it always shows exactly what the app runs.
2. For every row, fill **checked** (yes / no), **comment**, **reviewer** and **date**. The
   **rules_version** column is already filled in.
3. Rows cover: every red-flag rule (§7), the PUQE-24 wording and bands (§8, A2), the pattern rules and
   their numbers (§9, A3), the week settings, every patient message (§11.2), the phone numbers (§11.3)
   and the assumptions A1–A4 (§16.1).
4. Return the filled CSV to the owner. Agreed changes are applied to the rule files, `rules_version`
   is raised, and the changed rows are reviewed again (§16).

## Points to look at first
- **A2 (PUQE bands):** the official S5 sheet prints *4 - 6* for mild and gives no band for a total of 3;
  the spec (and the app) use *3-6*. Please confirm which one to use.
- **A1:** vision problems on their own are level 1.
- **A4:** labour pains at 37+ weeks under 12 hours are level 2.
- **Messages:** all seven show "[Text pending doctor approval]" until written or approved here.

## Sign-off

| Reviewer (name) | Role | Rules version | Date | All rows checked (yes/no) | Signature / note |
|---|---|---|---|---|---|
| | | 1.0.0 | | | |
