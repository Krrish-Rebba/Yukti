import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import unittest
from yukti.governance import assess, compute_content_hash, _calculate_token_repetition_ratio


class TestGovernanceEngine(unittest.TestCase):
    def test_missing_source_flag(self):
        flags = assess(text="Water boils at 100 degrees Celsius at sea level.", source="")
        codes = [f["code"] for f in flags]
        self.assertIn("missing_source", codes)

    def test_missing_evidence_quote_flag(self):
        flags = assess(
            text="Water boils at 100 degrees Celsius at sea level.",
            source="https://en.wikipedia.org/wiki/Water",
            evidence="",
        )
        codes = [f["code"] for f in flags]
        self.assertIn("missing_evidence_quote", codes)

    def test_low_source_trust_flag(self):
        flags = assess(
            text="Water boils at 100 degrees Celsius at sea level.",
            source="https://unverified-blog.xyz",
            evidence="Boiling point is 100C",
            trust=0.25,
        )
        codes = [f["code"] for f in flags]
        self.assertIn("low_source_trust", codes)

    def test_degenerate_repetition_flag(self):
        # Reproducing the RM CS10 failure case where repetitive noise must be blocked
        noise_text = "apple apple apple 1 1 1 asdf apple apple apple 1 1 1"
        flags = assess(
            text=noise_text,
            source="https://example.org",
            evidence="noise data",
            trust=0.9,
        )
        codes = [f["code"] for f in flags]
        self.assertIn("degenerate_repetition", codes)

    def test_ungrounded_speculation_flag(self):
        speculative_text = "It is rumored that the discovery will change physics completely."
        flags = assess(
            text=speculative_text,
            source="https://tech-rumors.org",
            evidence="",  # no evidence quote
            trust=0.8,
        )
        codes = [f["code"] for f in flags]
        self.assertIn("ungrounded_speculation", codes)

    def test_exact_duplicate_detection(self):
        existing = [
            {
                "id": 1,
                "text": "The speed of light in vacuum is exactly 299,792,458 meters per second.",
                "source": "https://nist.gov/constants",
                "content_hash": compute_content_hash(
                    "The speed of light in vacuum is exactly 299,792,458 meters per second.",
                    "https://nist.gov/constants",
                ),
            }
        ]
        flags = assess(
            text="The speed of light in vacuum is exactly 299,792,458 meters per second.",
            source="https://nist.gov/constants",
            evidence="exact match",
            trust=0.95,
            existing=existing,
        )
        codes = [f["code"] for f in flags]
        self.assertIn("exact_duplicate_of:1", codes)

    def test_near_duplicate_detection(self):
        existing = [
            {
                "id": 5,
                "text": "Photosynthesis converts carbon dioxide and water into glucose and oxygen using sunlight.",
                "source": "https://biology.org/photosynthesis",
            }
        ]
        # High overlap wording
        candidate = "Photosynthesis converts carbon dioxide and water into glucose and oxygen with sunlight energy."
        flags = assess(
            text=candidate,
            source="https://nature.org/cells",
            evidence="Plants convert sunlight into glucose",
            trust=0.9,
            existing=existing,
        )
        codes = [f["code"] for f in flags]
        self.assertTrue(any(c.startswith("possible_duplicate_of:5") for c in codes))

    def test_contradiction_detection_negation(self):
        existing = [
            {
                "id": 10,
                "text": "The gravitational constant G is invariant across time and space.",
                "source": "https://physics.org/gr",
            }
        ]
        candidate = "The gravitational constant G is not invariant across time and space."
        flags = assess(
            text=candidate,
            source="https://alt-physics.org/paper",
            evidence="G fluctuates over time",
            trust=0.8,
            existing=existing,
        )
        codes = [f["code"] for f in flags]
        self.assertIn("possible_contradiction_of:10", codes)

    def test_contradiction_detection_antonyms(self):
        existing = [
            {
                "id": 12,
                "text": "Non-adiabatic mirror acceleration causes vacuum mode temperature to increase.",
                "source": "https://journals.aps.org/prl",
            }
        ]
        candidate = "Non-adiabatic mirror acceleration causes vacuum mode temperature to decrease."
        flags = assess(
            text=candidate,
            source="https://journals.aps.org/prd",
            evidence="mode temperature decreases",
            trust=0.85,
            existing=existing,
        )
        codes = [f["code"] for f in flags]
        self.assertIn("possible_contradiction_of:12", codes)


if __name__ == "__main__":
    unittest.main()
