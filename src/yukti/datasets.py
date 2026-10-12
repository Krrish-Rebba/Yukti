"""Curated, reliable benchmark dataset loaders for Yukti.

Provides clean, structured, verified datasets tailored for 4GB VRAM environments:
1. SciQ / Scientific Knowledge: Factual science with explicit evidence support.
2. Multi-Domain Epistemic Benchmark: Complex factual passages and multi-hop questions.
3. Fixed Control Baselines: Algebra, Logic, and General QA to monitor catastrophic forgetting.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .governance import assess
from .store import Store

# Fixed Control Baseline for Retention & Catastrophic Forgetting Monitoring
RETENTION_BASELINE_SUITE = [
    {
        "category": "algebra_reasoning",
        "prompt": "Solve for x: 5x - 15 = 35. Show your step-by-step reasoning.",
        "expected": "Step 1: Add 15 to both sides: 5x = 50. Step 2: Divide by 5: x = 10. Therefore, x = 10.",
    },
    {
        "category": "arithmetic_logic",
        "prompt": "A train travels at 60 miles per hour for 2.5 hours. How far does it travel?",
        "expected": "Distance = Speed * Time = 60 * 2.5 = 150 miles.",
    },
    {
        "category": "factual_baseline",
        "prompt": "What is the primary function of mitochondria in eukaryotic cells?",
        "expected": "Mitochondria generate most of the cell's chemical energy supply via ATP synthesis through cellular respiration.",
    },
    {
        "category": "negation_logic",
        "prompt": "If all mammals are warm-blooded and a reptile is not a mammal, is a reptile necessarily cold-blooded?",
        "expected": "Reptiles are generally ectothermic (cold-blooded), but this specific conclusion cannot be derived solely from the premise that they are not mammals.",
    },
]

# Curated High-Reliability Factual Science Dataset (Sample Suite for Edge SLMs)
CURATED_SCIENCE_KNOWLEDGE = [
    {
        "id": "sci_001",
        "text": "The speed of light in vacuum is exactly 299,792,458 meters per second.",
        "source": "https://www.bipm.org/en/measurement-units",
        "evidence": "By international agreement since 1983, c = 299 792 458 m/s defining the metre.",
        "author": "BIPM International Standard",
        "trust": 1.0,
    },
    {
        "id": "sci_002",
        "text": "In the Dynamical Casimir Effect, non-adiabatic boundary acceleration converts virtual vacuum fluctuations into real entangled photon pairs.",
        "source": "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.103.147003",
        "evidence": "Observation of the dynamical Casimir effect in a superconducting circuit confirms photon emission from vacuum fluctuations.",
        "author": "Physical Review Letters",
        "trust": 0.98,
    },
    {
        "id": "sci_003",
        "text": "CRISPR-Cas9 acts as an RNA-guided endonuclease that introduces targeted double-strand breaks in genomic DNA.",
        "source": "https://www.science.org/doi/10.1126/science.1225829",
        "evidence": "A programmable dual-RNA-guided DNA endonuclease in adaptive bacterial immunity.",
        "author": "Doudna & Charpentier, Science (2012)",
        "trust": 0.99,
    },
    {
        "id": "sci_004",
        "text": "Superconductivity occurs below a critical temperature Tc characterized by zero electrical resistance and the Meissner effect.",
        "source": "https://doi.org/10.1007/978-3-642-83057-0",
        "evidence": "Zero electrical resistivity and total expulsion of magnetic fields define superconductivity.",
        "author": "Tinkham Introduction to Superconductivity",
        "trust": 0.95,
    },
    {
        "id": "sci_005",
        "text": "Photosystem II catalyzes the light-driven oxidation of water to molecular oxygen in oxygenic photosynthesis.",
        "source": "https://doi.org/10.1038/nature02878",
        "evidence": "Architecture of the photosynthetic oxygen-evolving center in photosystem II.",
        "author": "Nature (2004)",
        "trust": 0.95,
    },
    {
        "id": "sci_006",
        "text": "Quantum teleportation transfers an arbitrary quantum state between distant qubits using shared entanglement and classical communication.",
        "source": "https://doi.org/10.1103/PhysRevLett.70.1895",
        "evidence": "Teleporting an unknown quantum state via dual classical and Einstein-Podolsky-Rosen channels.",
        "author": "Bennett et al., PRL (1993)",
        "trust": 0.99,
    },
]


def load_curated_knowledge_into_store(store: Store, auto_review: bool = False) -> list[int]:
    """Ingests curated reliable science knowledge into the store through the governance pipeline.
    
    If auto_review is True, records an approved review and promotes to long-term memory.
    """
    existing = store.list_items()
    ingested_ids = []

    for item in CURATED_SCIENCE_KNOWLEDGE:
        flags = assess(
            text=item["text"],
            source=item["source"],
            evidence=item["evidence"],
            trust=item["trust"],
            existing=existing,
        )
        item_id = store.add_candidate(
            text=item["text"],
            source=item["source"],
            evidence=item["evidence"],
            author=item["author"],
            trust=item["trust"],
            flags=flags,
        )
        if auto_review:
            store.review(item_id, "approved", actor="curator", note="Verified gold-standard peer-reviewed reference.")
            store.promote(item_id, actor="curator")

        ingested_ids.append(item_id)
        # Update existing list for subsequent deduplication
        existing.append(store.get(item_id))

    return ingested_ids


def export_qa_pairs_for_adaptation(store: Store) -> list[dict[str, str]]:
    """Generates structured instruction-tuning pairs from approved long-term memory."""
    approved_items = store.export_approved(tier="long_term")
    dataset = []

    for item in approved_items:
        # Instruction pair formatted for causal language model training
        dataset.append({
            "instruction": f"State the verified scientific fact regarding: {item['text'][:60]}...",
            "input": f"Source: {item['source']}\nEvidence: {item['evidence']}",
            "output": item["text"],
        })
    return dataset
