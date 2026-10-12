import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import os
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch
from yukti.cli import main


class TestCLIWorkflow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        self.tmp.close()
        self.db_path = self.tmp.name

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_full_governance_cli_journey(self):
        # 1. Add candidate
        with patch("sys.stdout", new_callable=StringIO) as out:
            exit_code = main([
                "--db", self.db_path, "add",
                "--text", "Carbon has 6 protons in its nucleus.",
                "--source", "https://iupac.org/elements",
                "--evidence", "atomic number of carbon is 6",
                "--trust", "0.95"
            ])
            self.assertEqual(exit_code, 0)
            self.assertIn('"status": "pending"', out.getvalue())

        # 2. List pending
        with patch("sys.stdout", new_callable=StringIO) as out:
            exit_code = main(["--db", self.db_path, "list", "--status", "pending"])
            self.assertEqual(exit_code, 0)
            self.assertIn("Carbon has 6 protons", out.getvalue())

        # 3. Review: approve
        with patch("sys.stdout", new_callable=StringIO) as out:
            exit_code = main([
                "--db", self.db_path, "review", "1",
                "--decision", "approve",
                "--by", "senior_researcher",
                "--note", "Verified with IUPAC tables"
            ])
            self.assertEqual(exit_code, 0)
            self.assertIn("approved", out.getvalue())

        # 4. Promote to long-term memory
        with patch("sys.stdout", new_callable=StringIO) as out:
            exit_code = main([
                "--db", self.db_path, "promote", "1",
                "--by", "senior_researcher"
            ])
            self.assertEqual(exit_code, 0)
            self.assertIn("promoted to long-term memory", out.getvalue())

        # 5. Search approved memory
        with patch("sys.stdout", new_callable=StringIO) as out:
            exit_code = main(["--db", self.db_path, "search", "protons"])
            self.assertEqual(exit_code, 0)
            self.assertIn("Carbon has 6 protons", out.getvalue())

        # 6. Check stats
        with patch("sys.stdout", new_callable=StringIO) as out:
            exit_code = main(["--db", self.db_path, "stats"])
            self.assertEqual(exit_code, 0)
            self.assertIn('"total_items": 1', out.getvalue())

        # 7. Withdraw item
        with patch("sys.stdout", new_callable=StringIO) as out:
            exit_code = main([
                "--db", self.db_path, "withdraw", "1",
                "--by", "senior_researcher",
                "--reason", "Superseded by updated standard"
            ])
            self.assertEqual(exit_code, 0)
            self.assertIn("withdrawn", out.getvalue())

        # 8. Verify search returns empty after withdrawal
        with patch("sys.stdout", new_callable=StringIO) as out:
            exit_code = main(["--db", self.db_path, "search", "protons"])
            self.assertEqual(exit_code, 0)
            self.assertEqual(out.getvalue().strip(), "[]")


if __name__ == "__main__":
    unittest.main()
