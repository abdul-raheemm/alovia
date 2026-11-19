# Genetic Risk — rule review sign-off (Genetic spec §13)

**Status:** not signed off. The module is not released until every row is checked "yes" (§13.3, §16).

## How to review
1. Open `genetic_rule_review.csv` in this folder (Excel opens it). It is generated from the live rule
   files by `backend/scripts/export_genetic_rule_review.py`, so it always shows exactly what the app runs.
2. For every row, fill **checked** (yes / no), **comment**, **reviewer** and **date**. The
   **rules_version** column is already filled in.
3. Rows cover: every haemoglobin rule row with its exact parent pairs (§7.1, all 45 pairs), every
   haemophilia row with its "if the baby is a boy / a girl" outcomes (§7.2), every Marfan row (§7.3),
   the evidence rules (§6.2), conflicts and errors (§6.3), every patient message (§11.4) and the
   assumptions A1–A4 (§13.1).
4. Return the filled CSV to the owner. Agreed changes are applied to the rule files, `rules_version`
   is raised, and the changed rows are reviewed again (§13.4).

## Points to look at first
- **A1** (sickle cell card with a normal result treated as unknown), **A2** (HbE/HbD carrier with a
  tested-negative partner), **A3** (haemophilia A and B the same), **A4** (affected parent with a
  tested-negative partner: all children carriers).
- **Messages:** every message except the fixed disclaimer shows "[Text pending doctor approval]" until
  written or approved here.

## Sign-off

| Reviewer (name) | Role | Rules version | Date | All rows checked (yes/no) | Signature / note |
|---|---|---|---|---|---|
| | | 1.0.0 | | | |
