import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import os
import tempfile
import unittest
from yukti.registry import ModelRegistry
from yukti.store import Store


class TestModelRegistryAndRollback(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.reg_path = Path(self.tmp_dir.name) / "registry.json"
        self.db_path = Path(self.tmp_dir.name) / "test.sqlite3"
        self.registry = ModelRegistry(self.reg_path)
        self.store = Store(self.db_path)

    def tearDown(self):
        self.store.close()
        self.tmp_dir.cleanup()

    def test_register_and_promote_passing_candidate(self):
        manifest = self.registry.register_candidate(
            version_id="v1",
            adapter_path="models/checkpoints/v1",
            base_model="HuggingFaceTB/SmolLM2-135M",
            training_knowledge_ids=[1, 2, 3],
            control_perplexity=30.2,
            novel_perplexity=28.1,
            prior_control_perplexity=30.0,
            max_degradation_pct=10.0,
        )
        self.assertTrue(manifest["gate_passed"])
        self.assertEqual(manifest["status"], "candidate")

        # Promote
        promoted = self.registry.promote_version("v1", actor="researcher", store=self.store)
        self.assertEqual(promoted["status"], "active")
        self.assertEqual(self.registry.get_active_version()["version_id"], "v1")

        # Verify audit log in store
        decisions = self.store.decisions()
        self.assertTrue(any(d["action"] == "model_promoted" for d in decisions))

    def test_benchmark_gate_rejects_catastrophic_forgetting(self):
        # Severe degradation from 30.0 to 45.0 (+50% increase in perplexity)
        manifest = self.registry.register_candidate(
            version_id="v_bad",
            adapter_path="models/checkpoints/v_bad",
            base_model="HuggingFaceTB/SmolLM2-135M",
            training_knowledge_ids=[4],
            control_perplexity=45.0,
            novel_perplexity=25.0,
            prior_control_perplexity=30.0,
            max_degradation_pct=10.0,
        )
        self.assertFalse(manifest["gate_passed"])
        self.assertEqual(manifest["status"], "rejected")
        self.assertIn("Catastrophic forgetting detected", manifest["gate_notes"])

        # Attempting to promote rejected model must raise ValueError
        with self.assertRaises(ValueError):
            self.registry.promote_version("v_bad", actor="researcher")

    def test_deterministic_rollback(self):
        # Register and promote v1
        self.registry.register_candidate(
            version_id="v1",
            adapter_path="models/checkpoints/v1",
            base_model="HuggingFaceTB/SmolLM2-135M",
            training_knowledge_ids=[1],
            control_perplexity=30.0,
            novel_perplexity=28.0,
        )
        self.registry.promote_version("v1", actor="researcher", store=self.store)

        # Register and promote v2
        self.registry.register_candidate(
            version_id="v2",
            adapter_path="models/checkpoints/v2",
            base_model="HuggingFaceTB/SmolLM2-135M",
            training_knowledge_ids=[2],
            control_perplexity=30.5,
            novel_perplexity=27.0,
            prior_control_perplexity=30.0,
        )
        self.registry.promote_version("v2", actor="researcher", store=self.store)
        self.assertEqual(self.registry.get_active_version()["version_id"], "v2")

        # Rollback: should revert to v1
        result = self.registry.rollback(actor="safety_officer", store=self.store)
        self.assertEqual(result["active_version"], "v1")
        self.assertEqual(self.registry.get_active_version()["version_id"], "v1")

        # Verify rollback audit event in store
        decisions = self.store.decisions()
        self.assertTrue(any(d["action"] == "model_rollback" for d in decisions))


if __name__ == "__main__":
    unittest.main()
