"""SQLite persistence for candidate and approved knowledge.

Maintains immutable audit records, multi-state review lifecycle,
and provenance tracking while enforcing foreign keys and schema migrations.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def compute_hash(text: str, source: str = "") -> str:
    canonical = f"{text.strip().casefold()}|{source.strip().casefold()}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._initialize()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    def _initialize(self) -> None:
        """Create base tables and run safe column migrations."""
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                source TEXT NOT NULL,
                trust REAL NOT NULL CHECK (trust >= 0 AND trust <= 1),
                status TEXT NOT NULL CHECK (status IN ('pending','approved','rejected','deferred','needs_evidence','withdrawn','expired')),
                tier TEXT NOT NULL CHECK (tier IN ('working','long_term')),
                flags TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                reviewed_by TEXT,
                review_note TEXT
            );
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_id INTEGER REFERENCES knowledge(id),
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_knowledge_status ON knowledge(status);
            CREATE INDEX IF NOT EXISTS idx_knowledge_tier ON knowledge(tier);
            """
        )
        self.connection.commit()
        self._migrate()

    def _migrate(self) -> None:
        """Add missing schema columns safely if upgrading from earlier schema."""
        cursor = self.connection.execute("PRAGMA table_info(knowledge)")
        columns = {row["name"] for row in cursor.fetchall()}

        new_columns = [
            ("evidence", "TEXT NOT NULL DEFAULT ''"),
            ("author", "TEXT NOT NULL DEFAULT ''"),
            ("content_hash", "TEXT NOT NULL DEFAULT ''"),
            ("recurrence_count", "INTEGER NOT NULL DEFAULT 1"),
        ]
        for col_name, col_def in new_columns:
            if col_name not in columns:
                self.connection.execute(f"ALTER TABLE knowledge ADD COLUMN {col_name} {col_def}")

        self.connection.commit()

    def add_candidate(
        self,
        text: str,
        source: str = "",
        evidence: str = "",
        author: str = "",
        trust: float = 0.5,
        flags: list[dict[str, str]] | None = None,
    ) -> int:
        now = utc_now()
        flags_data = flags or []
        chash = compute_hash(text, source)

        # Check if identical hash exists to update recurrence count
        existing = self.connection.execute(
            "SELECT id, recurrence_count FROM knowledge WHERE content_hash=?", (chash,)
        ).fetchone()

        if existing:
            item_id = int(existing["id"])
            new_count = int(existing["recurrence_count"]) + 1
            self.connection.execute(
                "UPDATE knowledge SET recurrence_count=?, updated_at=? WHERE id=?",
                (new_count, now, item_id),
            )
            self.record(
                item_id,
                "corroborated",
                author or "system",
                f"Recurrence incremented to {new_count} by identical submission.",
            )
            self.connection.commit()
            return item_id

        cursor = self.connection.execute(
            """
            INSERT INTO knowledge(
                text, source, evidence, author, trust, status, tier,
                flags, content_hash, recurrence_count, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, 'pending', 'working', ?, ?, 1, ?, ?)
            """,
            (
                text,
                source,
                evidence,
                author,
                trust,
                json.dumps(flags_data),
                chash,
                now,
                now,
            ),
        )
        item_id = int(cursor.lastrowid)
        flag_codes = [f["code"] for f in flags_data] if flags_data else []
        self.record(item_id, "submitted", author or "system", "; ".join(flag_codes))
        self.connection.commit()
        return item_id

    def get(self, item_id: int) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT * FROM knowledge WHERE id=?", (item_id,)).fetchone()
        return self._decode(row) if row else None

    def list_items(
        self, status: str | None = None, tier: str | None = None
    ) -> list[dict[str, Any]]:
        sql = "SELECT * FROM knowledge WHERE 1=1"
        args: list[Any] = []
        if status:
            sql += " AND status=?"
            args.append(status)
        if tier:
            sql += " AND tier=?"
            args.append(tier)
        sql += " ORDER BY id"
        return [self._decode(row) for row in self.connection.execute(sql, args)]

    def review(self, item_id: int, decision: str, actor: str, note: str = "") -> None:
        valid_decisions = {"approved", "rejected", "deferred", "needs_evidence"}
        if decision not in valid_decisions:
            raise ValueError(f"Invalid review decision '{decision}'. Must be one of {valid_decisions}")

        row = self.get(item_id)
        if row is None:
            raise ValueError(f"No knowledge item with id {item_id}")
        if row["status"] in {"withdrawn", "expired"}:
            raise ValueError(f"Item {item_id} is {row['status']} and cannot be reviewed")

        now = utc_now()
        self.connection.execute(
            "UPDATE knowledge SET status=?, reviewed_by=?, review_note=?, updated_at=? WHERE id=?",
            (decision, actor, note, now, item_id),
        )
        self.record(item_id, decision, actor, note)
        self.connection.commit()

    def promote(self, item_id: int, actor: str = "researcher") -> None:
        row = self.get(item_id)
        if row is None:
            raise ValueError(f"No knowledge item with id {item_id}")
        if row["status"] != "approved":
            raise ValueError(f"Only approved items can be promoted to long-term memory (currently '{row['status']}')")
        if row["tier"] == "long_term":
            raise ValueError("Item is already in long-term memory")

        now = utc_now()
        self.connection.execute(
            "UPDATE knowledge SET tier='long_term', updated_at=? WHERE id=?",
            (now, item_id),
        )
        self.record(item_id, "promoted", actor, "Promoted from working memory to long-term memory.")
        self.connection.commit()

    def withdraw(self, item_id: int, actor: str, reason: str) -> None:
        """Tombstone and withdraw an item from active memory with audit rationale."""
        row = self.get(item_id)
        if row is None:
            raise ValueError(f"No knowledge item with id {item_id}")
        if row["status"] == "withdrawn":
            raise ValueError(f"Item {item_id} is already withdrawn")

        now = utc_now()
        self.connection.execute(
            "UPDATE knowledge SET status='withdrawn', review_note=?, updated_at=? WHERE id=?",
            (reason, now, item_id),
        )
        self.record(item_id, "withdrawn", actor, reason)
        self.connection.commit()

    def search(self, query: str, tier: str | None = None) -> list[dict[str, Any]]:
        """Search approved knowledge by query substring."""
        sql = "SELECT * FROM knowledge WHERE status='approved' AND text LIKE ? COLLATE NOCASE"
        args: list[Any] = [f"%{query}%"]
        if tier:
            sql += " AND tier=?"
            args.append(tier)
        sql += " ORDER BY CASE tier WHEN 'long_term' THEN 0 ELSE 1 END, id"
        return [self._decode(row) for row in self.connection.execute(sql, args)]

    def export_approved(self, tier: str = "long_term") -> list[dict[str, Any]]:
        """Export approved, in-scope records for downstream use/training with full provenance."""
        sql = "SELECT * FROM knowledge WHERE status='approved' AND tier=? ORDER BY id"
        return [self._decode(row) for row in self.connection.execute(sql, (tier,))]

    def decisions(self, item_id: int | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM decisions"
        args: tuple[Any, ...] = ()
        if item_id is not None:
            sql += " WHERE knowledge_id=?"
            args = (item_id,)
        sql += " ORDER BY id"
        return [dict(row) for row in self.connection.execute(sql, args)]

    def stats(self) -> dict[str, Any]:
        """Aggregate counts across statuses, tiers, and flags."""
        total = self.connection.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
        status_counts = dict(
            self.connection.execute("SELECT status, COUNT(*) FROM knowledge GROUP BY status").fetchall()
        )
        tier_counts = dict(
            self.connection.execute("SELECT tier, COUNT(*) FROM knowledge GROUP BY tier").fetchall()
        )
        decision_count = self.connection.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        return {
            "total_items": total,
            "status_distribution": status_counts,
            "tier_distribution": tier_counts,
            "total_decisions_logged": decision_count,
        }

    def record(self, item_id: int | None, action: str, actor: str, note: str = "") -> None:
        self.connection.execute(
            "INSERT INTO decisions(knowledge_id, action, actor, note, created_at) VALUES (?, ?, ?, ?, ?)",
            (item_id, action, actor, note, utc_now()),
        )
        self.connection.commit()

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["flags"] = json.loads(item["flags"])
        return item
