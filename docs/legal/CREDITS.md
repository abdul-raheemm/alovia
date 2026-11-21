# Credits and Licences — Alovia

Every third-party asset used in the apps must be listed here **before** it is used. Shown (summarised) on the `/about` or Credits page.

## Fonts
| Asset | Licence | Use |
|---|---|---|
| Nunito (via @fontsource, self-hosted) | SIL Open Font Licence 1.1 | Patient app |
| Inter (via @fontsource, self-hosted) | SIL Open Font Licence 1.1 | Doctor app |

## Icons and emoji
| Asset | Licence | Use |
|---|---|---|
| Lucide icons | ISC | UI icons |
| Microsoft Fluent UI Emoji (https://github.com/microsoft/fluentui-emoji), colour SVGs: apple, brinjal (Eggplant), broccoli, capsicum (Bell pepper), coconut, corn (Ear of corn), grapes, lemon, mango, melon, orange (Tangerine), pineapple, tomato, watermelon — unchanged; downloaded 2026-11-17 and 2026-11-18, in `frontend/apps/patient-web/public/icons/fluent/` with the MIT `LICENSE` file | MIT (include licence notice) | Baby-size comparison objects |

## Datasets (model training and training ranges)
| Dataset | Use | Licence |
|---|---|---|
| Campos, D. & Bernardes, J. (2000). *Cardiotocography* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C51S4N (`CTG.xls`, id 193) | Fetal model training (owner); training ranges in `backend/ml_models/fetal_risk_feature_ranges.json` (min/max only; the data itself is not shipped) | CC BY 4.0 (attribution required), checked on the UCI page 2026-11-19 (owner confirmed) |
| Hossain, M. M. (2025). *Maternal health risk data* (Version 1) [Dataset]. Mendeley Data. https://doi.org/10.17632/ckhgtgdg4f.1 (`Maternal_Risk.csv`; cleaned to the criteria of Hossain et al. 2026) | Maternal model training (owner); training ranges in `backend/ml_models/maternal_risk_feature_ranges.json` (min/max only; not shipped) | CC BY 4.0 (attribution required), checked on the Mendeley Data page 2026-11-19 (owner confirmed) |

## Illustrations (Journey month cards)
| File | Source | Artist | Licence status | Date added | Changes |
|---|---|---|---|---|---|
| `frontend/apps/patient-web/public/illustrations/month_1.webp` | Dreamstime, image ID 304802954 | Liubomyr Feshchyn | Stock, watermarked preview, **not licensed for release** | 2026-11-21 | Cropped from the sheet only |
| `frontend/apps/patient-web/public/illustrations/month_2.webp` | Dreamstime, image ID 304802954 | Liubomyr Feshchyn | Stock, watermarked preview, **not licensed for release** | 2026-11-21 | Cropped from the sheet only |
| `frontend/apps/patient-web/public/illustrations/month_3.webp` | Dreamstime, image ID 304802954 | Liubomyr Feshchyn | Stock, watermarked preview, **not licensed for release** | 2026-11-21 | Cropped from the sheet only |
| `frontend/apps/patient-web/public/illustrations/month_4.webp` | Dreamstime, image ID 304802954 | Liubomyr Feshchyn | Stock, watermarked preview, **not licensed for release** | 2026-11-21 | Cropped from the sheet only |
| `frontend/apps/patient-web/public/illustrations/month_5.webp` | Dreamstime, image ID 304802954 | Liubomyr Feshchyn | Stock, watermarked preview, **not licensed for release** | 2026-11-21 | Cropped from the sheet only |
| `frontend/apps/patient-web/public/illustrations/month_6.webp` | Dreamstime, image ID 304802954 | Liubomyr Feshchyn | Stock, watermarked preview, **not licensed for release** | 2026-11-21 | Cropped from the sheet only |
| `frontend/apps/patient-web/public/illustrations/month_7.webp` | Dreamstime, image ID 304802954 | Liubomyr Feshchyn | Stock, watermarked preview, **not licensed for release** | 2026-11-21 | Cropped from the sheet only |
| `frontend/apps/patient-web/public/illustrations/month_8.webp` | Dreamstime, image ID 304802954 | Liubomyr Feshchyn | Stock, watermarked preview, **not licensed for release** | 2026-11-21 | Cropped from the sheet only |
| `frontend/apps/patient-web/public/illustrations/month_9.webp` | Dreamstime, image ID 304802954 | Liubomyr Feshchyn | Stock, watermarked preview, **not licensed for release** | 2026-11-21 | Cropped from the sheet only |
| `assets/illustrations/source/dreamstime_304802954_preview.jpg` (original sheet) | Dreamstime, image ID 304802954 | Liubomyr Feshchyn | Stock, watermarked preview, not licensed for release | 2026-11-21 | None |

Owner decision DEC-108 (2026-11-21): used for the capstone prototype and demo only, while `show_prototype_banner = true`. **Before any public deployment, buy the licence or replace the set**; watermarked previews must not be shown to the public. Doctor approval: `docs/illustration_review.md`. The earlier placeholder shapes (`month_*.svg`) were removed.

Checked and **not allowed** (2026-11-18): the nine fetal-stage images on womenshealth.gov "Stages of pregnancy" (`/sites/default/files/images/01months.jpg` … `09months.jpg`) carry a printed "©peggerrity.com" mark — a third-party illustrator's copyright that the site's "free of copyright restrictions" statement does not cover. Servier Medical Art (CC BY 4.0) has no month-by-month series.

## Animations
| File | Source | Licence |
|---|---|---|
| `[OPEN]` | LottieFiles (free) | Lottie Simple License |

## Content sources
Journey prototype content and the knowledge base: see `docs/knowledge-base/` (sources registry, licences, attributions) and each content item's `source` field. Shown in the app with a source line on every card:

| Source | Licence | Use |
|---|---|---|
| Office on Women's Health (HHS), "Stages of pregnancy" | Public domain (US government page, stated free of copyright restrictions) | Month items (values only) |
| NHS website (pages saved in `knowledge-base/raw/`, licence-checked by the owner) | Open Government Licence v3.0 (attribution line in each item) | Unchanged excerpts |
| MedlinePlus (US National Library of Medicine) | Public domain | Guidance, checklist, discuss-with-doctor, trimester overview |
| WHO Fetal Growth Charts — Kiserud T et al., PLOS Medicine 2017, Table 11 (doi:10.1371/journal.pmed.1002220) | CC BY 4.0 (attribution on the size line) | 50th-percentile weights for the size sample |
| PUQE-24 scale (created by Motherisk), as printed by the Association of Ontario Midwives (Symptom spec S5) | Published clinical scale, cited by the spec; title and publisher shown under the questions | Nausea and vomiting questions on the log page |
