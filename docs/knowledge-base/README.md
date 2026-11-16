# Knowledge base documents

- `knowledgebase.md` — the collection guide (v2.0). Rule changes since v2.0 are recorded in the KB progress file.
- `KB_PROGRESS_2026-10-22.md` — snapshot of the knowledge base `PROGRESS.md` (196 valid files: MedlinePlus 37, NHS 159). The live copy moves with the collection into `knowledge-base/PROGRESS.md`.

**Move into the repo (Phase 1 task):** the collection is copied from the old `rag/` folder (inside the repo root, git-ignored) into `knowledge-base/`: the contents of `rag/alovia-knowledge-base/` at the top level, `rag/*.py` in `knowledge-base/tools/`, old scripts in `knowledge-base/tools/archive/`. The four CSVs in the `rag/` root and the `rag/archive/` data folders are copied only after the owner decides. The commands in the KB progress file were written for an earlier folder name (`alovia-rag`); run them from `knowledge-base/` and update the paths in that file when the copy is done. After the copy, collection continues in `knowledge-base/`.

The knowledge base is used by Module 5 (RAG, Phase 7) and later by the Journey content provider. Collection continues in parallel with the build.
