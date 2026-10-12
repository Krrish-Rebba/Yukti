# Yukti Implementation Roadmap

**Plan version:** 1.0  
**Project status:** Step 1 requirements baseline drafted; pilot subject and user review remain open  
**Primary constraint:** 20 GB maximum project storage allowance  
**Target hardware:** 16 GB system RAM; NVIDIA RTX 3050 with 4 GB VRAM; Ryzen 7 CPU  
**Operating principle:** Keep model use optional until the non-model governance and evaluation loop is useful and its resource cost has been measured.

## Product objective

Build a local-first research prototype that accepts candidate knowledge, preserves its provenance, applies inspectable governance checks, requires human approval before durable retention or model training, evaluates proposed model updates, and can restore a previously accepted version.

Yukti must distinguish *a candidate*, *an approved memory item*, and *knowledge used to train a model*. A heuristic score or model-generated judgment is evidence for a human decision, not proof that a claim is true, safe, or suitable for learning.

## Scope and constraints

- The first usable release is a local research tool, not a production service or autonomous self-training system.
- The current standard-library Python and SQLite scaffold remains the starting point.
- The authoritative storage budget is 20 GB for Yukti data, model files, caches, datasets, checkpoints, logs, and reports combined. Track actual size and leave headroom; do not download weights until their destination and size are known.
- GPU memory is limited to 4 GB. Benchmark small models and adapter-only training only after the governance workflow works. CPU operation should remain possible for non-training functions.
- Default operation should be offline after dependencies and any deliberately selected model are installed. Do not send user data to external services by default.
- No candidate is trained on, exported as approved knowledge, or placed in long-term memory until the required human review is recorded.
- Keep logs useful and auditable without storing credentials, access tokens, or unnecessary personal/sensitive content.

## Ten implementation steps

### 1. Freeze requirements, use cases, and safety boundaries — IN PROGRESS

**Work:** Define target users, supported knowledge-item types, source/provenance fields, trust semantics, review roles, allowed policy categories, threat assumptions, offline expectations, retention behavior, and success criteria. Decide which decisions can be automated (triage only) and which require a human. Confirm the 20 GB accounting method and the target Windows/Python/CUDA environment.

**Deliverables:** Requirements and decision register in `REQUIREMENTS.md`; data-flow sketch; threat and privacy notes; measurable prototype acceptance criteria; this roadmap updated with any agreed scope changes.

**Exit gate:** Each requirement is testable or explicitly marked research-only; no feature implies automatic truth verification or autonomous deployment. The selected initial use cases and non-goals are documented.

### 2. Establish repository, configuration, and durable data contracts

**Work:** Add versioned configuration, schema migration strategy, validated settings, structured error handling, a reproducible environment/dependency lock strategy, and database backup/export/import rules. Define stable schemas for candidates, sources, evidence, reviews, memory records, policies, runs, model versions, and audit events. Migrate existing SQLite tables safely as schemas evolve.

**Deliverables:** Data dictionary and migrations; configuration example; dependency and setup instructions; backup/restore format; storage accounting command or report.

**Exit gate:** A clean install can initialize the database reproducibly; migrations preserve existing records; invalid configuration is rejected clearly; backup and restore preserve IDs, provenance, and audit history.

### 3. Build candidate intake and provenance capture

**Work:** Implement validated candidate intake from the initial CLI and a documented import format. Capture source URI/identifier, publisher or author where available, observed/ingested timestamps, content hash, quoted evidence or locator, domain, language, and submitter. Record missing or unverifiable metadata instead of inventing it. Add duplicate detection that distinguishes exact duplicates from possible near-duplicates.

**Deliverables:** Intake workflow; provenance model; supported import/export format; duplicate candidate linking; helpful validation errors.

**Exit gate:** A candidate can be traced back to its submitted source and exact captured evidence; malformed inputs fail without partial writes; repeat submission is identified without silently discarding provenance.

### 4. Implement transparent governance and human review

**Work:** Expand the starter heuristic checks into separately configurable checks for provenance completeness, source trust rationale, evidence support, possible contradiction, duplication, freshness, sensitivity, and policy restrictions. Record each check name, version, inputs or safe references, result, and explanation. Add a review queue with approve, reject, request-more-evidence, and defer outcomes, reviewer identity, notes, and any required second review.

**Deliverables:** Governance rules and policy configuration; reviewer workflow; explainable check results; immutable review/audit events; clear separation of machine flags from reviewer decisions.

**Exit gate:** Automated checks cannot approve or promote data; every state transition has an actor and reason; a reviewer can inspect source/evidence and understand why each flag appeared; policy conflicts stop promotion pending review.

### 5. Complete working memory, long-term memory, and retrieval

**Work:** Define lifecycle and retention rules for pending, approved, rejected, expired, and withdrawn information. Support promotion only from approved records, provenance-preserving edits/supersession, deletion or withdrawal with an audit tombstone, text search, filters, and export. Keep working memory separate from long-term memory. Add semantic retrieval only if a measured use case justifies its extra model/storage cost.

**Deliverables:** Memory lifecycle service; search and inspection commands; export/backup workflow; retention and deletion documentation; storage statistics.

**Exit gate:** Rejected and pending records never appear as approved retrieval results; approved items retain provenance; withdrawal removes an item from active retrieval while preserving the required audit record; restore works from a backup.

### 6. Create the evaluation corpus and governance evaluation harness

**Work:** Assemble a small, versioned, locally stored test corpus with carefully labeled examples for supported use cases: strong and weak sources, missing evidence, exact/near duplicates, contradictions, stale claims, sensitive information, and policy conflicts. Include expected flags and reviewer outcomes, adjudication notes, and a holdout split. Build deterministic evaluation reports for precision/recall by check, false-positive/false-negative review, coverage, latency, and reviewer override rate. Keep the corpus within the storage cap and document licensing/permissions.

**Deliverables:** Versioned evaluation dataset and label guide; evaluator; baseline metrics; error analysis; repeatable commands and machine-readable outputs.

**Exit gate:** Dataset provenance and label decisions are documented; evaluation is repeatable; each governance change is compared to the recorded baseline; no broad safety or factuality claim is made from a small corpus.

### 7. Add optional, resource-bounded model adaptation

**Work:** Only after steps 1–6 pass, select a small model using a measured compatibility and size review. Record model license, source, exact revision, tokenizer, quantization, download size, and cache location. Build a training-data export that includes only reviewed, approved, in-scope examples and excludes withdrawn/rejected material. Implement adapter-only training with bounded sequence length, batch size, checkpoint frequency, disk headroom checks, and an explicit dry-run/estimate mode. Do not train automatically on intake.

**Deliverables:** Model selection record; pinned dependency/model configuration; approved-data exporter; bounded training runner; resource and provenance metadata for each training run.

**Exit gate:** A small end-to-end adapter run completes within measured RAM/VRAM/disk bounds, or a documented compatibility failure prevents training safely; training data can be traced to approvals; the base model remains untouched.

### 8. Add benchmark gates, model registry, and rollback

**Work:** Evaluate each candidate adapter against fixed task-quality, knowledge-retention/regression, governance, and resource checks. Compare against the unchanged base and currently accepted adapter. Store immutable version manifests with hashes, parent version, training-data IDs, config, evaluation results, and artifact paths. Provide explicit promotion of a passing version and rollback to a previous accepted version; keep candidate and active versions distinct.

**Deliverables:** Benchmark suite and thresholds; model-version registry; promotion command/workflow; rollback workflow; artifact integrity verification.

**Exit gate:** A failed or incomplete evaluation cannot become active; a passing version can be selected explicitly; rollback restores the prior version and records the actor, reason, and artifact hashes.

### 9. Run final verification and release-readiness checks

**Work:** Run and record all final tests against a clean install and a copy of the project database. The final suite includes:

1. Unit tests for validation, governance rules, state transitions, policy precedence, retrieval filters, and serialization.
2. Database integration tests for migrations, atomic writes, audit completeness, backup/restore, and withdrawal behavior.
3. End-to-end workflow tests from intake through review, memory promotion, approved-data export, training-run registration, evaluation, model promotion, and rollback (using a tiny fixture model or mocked trainer where appropriate).
4. Security/privacy checks for path handling, untrusted imported content, secret redaction, access boundaries, deletion/withdrawal, and offline-default behavior.
5. Evaluation-corpus regression run with per-check metrics, false-positive/false-negative inspection, and reviewer override analysis.
6. Resource and storage checks on target hardware: peak RAM/VRAM, runtime, model/cache/checkpoint sizes, disk headroom, and behavior when limits are exceeded.
7. Reproducibility checks for a clean environment, pinned versions, deterministic data/evaluation exports where feasible, and documented nondeterminism where not.
8. CLI/documentation checks for each supported command, setup, backup/restore, failure messages, and recovery instructions.

Fix release-blocking findings and rerun the affected checks plus the complete regression suite. Record exact commands, environment, timestamps, exit codes, concise outputs, skipped checks and reasons, and remaining limitations in the logbook and test report. Do not claim a check passed without its recorded result.

**Deliverables:** Final test run artifacts; signed-off limitations/risk list; clean-install and recovery evidence; release candidate manifest; completed verification entries in the logbook.

**Exit gate:** All required checks pass or have an explicitly accepted, clearly bounded exception; no unresolved critical issue; disk and hardware usage remain within limits; another person can reproduce the verification from the recorded instructions.

### 10. Generate the final project report and handoff package

**Work:** Generate a dated report from the requirements register, implementation state, logbook, evaluation outputs, and final verification results. Include executive summary, architecture/data flow, implemented versus planned features, governance semantics, model/data provenance, test matrix and results, benchmark results with limitations, resource/disk measurements, known issues, reproduction steps, backup/restore and rollback instructions, and next-step recommendations. Cross-check report claims against evidence and attach or link the exact output artifacts. Freeze a release manifest with source revision, configuration, dependency/model revisions, hashes, and report version.

**Deliverables:** `reports/FINAL_REPORT.md` plus machine-readable result summaries and release manifest; completed logbook; reproducibility and recovery instructions; handoff checklist.

**Exit gate:** Every factual claim points to a recorded artifact or log entry; tests and skipped checks are stated accurately; model and data versions are identifiable; report generation is repeatable; unresolved limitations are visible.

## Milestone order and dependencies

Steps 1–2 establish scope and data safety. Steps 3–5 create the useful, human-governed knowledge loop. Step 6 measures whether governance is behaving as intended. Model work in steps 7–8 is conditional on those gates and on measured hardware/disk fit. Steps 9–10 close the project with evidence and a reproducible report. A failed exit gate returns the work to the relevant earlier step; step completion is recorded in the logbook.

## Project-wide completion criteria

- The complete human-reviewed knowledge lifecycle is usable and auditable.
- The evaluation corpus and regression results expose known strengths and failure modes.
- If model adaptation is feasible, each active model version is traceable, benchmark-gated, and reversible. If it is not feasible on this device, Yukti still delivers the governed memory prototype and documents the limitation without implying model adaptation succeeded.
- Measured total project storage stays at or below 20 GB, with working headroom documented.
- Final verification and report generation are complete, reproducible, and entered in the logbook.

## Change control

Any material change to scope, policies, storage/model choices, acceptance criteria, or roadmap order must be recorded in `LOGBOOK.md` with date/time, rationale, impact, and the decision maker. Update this roadmap when a change alters deliverables or exit gates. Keep completed entries and prior decisions; add corrections as new entries rather than silently rewriting history.
