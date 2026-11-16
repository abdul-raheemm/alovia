# Compliance Checklist — Alovia

**Version:** 1.0 · **Date:** 2026-11-16
**Important:** this is a project checklist, not legal advice. Review it with the project supervisor (and a legal adviser before any real users). Laws checked: India's DPDP Act 2023 and DPDP Rules 2025 (phased to 14 May 2027), PCPNDT Act 1994, CDSCO medical device software guidance (2026), content licences.

| # | Item | Applies? | What Alovia does | Where | Phase |
|---|---|---|---|---|---|
| 1 | Privacy policy | Yes | Draft in `PRIVACY_POLICY.md`; page `/privacy` in both apps; linked at sign-up and in footer/settings | patient + doctor apps | 1 (draft), 8 (final) |
| 2 | Terms of service | Yes | Draft in `TERMS_OF_USE.md`; page `/terms` | both apps | 1, 8 |
| 3 | Refund policy | **No** | Alovia is free; no payments. Terms state "free, no payments". Add a refund policy only if payments are ever introduced. | — | — |
| 4 | Cookie policy | Yes (short notice) | `COOKIE_NOTICE.md`: only essential browser storage (sign-in session, theme, reduce-motion); no tracking cookies | `/cookies` | 1 |
| 5 | Cookie consent banner | **No, for v1** | Not needed while only essential storage is used and there is no analytics, ads or third-party tracking (DEC-027). If analytics is ever added: consent first, then add a banner. | — | — |
| 6 | Form consents | Yes | App-wide consent at sign-up (unticked checkbox, versioned, stored in `consents`); genetic form reminds that father's data is included; pregnancy-end "inform doctor?" has no default; chat notes that messages are stored | sign-up, genetic, journey, assistant | 1–7 |
| 7 | No unnecessary data | Yes | No phone, address, government ID or payment data; age optional; first name allowed; AI calls without names/IDs | all | all |
| 8 | Audit third-party SDKs | Yes | Allowed: Supabase JS (auth only), self-hosted fonts, Lucide, Fluent Emoji, Lottie files (local), Recharts, etc. **No** analytics, ads, social embeds, external CDNs, chat widgets. LLM/embedding APIs called from the backend only. Re-audit in Phase 8 (`npm ls`, `pip list`). | `ARCHITECTURE.md` §3 | 1, 8 |
| 9 | Remove dark patterns | Yes | No pre-ticked boxes; clear "Cancel"; account deletion easy to find; no confirm-shaming; no fake urgency (red only for real red flags) | design review | each phase |
| 10 | Remove hidden fees | N/A | Free; no fees | — | — |
| 11 | Remove fake reviews | Yes | No testimonials, ratings or user counts anywhere | landing page | 1 |
| 12 | Remove unsupported claims | Yes | Never say "diagnoses", "detects", "accurate", "clinically proven", "safe". Model results always shown with limitations; landing page says "research prototype" | all copy | each phase |
| 13 | Accessibility alt text | Yes | Alt text on all meaningful images; `alt=""` for decorative | `DESIGN_SYSTEM.md` §13 | each phase |
| 14 | Fix colour contrast | Yes | Palette contrast-checked (all ≥ 4.5:1); axe checks in E2E | `DESIGN_SYSTEM.md` §3.4 | each phase |
| 15 | Keyboard navigation | Yes | Radix-based components, visible focus, tab order, keyboard E2E checks | `DESIGN_SYSTEM.md` §16 | each phase |
| 16 | Add business details | Yes (academic) | "About" page: project name, team, institution (MJCET), supervisor, contact email for privacy questions | `/about` | 1 `[OPEN]` details |
| 17 | Age consent for kids' data | Yes | DPDP treats under-18s as children (verifiable parental consent). v1: **18+ only**, checkbox at sign-up (DEC-023) | sign-up | 1 |
| 18 | Unsubscribe link in emails | N/A | No marketing emails; only Supabase account emails (confirmation, password reset, doctor invite) | — | — |
| 19 | Licence fonts/images | Yes | Nunito, Inter (SIL OFL), Lucide (ISC), Fluent Emoji (MIT), openly licensed illustrations, Lottie Simple License; all listed in `CREDITS.md` | `CREDITS.md` | each phase |
| 20 | Data deletion request | Yes | In-app request → admin executes → logged (`SECURITY.md` §7) | settings, admin | 8 |

## Other risks flagged
- **Medical device regulation (CDSCO):** clinical decision-support software can be regulated as a medical device. Keep Alovia a research prototype with synthetic data and a visible "not for clinical use" notice.
- **DPDP timeline:** the strict obligations (consent notices, breach reporting, children's data) apply in later phases of the rollout; still implement them now as good practice.
- **PCPNDT:** no feature may reveal or predict the baby's sex (built into Genetic and RAG specs).
- **Content licences:** NHS OGL attribution and 7-day refresh rule; ICMR-NIN content is reference-only unless permission is received.
- **Health data in an LLM:** only synthetic data until a provider's privacy terms are reviewed.
- **Vercel Hobby:** non-commercial only; fine for the academic project.
