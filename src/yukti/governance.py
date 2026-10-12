"""Transparent, multi-vector epistemic governance triage engine.

Flags are triage signals for human review; they NEVER approve claims automatically.
Replaces brittle token-entropy-only gating with multi-factor epistemic verification:
1. Provenance completeness (source, quotation/evidence, author)
2. Source credibility and trust scoring
3. Exact & semantic duplicate detection
4. Contradiction & polar conflict detection against validated long-term memory
5. Degeneracy, repetitive looping, and low-information-density detection
6. Hedging and ungrounded speculative assertion triage
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from collections.abc import Iterable
from typing import Any, NamedTuple


class TriageFlag(NamedTuple):
    code: str
    category: str  # 'provenance' | 'trust' | 'conflict' | 'quality' | 'epistemic'
    severity: str  # 'blocker' | 'warning' | 'info'
    explanation: str


def compute_content_hash(text: str, source: str = "") -> str:
    """Compute canonical SHA-256 hash for exact deduplication."""
    canonical = f"{text.strip().casefold()}|{source.strip().casefold()}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def extract_tokens(text: str) -> list[str]:
    """Tokenize into alphanumeric words of length >= 2."""
    return re.findall(r"[a-z0-9']{2,}", text.casefold())


def token_set(text: str) -> set[str]:
    return set(extract_tokens(text))


def assess(
    text: str,
    source: str = "",
    evidence: str = "",
    trust: float = 0.5,
    existing: Iterable[dict[str, Any]] | None = None,
    min_trust_threshold: float = 0.5,
) -> list[dict[str, str]]:
    """Run comprehensive governance triage across all epistemic dimensions.
    
    Returns a list of structured flag dictionaries.
    """
    flags: list[TriageFlag] = []
    text_clean = text.strip()
    source_clean = source.strip()
    evidence_clean = evidence.strip()

    # ---------------------------------------------------------
    # 1. Provenance & Attribution Checks
    # ---------------------------------------------------------
    if not source_clean:
        flags.append(
            TriageFlag(
                code="missing_source",
                category="provenance",
                severity="blocker",
                explanation="No source URL, DOI, or document identifier provided. Claim is completely unanchored.",
            )
        )
    elif not _is_plausible_source(source_clean):
        flags.append(
            TriageFlag(
                code="dubious_source_format",
                category="provenance",
                severity="warning",
                explanation="Source identifier does not look like a valid URL, DOI, ISBN, or recognized reference format.",
            )
        )

    if not evidence_clean:
        flags.append(
            TriageFlag(
                code="missing_evidence_quote",
                category="provenance",
                severity="warning",
                explanation="No verbatim quotation or page/section locator from the source was provided.",
            )
        )

    # ---------------------------------------------------------
    # 2. Source Credibility & Trust Assessment
    # ---------------------------------------------------------
    if trust < min_trust_threshold:
        flags.append(
            TriageFlag(
                code="low_source_trust",
                category="trust",
                severity="warning",
                explanation=f"Source trust score ({trust:.2f}) is below the required governance threshold ({min_trust_threshold:.2f}).",
            )
        )

    # ---------------------------------------------------------
    # 3. Content Quality, Degeneracy & Repetition Checks
    # (Addresses RM's HES loophole where repetitive noise or gibberish passes)
    # ---------------------------------------------------------
    tokens = extract_tokens(text_clean)
    if len(tokens) < 3:
        flags.append(
            TriageFlag(
                code="insufficient_claim_length",
                category="quality",
                severity="blocker",
                explanation="Claim is too brief (< 3 tokens) to represent a meaningful, verifiable knowledge assertion.",
            )
        )
    else:
        # Check repetitive loop / degeneracy (e.g. "apple apple apple 1 1 1 asdf")
        repetition_ratio = _calculate_token_repetition_ratio(tokens)
        if repetition_ratio > 0.5:
            flags.append(
                TriageFlag(
                    code="degenerate_repetition",
                    category="quality",
                    severity="blocker",
                    explanation=f"Abnormally high token repetition detected ({repetition_ratio:.1%}). Text exhibits degenerative looping.",
                )
            )

        # Check compression / vocabulary diversity ratio
        vocab_diversity = len(set(tokens)) / len(tokens)
        if len(tokens) >= 10 and vocab_diversity < 0.35:
            flags.append(
                TriageFlag(
                    code="low_lexical_diversity",
                    category="quality",
                    severity="warning",
                    explanation=f"Very low vocabulary diversity ({vocab_diversity:.1%}). Possible spam or boilerplate.",
                )
            )

    # ---------------------------------------------------------
    # 4. Epistemic Uncertainty & Hedging Checks
    # ---------------------------------------------------------
    hedges = _detect_hedging_phrases(text_clean)
    if hedges and not evidence_clean:
        flags.append(
            TriageFlag(
                code="ungrounded_speculation",
                category="epistemic",
                severity="warning",
                explanation=f"Speculative or unverified language detected ({', '.join(hedges)}) without supporting evidence quotation.",
            )
        )

    # ---------------------------------------------------------
    # 5. Overlap, Duplicate & Contradiction Triage against Existing Memory
    # ---------------------------------------------------------
    if existing:
        new_tokens = set(tokens)
        new_hash = compute_content_hash(text_clean, source_clean)

        for item in existing:
            item_text = item.get("text", "").strip()
            if not item_text:
                continue

            item_id = item.get("id", "?")
            item_source = item.get("source", "").strip()
            item_hash = item.get("content_hash") or compute_content_hash(item_text, item_source)

            # Exact duplicate check
            if new_hash == item_hash or text_clean.casefold() == item_text.casefold():
                flags.append(
                    TriageFlag(
                        code=f"exact_duplicate_of:{item_id}",
                        category="conflict",
                        severity="blocker",
                        explanation=f"Identical claim already recorded under item ID {item_id}.",
                    )
                )
                break

            # Near-duplicate & Contradiction triage
            old_tokens = token_set(item_text)
            union = new_tokens | old_tokens
            if union:
                jaccard = len(new_tokens & old_tokens) / len(union)
                is_conflict = _detect_conflict(text_clean, item_text)

                # Prioritize contradiction check: even with high token overlap, opposing claims are contradictions!
                if jaccard >= 0.35 and is_conflict:
                    flags.append(
                        TriageFlag(
                            code=f"possible_contradiction_of:{item_id}",
                            category="conflict",
                            severity="blocker",
                            explanation=f"Semantically opposing claim detected with item ID {item_id} (shared context overlap {jaccard:.1%}).",
                        )
                    )
                elif jaccard >= 0.75:
                    flags.append(
                        TriageFlag(
                            code=f"possible_duplicate_of:{item_id}",
                            category="conflict",
                            severity="warning",
                            explanation=f"High lexical similarity ({jaccard:.1%}) with item ID {item_id}.",
                        )
                    )
                    break

    return [{"code": f.code, "category": f.category, "severity": f.severity, "explanation": f.explanation} for f in flags]


# ----------------------------------------------------------------------
# Internal Helper Heuristics
# ----------------------------------------------------------------------

def _is_plausible_source(source: str) -> bool:
    """Check if source resembles a recognized reference (URL, DOI, ISBN, urn, file, doc)."""
    s = source.strip().lower()
    if s.startswith(("http://", "https://", "doi:", "urn:", "file://", "isbn:")):
        return True
    if re.search(r"10\.\d{4,9}/[-._;()/:a-z0-9]+", s):  # DOI pattern
        return True
    if len(s.split()) <= 6 and ("/" in s or "\\" in s or "." in s):  # File path or reference
        return True
    return False


def _calculate_token_repetition_ratio(tokens: list[str]) -> float:
    """Computes the fraction of tokens represented by top repeated elements."""
    if len(tokens) <= 3:
        return 0.0
    counts = Counter(tokens)
    most_common_count = counts.most_common(1)[0][1]
    return most_common_count / len(tokens)


def _detect_hedging_phrases(text: str) -> list[str]:
    """Detect ungrounded speculation or rumor patterns."""
    text_lower = text.casefold()
    hedges = [
        "rumored that",
        "some say that",
        "supposedly",
        "allegedly",
        "unconfirmed reports",
        "might possibly",
        "may perhaps",
        "it is speculated",
    ]
    return [h for h in hedges if h in text_lower]


def _detect_conflict(left: str, right: str) -> bool:
    """Evaluates whether two related claims exhibit opposing polarities or mutual exclusions."""
    negations = {"not", "never", "no", "cannot", "can't", "doesn't", "isn't", "wasn't", "won't", "neither"}
    left_words = set(re.findall(r"[a-z']+", left.casefold()))
    right_words = set(re.findall(r"[a-z']+", right.casefold()))

    left_has_neg = bool(left_words & negations)
    right_has_neg = bool(right_words & negations)
    if left_has_neg != right_has_neg:
        return True

    # Antonym / mutual exclusion pairs
    opposing_pairs = [
        ({"increase", "increases", "increased", "increasing"}, {"decrease", "decreases", "decreased", "decreasing"}),
        ({"rise", "rises", "rose", "rising"}, {"fall", "falls", "fell", "falling"}),
        ({"true", "valid", "correct"}, {"false", "invalid", "incorrect"}),
        ({"safe", "harmless"}, {"dangerous", "harmful", "toxic"}),
        ({"accelerate", "accelerated"}, {"decelerate", "decelerated"}),
        ({"positive"}, {"negative"}),
        ({"allowed", "permitted"}, {"forbidden", "prohibited", "banned"}),
    ]
    for group_a, group_b in opposing_pairs:
        if (left_words & group_a and right_words & group_b) or (left_words & group_b and right_words & group_a):
            return True

    return False
