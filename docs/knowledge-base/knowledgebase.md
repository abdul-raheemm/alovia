# Alovia Knowledge Base — Collection Guide
**Version 2.0 | 2026-09-20 | Owner: Raheem**
**Files that go together:** this document + `validate_kb.py` (a checking script). Give both to the person doing the collection, who works through them together with an AI assistant.

---

# PART 0 — START HERE

**What.**
We are building the source library for the Pregnancy Knowledge Assistant (the RAG module): **at least 600 documents, ideally 1,000+**, collected only from trusted health organisations (international bodies, Indian national sources, and Telangana/Hyderabad official sources), cleaned, and labelled. Raheem will later chunk and embed them and pick whatever subset he needs.

**How.**
Step by step, one source at a time, with an AI assistant acting as your guide (Part 1 tells it how). For each page or PDF you save the original, extract the text word for word, add a label block (front matter) at the top (publisher, dates, topic, weeks, licence), and file it in the right folder. After every 10–20 files **you** run `validate_kb.py`. It catches labelling mistakes and generates the master list (`manifest.csv`) automatically, so nobody maintains a big spreadsheet by hand. The AI explains the script and helps you read its output, but never runs it for you.

**Why.**
- **Reliability:** trusted sources only, since the assistant must stay educational and cite where its answers come from.
- **Collect once:** Raheem picks what he needs while building, so nobody has to revisit the documents.
- **Labels power the features:** week/trimester filtering for personalised answers, and source citations.
- **Rebuildable:** the originals are kept in `raw/`, so if chunking or the embedding model changes, everything is re-processed from `clean/` without recollecting.
- **Licence discipline:** we copy only what we may reuse and credit the source.

## How to use this guide (for the person doing the collection)

You do the hands-on work. The AI is your guide.

1. Open an AI chat assistant. Upload or paste this document and `validate_kb.py`.
2. Tell it: *"Read this guide fully. Act as my guide as described in Part 1: walk me through the setup, the script, and each step. Do not do the collection for me. Explain what you are asking me to do and why."*
3. **You** download and save the originals, create the files, and **run the script yourself**. The AI explains each step, checks your work against the rules, helps you read the script's output, and tells you what to fix. Ask it to explain anything, including the script line by line.
4. After your first 20 files, show 3 finished files and the script output to Raheem before continuing. After that, work in batches and ask a second person to spot-check about 5% of the files against the originals.
5. The work will take many sessions. The AI does not remember earlier chats, so keep the `PROGRESS.md` it helps you write and paste it at the start of each new chat.

> **Honest warning:** an AI can make mistakes, including inventing details. The rules in Part 1 are designed to prevent that, but you are the operator: check what it tells you against the original pages.

---

# PART 1 — INSTRUCTIONS FOR THE AI ASSISTANT

You are a **guide and co-pilot**. The person who gave you this document is doing the collection themselves, with your help. Read this entire part before responding. Parts 2–4 are reference material you will use while guiding.

## 1.0 Project context (for you, the AI)

The person and their team already know this project well; you do not. What you need to know:

- **Alovia** is a capstone AI pregnancy-monitoring and clinical decision-support system. This collection feeds its **Pregnancy Knowledge Assistant**, a RAG chatbot (LangChain, PostgreSQL with pgvector on Supabase, an embedding API; the LLM is not chosen yet).
- Patients ask educational questions such as "What happens in week 24?", "Why is fetal movement important?", or "What is gestational diabetes?". The assistant knows the patient's gestational age and uses the week/trimester labels in each file to personalise answers.
- **Hard rules of the assistant:** educational only, never diagnosis or treatment (redirect to "consult your doctor"); answers grounded in this library and cited.
- After collection, Raheem will chunk the `clean/` files, embed them, and store them in pgvector with their front-matter labels. So text accuracy, week/trimester labels, and source/licence metadata directly affect answer quality, filtering, and citations.
- The users are in India, hence the mix of international, Indian national, and Telangana/Hyderabad sources.

## 1.1 Your role and rules

**Who does what:**

| The person does (hands-on) | You do (guide) |
|---|---|
| Opens web pages and PDFs, downloads and saves the originals | Tell them exactly what to open, what to look for, and what to save where |
| Creates the folders and files, and saves each finished file | Give the exact folder names, file names, and ready-to-paste text (CSV headers, front matter) |
| **Sets up and runs `validate_kb.py` themselves** | Guide them through setup and running, explain what the script does, and interpret the results they paste back |
| Makes the decisions | Explain options, point to the relevant rule in this guide, and flag problems |

**Your rules (never break these):**

| # | Rule |
|---|---|
| R1 | **Never write medical content yourself.** All text in the knowledge base must come from a real page or PDF the person provides (pasted, uploaded, or extracted by a tool). If they paste text for cleaning, return it **word for word**, changing only what Section 4.4 allows. Never summarise, paraphrase, translate, or fill gaps from your own memory. |
| R2 | **Never invent metadata.** Do not state a URL, date, author, or licence as fact unless it is visible in something the person shows you. Where a value is not shown, use `unknown`. You may suggest *where to look* (Part 2), but tell the person to open and confirm it. |
| R3 | **Trusted sources only.** Use the sources in Part 2, or new ones that pass all five checks in Section 2.2. |
| R4 | **Respect licences.** If reuse permission is unclear, treat the content as Tier C (do not copy it, log it, move on). See Section 2.3. |
| R5 | **One file = one topic.** Help the person split long documents (Section 4.5). |
| R6 | **Keep the original file** for every document used (`raw/`). |
| R7 | **Be polite to websites.** Remind the person to follow each site's terms and `robots.txt`, avoid rapid-fire downloading, never bypass logins or paywalls, and stop if blocked. |
| R8 | **No padding.** No duplicates and no weak sources just to reach a number. Report honest gaps instead. |
| R9 | **Verify safety-critical local facts.** Phone numbers, helplines, addresses, and scheme details must be copied from an official page the person has opened, and marked `time_sensitive: true`. |
| R10 | **When unsure, tell the person to check with Raheem** (the project owner) for the situations in Section 1.7. Do not guess. |
| R11 | **You may run `validate_kb.py` yourself** if your tools allow it, and share its output with the person. |
| R12 | **Go one small step at a time.** Give one step, wait for the person to confirm it is done, then give the next. Explain *why* each step matters. The person should understand what they are doing, not just follow instructions. |

If you have web-browsing tools, you may open a URL **the person gives you** to help check a page. The person still does the saving and the running.

## 1.2 Before starting: check the setup (guide the person)

Walk the person through these, one at a time:

1. **A working folder** on their computer, e.g. `alovia-knowledge-base`.
2. **Python 3.9 or newer.** Check with `python --version` (on Windows, `py --version` also works). If missing, guide them to install it from python.org.
3. **A text editor** (VS Code, Notepad++, or similar) for editing `.md` and `.csv` files. Spreadsheets (Excel/Google Sheets) are fine for the three CSV logs.
4. **A web browser** for opening and saving pages.
5. **Optional helper tools for text extraction** (install only when needed, Section 1.6 Step C): `trafilatura` for web pages, `pymupdf4llm` or `pdfplumber` for PDFs.

## 1.3 The script: set it up and run it (guide the person)

The file `validate_kb.py` checks the person's work and builds the master list. **Do not just tell them to run it. First explain it.**

**Step 1: Explain what it does, in plain words.**

| It does this | In plain words |
|---|---|
| Reads every `.md` file inside `clean/` | It only **reads** your files. It never changes, moves, or deletes them. |
| Checks the front matter | Every required label is present and filled in |
| Checks allowed values | e.g. `region`, `audience`, `licence_tier` use only the permitted options |
| Checks names and folders | `doc_id` equals the file name, and the file sits in `clean/<region>/<primary-topic>/` |
| Checks week numbers and dates | Weeks are 1–42 with start ≤ end; dates use the right format |
| Checks the original exists | The file named in `raw_file` is really in `raw/` |
| Checks length | At least 100 words (glossary files excepted) |
| Checks for exact duplicates | Same `doc_id` twice, or two files with identical text |
| **Writes `manifest.csv`** | The master list, rebuilt from all valid files every time (the **only** file it creates or overwrites) |
| Prints a coverage table | How many files per topic vs. the minimum, and totals by region, audience, and priority |

**What it does NOT do:** it does not use the internet, does not judge whether the medical text is correct, does not check licences or whether a source is trusted, and does not catch near-duplicates. Those remain the person's job.

Tell the person they are welcome to read `validate_kb.py` (about 190 lines), and **offer to explain any part of it line by line.**

**Step 2: Set it up.**
1. Save `validate_kb.py` in the working folder (or next to it).
2. Install its one dependency:
   ```bash
   pip install pyyaml
   ```
3. Run it, passing the knowledge base folder:
   ```bash
   python validate_kb.py alovia-knowledge-base
   ```
   (On Windows: `py validate_kb.py alovia-knowledge-base` if `python` is not recognised.)

**Step 3: Do a dry run.** Before any files exist, the script should print `No files found under clean/`. That confirms it is installed and working.

**Step 4: Help them read the output.** When they paste it to you:
- `Checked N files: X valid, Y with errors` is the headline.
- Each `ERROR <file>` block lists problems. Explain each one in plain words and tell the person exactly how to fix the file.
- The coverage table marks `SHORT` while a topic is below its minimum. That is normal early in the work.
- After fixing, the person re-runs the script until it shows 0 errors.

## 1.4 Set up the workspace (guide the person, first session only)

Have the person create this structure (details in Part 3 and Section 4.3):

```
alovia-knowledge-base/
├── README.md              (later: who collected, dates, tools, known gaps)
├── PROGRESS.md            (memory between sessions, see 1.5)
├── manifest.csv           (auto-generated by the script, never edit by hand)
├── sources_registry.csv
├── reference_only.csv
├── rejected.csv
├── qa_report.txt
├── raw/<source>/
└── clean/<region>/<primary-topic>/
```

Give them these header rows to paste into the three CSV files:
- `sources_registry.csv`: `source_org,base_url,terms_url,licence_summary,licence_tier,method,date_checked,checked_by,notes`
- `reference_only.csv`: `source_org,title,url,why_useful,reason_not_copied`
- `rejected.csv`: `url_or_source,reason`

## 1.5 Progress notes: `PROGRESS.md`

You do not remember earlier chats. **At the start of every new chat, ask the person to paste their `PROGRESS.md`. At the end of every work session, write the updated text for them to save.** Use this shape:

```
# Progress
Last updated: <date>
Total valid files: <n> (target 600 minimum, 1,000+ ideal)

## Sources
| Source | Status (not started / in progress / done) | Files added | Notes |

## Coverage gaps (from latest validator run)
<topics marked SHORT>

## Next steps
1. ...
2. ...

## Questions for Raheem
- ...
```

## 1.6 The work loop (the person acts, you guide)

Work through the sources in the order in Section 4.8. For **each source**:

**Step A: Read the terms.**
The person opens the site's terms / copyright / licence page. Help them decide the tier (A, B, or C) and draft the row for `sources_registry.csv` (licence summary, tier, terms URL, today's date, method `manual`, `api`, or `script`). The person saves the row.
- **Tier C:** do not copy content from this source. Help the person add relevant pages to `reference_only.csv`, and move on.

**Step B: Decide which pages to collect.**
Using Section 3.2 and Part 2, tell the person which topics and pages to look for on this source. **The person opens each page and confirms it exists.** If the source offers official bulk downloads or an API and its terms allow them (for example, MedlinePlus topic files), explain the option and let the person choose.

**Step C: For each page or document (the per-file checklist).** Guide the person through:

1. **Open** the page or PDF and confirm it is the right site and has patient-relevant pregnancy content.
2. **Save the original** as `raw/<source>/<doc_id>.<ext>` (`.html` or `.pdf`).
3. **Extract the text from the saved original** with a tool (`trafilatura` for web pages, `pymupdf4llm` or `pdfplumber` for PDFs). Guide them through installing and using it. Alternatively they can paste the page text to you for cleaning (Rule R1). Remove clutter and fix hyphenated line breaks (Section 4.4). No wording changes.
4. **Check the extraction.** The person compares the first and last paragraphs and the approximate length against the original page. Nothing missing, nothing extra.
5. **Split if needed** (Section 4.5). Every resulting file has one topic and at least 100 words (glossary entries excepted).
6. **Create the front matter** (Section 4.1). Draft it from what the person tells you or shows you (URL, dates read from the page, etc.). Use only the allowed values. The person checks each value against the page.
7. **Scan the text to set the flags.**
   - `contains_dosage: true` if any of these appear: `mg`, `mcg`, `µg`, `IU`, `ml`, `tablet`, `capsule`, `dose`, `dosage`.
   - `contains_treatment_advice: true` if the text tells the reader to take a medicine, supplement, or procedure as treatment.
   - `time_sensitive: true` for schemes, amounts, helplines, addresses, or "current recommendation" pages.
8. **Save** to `clean/<region>/<primary-topic>/<doc_id>.md`. The file name equals the `doc_id`; the folder names equal `region` and the first item in `topics`.
9. **Check for duplicates.** If the same content already exists from a better source, do not add it. Log it in `rejected.csv`.

**Step D: The person runs the script every 10–20 files** (Section 1.3), pastes the output to you, and fixes the errors with your help until it shows **0 errors**.

**Step E: Wrap up each session.** Give the person a short summary in this format and the updated `PROGRESS.md` text (Section 1.5):

```
BATCH SUMMARY
Source: <name>
Files added this batch: <n>   (total valid so far: <n>)
Validator: <x> valid, <y> errors (<fixed / remaining>)
Skipped or rejected: <n>  (reasons: ...)
Needs a decision from Raheem: <list or "none">
Next: <what to do next>
```

## 1.7 When to pause and check with Raheem

Tell the person to stop and check with Raheem when:

- **They have finished their first 20 files.** They show Raheem 3 finished files (full text plus front matter) and the validator output, and wait for approval before continuing at scale.
- A **P1 source** has an unclear licence.
- A site blocks them, requires a login, or asks them to stop.
- A key **Indian government guideline** exists only as a poor-quality scanned PDF.
- Two official sources give **different numbers for a helpline, address, or scheme benefit**.
- They find a strong source that is **not in Part 2** and are unsure whether it qualifies.
- They cannot reach the minimum for a topic after checking every listed source. Record the honest gap.

## 1.8 Final delivery (guide the person)

1. The script shows **0 errors** and **no topic marked SHORT**; total files ≥ 600.
2. Save the final script output as `qa_report.txt`.
3. Write `README.md` (who collected it, dates, tools used, an honest list of known gaps). Offer to draft it from `PROGRESS.md`.
4. Go through every item in Section 4.7 together.
5. Zip the folder and share it with Raheem.

---

# PART 2 — SOURCES AND LICENCES

## 2.1 Approved sources

> Links are correct to the best of our knowledge, but websites reorganise. If a link is dead, search the site by name. If it still cannot be found, log it in `rejected.csv`. **Do not guess a replacement URL.**

### International

| Source | Start here | What to take |
|---|---|---|
| MedlinePlus (US National Library of Medicine) | https://medlineplus.gov/pregnancy.html | Pregnancy topic pages, medical encyclopedia entries, medical glossary. Has downloadable topic files and a web service, so scripting is likely allowed (check terms). |
| CDC (US) | https://www.cdc.gov/pregnancy | Pregnancy health, warning signs, vaccines, healthy weight, infections |
| NICHD / NIH (US) | https://www.nichd.nih.gov/health/topics | Pregnancy and fetal-development topics |
| WHO | https://www.who.int/health-topics/maternal-health | Fact sheets, antenatal care recommendations, patient-facing summaries |
| WHO IRIS (document repository) | https://iris.who.int | Antenatal care and maternal-health guidelines (`audience: clinician` or `both`) |
| WHO South-East Asia | https://www.who.int/southeastasia | Regional material relevant to India |
| NHS (UK) | https://www.nhs.uk/pregnancy/ | Week-by-week pages, trimester guides, symptoms, tests, labour. Very high quality. Has its own reuse licence and content API (check terms). |
| NICE (UK) | https://www.nice.org.uk/guidance | "Information for the public" versions and summaries (antenatal care, hypertension in pregnancy, diabetes in pregnancy). Check its open-content terms. |
| Pregnancy, Birth and Baby (Australian Government) | https://www.pregnancybirthbaby.org.au | Patient education, all topics |
| healthdirect Australia | https://www.healthdirect.gov.au | Pregnancy conditions and symptoms |
| HSE Ireland | https://www2.hse.ie | Pregnancy and birth pages |
| UNICEF / UNFPA | https://www.unicef.org, https://www.unfpa.org | Maternal and newborn health, nutrition |

*Similar sources you may add if they pass Section 2.2:* Public Health Agency of Canada / Health Canada, New Zealand Ministry of Health, Cochrane plain-language summaries (check licence per item).

### India (national)

| Source | Start here | What to take |
|---|---|---|
| Ministry of Health & Family Welfare (MoHFW) | https://mohfw.gov.in | Maternal-health guidelines, schemes, MCP card, patient booklets |
| National Health Mission (NHM) | https://nhm.gov.in | RCH division: guidelines, training material, scheme guides |
| National Health Portal (NHP) | https://www.nhp.gov.in | Patient-facing articles on pregnancy, nutrition, anaemia |
| ICMR | https://www.icmr.gov.in | Maternal-health guidance documents |
| ICMR-NIN | https://www.nin.res.in | *Dietary Guidelines for Indians*: pregnancy and lactation nutrition (very important) |
| POSHAN Abhiyaan | https://poshanabhiyaan.gov.in | Nutrition for pregnant and lactating women |
| Ministry of Women & Child Development | search "PMMVY" on the official site | Pradhan Mantri Matru Vandana Yojana (maternity benefit) |
| FOGSI | https://www.fogsi.org | **Patient-education material only**, if openly available |
| WHO India / UNICEF India | https://www.who.int/india, https://www.unicef.org/india | India-specific maternal and newborn material |

**Government documents and schemes to look for by name** (confirm each exists and is current before using):
Guidelines for Antenatal Care and Skilled Attendance at Birth (ANMs/LHVs/SNs) · Maternal and Newborn Health Toolkit · MCP Card / Safe Motherhood Booklet · Janani Suraksha Yojana (JSY) · Janani Shishu Suraksha Karyakram (JSSK) · Pradhan Mantri Surakshit Matritva Abhiyan (PMSMA) · Surakshit Matritva Aashwasan (SUMAN) · Anemia Mukt Bharat · Diagnosis & Management of Gestational Diabetes Mellitus (MoHFW) · LaQshya · RMNCH+A strategy.

### Telangana / Hyderabad (local)

Local content is limited. **Collect what genuinely exists. Do not pad.**

| Source | What to take |
|---|---|
| Government of Telangana, Health, Medical & Family Welfare Department (find via https://www.telangana.gov.in) | State maternal-health schemes, public facility information, programme guidelines |
| NHM Telangana (via the state health portal) | State RCH programme information |
| Public maternity/teaching hospitals in Hyderabad (e.g. Government Maternity Hospitals at Petlaburj and Sultan Bazar, Osmania General Hospital, Gandhi Hospital), **official pages only** | Services offered, antenatal care availability, how to register |
| GHMC / urban primary health services (e.g. Basti Dawakhana), official pages only | Free antenatal check-up access in the city |
| State schemes (e.g. nutrition support for pregnant women, newborn kit, ambulance services) | Scheme description, eligibility, how to apply |

**Local-content rules:**
- Scheme names and status change (including after changes of state government). Set `time_sensitive: true` and note the date.
- Every phone number, helpline, or address must be copied from an official page you opened. Never from memory or a third-party site.
- **Do not use private-hospital or clinic websites as knowledge content** (marketing copy, unclear review, copyright). They may only appear in `reference_only.csv`.

## 2.2 How to accept a new source (all five must be true)

| # | Check |
|---|---|
| 1 | Publisher is an official body or recognised medical institution, not a company selling something |
| 2 | Author or reviewing organisation is visible |
| 3 | A publication or "last reviewed" date is visible |
| 4 | Content is evidence-based and not promotional (no ads, no product pushing) |
| 5 | Licence or terms of reuse can be read and recorded |

If any check fails, do not use it. Log it in `rejected.csv` with the reason.

## 2.3 Licence tiers (what you may copy)

| Tier | Meaning | What to do |
|---|---|---|
| **A** | Public domain, open government licence, or Creative Commons (attribution only) | Copy into `clean/`, with attribution |
| **B** | Free to reuse for **non-commercial / educational** purposes with attribution (e.g. WHO's usual non-commercial Creative Commons licence; many Indian government sites ask you to acknowledge the source) | Copy into `clean/`, with attribution; note the conditions |
| **C** | Copyrighted, no clear reuse permission (e.g. ACOG, RCOG leaflets, March of Dimes, Mayo Clinic, Cleveland Clinic, BabyCenter, WebMD, most private hospitals) | **Do NOT copy content.** Add to `reference_only.csv` (title, URL, why useful). |

**If the licence is unclear, treat it as Tier C**, log it, and move on. Only Tier A and B content goes into `clean/`.

---

# PART 3 — WHAT TO COLLECT AND HOW MUCH

## 3.1 Volume

| Level | Files (after splitting) | Approx. words |
|---|---|---|
| **Minimum (acceptance)** | **600** | 600k+ |
| **Target** | **1,000+** | 1–2M |
| **Ceiling** | about 3M words in total | roughly 7,500 chunks, comfortably inside the free Supabase 500 MB limit |

Region mix to aim for: **International ≥ 40%, India national ≥ 35%, Telangana/Hyderabad = whatever quality content exists.**

## 3.2 Minimum files per primary topic

The `topics` value in each file's label must use these exact slugs. The **first** slug in the list is the file's **primary topic** and decides its folder.

| Topic slug | Min files | What to cover |
|---|---|---|
| `week-by-week` | 80 | Weeks 1–40, **at least 2 sources per week** (baby's development, mother's changes, tips) |
| `trimester-overview` | 12 | First / second / third trimester overviews, at least 4 sources each |
| `fetal-development` | 20 | Growth stages, organs, **fetal movement (kick counts, why it matters)**, fetal heart rate |
| `nutrition` | 40 | Healthy diet, iron, folic acid, calcium, vitamin D, foods to avoid, weight gain, **Indian diet and vegetarian options**, hydration |
| `activity-lifestyle` | 20 | Exercise, sleep, work, travel, sex, hygiene, dental care, clothing |
| `common-symptoms` | 40 | Nausea, back pain, heartburn, swelling, cramps, constipation, fatigue, skin changes |
| `warning-signs` | 25 | Danger signs, when to seek urgent care, bleeding, severe headache, reduced movement, fluid leakage |
| `conditions` | 100 | Gestational diabetes, preeclampsia / high BP, anaemia, thyroid, UTI, infections, Rh factor, miscarriage, ectopic pregnancy, preterm labour, multiple pregnancy, placenta problems |
| `tests-scans` | 40 | Ultrasound types, blood tests, glucose tolerance test, NT scan, anomaly scan, screening vs diagnostic |
| `vitals-monitoring` | 20 | **Explainers tied to the Alovia risk models:** blood pressure in pregnancy, blood sugar, HbA1c, BMI, weight gain, body temperature, heart rate, **CTG / cardiotocography, NST, fetal heart rate patterns, what "normal / suspect / pathological" mean** |
| `antenatal-care` | 25 | Visit schedule, vaccines (TT/Tdap, flu, COVID), supplement schedule, birth preparation |
| `labour-birth` | 40 | Stages of labour, pain relief, C-section, induction, birth plan, hospital bag |
| `postpartum-newborn` | 40 | Recovery, breastfeeding, newborn care basics, postpartum warning signs |
| `mental-health` | 15 | Mood changes, anxiety, perinatal depression (educational, patient-facing only) |
| `substances-medicines` | 20 | What to avoid in pregnancy (alcohol, smoking, some medicines). **General safety information only, no dosage tables.** |
| `india-schemes` | 30 | JSY, JSSK, PMSMA, PMMVY, SUMAN, MCP card, ASHA/ANM roles, institutional delivery, registration process |
| `local-telangana` | 15 | State schemes, public hospitals, urban health services, ambulance/helpline information |
| `myths` | 15 | Myth-vs-fact pages from WHO / NHS / health ministries |
| `glossary` | 3 | Plain-language pregnancy glossaries (split by letter or section, one file each) |
| **Total** | **600** | |

## 3.3 Do NOT collect

- Blogs, forums, social media, Q&A sites, influencer content, AI-generated pages
- Commercial or pharmaceutical content; private hospital marketing pages
- Research papers and trial write-ups (too dense; only if open access and Raheem asks)
- Drug dosage tables, clinician-only procedures, prescribing protocols
- Unverified herbal or alternative-medicine claims
- Anything in Tier C (log it in `reference_only.csv` instead)

**Guideline documents** (WHO, NICE, MoHFW) are allowed as backup sources. Set `audience: clinician` or `both`, and set `contains_treatment_advice` / `contains_dosage` honestly. Aim for **at least 70% of files with `audience: patient` or `both`.**

**Regional-language material (Telugu / Hindi / Urdu):** optional, `priority: P3`, only official translations of official patient material. Set `language` to `te`, `hi`, or `ur`.

---

# PART 4 — FILE FORMAT AND QUALITY RULES

## 4.1 Front matter (the label block at the top of every clean file)

Every file in `clean/` starts with this block, then a blank line, then the text. **Filled example:**

```yaml
---
doc_id: NHS-WEEKLY-024
title: "Your pregnancy at 24 weeks"
source_org: "NHS (UK)"
source_type: government
licence_tier: A
licence: "Open Government Licence v3.0"
attribution: "Contains public sector information licensed under the Open Government Licence v3.0."
url: "https://www.nhs.uk/..."
date_accessed: 2026-09-21
published_or_reviewed: 2023-05
region: international
country: UK
language: en
doc_type: patient_education
audience: patient
topics: [week-by-week, fetal-development]
trimester: "2"
week_start: 24
week_end: 24
contains_treatment_advice: false
contains_dosage: false
time_sensitive: false
priority: P1
raw_file: raw/nhs/NHS-WEEKLY-024.html
part: null
notes: ""
---

# Your pregnancy at 24 weeks
(the cleaned text, exactly as published, continues here)
```

**Notes on the fields:**
- `attribution`, `part`, and `notes` are optional; every other field is required.
- Use straight quotes `"` around text values that contain colons or special characters.
- `trimester` must always be in quotes.

## 4.2 Field rules

| Field | Rule |
|---|---|
| `doc_id` | Format `SOURCE-TOPIC-NNN`, capital letters, 3–4 digit number, e.g. `NHS-WEEKLY-024`, `MOHFW-ANC-003`, `WHO-ANC-011`. Unique. **Must equal the file name.** |
| `source_type` | `government` · `intergovernmental` · `professional_body` · `nonprofit` · `academic` |
| `licence_tier` | `A` or `B` only (Tier C never goes into `clean/`) |
| `date_accessed` | The date you actually opened the page, `YYYY-MM-DD` |
| `published_or_reviewed` | `YYYY`, `YYYY-MM`, `YYYY-MM-DD`, or `unknown`. **Use the "last reviewed" date if shown, otherwise the publication date.** |
| `region` | `international` · `india` · `telangana` · `hyderabad` |
| `language` | `en` (default), or `te` / `hi` / `ur` |
| `doc_type` | `patient_education` · `guideline` · `factsheet` · `glossary` · `scheme_info` · `faq` · `myth_buster` |
| `audience` | `patient` · `clinician` · `both` |
| `topics` | List of slugs from Section 3.2. **First = primary topic.** |
| `trimester` | `"1"` (weeks 1–13) · `"2"` (14–27) · `"3"` (28–42) · `"all"` · `"postpartum"` |
| `week_start`, `week_end` | Gestational weeks (1–42). Fill for week-specific documents, and for trimester documents use that trimester's range. Otherwise both `null`. |
| `contains_treatment_advice` | `true` / `false` (see Section 1.6, Step C, item 7) |
| `contains_dosage` | `true` / `false` (see Section 1.6, Step C, item 7) |
| `time_sensitive` | `true` for schemes, amounts, helplines, addresses, "current recommendation" pages |
| `priority` | `P1` core (MedlinePlus, NHS, WHO, CDC, MoHFW/NHM, ICMR-NIN) · `P2` second or supporting source · `P3` optional extras and translations |
| `raw_file` | Path to the saved original. Parts of one split document share the same `raw_file`. |
| `part` | `null`, or e.g. `"3/12"` if split from a longer document |

**Week convention:** always **gestational weeks counted from the last menstrual period (LMP)**, as NHS, WHO, and CDC do. If a source counts weeks since conception (fetal age), add 2 and say so in `notes`.

## 4.3 Folder and file naming

- Clean file: `clean/<region>/<primary-topic>/<doc_id>.md`
- Original: `raw/<source>/<doc_id>.<html|pdf>`
- The folder names must equal the file's `region` and its first `topics` entry. The validator checks this.

## 4.4 Cleaning rules

The clean text is exactly what will later be cut into chunks and embedded. Do it right once.

**Keep:** headings (`#`, `##`, `###`), paragraphs, bullet lists, tables (as Markdown tables), units exactly as written (mmHg, mg/dL, mmol/L), and all medical content word for word.

**Remove:** navigation menus, cookie banners, ads, share buttons, "related articles", author bios, footers, page numbers, repeated PDF headers/footers, reference lists, image files (keep a caption only if it explains something), navigation-only links.

**Fix:** words split by line breaks in PDFs (`hyper-\ntension` becomes `hypertension`), broken table rows, odd characters from OCR.

**Never:** paraphrase, summarise, translate, or "improve" the text (Rule R1).

**Every file:** starts with a level-1 heading matching its `title`, and has at least **100 words** (glossary entries excepted).

## 4.5 Splitting rules (one file = one topic)

- A page or PDF about **one topic** stays as one file (ideal length 300–3,000 words).
- A document covering **several topics** (guidelines, toolkits, long PDFs) is **split at heading boundaries**. Each part gets its own `doc_id`, `topics`, `trimester`, and weeks; all parts share the same `raw_file`; set `part` (e.g. `"3/12"`).
- Never split in the middle of a section or table.
- Long week-by-week pages: one file per week.
- If a part would be under 100 words, merge it into its neighbour.

## 4.6 Duplicates and conflicts

- The same content often appears on several sites. Keep it **once**, from the most authoritative source, and log the other in `rejected.csv`. The validator catches exact duplicates only, so the person must watch for near-duplicates (the AI can help compare texts).
- If two sources **disagree** (for example on caffeine limits), keep both, fill `published_or_reviewed` correctly, and describe the conflict in `notes`. Raheem decides which is primary.

## 4.7 Acceptance checklist (all must be true)

- [ ] Validator reports **0 errors**
- [ ] No topic marked **SHORT**; total files ≥ 600
- [ ] Every source used is in `sources_registry.csv` with a terms URL and licence tier
- [ ] No Tier C content in `clean/`
- [ ] Every scheme, helpline, and address file has `time_sensitive: true` and was verified on an official page
- [ ] A random **5% sample** was checked by a second person against the originals (text matches, nothing missing, no page clutter)
- [ ] `README.md` honestly lists known gaps (e.g. "few Telangana sources found")

## 4.8 Suggested order of work

| Phase | Work |
|---|---|
| 1. Setup | Create the folders and CSV logs; read and record the terms of every P1 source |
| 2. Scriptable sources | MedlinePlus, NHS, CDC (fastest volume). **After the first 20 files, stop and show Raheem (Section 1.7).** |
| 3. Guidelines and PDFs | WHO, NICE, MoHFW, NHM, ICMR-NIN: download, clean, split |
| 4. India schemes and local | Scheme pages, Telangana/Hyderabad official sources; verify every helpline and address |
| 5. Second sources | Fill week-by-week (2 per week), myths, glossary, and any gaps shown by the validator |
| 6. QA and handoff | Validator to 0 errors, 5% second-person spot-check, `README.md`, zip and share |

**Tip:** run the validator every 10–20 files. Fixing labelling mistakes early is far cheaper than at the end.

## 4.9 Quick decisions

| Situation | Do this |
|---|---|
| Licence unclear | Treat as Tier C, log in `reference_only.csv`, move on |
| Page has no date | `published_or_reviewed: unknown`; prefer another source if one exists |
| Two sources say the same thing | Keep the more authoritative one, log the other in `rejected.csv` |
| Document is 200 pages | Split by heading (Section 4.5), or extract only the relevant chapters and note it in `README.md` |
| Scanned PDF with bad text quality | Skip and log in `rejected.csv` ("poor OCR"), unless it is a key India government guideline, then check with Raheem |
| Not sure which topic slug fits | Choose the closest one and add the other in `topics`. **Never invent new slugs.** |
| Found a strong source not listed | Run the five checks (Section 2.2), add it to `sources_registry.csv`, proceed; check with Raheem if unsure |
| A page fails to download or a link is dead | Search the site by name once; if still not found, log in `rejected.csv`. Do not guess URLs. |
