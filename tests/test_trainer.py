import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import os
import tempfile
import unittest
from yukti.datasets import load_curated_knowledge_into_store
from yukti.registry import ModelRegistry
from yukti.store import Store
from yukti.trainer import check_resource_envelope, run_adaptation


class TestTrainerWorkflow(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.reg_path = Path(self.tmp_dir.name) / "registry.json"
        self.db_path = Path(self.tmp_dir.name) / "test.sqlite3"
        self.registry = ModelRegistry(self.reg_path)
        self.store = Store(self.db_path)

    def tearDown(self):
        self.store.close()
        self.tmp_dir.cleanup()

    def test_check_resource_envelope(self):
        env = check_resource_envelope()
        self.assertIn("disk_free_gb", env)
        self.assertIn("storage_budget_gb", env)
        self.assertTrue(env["storage_within_budget"])

    def test_adaptation_fails_without_approved_data(self):
        # Store is empty; adaptation must reject execution
        with self.assertRaises(ValueError):
            run_adaptation(
                store=self.store,
                registry=self.registry,
                version_id="v_empty",
                dry_run=True,
            )

    def test_dry_run_estimation(self):
        # Seed and approve data
        load_curated_knowledge_into_store(self.store, auto_review=True)
        
        result = run_adaptation(
            store=self.store,
            registry=self.registry,
            version_id="v_dry",
            dry_run=True,
        )
        self.assertEqual(result["status"], "dry_run_complete")
        self.assertGreater(result["approved_records_count"], 0)
        self.assertIn("Feasible under 4GB VRAM", result["dry_run_verdict"])

    def test_end_to_end_adaptation_run(self):
        # Seed and approve data
        load_curated_knowledge_into_store(self.store, auto_review=True)
        
        out_dir = Path(self.tmp_dir.name) / "checkpoints"
        result = run_adaptation(
            store=self.store,
            registry=self.registry,
            version_id="v_test_1",
            output_dir=str(out_dir),
            dry_run=False,
            actor="test_runner",
        )
        self.assertEqual(result["status"], "training_complete")
        self.assertTrue(result["manifest"]["gate_passed"])
        self.assertTrue(Path(result["dataset_snapshot"]).exists())

        # Verify audit log in store
        decisions = self.store.decisions()
        self.assertTrue(any(d["action"] == "model_trained" for d in decisions))


if __name__ == "__main__":
    unittest.main()
