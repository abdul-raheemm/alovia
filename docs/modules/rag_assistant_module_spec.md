# Alovia — Module 5: Pregnancy Knowledge Assistant (RAG) — Module Specification

**Version:** 1.0
**Date:** 2026-11-16
**Owner:** Raheem
**Status:** Final for build, except items tagged `[OPEN]` or `[CONFIRM AT REVIEW]`. Built last, after the knowledge base is complete.
**Related:** PRD v2 §4.5, TRD v2 §4.5, DRD v2 (`kb_documents`, `kb_chunks`, `chat_history`), `knowledgebase.md`, `PROGRESS.md`, and the module specs for Symptom Tracking (7), Pregnancy Journey (4) and Doctor Dashboard (6).

---

## 0. How to use this document (read first)

These rules apply to anyone building from this document, including AI coding assistants.

1. **Use only what is written here.** Steps, categories, filters, checks and outputs are defined in this file.
2. **The assistant never answers from the LLM's own knowledge.** Every answer comes from retrieved knowledge base chunks, or it is a fixed message.
3. **Tags:** `[CONFIGURABLE]` = a setting in `config.yaml`; `[OPEN]` = not decided, leave a placeholder; `[CONFIRM AT REVIEW]` = a doctor must confirm before release.
4. **Fixed wording** is defined by message keys only. Final text lives in `messages.yaml`, doctor-approved.
5. **Starting values** for numeric settings (chunk size, top-k, thresholds) are placeholders to be tuned with the test set (section 12). They are not medical values.

---

## 1. Purpose and scope

### 1.1 What the assistant does
Answers pregnancy questions in plain language using only the curated knowledge base, with a citation for every point, personalised by the patient's gestational age where relevant.

### 1.2 What it never does
- Never diagnoses, and never says a symptom or result is "normal for you".
- Never gives medicine doses or treatment instructions.
- Never explains the patient's own fetal, maternal or genetic results (decision D3).
- Never predicts or helps determine the baby's sex (PCPNDT Act, S1).
- Never answers without a valid citation.
- Never answers from the model's general knowledge when retrieval finds nothing.
- Never replaces emergency advice: urgent messages get the Module 7 advice first.

---

## 2. Glossary

| Term | Meaning |
|---|---|
| **chunk** | A piece of a clean knowledge base file, stored with its embedding and copied labels in `kb_chunks`. |
| **labels** | Front-matter fields of a knowledge base file (`audience`, `week_start`, `week_end`, `trimester`, `region`, `topics`, `contains_dosage`, `contains_treatment_advice`, `time_sensitive`, licence fields). |
| **content week** | The patient's completed gestational weeks (Module 4 §6). `null` if no due date. |
| **category** | The type of question decided in step 2 (section 5). |
| **urgent match** | A message that matches the urgent phrase list (section 4). |
| **fallback** | A fixed, safe message used when an answer cannot be given safely. |

---

## 3. Final decisions

| # | Topic | Decision | Date |
|---|---|---|---|
| D1 | Stack | LangChain, pgvector on Supabase, an embedding API, an LLM API (provider `[OPEN]`) | 2026-10-02 |
| D2 | Dosage documents | Files with `contains_dosage: true` are excluded from patient answers | 2026-11-16 |
| D3 | Own results | Not explained in v1; the assistant points to the doctor's shared message. General terms (for example what "suspect" means on a CTG) may be explained from the knowledge base. | 2026-11-16 |
| D4 | Treatment-advice documents | Allowed, but answers phrase them as "doctors may recommend…" and point to her doctor | 2026-11-16 |
| D5 | Doctor visibility | Chats are private. Only urgent matches create a doctor inbox item with that one message | 2026-11-16 |
| D6 | NHS citations | Answers carry the OGL statement; a Sources panel shows the original NHS excerpt word for word with "Information from the NHS website as at DDMMYY" (section 8.3) | 2026-11-16 |
| D7 | Baby's sex questions | Declined with the legal reason | 2026-11-16 |
| D8 | Urgent messages | Checked before anything else; same advice and levels as Module 7 | 2026-11-16 |
| D9 | No match | No answer from model knowledge; fixed fallback | 2026-11-16 |
| D10 | Memory | Last few turns only; no long-term memory | 2026-11-16 |
| D11 | Language | English in v1 | 2026-11-16 |
| D12 | Evaluation | A fixed test set with measured results (section 12) | 2026-11-16 |
| D13 | Build order | Built last, after the knowledge base is complete | 2026-11-16 |

---

## 4. Step 1 — Safety check (rules, no AI)

Runs on every message before anything else.

### 4.1 Urgent symptoms
- `urgent_phrases.yaml` maps phrases to Module 7 warning-sign IDs (for example "bleeding" → `vaginal_bleeding`, "water broke" → `fluid_leaking`, "baby not moving" → `baby_movements_reduced`). Each match takes the level of that Module 7 rule (L1 or L2).
- On a match: show the Module 7 advice for that level (`msg_level1_go_now` or `msg_level2_contact_today`) and the urgent button. **No knowledge base answer is generated for this message.**
- Create a doctor inbox item `chat_urgent` with the message text (Dashboard §7, D5).
- The full phrase list is written during the build and reviewed by a doctor `[OPEN]` `[CONFIRM AT REVIEW]` (R1). Matching is case-insensitive and whole-word.

### 4.2 Distress or self-harm wording
- `distress_phrases.yaml` (doctor-reviewed `[OPEN]`, R2). On a match: show `msg_support` with the helpline number (helpline `[OPEN]`, copied from an official source as in Module 7 §11.3). No knowledge base answer. Create a `chat_urgent` inbox item.

### 4.3 Limits of this check
The phrase lists cannot catch every wording. The chat screen always shows the urgent button and `msg_not_monitored_live` (Module 7).

---

## 5. Step 2 — Classify the question

The LLM returns exactly one category from this list (structured output). If the output is not one of these values, use `educational` and continue (later checks still apply).

| Category | Example | Action |
|---|---|---|
| `educational` | "What happens at week 24?" | Steps 3–5 |
| `personal_diagnosis` | "Do I have gestational diabetes?" | Steps 3–5 for the general topic, plus `msg_only_doctor_can_tell` |
| `medicine_dose` | "How much paracetamol can I take?" | `msg_ask_doctor_pharmacist`; no answer |
| `own_results` | "What does my CTG result mean?" | `msg_see_doctor_message` with a link to My results; no answer |
| `baby_sex` | "How can I tell if it's a boy?" | `msg_sex_determination_not_allowed`; no answer |
| `off_topic` | Not about pregnancy or newborn care | `msg_off_topic`; no answer |

---

## 6. Step 3 — Retrieval

### 6.1 Query
The question is rewritten into a standalone query using the last `history_turns` messages (default 6) `[CONFIGURABLE]`.

### 6.2 Filters (applied in the database query)
- `audience` in (`patient`, `both`).
- `contains_dosage = false` (D2).
- **Week filter:** if the question is about the current stage (detected by the classifier as a flag `about_current_stage`, or by phrases like "this week", "now", "at my stage") and content week is known: keep chunks where `week_start ≤ content_week ≤ week_end`, or both weeks are `null`.

### 6.3 Ranking
- Vector similarity, top `top_k` chunks (starting value 5) `[CONFIGURABLE]`.
- When content week is known and no week filter applies: chunks whose week range contains the content week get a boost (`week_boost`, starting value 0.05) `[CONFIGURABLE]`.
- For questions with the topics `india-schemes` or `local-telangana`, or that mention schemes, services, cost or hospitals: chunks with `region` `india`, `telangana` or `hyderabad` get a boost (`region_boost`, starting value 0.05).

### 6.4 No match
If no chunk has similarity ≥ `min_similarity` (starting value `[OPEN]`, tuned with the test set), reply `msg_no_trusted_info`. No generation.

---

## 7. Step 4 — Generation

### 7.1 Input to the LLM
System rules (section 7.2), the retrieved chunks numbered [1]…[k] with their titles, the patient's content week (if known and relevant), and the question. **No names or IDs** are sent.

### 7.2 System rules (the prompt must state all of these)
1. Use only the numbered sources. If they do not answer the question, say so.
2. Cite every factual sentence with the source number(s), like [1] or [2][3].
3. Plain, short language. Maximum `max_answer_words` (default 200) `[CONFIGURABLE]`.
4. Mention the patient's week only when it helps the answer.
5. Never diagnose, never say something is normal for her, never give doses or treatment instructions.
6. For treatment information, use "doctors may recommend…" and say to discuss it with her doctor (D4).
7. If the topic touches her health, end with a short suggestion to talk to her doctor.

---

## 8. Step 5 — Output checks (code, not AI)

### 8.1 Checks
| Check | On failure |
|---|---|
| Every citation number refers to a retrieved chunk | Remove invalid citations; if none remain → `msg_no_trusted_info` |
| At least one valid citation | `msg_no_trusted_info` |
| No dose patterns (number followed by mg, mcg, µg, IU, ml, tablet(s), capsule(s)) | `msg_no_trusted_info` |
| No blocked phrases (`blocked_phrases.yaml`, e.g. "you have", "this is normal", "you don't need to see") `[CONFIRM AT REVIEW]` (R3) | `msg_no_trusted_info` |
| Length within the limit | Cut at the last full sentence |

### 8.2 Always added
- `disclaimer_assistant`: educational information, not medical advice.
- A **Sources** panel: for each cited chunk, title, publisher, URL, and the chunk's `published_or_reviewed` date.
- For chunks with `time_sensitive: true`: their date and `msg_check_current`.

### 8.3 Licence-specific citation display (D6)
| Licence of the cited file | Answer shows | Sources panel shows |
|---|---|---|
| NHS (OGL v3.0) | "Contains public sector information licensed under the Open Government Licence v3.0." | The original chunk text **word for word**, with "Information from the NHS website as at DDMMYY" (the file's copy date) and its URL |
| Public domain / CC BY (e.g. MedlinePlus, womenshealth.gov) | Normal citation numbers | Title, publisher, URL, licence; CC BY attribution text where required |
| Tier B (e.g. WHO, NHM) | Normal citation numbers | Title, publisher, URL, licence with its conditions |

The `licence` and `attribution` fields come from the chunk's labels; nothing is typed by hand.

---

## 9. Chunking and indexing (build-time)

- Input: every valid file in `clean/` (`manifest.csv`).
- Split at headings first, then by size: `chunk_size` (starting value 500 tokens) and `chunk_overlap` (starting value 50) `[CONFIGURABLE]`. Never split inside a table.
- Each chunk stores the file's `title` and the section heading it came from at the start of its text (keeps context, and helps the NHS "not out of context" condition).
- Each chunk copies the labels listed in DRD v2 `kb_chunks`, plus `licence`, `attribution`, `contains_dosage`, `contains_treatment_advice`, `time_sensitive`, `published_or_reviewed`, `date_accessed`.
- Embedding model and vector size `N` `[OPEN]` (DRD v2 blocker). Re-indexing from `clean/` must be one command.
- NHS files are re-copied at least every 7 days or carry their copy date (licence clause 3.6(a), see `PROGRESS.md`).

---

## 10. Conversation, storage and integration

- **Memory:** the last `history_turns` messages only, for follow-up questions. Nothing is remembered between sessions except the stored history.
- **Storage:** each message in `chat_history` (DRD v2), with `retrieved_sources` (doc_id, chunk_id, title, source_org, url), plus `category`, `urgent_match` (boolean), `check_result` (passed / fallback reason), `model_name`, `prompt_version`.
- **Patient controls:** the patient can view her chat history `[OPEN]` whether she can delete it.
- **Doctor:** sees only `chat_urgent` inbox items (D5).
- **Journey link:** "Ask about this week" opens the assistant with the content week set (Module 4 §8.5); shown only when `assistant_enabled = true`.
- **Feedback:** thumbs up / down on each answer, stored for evaluation.

---

## 11. Message keys (intent only; final text in `messages.yaml`, doctor-approved)

| Key | Intent |
|---|---|
| `msg_level1_go_now`, `msg_level2_contact_today` | Same as Module 7 |
| `msg_support` | Support message with helpline (number `[OPEN]`) |
| `msg_only_doctor_can_tell` | Only your doctor can tell whether this applies to you |
| `msg_ask_doctor_pharmacist` | For medicines and doses, please ask your doctor or pharmacist |
| `msg_see_doctor_message` | Your doctor shares your results with you; see My results or ask your doctor |
| `msg_sex_determination_not_allowed` | In India, finding out the sex of the baby before birth is not allowed by law, so I can't help with this |
| `msg_off_topic` | I can only help with pregnancy and newborn questions |
| `msg_no_trusted_info` | I don't have trusted information on that; please ask your doctor |
| `msg_check_current` | This information may change; check it is still current |
| `disclaimer_assistant` | Educational information only, not medical advice |
| `msg_not_monitored_live` | Same as Module 7 |

---

## 12. Evaluation (required before release)

### 12.1 Test set
`tests/eval_questions.yaml`, about 50–100 questions, each with the expected category and expected behaviour:
- the example questions from the project guidelines (week 24, second trimester changes, fetal movement, gestational diabetes);
- general educational questions across the knowledge base topics;
- dose, diagnosis, own-result, baby's sex and off-topic questions;
- urgent and distress messages;
- questions the knowledge base cannot answer.

### 12.2 Measures

| Measure | How |
|---|---|
| Urgent messages caught | % of urgent test messages that get the Module 7 advice (target: 100%) |
| Correct category | % of questions with the expected category |
| Correct refusals | % of dose / diagnosis / own-result / sex / off-topic questions with no answer |
| Citation validity | % of answers where every citation is a retrieved chunk (target: 100% after checks) |
| Groundedness | Manual review of a sample: is each cited sentence supported by its chunk? |
| No-match handling | % of unanswerable questions answered with `msg_no_trusted_info` |
| Latency | Median and 90th-percentile response time (target under 3–5 s, warm service) |

Results are saved per run (`eval_results/<date>.csv`) so improvements can be shown in the report.

---

## 13. Settings (`config.yaml`, all `[CONFIGURABLE]`)

| Setting | Starting value |
|---|---|
| `assistant_enabled` | `false` until built |
| `llm_provider`, `llm_model` | `[OPEN]` (shared with Dashboard AI features) |
| `embedding_model`, `embedding_dim` | `[OPEN]` |
| `history_turns` | 6 |
| `top_k` | 5 |
| `min_similarity` | `[OPEN]` (tuned with the test set) |
| `week_boost`, `region_boost` | 0.05 |
| `chunk_size`, `chunk_overlap` | 500, 50 tokens |
| `max_answer_words` | 200 |
| `llm_timeout_seconds` | 15 (on timeout → `msg_no_trusted_info`) |

---

## 14. API (proposed)
`[OPEN]` Names to be aligned with the project-wide route design.

| Method | Path | Purpose |
|---|---|---|
| POST | `/assistant/messages` | Send a message; returns answer, sources, flags |
| GET | `/assistant/history` | The patient's own chat history |
| POST | `/assistant/messages/{id}/feedback` | Thumbs up / down |

---

## 15. Tests (in addition to the evaluation)
1. An urgent phrase never reaches retrieval or generation; it always returns Module 7 advice and creates a `chat_urgent` item.
2. A `contains_dosage: true` chunk is never retrieved.
3. Week filter returns only matching or week-less chunks when `about_current_stage` is true.
4. Fabricated citation numbers are removed; an answer with none left becomes `msg_no_trusted_info`.
5. Dose patterns and blocked phrases trigger the fallback.
6. NHS chunks are shown with the OGL statement and the verbatim excerpt with copy date.
7. No names or IDs appear in LLM inputs.
8. LLM timeout returns the fallback.

---

## 16. Out of scope (v1) and Do not

**Out of scope:** regional languages; voice input; explaining the patient's own results; reading uploaded documents; long-term memory; web search; answering doctors' clinical questions.

**Do not:**
- Do not answer without retrieved sources.
- Do not show an answer that failed the output checks.
- Do not send identifiers to the LLM.
- Do not include dosage documents in retrieval.
- Do not skip the safety check, even for questions opened from the Journey.

---

## 17. Open items

| Item | Tag |
|---|---|
| LLM provider and model | `[OPEN]` |
| Embedding model and vector size `N` | `[OPEN]` |
| `min_similarity` threshold (tuned) | `[OPEN]` |
| Urgent and distress phrase lists (R1, R2) | `[OPEN]` `[CONFIRM AT REVIEW]` |
| Blocked phrase list (R3) | `[CONFIRM AT REVIEW]` |
| Helpline number | `[OPEN]` |
| Whether patients can delete chat history | `[OPEN]` |
| Privacy conditions before real patient data reaches the LLM | `[OPEN]` |
| Final message text | `[OPEN]` |
| API route names | `[OPEN]` |

---

## Sources

| ID | Source |
|---|---|
| S1 | Pre-Conception and Pre-Natal Diagnostic Techniques (Prohibition of Sex Selection) Act, 1994 (India). |
| S2 | Open Government Licence v3.0 (NHS content terms; clauses 3.6(a) and 3.6(b) as recorded in `PROGRESS.md`). https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/ |
| S3 | Alovia `knowledgebase.md` v2.0 and `PROGRESS.md` (labels, licence tiers, conventions). |

> **Disclaimer:** the assistant provides educational information from trusted sources. It does not diagnose or give treatment advice and does not replace a doctor.
