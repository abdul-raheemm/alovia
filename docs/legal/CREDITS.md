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

## Illustrations (Journey month cards)
| File | Source URL | Author/publisher | Licence | Date downloaded | Changes |
|---|---|---|---|---|---|
| month_1 … month_9 | `[OPEN]` | | Public domain / CC0 / CC BY / CC BY-SA only | | |

Prototype only (Journey §7.1): `month_1.svg` … `month_9.svg` are simple placeholder shapes labelled "Placeholder", made by `frontend/scripts/make-placeholder-illustrations.mjs` — no third-party asset. Allowed only while the prototype banner is shown; they must be replaced by openly licensed drawings (and recorded above) before release.

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
