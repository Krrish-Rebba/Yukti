import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import os
import tempfile
import unittest
from yukti.store import Store


class TestStoreLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        self.tmp.close()
        self.db_path = self.tmp.name
        self.store = Store(self.db_path)

    def tearDown(self):
        self.store.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_add_and_get_candidate(self):
        flags = [{"code": "missing_evidence_quote", "category": "provenance", "severity": "warning", "explanation": "test"}]
        item_id = self.store.add_candidate(
            text="Quantum entanglement is observed in bipartite photon pairs.",
            source="https://nature.com/articles/example",
            evidence="entangled photon pairs were generated",
            author="physicist_1",
            trust=0.9,
            flags=flags,
        )
        item = self.store.get(item_id)
        self.assertIsNotNone(item)
        self.assertEqual(item["text"], "Quantum entanglement is observed in bipartite photon pairs.")
        self.assertEqual(item["status"], "pending")
        self.assertEqual(item["tier"], "working")
        self.assertEqual(item["evidence"], "entangled photon pairs were generated")
        self.assertEqual(item["recurrence_count"], 1)
        self.assertEqual(len(item["flags"]), 1)

    def test_recurrence_corroboration(self):
        # Adding exact same text and source should increment recurrence_count
        id1 = self.store.add_candidate(
            text="General relativity predicts gravitational time dilation.",
            source="https://arxiv.org/abs/example",
            evidence="time passes slower in strong gravitational fields",
        )
        id2 = self.store.add_candidate(
            text="General relativity predicts gravitational time dilation.",
            source="https://arxiv.org/abs/example",
            evidence="time passes slower in strong gravitational fields",
        )
        self.assertEqual(id1, id2)
        item = self.store.get(id1)
        self.assertEqual(item["recurrence_count"], 2)

    def test_review_lifecycle_transitions(self):
        item_id = self.store.add_candidate(text="Candidate statement for review.", source="https://doi.org/10.1000/182")
        
        # Test defer
        self.store.review(item_id, "deferred", actor="senior_auditor", note="Needs more peer reviews")
        item = self.store.get(item_id)
        self.assertEqual(item["status"], "deferred")

        # Test request evidence
        self.store.review(item_id, "needs_evidence", actor="senior_auditor", note="Please provide direct citation")
        item = self.store.get(item_id)
        self.assertEqual(item["status"], "needs_evidence")

        # Test approve
        self.store.review(item_id, "approved", actor="senior_auditor", note="Evidence verified")
        item = self.store.get(item_id)
        self.assertEqual(item["status"], "approved")

    def test_promotion_constraints(self):
        item_id = self.store.add_candidate(text="Unapproved candidate.", source="https://test.com")
        
        # Promoting pending item must raise ValueError
        with self.assertRaises(ValueError):
            self.store.promote(item_id, actor="researcher")

        # Approve then promote
        self.store.review(item_id, "approved", actor="researcher")
        self.store.promote(item_id, actor="researcher")
        
        item = self.store.get(item_id)
        self.assertEqual(item["tier"], "long_term")

        # Promoting already promoted item must raise ValueError
        with self.assertRaises(ValueError):
            self.store.promote(item_id, actor="researcher")

    def test_withdrawal_lifecycle(self):
        item_id = self.store.add_candidate(text="Erroneous claim to be retracted.", source="https://retracted-paper.com")
        self.store.review(item_id, "approved", actor="researcher")
        self.store.promote(item_id, actor="researcher")

        # Withdraw
        self.store.withdraw(item_id, actor="compliance_officer", reason="Paper retracted by journal.")
        item = self.store.get(item_id)
        self.assertEqual(item["status"], "withdrawn")

        # Withdrawn item must NOT appear in normal approved search
        results = self.store.search("Erroneous claim")
        self.assertEqual(len(results), 0)

    def test_search_and_export_approved(self):
        id1 = self.store.add_candidate(text="Helium has an atomic number of 2.", source="https://webelements.com")
        self.store.review(id1, "approved", actor="reviewer")
        self.store.promote(id1, actor="reviewer")

        id2 = self.store.add_candidate(text="Hydrogen has an atomic number of 1.", source="https://webelements.com")
        # id2 remains pending

        # Search should only return approved
        res = self.store.search("atomic number")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["id"], id1)

        # Export approved
        exported = self.store.export_approved(tier="long_term")
        self.assertEqual(len(exported), 1)
        self.assertEqual(exported[0]["id"], id1)

    def test_audit_decisions_integrity(self):
        item_id = self.store.add_candidate(text="Audit test claim.", source="https://audit.org")
        self.store.review(item_id, "approved", actor="auditor_jane", note="First approval")
        self.store.promote(item_id, actor="auditor_jane")
        
        history = self.store.decisions(item_id)
        actions = [entry["action"] for entry in history]
        self.assertIn("submitted", actions)
        self.assertIn("approved", actions)
        self.assertIn("promoted", actions)


if __name__ == "__main__":
    unittest.main()
