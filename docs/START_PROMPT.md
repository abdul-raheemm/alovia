# Start prompts for Claude Code

## A. First session (paste this to begin the project)

```
You are starting the Alovia project. Read CLAUDE.md fully, then docs/tracking/CONTEXT.md,
docs/tracking/PROGRESS.md, docs/modules/README.md, docs/ROADMAP.md, docs/ARCHITECTURE.md
and docs/DATABASE.md. Do not write any code yet.

1. Summarise the project, the build order and the Phase 1 tasks in plain language.
2. List every conflict, gap or [OPEN]/[CONFIRM] item that affects Phase 1.
3. Look at the old folders C:\Users\Engineer\Desktop\Alovia\ml-test and ...\rag
   (read only) and tell me what you will copy into the new repo and where.
4. Propose the plan for the FIRST Phase 1 task only, following CLAUDE.md §4.
Then wait for my approval. Use "ACTION NEEDED" whenever you need me
(Supabase project, GitHub repo, keys).
```

## B. Every later session

```
Continue Alovia. Follow CLAUDE.md. Read CONTEXT.md, PROGRESS.md, the last HISTORY.md
entry and the ERROR_LOG lessons. Tell me where we are and propose the plan for the next
task in PROGRESS.md. Do not code until I approve.
```

## C. Review request (after a task)

```
Review the changes you just made as a senior engineer against /docs and the module spec.
Do not modify anything yet. Give findings with severity, recommended fixes, and which
documents need updating.
```

## D. Export for the planning chat

```
Give me the HISTORY.md entries since <date/session>, the current PROGRESS.md, and any
new ERROR_LOG entries, as one block I can paste into another chat for review.
```
