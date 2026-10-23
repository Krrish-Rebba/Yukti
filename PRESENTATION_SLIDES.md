# Yukti: Presentation Slide Deck

**Title:** Yukti: Resource-Bounded Epistemic Governance & Continuous Adaptation  
**Authors:**  
- **Krrish Rebbawar** (1012412134)  
- **Pranav Chandane** (1012412146)  
- **Jayosmit Shinde** (1012412145)  
**Interactive Web Deck:** Open [`presentation/index.html`](presentation/index.html) in any browser.  
**Hardware Profile:** NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM ceiling), PyTorch 2.6.0+cu124, <= 20GB disk allowance.

---

## Slide 1: Title & Author Showcase
- **Headline:** Yukti: Resource-Bounded Epistemic Governance & Continuous Adaptation
- **Subtitle:** Bridging edge-constrained dual-SLM distillation into an inspectable, provably grounded continual learning architecture for small language models.
- **Authors & Roles:**
  - **Krrish Rebbawar** (1012412134) — Lead Architecture, Epistemic Core & Store Persistence
  - **Pranav Chandane** (1012412146) — Entropy Normalization, Dual-Bound Calibration (PR #1)
  - **Jayosmit Shinde** (1012412145) — Evaluation Harness, Benchmark Suites & Regression Gates
- **Key Constraints:**
  - 4096 MiB VRAM Ceiling (NVIDIA RTX 3050 Laptop GPU)
  - 20.0 GB Storage Allowance (Zero weight bloat, ~1.8 MB LoRA checkpoints)
  - 100% Local-First & Zero-Cloud Dependency

---

## Slide 2: The Core Problem & Motivation
- **The Continual Learning Dilemma:** How can small language models continuously assimilate new domain knowledge without suffering catastrophic forgetting or propagating toxic hallucinations?
- **Failure of Current Cloud Paradigms (e.g. MIT SEAL):**
  - Requires massive 80GB GPU clusters running heavy Reinforcement Learning (PPO) policy rollouts.
  - Dependent on held-out external validation sets with algorithmic reward scoring for every proposed edit.
  - Monolithic self-editing creates progressive drift when corrupted edits degrade generator capacity.
- **Our Goal:** A local-first, mathematically sound architecture running on consumer edge devices with zero outer RL rollout overhead.

---

## Slide 3: The 6-Phase Engineering Progression
1. **Phase 1: 4GB Hardware Constraint Optimization & Asymmetric Dual-SLM**
   - Teacher (`SmolLM2-360M-Instruct`) frozen in 4-bit NF4; Student (`SmolLM2-135M`) in 4-bit with LoRA ($r=8, \alpha=16$).
   - Sequential In-Memory Purging (`gc.collect()` + `cuda.empty_cache()`) bounds peak VRAM to $< 1.85$ GB.
2. **Phase 2: Information-Theoretic Gatekeeping (High-Entropy Sum)**
   - Extracted raw generation logits; computed token Shannon entropy $H(t) = -\sum P \log_2 P$.
   - Sorted and summed top 20% tokens ($\text{HES} \ge 10.0$ bits) to discard repetitive babble.
3. **Phase 3: Continual LoRA Adaptation Across 9 Domains (CS1–CS9)**
   - Sequentially adapted across Algebra, French/German syntax, Fact Flooding, Poetry, Assembly.
   - **CS6 Discovery:** Adversarial "1+1=3" passed HES because reasoning format was structured, proving token entropy does not reflect truth.
4. **Phase 4: Full-Parameter Collapse Boundary Experiment (CS10)**
   - Removed LoRA; trained all 135M base parameters on noise. Gradients exploded to `NaN` in 15 steps.
   - Proved LoRA subspace projection $W = W_0 + \frac{\alpha}{r} BA$ mathematically shields base manifold $W_0$.
5. **Phase 5: Grounded Passage Incorporation & Contributor Bounds Calibration (CS14 & CS15)**
   - **CS14:** Scientific passage (Quantum Vacuum Fluctuations); true perplexity dropped by -35.67 PPL while control algebra retained ($31.70 \to 30.15$ PPL).
   - **CS15 (PR #1 by Pranavhc):** Normalized mean entropy and dual-bounds $[u_{\min}, u_{\max}]$. Fixed stalling bug ($u_{\max}=2.40$ vs natural floor of $3.0-6.2$ bits) and achieved 60% retention under $[2.0, 5.5]$.
6. **Phase 6: The Epistemic Shift — Transition to Yukti**
   - Replaced single-point entropy filtering with durable Epistemic Governance: decoupled staging memory, provenance attribution, multi-vector triage, benchmark regression gates, and deterministic model rollback.

---

## Slide 4: Empirical Milestone Deep-Dive: CS14 Passage Grounding
- **The Scientific Grounding Text:** "Non-adiabatic boundary acceleration in the Dynamical Casimir Effect and Hawking horizon mode-splitting generates spontaneous continuous-variable bipartite entanglement violating classical shot-noise limits..."
- **Physical Verification via `audit_cs14.py`:**
  - Held-Out Quantum QA Cross-Entropy: $5.9552 \to 5.8582$ ($\Delta = -0.0970$)
  - Held-Out Quantum QA Token Accuracy: $30.60\% \to 31.34\%$ ($\Delta = +0.74\%$)
  - True Perplexity ($e^L$): $385.76 \to 350.10$ ($\Delta = -35.67$ PPL)
  - Control Algebra Baseline: $31.70 \to 30.15$ PPL (Capability preserved and slightly improved!)

---

## Slide 5: The Full-Parameter Collapse Discovery (CS10)
- **Experiment:** Train all 135M base parameters of `SmolLM2-135M` without LoRA on repetitive noise.
- **Empirical Dynamics:**
  - Steps 1–5: Loss instability.
  - Step 15: Mathematical overflow $\to$ `Loss: NaN`.
  - Invalidation: Model weights (`model.safetensors`, 269 MB) completely scrambled; outputs degenerated to `[NaN]`.
- **LoRA Protection Mechanism:** In LoRA, base weights $W_0$ are frozen. Gradient updates are restricted to $B \cdot A$ ($r=8$). Even if an adapter absorbs noise (CS9), $W_0$ remains pristine, allowing instant deactivation or rollback.

---

## Slide 6: The Epistemic Overhaul — Transition to Yukti
- **Why Autonomous Entropy Sums Failed:** High entropy can be generated by hallucinations, ungrounded speculation, or false proofs just as easily as novel facts.
- **Yukti's Decoupled Epistemic Core:**
  1. **Two-Tier Memory Hierarchy:** Candidate claims are staged in `working` memory. Only human-reviewed and approved claims are promoted to `long_term` memory.
  2. **ACID SQLite Persistence:** Immutable schema tracking `text`, `source`, `evidence`, `author`, `trust`, and `content_hash`.
  3. **Multi-Vector Epistemic Triage:** Replaces scalar entropy with deterministic semantic checks.
  4. **Retention Benchmark Gating:** Candidate adapters are evaluated against Algebra, Arithmetic, and Logic suites; $>10\%$ degradation triggers automatic rejection.
  5. **Deterministic Rollback:** Atomic reversion to unadapted base model via `yukti model rollback`.

---

## Slide 7: Multi-Vector Epistemic Triage Engine Formulations
| Check Code | Category | Severity | Algorithmic Evaluation |
| :--- | :--- | :--- | :--- |
| `missing_source` | Provenance | Blocker | Validates presence of valid URL, DOI, ISBN, or document ID |
| `missing_evidence_quote` | Provenance | Warning | Verifies direct quotation or page/section locator |
| `low_source_trust` | Trust | Warning | Flags sources with trust coefficient below threshold ($< 0.50$) |
| `exact_duplicate` | Deduplication | Warning | Canonical SHA-256 match: `sha256(text\|source)` |
| `near_duplicate` | Deduplication | Warning | Lexical Jaccard token overlap $J(A, B) \ge 0.85$ |
| `possible_contradiction` | Conflict | Blocker | Antonym pairing and polarity negation against approved memory |
| `degenerate_repetition` | Quality | Blocker | Unigram entropy and repetition ratio catches CS10 noise loops |
| `ungrounded_speculation`| Epistemic | Warning | Regex detects epistemic hedging ("I believe", "maybe", "allegedly") |

---

## Slide 8: Empirical Validation & Diagnostic Telemetry
- **Test Suite Results:** 24 out of 24 unit tests passing cleanly in 34.8 seconds (`tests/`).
- **Standardized Evaluation Benchmark:** 8 out of 8 test cases passed on `tests/corpus/evaluation_corpus.json`:
  - Precision: **100.0%**
  - Recall: **100.0%**
  - False Positives: **0**
  - False Negatives: **0**
- **Hardware Envelopes:**
  - Active VRAM during training: ~650 MB
  - LoRA Adapter disk size: ~1.8 MB
  - Disk headroom: 122+ GB free (well within 20 GB allowance)

---

## Slide 9: Architectural Comparison Matrix
| Feature | Prior Empirical Prototype (RM) | Yukti Production Framework |
| :--- | :--- | :--- |
| **Governance Metric** | Single-point Shannon token entropy (HES) | **Multi-vector epistemic triage + human review** |
| **Memory Isolation** | Transient JSONL training records | **ACID SQLite with dual tiers (`working` / `long_term`)** |
| **Attribution** | None (unanchored prompt string) | **Mandatory URL/DOI, direct evidence quote, author & trust** |
| **Contradiction Defense**| Vulnerable to deceptive math (CS6) | **Antonym and polar negation checks against approved memory** |
| **Training Trigger** | Autonomous on every generated prompt | **Decoupled; explicit operator CLI invocation** |
| **Catastrophic Forgetting**| Vulnerable to representational collapse (CS10) | **Retention baseline suite with >10% rejection gate** |
| **Rollback Support** | Manual file deletion | **Deterministic, atomic CLI rollback (`yukti model rollback`)** |

---

## Slide 10: Future Steps, Goals & Strategic Milestones
- **Milestone 1 (Q1 2027) — Streaming Ingestion Daemon:** Background service streaming preprints from arXiv, bioRxiv, and PubMed directly into `working` memory with automated DOI resolution.
- **Milestone 2 (Q2 2027) — Neural Contradiction Retrieval:** Local quantized ONNX embedding model (`all-MiniLM-L6-v2`, < 80MB RAM) for sub-millisecond semantic search and polar NLI contradiction scoring across 100k+ claims.
- **Milestone 3 (Q3 2027) — Dynamic Multi-LoRA Routing:** Enable the 135M student model to host modular domain adapters simultaneously with zero inference weight merging.
- **Milestone 4 (Q4 2027) — Cryptographic Provenance Consensus:** Ed25519 digital signatures on all review decisions, enabling peer-to-peer verification across distributed edge nodes.

---

## Slide 11: Summary & Version Control
- **Primary Repository:** [Yukti on GitHub](https://github.com/Krrish-Rebba/Yukti)  
  *Contains complete epistemic governance engine, SQLite store, test suites, and model adaptation runner.*
- **Reference Milestone Prototype:** [SEAL-Dual-SLM on GitHub](https://github.com/Krrish-Rebba/SEAL-Dual-SLM)  
  *Contains full 15 case study records, LoRA checkpoints, and entropy calibration audits.*
- **Project Team:**
  - Krrish Rebbawar (1012412134)
  - Pranav Chandane (1012412146)
  - Jayosmit Shinde (1012412145)
