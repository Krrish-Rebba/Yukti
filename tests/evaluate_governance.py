"""Evaluation harness for Yukti governance triage engine.

Runs against tests/corpus/evaluation_corpus.json and computes:
- Precision, Recall, and F1-score across all governance flags
- False-positive rate on verified gold facts
- Diagnostic report on flag detection accuracy
"""

import json
import sys
from pathlib import Path

# Ensure src in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from yukti.governance import assess, compute_content_hash


def run_evaluation() -> dict:
    corpus_file = Path(__file__).resolve().parent / "corpus" / "evaluation_corpus.json"
    with open(corpus_file, "r", encoding="utf-8") as f:
        cases = json.load(f)

    # Base reference item for duplicate/contradiction cases
    base_item = {
        "id": 1,
        "text": "The speed of light in a vacuum is defined as 299,792,458 meters per second.",
        "source": "https://www.bipm.org/en/measurement-units",
        "content_hash": compute_content_hash(
            "The speed of light in a vacuum is defined as 299,792,458 meters per second.",
            "https://www.bipm.org/en/measurement-units",
        ),
    }

    total_expected = 0
    true_positives = 0
    false_positives = 0
    false_negatives = 0

    detailed_results = []

    for case in cases:
        existing = [base_item] if case.get("context_existing_id") else []
        flags = assess(
            text=case["text"],
            source=case.get("source", ""),
            evidence=case.get("evidence", ""),
            trust=case.get("trust", 0.5),
            existing=existing,
        )
        observed_codes = set(f["code"] for f in flags)
        expected_codes = set(case.get("expected_flags", []))

        tp = len(observed_codes & expected_codes)
        fp = len(observed_codes - expected_codes)
        fn = len(expected_codes - observed_codes)

        true_positives += tp
        false_positives += fp
        false_negatives += fn
        total_expected += len(expected_codes)

        detailed_results.append({
            "id": case["id"],
            "name": case["name"],
            "expected": list(expected_codes),
            "observed": list(observed_codes),
            "match": (observed_codes == expected_codes),
        })

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 1.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 1.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    report = {
        "total_test_cases": len(cases),
        "total_expected_flags": total_expected,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "case_details": detailed_results,
    }
    return report


if __name__ == "__main__":
    rep = run_evaluation()
    print("=== YUKTI GOVERNANCE EVALUATION REPORT ===")
    print(f"Total Test Cases:       {rep['total_test_cases']}")
    print(f"Precision:              {rep['precision'] * 100:.1f}%")
    print(f"Recall:                 {rep['recall'] * 100:.1f}%")
    print(f"F1 Score:               {rep['f1_score'] * 100:.1f}%")
    print(f"False Positives:        {rep['false_positives']}")
    print(f"False Negatives:        {rep['false_negatives']}")
    print("\nCase Breakdowns:")
    for c in rep["case_details"]:
        status = "PASS" if c["match"] else "FAIL"
        print(f"  [{status}] {c['id']}: {c['name']}")
        if not c["match"]:
            print(f"     Expected: {c['expected']}")
            print(f"     Observed: {c['observed']}")
    
    if rep["false_positives"] == 0 and rep["false_negatives"] == 0:
        print("\nAll evaluation cases PASSED with 100% precision and recall.")
        sys.exit(0)
    else:
        sys.exit(1)
