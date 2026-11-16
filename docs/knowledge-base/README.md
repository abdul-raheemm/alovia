# Knowledge base documents

- `knowledgebase.md` — the collection guide (v2.0). Rule changes since v2.0 are recorded in the KB progress file.
- `KB_PROGRESS_2026-10-22.md` — snapshot of the knowledge base `PROGRESS.md` (196 valid files: MedlinePlus 37, NHS 159). The live copy moves with the collection into `knowledge-base/PROGRESS.md`.

**After the move into the repo (Phase 1):** the old `rag/` folder becomes `knowledge-base/` (collection data at the top level, scripts in `knowledge-base/tools/`, old scripts in `knowledge-base/tools/archive/`). The commands in the KB progress file assume the old `alovia-rag` folder; run them from `knowledge-base/` and update the paths in that file when the move is done.

The knowledge base is used by Module 5 (RAG, Phase 7) and later by the Journey content provider. Collection continues in parallel with the build.
