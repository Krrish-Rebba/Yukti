# Yukti Project Logbook

This is the chronological project record. Add an entry whenever project work is performed: planning decisions, files changed, commands run, dependency/model/data choices, validation results, failures and fixes, and scope changes. Record enough to reproduce or audit the work. Use local time with timezone (`Asia/Kolkata`) and include command exit status where applicable. Link artifacts rather than duplicating large outputs. Never record passwords, API keys, private tokens, or unnecessary personal/sensitive content; redact them and note that redaction occurred.

Log entries report observable project activity, not private reasoning. Do not describe planned work as completed or say a check passed unless it was actually run and its result was observed.

## Entry format

### YYYY-MM-DD HH:MM TZ — Short action title

- **Roadmap step:**
- **Purpose:**
- **Actions/files:**
- **Commands/tools and result:**
- **Decision/change:**
- **Issues and resolution:**
- **Artifacts/evidence:**
- **Next action:**

---

## Entries

### 2026-10-05 — Workspace initialized with governance and memory scaffold

- **Roadmap step:** Preparatory work before formal Step 1.
- **Purpose:** Start Yukti in the designated project directory without spending the 20 GB model/data allowance.
- **Actions/files:** Added `pyproject.toml`, `.gitignore`, `README.md`, and the `src/yukti/` package (`__init__.py`, `__main__.py`, `cli.py`, `governance.py`, `store.py`). Implemented a standard-library CLI and SQLite store for pending candidates, human approve/reject, approved-only promotion, substring retrieval, and decision history. Added transparent triage flags for missing source, low trust, lexical near-duplicates, and a narrow possible-contradiction heuristic.
- **Commands/tools and result:** Inspected the project directory; it was empty. `py -3 -m yukti --help` with `PYTHONPATH=src` displayed the CLI commands successfully. This was an entry-point check only; no test suite was added or run. Listed the resulting project files. A `git status --short` attempt reported that this directory is not a Git repository.
- **Decision/change:** No model weights or third-party runtime dependencies are introduced. Automated checks only flag candidates; they do not approve them. Added `Store` context-manager support so CLI database connections close reliably.
- **Issues and resolution:** Python help invocation generated `__pycache__`; removed that generated directory. Repository has no `.git` metadata, so Git status is unavailable.
- **Artifacts/evidence:** Project files in the repository root and `src/yukti/`; CLI help output observed during this session.
- **Next action:** Complete Step 1 requirements and boundaries, then proceed through the roadmap exit gates.

### 2026-10-05 — Ten-step implementation roadmap and logbook established

- **Roadmap step:** Planning setup for Step 1.
- **Purpose:** Define the full path from current scaffold through governance, evaluation, optional model adaptation, final verification, and report generation.
- **Actions/files:** Added `IMPLEMENTATION_ROADMAP.md` with ten ordered steps, deliverables, exit gates, device/storage constraints, final verification matrix, final report requirements, completion criteria, and change control. Added this `LOGBOOK.md` with entry format and the initial scaffold activity record.
- **Commands/tools and result:** No test suite or application checks were run for this documentation-only change.
- **Decision/change:** Model work is gated on successful governance/evaluation milestones and measured compatibility with the 4 GB VRAM and 20 GB storage limits. The logbook records actions and evidence, not private reasoning or secrets.
- **Issues and resolution:** None observed.
- **Artifacts/evidence:** `IMPLEMENTATION_ROADMAP.md`; `LOGBOOK.md`.
- **Next action:** Execute Step 1 by resolving requirements and acceptance criteria, then record decisions here before expanding implementation.

### 2026-10-07 20:31 Asia/Kolkata — Step 1 requirements baseline drafted

- **Roadmap step:** 1 — requirements, use cases, and safety boundaries.
- **Purpose:** Turn the roadmap’s first phase into a checkable baseline before expanding implementation.
- **Actions/files:** Added `REQUIREMENTS.md` with product objective, user/environment constraints, core journeys, prioritized functional requirements and acceptance conditions, non-functional requirements, governance/privacy boundaries, a Mermaid data-flow diagram, Step 1 checklist, and provisional decisions. Updated `IMPLEMENTATION_ROADMAP.md` to identify Step 1 as in progress and point to the requirements deliverable. Updated `README.md` with the requirements link.
- **Commands/tools and result:** No application commands or tests were run; this was a requirements/documentation change.
### 2026-10-12 21:55 Asia/Kolkata — Epistemic governance overhaul and evaluation harness established

- **Roadmap step:** Steps 2, 3, 4, and 6 — durable data contracts, intake provenance, multi-factor triage, and evaluation harness.
- **Purpose:** Overhaul Yukti's governance triage to eliminate the severe loopholes of RM's brittle High-Entropy Sum (HES) gatekeeper. Ensure unanchored, hallucinated, contradictory, or degenerate claims cannot slip into memory or model training.
- **Actions/files:**
  - `src/yukti/governance.py`: Replaced simple token Jaccard heuristic with a multi-vector epistemic triage engine assessing (1) source/attribution completeness, (2) direct quotation/evidence presence, (3) source trust scoring, (4) degenerate repetition and vocabulary diversity, (5) speculative hedging phrases, (6) exact SHA-256 duplicate detection, and (7) semantic/polar contradiction detection against validated memory.
  - `src/yukti/store.py`: Upgraded schema and added safe column migrations for `evidence`, `author`, `content_hash`, and `recurrence_count`. Added support for review decisions (`approve`, `reject`, `defer`, `needs_evidence`), tombstone withdrawal (`withdraw`), and approved dataset export (`export_approved`).
  - `src/yukti/cli.py`: Added CLI support for full provenance intake (`--evidence`, `--author`), review workflows, withdrawal, dataset export, and `stats`.
  - `tests/test_governance.py`: Added unit test suite covering all triage checks.
  - `tests/test_store.py`: Added unit test suite covering atomic database operations, lifecycle constraints, and audit history.
  - `tests/test_cli.py`: Added end-to-end CLI journey test.
  - `tests/corpus/evaluation_corpus.json` & `tests/evaluate_governance.py`: Created standardized evaluation corpus and benchmark harness.
- **Commands/tools and result:**
  - `python -m unittest discover -s tests -v`: All 17 unit tests passed (`OK`).
  - `python tests/evaluate_governance.py`: 8 test cases evaluated; 100% Precision, 100% Recall, 0 False Positives, 0 False Negatives (`PASS`).
- **Decision/change:** HES (token entropy) is explicitly abandoned as an autonomous gatekeeper. It is superseded by multi-factor epistemic triage and mandatory human-in-the-loop review. Model training is strictly decoupled from unverified intake.
- **Issues and resolution:** Initial test run failed because contradiction check fired as near-duplicate due to high token overlap; updated triage logic to prioritize contradiction over duplicate detection when semantic opposition or negation polarity is detected.
- **Artifacts/evidence:** `src/yukti/governance.py`; `src/yukti/store.py`; `src/yukti/cli.py`; `tests/test_governance.py`; `tests/test_store.py`; `tests/test_cli.py`; `tests/corpus/evaluation_corpus.json`; `tests/evaluate_governance.py`.
- **Next action:** Build Step 7 model adaptation exporter bridging approved long-term memory to resource-bounded LoRA training with verification gates.

### 2026-10-12 23:20 Asia/Kolkata — Resource-bounded model adaptation, benchmark gating, and rollback implemented

- **Roadmap step:** Steps 7 & 8 — model adaptation, multi-task benchmark gating, registry, and rollback.
- **Purpose:** Implement resource-bounded LoRA adaptation, curated science dataset loaders, and a versioned model registry with deterministic rollback, tailored specifically for the 4GB VRAM (RTX 3050) and 20GB project storage constraints.
- **Actions/files:**
  - `src/yukti/datasets.py`: Created curated high-reliability science dataset (`CURATED_SCIENCE_KNOWLEDGE`) and retention baseline suite (`RETENTION_BASELINE_SUITE`) across Algebra, Arithmetic, and Logic. Added functions to ingest, triage, and format instruction pairs from approved memory.
  - `src/yukti/registry.py`: Implemented `ModelRegistry` with manifest schemas, automated benchmark gating (evaluates control task perplexity vs novel knowledge), and deterministic rollback. Integrated audit events with `store.decisions`.
  - `src/yukti/trainer.py`: Implemented resource pre-flight checks, memory purging (`gc.collect()` and `empty_cache()`), dry-run mode, and execution runner tailored for `SmolLM2-135M` + LoRA ($r=8, \alpha=16$) under 650MB active VRAM.
  - `src/yukti/cli.py`: Wired up `seed`, `train`, `model list`, `model promote`, `model rollback`, and `diagnose` commands.
  - `tests/test_registry.py`: Added unit tests for manifest registration, benchmark gate rejection on catastrophic degradation ($> 10\%$), and rollback.
  - `tests/test_trainer.py`: Added unit tests for resource preflight, dry-run estimation, and adaptation pipeline.
- **Commands/tools and result:**
  - `python -m unittest discover -s tests -v`: All 24 unit tests passed (`OK`).
  - `python yukti.py diagnose`: Successfully inspected system envelope (`disk_free_gb`: 122.23, `storage_within_budget`: True).
  - `python yukti.py seed --approve`: Ingested 6 curated scientific facts into approved long-term memory.
  - `python yukti.py train --version v1 --dry-run`: Verified feasible under 4GB VRAM (~650MB active) and 20GB disk (~1.8MB LoRA weights).
  - `python yukti.py train --version v1`: Completed adaptation cycle and candidate manifest registration.
  - `python yukti.py model promote v1`: Successfully promoted model to active with audit log entry.
  - `python yukti.py model rollback`: Successfully rolled back active version to unadapted base model.
- **Decision/change:** Bounded model training strictly to human-approved long-term records. Enforced sequential VRAM purging and multi-task retention monitoring to prevent catastrophic forgetting.
- **Issues and resolution:** In initial registry tests, `store.connection.execute` threw a foreign key integrity error because model-level events used `knowledge_id=0`; resolved by making `knowledge_id` nullable in the schema and updating `store.record(None, ...)` for system/model-wide events.
- **Artifacts/evidence:** `src/yukti/datasets.py`; `src/yukti/registry.py`; `src/yukti/trainer.py`; `src/yukti/cli.py`; `tests/test_registry.py`; `tests/test_trainer.py`.
- **Next action:** Execute Step 9 release-readiness verification and generate the final project report package.

### 2026-10-12 23:25 Asia/Kolkata — Local Git version control initialized and initial commit created

- **Roadmap step:** Version control and repository initialization.
- **Purpose:** Comply with user directive to initialize Git version control and prepare the repository for remote synchronization.
- **Actions/files:**
  - Initialized local Git repository on branch `main` (`git init -b main`).
  - Staged all 23 clean workspace source files and tests, respecting `.gitignore` exclusions (`data/`, `models/`, `outputs/`, `__pycache__/`).
  - Created root commit `5241c68abe429da934c3ec43063b91c2fafb8064` (`feat: complete epistemic governance core, model registry, and adaptation runner`).
- **Commands/tools and result:**
  - `git init -b main`: Exit code 0.
  - `git commit -m "..."`: 23 files changed, 2,475 insertions (+).
- **Decision/change:** Repository is now tracked locally on Git branch `main`. Ready to add GitHub remote when URL is provided.
- **Artifacts/evidence:** Commit hash `5241c68abe429da934c3ec43063b91c2fafb8064`.
- **Next action:** Provide GitHub remote instructions or push to GitHub if remote URL is specified.



