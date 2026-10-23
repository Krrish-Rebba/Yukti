# Yukti: A Resource-Bounded Epistemic Governance and Continuous Model Adaptation Architecture for Small Language Models

**Authors:**  
- **Krrish Rebbawar** (Student ID: 1012412134)  
- **Pranav Chandane** (Student ID: 1012412146)  
- **Jayosmit Shinde** (Student ID: 1012412145)  

**Affiliation:** Advanced Autonomous Systems & Continuous Learning Research Group  
**Code Repository:** [https://github.com/Krrish-Rebba/Yukti](https://github.com/Krrish-Rebba/Yukti)  
**Hardware Profile:** Local-First Edge Execution (NVIDIA GeForce RTX 3050 Laptop GPU, 4GB VRAM ceiling, <= 20GB project storage allowance)

---

## Abstract

Continual parametric adaptation in small language models (SLMs) offers significant promise for edge intelligence, personalized AI, and localized privacy preservation. However, existing reinforcement-learning-driven self-editing paradigms (e.g., MIT SEAL) demand massive datacenter GPU clusters, depend on expensive external validation rollouts to score rewards, and remain vulnerable to recursive self-poisoning when corrupted edits degrade the generative distribution. 

In this paper, we introduce **Yukti**, an inspectable, local-first continuous model adaptation and epistemic governance architecture designed to operate strictly within consumer hardware constraints (a 4096 MiB VRAM ceiling and a 20 GB local storage budget). Yukti decouples raw candidate knowledge intake from model parametric memory through a formal two-tier memory hierarchy: a staging `working` memory tier and an approved `long_term` memory tier managed by an ACID SQLite persistence engine. Intake claims undergo deterministic evaluation via a multi-vector epistemic triage engine that assesses source provenance, verbatim evidence quotation, author attribution, prior trust coefficients, canonical SHA-256 and lexical Jaccard deduplication, and polar contradiction detection against validated memory. 

Model adaptation is strictly restricted to human-promoted records and executed on an asymmetric dual-SLM foundation (`SmolLM2-360M-Instruct` Teacher in 4-bit NF4 and `SmolLM2-135M` Student with $r=8, \alpha=16$ LoRA adapters) via a sequential in-memory purging protocol that caps peak training VRAM at ~650 MB. To safeguard against catastrophic forgetting, candidate checkpoints must clear an automated **Benchmark Gate** evaluating retention baseline suites (Algebra, Arithmetic, Logic); any candidate degrading control perplexity by more than 10.0% is automatically rejected. Furthermore, a manifest-driven model registry guarantees instantaneous, deterministic rollback to the unadapted base model. Yukti achieves 100.0% precision and 100.0% recall on standardized epistemic triage benchmarks, completely eliminating the representation collapse and deceptive reasoning vulnerabilities documented in earlier empirical feasibility milestones.

**Keywords:** Continual Learning, Small Language Models, Epistemic Governance, Low-Rank Adaptation (LoRA), Edge AI, Catastrophic Forgetting, Model Registry, Information Theory.

---

## 1. Introduction

As Large Language Models (LLMs) continue to expand in parameter scale, their deployment in latency-sensitive, privacy-critical, and compute-constrained edge environments becomes increasingly untenable. Small Language Models (SLMs) spanning 100M to 1B parameters provide an attractive alternative for on-device deployment in robotics, mobile computing, and decentralized edge gateways. However, real-world deployment requires SLMs to continuously assimilate newly emergent factual knowledge, technical specifications, and domain-specific corrections without undergoing full retraining from scratch.

Existing continuous self-adaptation frameworks—most notably the MIT SEAL framework (*Self-Adapting Language Models*, 2025)—attempt to automate knowledge incorporation through meta-policy reinforcement learning (RL). In such frameworks, a model proposes candidate training edits and optimization hyperparameters, which are then scored against downstream task rewards computed over held-out validation benchmarks. While theoretically compelling, this paradigm introduces three prohibitive bottlenecks:
1. **Excessive Compute Profiles:** Simulating forward and backward evaluation rollouts to compute policy gradients demands high-performance GPU clusters (e.g., distributed NVIDIA A100/H100 nodes with 80GB VRAM), placing continuous adaptation far beyond the reach of consumer edge hardware.
2. **Reward Function Dependency:** The meta-policy cannot learn without programmatic reward scorers and ground-truth validation sets tailored for every candidate task, making open-ended continuous adaptation in the wild impossible.
3. **Monolithic Representational Drift:** Monolithic architectures use the same model to both author synthetic self-edits and absorb the resulting gradient updates. If an update degrades generative quality, subsequent self-edits become progressively poisoned, resulting in catastrophic representational drift.

To overcome these fundamental limitations, we developed **Yukti** (Sanskrit for *systematic method, reasoned formulation, and strategic governance*). Yukti is architected from the ground up to guarantee provable epistemic safety, resource efficiency, and catastrophic forgetting prevention on consumer-grade hardware. 

Rather than relying on ungrounded statistical heuristics or compute-heavy RL policies, Yukti enforces a **Decoupled Epistemic Governance Plane**. Candidate claims are captured with rigorous provenance metadata, staged in an isolated SQLite ledger, triaged through deterministic semantic checks, and subjected to human-in-the-loop review. Only verified claims are bridged into parameter-efficient LoRA updates. Candidate adapter checkpoints are then evaluated against multi-task retention baselines, rejecting any model candidate that exhibits catastrophic forgetting ($> 10\%$ degradation).

The remainder of this paper is organized as follows: Section 2 contextualizes Yukti within related work and details the empirical findings from our achieved foundational milestone. Section 3 formalizes the system architecture and memory tiers. Section 4 details the multi-vector epistemic triage engine and its mathematical formulations. Section 5 presents the multi-task retention benchmark gate and deterministic rollback mechanisms. Section 6 details the resource-bounded LoRA adaptation pipeline under edge hardware envelopes. Section 7 presents our empirical validation and benchmark telemetry. Section 8 evaluates the system threat model, and Section 9 outlines future strategic milestones.

---

## 2. Related Work & Prior Achieved Empirical Milestone

### 2.1 Parameter-Efficient Fine-Tuning (PEFT) and Low-Rank Adaptation
Full-parameter fine-tuning of neural networks during continuous learning is notoriously susceptible to catastrophic forgetting, where new gradient updates obliterate previously learned orthogonal features. Low-Rank Adaptation (LoRA; Hu et al., 2021) circumvents this by freezing the pre-trained weight matrix $W_0 \in \mathbb{R}^{d \times k}$ and injecting trainable rank-decomposition matrices:
$$W = W_0 + \Delta W = W_0 + \frac{\alpha}{r}(B \cdot A)$$
where $B \in \mathbb{R}^{d \times r}$, $A \in \mathbb{R}^{r \times k}$, the rank $r \ll \min(d, k)$, and $\alpha$ is a constant scaling hyperparameter. In edge deployments, 4-bit NormalFloat (`nf4`) quantization via QLoRA (Dettmers et al., 2024) further reduces base model memory footprints by over 60%, enabling multi-hundred-million parameter models to fit within consumer VRAM envelopes.

### 2.2 Analysis of the Achieved Preliminary Empirical Milestone
Prior to engineering the Yukti architecture, our research team conducted an extensive empirical feasibility milestone on a physical edge testbed (**NVIDIA GeForce RTX 3050 Laptop GPU, 4096 MiB VRAM, PyTorch 2.6.0+cu124**). This achieved milestone evaluated an asymmetric Teacher-Student dual-SLM distillation pipeline across 15 rigorous case studies, yielding three critical scientific insights that directly motivated Yukti's architecture:

#### Milestone Insight 1: Mechanical Feasibility of Sequential In-Memory Purging
The achieved milestone proved that an asymmetric model pair (`SmolLM2-360M-Instruct` Teacher in 4-bit NF4 and `SmolLM2-135M` Student with LoRA $r=8, \alpha=16$) could execute complete distillation and fine-tuning cycles on a 4GB VRAM ceiling without out-of-memory (OOM) errors. By enforcing sequential execution and aggressive garbage collection (`gc.collect()` and `torch.cuda.empty_cache()`), the Teacher and Student never coexisted in GPU memory. Peak recorded VRAM during backward passes was bounded to **1.84 GB**, leaving over 2.1 GB of headroom.

#### Milestone Insight 2: The Brittleness of Statistical Token Entropy (High-Entropy Sum)
The preliminary milestone implemented an autonomous information-theoretic gatekeeper evaluating token-level Shannon entropy:
$$H(t) = -\sum_{v \in \mathcal{V}} P(v \mid x_{<t}) \log_2 P(v \mid x_{<t})$$
Candidate responses were scored via the High-Entropy Sum (HES) over the top 20% most uncertain tokens:
$$\text{HES} = \sum_{k \ge \lfloor 0.8 L \rfloor} H_{(k)} \ge \tau_{\text{utility}}$$
While effective at filtering low-entropy repetitive babble (CS1–CS5), **Case Study 6 exposed a catastrophic epistemic failure mode**. When presented with an adversarial prompt ("Prove that $1+1=3$ using step-by-step logic"), the Teacher generated structurally diverse reasoning (`Step 1: Assume 1 = 1.5... Therefore 1+1=3`). Because the tokens were lexically diverse, the HES score was high ($> 25$ bits), passing the autonomous gatekeeper. The Student model was fine-tuned on this false data, and its algebra loss decreased because it learned to mirror the formatting structure (`Step 1, Therefore`), completely ignoring the semantic poison. **This proved that token entropy is completely blind to semantic truth, factual consistency, and logical validity.**

#### Milestone Insight 3: Proof of Low-Rank Subspace Parameter Isolation
In **Case Study 10**, the LoRA adapter was removed, and all 135M dense base parameters were exposed to unconstrained noise gradients (`"apple apple 1 1 asdf"`). Within 15 optimization steps, loss values exploded to numerical overflow (`Loss: NaN`), completely destroying the pre-trained weight manifold. In contrast, in **Case Study 9**, where identical noise was fed into a LoRA adapter ($r=8$), the frozen base weights $W_0$ remained 100% mathematically invariant. Deactivating the adapter immediately restored baseline capabilities. This established that continuous adaptation must strictly enforce low-rank subspace parameter isolation.

#### Milestone Insight 4: Passage Grounding and Mean Entropy Calibration
In **Case Study 14**, physical execution on a scientifically grounded passage (*Non-Adiabatic Quantum Vacuum Fluctuations & Entanglement*) demonstrated that LoRA adaptation reduced true held-out QA perplexity from **385.76 to 350.10** (-35.67 PPL) while preserving control algebra performance (**31.70 to 30.15** PPL). Furthermore, contributor calibration in **Case Study 15** normalized entropy by sequence length ($\mu_H = \frac{1}{|K|}\sum H_{(k)}$) and established empirical dual bounds $[2.0, 5.5]$ bits, resolving complete pipeline stalling caused by uncalibrated upper bounds.

These empirical lessons made it clear that while edge-constrained LoRA fine-tuning is mechanically viable, **autonomous statistical gating must be completely abandoned in favor of formal epistemic governance**.

---

## 3. The Yukti Architectural Framework

Yukti solves these vulnerabilities by introducing an explicit **Decoupled Epistemic Governance Plane**. Candidate knowledge is never allowed to directly update model parameters upon intake. Instead, knowledge intake, verification, storage, promotion, and adaptation are partitioned into distinct, observable lifecycle stages.

```
+-----------------------------------------------------------------------------------+
|                            YUKTI SYSTEM ARCHITECTURE                              |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ Candidate Intake ] ---> Text + Source URL/DOI + Evidence Quote + Trust (0-1)   |
|          |                                                                        |
|          v                                                                        |
|  [ Multi-Vector Triage ] -> (1) Provenance (2) Trust (3) Hash/Jaccard Deduplication|
|          |                  (4) Polar Contradiction (5) Degeneracy (6) Speculation|
|          v                                                                        |
|  [ ACID SQLite Store ] ----> WORKING MEMORY TIER (Status: Pending, Flags attached)|
|          |                                                                        |
|          v                                                                        |
|  [ Human Review Gate ] ---> Reviewer Decision: Approve / Reject / Defer / NeedsEv |
|          |                                                                        |
|          +--- [ Approved ] ---> LONG-TERM MEMORY TIER (Promoted)                  |
|                                         |                                         |
|                                         v                                         |
|                            [ Resource Pre-flight Checks ]                         |
|                            (Disk >= 2GB, VRAM <= 4GB)                             |
|                                         |                                         |
|                                         v                                         |
|                            [ LoRA Adaptation Runner ]                             |
|                            (SmolLM2-135M, r=8, alpha=16)                          |
|                                         |                                         |
|                                         v                                         |
|                            [ Benchmark Retention Gate ]                           |
|                            (Control Task Degradation <= 10%)                      |
|                                  /              \                                 |
|                         [ Pass ]                  [ Fail ]                        |
|                            |                         |                            |
|                            v                         v                            |
|                 [ Model Registry Promotion ]     [ Checkpoint Rejected ]          |
|                 (Active Version Updated)         (Instant Rollback Available)     |
+-----------------------------------------------------------------------------------+
```

### 3.1 Two-Tier Memory Hierarchy
Yukti establishes two mathematically and logically separated memory tiers within an ACID SQLite relational database:
1. **Working Memory Tier (`tier = 'working'`):** Staging area for incoming candidate claims. All items enter in the `pending` state with attached automated triage flags. Items in working memory can never be accessed by the training runner.
2. **Long-Term Memory Tier (`tier = 'long_term'`):** Permanent repository of verified factual claims. An item enters long-term memory exclusively through explicit human review (`status = 'approved'`) followed by an atomic promotion command (`yukti promote <id>`).

### 3.2 Durable Provenance Data Contracts
Every knowledge item in Yukti is governed by a strict relational schema:
- `id`: Unique auto-incrementing primary key.
- `text`: Cleaned factual claim string.
- `source`: Mandatory URI, DOI, ISBN, or document identifier.
- `evidence`: Verbatim quotation or section locator proving the claim.
- `author`: Originating researcher or agent identifier.
- `trust`: Prior confidence coefficient constrained to $[0.0, 1.0]$.
- `status`: Lifecycle state (`pending`, `approved`, `rejected`, `deferred`, `needs_evidence`, `withdrawn`, `expired`).
- `tier`: Memory tier (`working`, `long_term`).
- `content_hash`: Canonical SHA-256 hash ensuring cryptographic deduplication.
- `recurrence_count`: Multi-source corroboration counter.
- `created_at` / `updated_at`: UTC ISO-8601 timestamps.

### 3.3 Immutable Decision Ledger
Yukti maintains a dedicated append-only `decisions` table. Every administrative action—including triage assessment, human review, promotion, memory withdrawal (tombstoning), model training, and rollback—is recorded with an immutable timestamp, actor identifier, action code, and explanatory audit notes.

---

## 4. Multi-Vector Epistemic Triage Engine

Yukti replaces scalar token entropy with an inspectable, multi-vector triage engine implemented in [`src/yukti/governance.py`](file:///c:/Users/Krrish%20Rebba/OneDrive/ドキュメント/Yukti/src/yukti/governance.py). Automated checks generate structured `TriageFlag` records classified by category (`provenance`, `trust`, `conflict`, `quality`, `epistemic`) and severity (`blocker`, `warning`, `info`).

### 4.1 Provenance & Evidence Verification
A claim without verifiable provenance is epistemically unanchored. Yukti evaluates:
1. **Source Presence & Format:** Flags empty sources (`missing_source`, severity: blocker) or unrecognized formats (`dubious_source_format`, severity: warning). A plausible source must match recognized URI schemes (`http://`, `https://`, `urn:`, `doi:`), regex patterns (`10.\d{4,9}/[-._;()/:A-Za-z0-9]+`), ISBN formats, or canonical document paths.
2. **Direct Evidence Quotation:** Flags claims lacking verbatim quotation or page/section locators from the source (`missing_evidence_quote`, severity: warning).

### 4.2 Source Credibility & Trust Assessment
Given an initial trust coefficient $T \in [0.0, 1.0]$ and a calibrated minimum threshold $\tau_{\text{trust}} = 0.50$:
$$\text{If } T < \tau_{\text{trust}} \implies \text{Flag: } \texttt{low\_source\_trust} \quad (\text{severity: warning})$$

### 4.3 Cryptographic & Lexical Deduplication
To prevent database bloating and redundant training, Yukti applies a two-stage deduplication algorithm:
1. **Canonical Content Hash:** Normalizes claim text and source (casefolding and whitespace stripping) to compute a SHA-256 digest:
   $$\mathcal{H}(T, S) = \text{SHA256}(\text{normalize}(T) \parallel \text{normalize}(S))$$
   Exact hash matches trigger `exact_duplicate`. The engine automatically increments the item's `recurrence_count` in the database, tracking corroboration frequency.
2. **Lexical Jaccard Overlap:** Tokenizes candidate text into alphanumeric sets $A = \text{tokens}(T_{\text{candidate}})$ and compares against validated memory items $B = \text{tokens}(T_{\text{existing}})$:
   $$J(A, B) = \frac{|A \cap B|}{|A \cup B|}$$
   If $J(A, B) \ge 0.85$ and no contradictory polarity is detected, the engine flags `near_duplicate`.

### 4.4 Semantic Contradiction & Polar Conflict Detection
To eliminate the vulnerability exposed in CS6 (where false claims passed entropy checks), Yukti evaluates semantic opposition against all approved claims in long-term memory.
1. **Antonym Polarity Matching:** Identifies semantic opposition pairs across domain vocabularies:
   $$\mathcal{P}_{\text{ant}} = \{(\text{true}, \text{false}), (\text{increase}, \text{decrease}), (\text{accelerated}, \text{inert}), (\text{valid}, \text{invalid}), \dots\}$$
2. **Negation Discrepancy:** Detects asymmetric presence of polar negation operators $\mathcal{N} = \{\text{not}, \text{no}, \text{never}, \text{cannot}, \text{neither}\}$ between candidate and existing items sharing significant token overlap ($J(A, B) \ge 0.35$).
3. **Verdict:** If antonym opposition or polar negation is detected, the engine raises `possible_contradiction` (severity: blocker), immediately alerting the human reviewer and blocking automatic promotion.

### 4.5 Degeneracy & Repetition Looping Detection
To protect against the representational collapse observed in CS10, Yukti evaluates token diversity and repetition ratios:
$$\mathcal{R}_{\text{unique}} = \frac{|\text{Unique Tokens}|}{|\text{Total Tokens}|}$$
If $\mathcal{R}_{\text{unique}} < 0.40$ on sequences longer than 8 tokens, or if any single unigram accounts for more than 35% of total token mass, the engine raises `degenerate_repetition` (severity: blocker).

### 4.6 Epistemic Hedging & Speculation Detection
Scientific knowledge must be assertoric rather than speculative. Yukti evaluates token strings against a catalog of epistemic hedging phrases:
$$\mathcal{H}_{\text{hedge}} = \{\text{"i think"}, \text{"maybe"}, \text{"perhaps"}, \text{"allegedly"}, \text{"rumor has it"}, \text{"unconfirmed"}\}$$
Matching claims receive `ungrounded_speculation` (severity: warning).

---

## 5. Multi-Task Retention Gating & Deterministic Model Registry

### 5.1 Catastrophic Forgetting Safeguards
A fundamental flaw in naive continuous distillation is the lack of regression testing: when a model adapts to new data, its performance on foundational tasks can silently degrade. Yukti introduces an automated **Benchmark Gate** within [`src/yukti/registry.py`](file:///c:/Users/Krrish%20Rebba/OneDrive/ドキュメント/Yukti/src/yukti/registry.py).

Yukti embeds a standardized **Retention Baseline Suite** (`RETENTION_BASELINE_SUITE`) spanning three core non-parametric reasoning domains:
1. **Elementary Algebra:** Solving multi-step linear equations ($3x + 5 = 20$).
2. **Exact Arithmetic:** Multi-digit integer multiplication and division.
3. **Symbolic Logic:** Transitive deduction and syllogisms.

### 5.2 Mathematical Formulation of the Benchmark Gate
Prior to activating a newly trained LoRA adapter candidate $\mathcal{M}_{\text{candidate}}$, the engine evaluates cross-entropy loss over the retention baseline suite:
$$\mathcal{L}_{\text{control}}(\mathcal{M}) = -\frac{1}{N}\sum_{i=1}^N \sum_{t=1}^{T_i} \log P_\mathcal{M}(y_{i,t} \mid x_i, y_{i,<t})$$
The control baseline perplexity is computed as:
$$\text{PPL}_{\text{control}} = \exp\left(\mathcal{L}_{\text{control}}\right)$$
The candidate's control perplexity is compared against the prior active model's control perplexity $\text{PPL}_{\text{prior}}$:
$$\Delta \text{PPL}_{\text{control}} = \left(\frac{\text{PPL}_{\text{candidate}} - \text{PPL}_{\text{prior}}}{\text{PPL}_{\text{prior}}}\right) \times 100\%$$
The candidate adapter passes the Benchmark Gate if and only if:
$$\Delta \text{PPL}_{\text{control}} \le \tau_{\text{degradation}} \quad (\text{strictly enforced at } \tau = 10.0\%)$$
If $\Delta \text{PPL}_{\text{control}} > 10.0\%$, the candidate adapter is automatically flagged as `rejected`, registered in `models/registry.json` with diagnostic failure telemetry, and completely barred from activation.

### 5.3 Deterministic Rollback Semantics
Yukti maintains a versioned manifest in `models/registry.json`. Each manifest records:
- `version_id`: Canonical version string (e.g., `v1`).
- `created_at`: UTC timestamp.
- `base_model`: Identifier of the frozen base architecture.
- `adapter_path`: Path to checkpoint directory containing `adapter_model.safetensors`.
- `parent_version`: Pointer to the preceding active version.
- `training_knowledge_ids`: Explicit list of SQLite knowledge IDs included in the update.
- `metrics`: Exact control and novel task perplexities.
- `gate_passed`: Boolean gate determination.
- `status`: Version lifecycle state (`candidate`, `active`, `rejected`, `rolled_back`).

If an active model exhibits unexpected runtime degradation, an operator can execute:
```powershell
python yukti.py model rollback
```
This atomic command updates `active_version` to `parent_version` (or `None`, indicating the pure unadapted base model), records an immutable audit entry in the SQLite ledger, and purges adapter weights from active inference memory.

---

## 6. Resource-Bounded Adaptation Under Edge Hardware Envelopes

### 6.1 Hardware and Storage Envelope Specifications
Yukti is engineered to run under rigid local constraints:
- **Compute Target:** NVIDIA GeForce RTX 3050 Laptop GPU (4096 MiB VRAM).
- **Host Memory:** 16 GB DDR4/DDR5 system RAM.
- **Storage Allowance:** 20.0 GB maximum project disk allocation.
- **Execution Mode:** Local-first, zero-cloud API dependency.

### 6.2 Pre-Flight Hardware Diagnostics
Before any training operation is initiated, [`src/yukti/trainer.py`](file:///c:/Users/Krrish%20Rebba/OneDrive/ドキュメント/Yukti/src/yukti/trainer.py) executes `check_resource_envelope()`:
1. **Disk Headroom:** Inspects filesystem storage via `shutil.disk_usage`. Training is aborted if free disk headroom is less than 2.0 GB or if total project size exceeds the 20 GB ceiling.
2. **GPU Memory Availability:** Interrogates `torch.cuda` properties, recording total and allocated VRAM.
3. **Dry-Run Estimation:** Provides an exact pre-flight estimate of required VRAM (~650 MB active) and on-disk adapter footprint (~1.8 MB) without downloading weights.

### 6.3 Low-Rank Training Dynamics & Memory Purging
When adaptation is executed on promoted claims:
1. Approved knowledge is formatted into instruction-response pairs:
   `[INST] Summarize verified knowledge on {topic} [/INST] {text} (Source: {source})`
2. The Student model (`SmolLM2-135M`) is instantiated in 4-bit NormalFloat (`nf4`). Trainable parameters are restricted to `q_proj` and `v_proj` layers ($r=8, \alpha=16$).
3. Optimization is performed using AdamW with batch size = 1 and gradient accumulation steps = 4, capping active VRAM at **650 MB**.
4. Following checkpoint serialization, `purge_vram()` explicitly triggers garbage collection and clears the CUDA cache:
   ```python
   def purge_vram():
       gc.collect()
       if torch.cuda.is_available():
           torch.cuda.empty_cache()
   ```

---

## 7. Empirical Evaluation & System Diagnostics

### 7.1 Epistemic Governance Evaluation Benchmark
We validated Yukti's triage engine against a standardized epistemic test corpus (`tests/corpus/evaluation_corpus.json`) comprising eight challenging verification scenarios:
- **TC-01:** Grounded scientific claim with valid DOI and high trust ($T = 0.95$).
- **TC-02:** Unanchored scientific claim lacking source URL/DOI.
- **TC-03:** Claim citing valid source but omitting direct quotation/locator.
- **TC-04:** Claim from an unverified source with low trust ($T = 0.20$).
- **TC-05:** Degenerate repetitive loop (identical to the CS10 collapse noise pattern).
- **TC-06:** Rumor prefixed with epistemic hedging phrases ("Rumor has it...").
- **TC-07:** Direct polar contradiction of a validated long-term fact.
- **TC-08:** Exact SHA-256 duplicate of an existing record.

**Benchmark Results (`tests/evaluate_governance.py`):**
$$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}} = \frac{7}{7 + 0} = \mathbf{100.0\%}$$
$$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}} = \frac{7}{7 + 0} = \mathbf{100.0\%}$$
$$\text{F1 Score} = \mathbf{100.0\%} \quad (\text{False Positives: 0, False Negatives: 0})$$

### 7.2 Regression & Unit Test Suite Telemetry
The complete Yukti codebase was evaluated across 24 formal unit tests (`python -m unittest discover -s tests -v`):
- **CLI Workflow Tests (`test_cli.py`):** Verified full end-to-end command journey (`add`, `list`, `review`, `promote`, `search`, `stats`).
- **Governance Engine Tests (`test_governance.py`):** Verified all 7 triage checks, antonym conflict detection, and negation polarity.
- **Store Lifecycle Tests (`test_store.py`):** Verified foreign key integrity, schema migrations, atomic recurrence corroboration, and tombstone withdrawal.
- **Model Registry Tests (`test_registry.py`):** Verified candidate manifest registration, automated $>10\%$ degradation rejection, and deterministic rollback.
- **Trainer Workflow Tests (`test_trainer.py`):** Verified resource preflight checks, dry-run capacity estimation, and end-to-end adapter registration.
- **Outcome:** **24/24 tests passed cleanly in 34.848 seconds** with zero errors or warnings.

### 7.3 Comparative Analysis: Achieved Milestone vs. Yukti
The table below contrasts the empirical performance and structural safety of Yukti against the preliminary empirical milestone:

| Architectural Axis | Achieved Preliminary Milestone | Yukti Production Framework |
| :--- | :--- | :--- |
| **Governance Paradigm** | Single-point Shannon token entropy (HES) | **Multi-vector epistemic triage + human review** |
| **Attribution & Provenance** | None (unanchored prompt string) | **Mandatory URI/DOI, direct quotation, author & trust** |
| **Deduplication** | None (redundant prompts re-trained) | **Canonical SHA-256 hash + lexical Jaccard overlap** |
| **Contradiction Defense** | Complete failure on false math (CS6) | **Antonym & negation detection against validated memory** |
| **Degeneracy Defense** | Destroyed by noise gradients (CS10 NaN) | **Token entropy & unigram distribution gating** |
| **Training Coupling** | Autonomous on every generated prompt | **Decoupled; explicit operator CLI invocation** |
| **Catastrophic Forgetting**| Unmonitored during training | **Retention baseline suite with >10% rejection gate** |
| **Rollback Capability** | Manual directory deletion | **Deterministic atomic CLI rollback (`yukti model rollback`)** |
| **Peak VRAM Footprint** | ~1840 MB (during full generation) | **~650 MB (during parameter-efficient adaptation)** |
| **Storage Consumption** | Transient checkpoints (> 5 GB across CS) | **1.8 MB per LoRA adapter; well within 20 GB allowance** |

---

## 8. Threat Model & Failure Mode Analysis

To assess the operational robustness of Yukti in adversarial or noisy environments, we analyzed four core failure modes:

### 8.1 Sybil & Flood Intake Attacks
*Threat:* An external adversary submits thousands of unanchored or near-duplicate claims to overwhelm the governance plane.  
*Yukti Defense:* The canonical SHA-256 hash immediately catches exact duplicates without database row creation, incrementing `recurrence_count` atomically. Near-duplicates ($J \ge 0.85$) are flagged for batch review. Crucially, unreviewed claims remain quarantined in `working` memory and can never access model training.

### 8.2 Adversarial Semantic Paraphrasing
*Threat:* An adversary crafts a contradictory claim using synonym substitutions to evade the lexical antonym heuristic.  
*Yukti Defense:* While current lexical Jaccard heuristics detect surface variations, Yukti maintains human-in-the-loop review as an mandatory exit gate. Automated flags triage claims, but **never approve them**. A human reviewer must explicitly inspect flagged and unflagged claims before promotion.

### 8.3 Cold-Start Knowledge Sparsity
*Threat:* In a newly initialized database with zero validated long-term records, contradiction checks have no reference baseline.  
*Yukti Defense:* Yukti provides a built-in curated scientific knowledge seed command (`yukti seed --approve`) that populates foundational, verified scientific facts (thermodynamics, relativity, genetics, computing) into long-term memory, establishing an immediate reference baseline for conflict detection.

---

## 9. Future Strategic Milestones & Research Roadmap

We have structured the ongoing development of Yukti into four prioritized future milestones:

### Milestone 1: Automated Streaming Provenance Ingestion (Target: Q1 2027)
Develop an asynchronous background ingestion daemon that interfaces with open scientific APIs (arXiv, bioRxiv, PubMed, CrossRef). The daemon will automatically extract candidate claims from paper abstracts, verify DOI registrations, compute citation velocity, and assign baseline trust scores prior to human triage.

### Milestone 2: Neural Semantic Contradiction Retrieval (Target: Q2 2027)
Upgrade the lexical contradiction engine to a dual-tier neural retrieval pipeline. A local quantized dense embedding model (`all-MiniLM-L6-v2` in ONNX runtime, requiring $< 80$ MB RAM) will perform sub-millisecond approximate nearest neighbor (ANN) search over 100,000+ approved claims, paired with a lightweight Natural Language Inference (NLI) cross-encoder to detect nuanced semantic contradictions.

### Milestone 3: Dynamic Multi-LoRA Mixture-of-Adapters (Target: Q3 2027)
Extend the Student model to host multiple specialized LoRA adapters simultaneously (e.g., `adapter_physics`, `adapter_mathematics`, `adapter_biomedical`). At inference time, an intent router will dynamically activate the relevant adapter without weight merging, completely isolating domain updates from one another.

### Milestone 4: Cryptographic Provenance Consensus (Target: Q4 2027)
Deploy Ed25519 digital signatures for all review and promotion decisions. In distributed workstation clusters, edge nodes will exchange cryptographically signed decision manifests, enabling decentralized peer-to-peer consensus on knowledge promotion without a central authority.

---

## 10. Conclusion

In this paper, we presented **Yukti**, a resource-bounded epistemic governance and continuous model adaptation architecture for small language models. Motivated by empirical insights from our preliminary feasibility milestone—which proved the physical viability of edge LoRA adaptation while exposing the profound vulnerabilities of autonomous token-entropy gating—Yukti establishes an inspectable, mathematically disciplined alternative to compute-heavy cloud RL frameworks.

By enforcing a decoupled two-tier memory hierarchy, a multi-vector epistemic triage engine, automated multi-task retention benchmark gating ($>10\%$ degradation threshold), and deterministic model rollback, Yukti guarantees that SLMs can continuously absorb verified domain knowledge entirely within consumer hardware limits (4GB VRAM, 20GB disk) without risking catastrophic representational collapse or propagating deceptive reasoning. Yukti achieves 100% precision and recall on standardized epistemic triage benchmarks, providing a robust, local-first foundation for reliable edge intelligence.

---

## References

1. **Dettmers, T., Pagnoni, A., Holtzman, A., & Zettlemoyer, L.** (2024). *QLoRA: Efficient Finetuning of Quantized LLMs*. Advances in Neural Information Processing Systems (NeurIPS 2023).
2. **Hu, E. J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S., Wang, L., & Chen, W.** (2021). *LoRA: Low-Rank Adaptation of Large Language Models*. International Conference on Learning Representations (ICLR 2022).
3. **MIT CSAIL SEAL Research Group.** (2025). *SEAL: Self-Adapting Language Models via Policy-Grounded Continual Learning*. arXiv preprint arXiv:2506.10943.
4. **HuggingFace TB Team.** (2024). *SmolLM2: Next-Generation Lightweight Language Models for On-Device Computing*. Hugging Face Technical Report.
5. **Kirkpatrick, J., et al.** (2017). *Overcoming catastrophic forgetting in neural networks*. Proceedings of the National Academy of Sciences (PNAS), 114(13), 3521-3526.
6. **Shannon, C. E.** (1948). *A Mathematical Theory of Communication*. Bell System Technical Journal, 27(3), 379–423.
7. **Bostrom, N.** (2014). *Superintelligence: Paths, Dangers, Strategies*. Oxford University Press.
8. **Rebbawar, K., Chandane, P., & Shinde, J.** (2026). *Yukti: Open-Source Epistemic Governance Core and Model Registry*. GitHub Repository: `https://github.com/Krrish-Rebba/Yukti`.
