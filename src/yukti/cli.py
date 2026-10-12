"""Command line interface for the Yukti epistemic governance system."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .datasets import load_curated_knowledge_into_store
from .governance import assess
from .registry import ModelRegistry
from .store import Store
from .trainer import check_resource_envelope, run_adaptation


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="yukti", description="Yukti — Governed Epistemic Memory & Continual Learning Core")
    root.add_argument("--db", default="data/yukti.sqlite3", help="SQLite database path (default: data/yukti.sqlite3)")
    root.add_argument("--registry", default="models/registry.json", help="Model registry path (default: models/registry.json)")
    commands = root.add_subparsers(dest="command", required=True)

    # 1. Add candidate
    add = commands.add_parser("add", help="Submit a candidate claim for epistemic triage and review")
    add.add_argument("--text", required=True, help="Claim or assertion text")
    add.add_argument("--source", default="", help="Source reference (URL, DOI, document URI, or publication citation)")
    add.add_argument("--evidence", default="", help="Verbatim quoted excerpt or locator from the source")
    add.add_argument("--author", default="", help="Author or submitter identity")
    add.add_argument("--trust", type=float, default=0.5, help="Assigned source credibility score from 0.0 to 1.0 (default: 0.5)")

    # 2. List items
    listing = commands.add_parser("list", help="List knowledge items with optional status/tier filters")
    listing.add_argument("--status", choices=["pending", "approved", "rejected", "deferred", "needs_evidence", "withdrawn", "expired"])
    listing.add_argument("--tier", choices=["working", "long_term"])

    # 3. Review candidate
    review = commands.add_parser("review", help="Record an explicit human review decision")
    review.add_argument("id", type=int, help="Knowledge item ID")
    review.add_argument(
        "--decision",
        required=True,
        choices=["approve", "reject", "defer", "request_evidence"],
        help="Review outcome",
    )
    review.add_argument("--by", default="researcher", help="Reviewer identity")
    review.add_argument("--note", default="", help="Rationale or review notes")

    # 4. Promote item
    promote = commands.add_parser("promote", help="Promote an approved item from working to long-term memory")
    promote.add_argument("id", type=int, help="Knowledge item ID")
    promote.add_argument("--by", default="researcher", help="Actor identity")

    # 5. Withdraw item
    withdraw = commands.add_parser("withdraw", help="Withdraw an item from active memory with an audit tombstone")
    withdraw.add_argument("id", type=int, help="Knowledge item ID")
    withdraw.add_argument("--by", default="researcher", help="Actor identity")
    withdraw.add_argument("--reason", required=True, help="Mandatory explanation for withdrawal")

    # 6. Search memory
    search = commands.add_parser("search", help="Search approved memory by substring query")
    search.add_argument("query", help="Search term")
    search.add_argument("--tier", choices=["working", "long_term"])

    # 7. Audit log
    decisions = commands.add_parser("decisions", help="Show the append-only audit trail")
    decisions.add_argument("--id", type=int, help="Optional filter by knowledge item ID")

    # 8. Export approved dataset
    export = commands.add_parser("export", help="Export frozen approved knowledge dataset for downstream training/inspection")
    export.add_argument("--tier", default="long_term", choices=["working", "long_term"], help="Memory tier to export (default: long_term)")
    export.add_argument("--output", default="", help="Optional JSONL file path to write to")

    # 9. System statistics
    commands.add_parser("stats", help="Display memory distribution and audit metrics")

    # 10. Seed curated dataset
    seed = commands.add_parser("seed", help="Ingest curated reliable scientific knowledge into memory")
    seed.add_argument("--approve", action="store_true", help="Automatically approve and promote curated peer-reviewed facts")

    # 11. Train / Adapt model
    train = commands.add_parser("train", help="Run resource-bounded LoRA adaptation on approved long-term memory")
    train.add_argument("--version", required=True, help="Version identifier (e.g., v1, v2)")
    train.add_argument("--dry-run", action="store_true", help="Simulate resource estimation without training")
    train.add_argument("--by", default="researcher", help="Actor identity")

    # 12. Model registry & rollback
    model_cmd = commands.add_parser("model", help="Inspect model version registry, benchmark gates, and execute rollback")
    model_sub = model_cmd.add_subparsers(dest="model_action", required=True)
    
    model_sub.add_parser("list", help="List all registered model versions and benchmark gate verdicts")
    
    m_promote = model_sub.add_parser("promote", help="Promote a passing candidate model version to active")
    m_promote.add_argument("version_id", help="Version ID to promote")
    m_promote.add_argument("--by", default="researcher", help="Actor identity")

    m_rollback = model_sub.add_parser("rollback", help="Revert active model to prior version")
    m_rollback.add_argument("--to", default=None, help="Target version ID to roll back to (default: prior active)")
    m_rollback.add_argument("--by", default="researcher", help="Actor identity")

    # 13. Hardware & VRAM diagnostics
    commands.add_parser("diagnose", help="Check system hardware, VRAM, and storage envelope against 20GB/4GB limits")

    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        with Store(args.db) as store:
            registry = ModelRegistry(args.registry)

            if args.command == "add":
                if not 0.0 <= args.trust <= 1.0:
                    raise ValueError("--trust score must be between 0.0 and 1.0")

                existing_items = store.list_items()
                flags = assess(
                    text=args.text,
                    source=args.source,
                    evidence=args.evidence,
                    trust=args.trust,
                    existing=existing_items,
                )
                item_id = store.add_candidate(
                    text=args.text,
                    source=args.source,
                    evidence=args.evidence,
                    author=args.author,
                    trust=args.trust,
                    flags=flags,
                )
                print(json.dumps({"id": item_id, "status": "pending", "flags": flags}, indent=2, ensure_ascii=False))

            elif args.command == "list":
                _print_items(store.list_items(args.status, args.tier))

            elif args.command == "review":
                decision_map = {
                    "approve": "approved",
                    "reject": "rejected",
                    "defer": "deferred",
                    "request_evidence": "needs_evidence",
                }
                status = decision_map[args.decision]
                store.review(args.id, status, args.by, args.note)
                print(f"Item {args.id}: {status} (by {args.by})")

            elif args.command == "promote":
                store.promote(args.id, args.by)
                print(f"Item {args.id}: promoted to long-term memory (by {args.by})")

            elif args.command == "withdraw":
                store.withdraw(args.id, args.by, args.reason)
                print(f"Item {args.id}: withdrawn from active retrieval (by {args.by})")

            elif args.command == "search":
                _print_items(store.search(args.query, args.tier))

            elif args.command == "decisions":
                print(json.dumps(store.decisions(args.id), indent=2, ensure_ascii=False))

            elif args.command == "export":
                items = store.export_approved(args.tier)
                if args.output:
                    out_path = Path(args.output)
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(out_path, "w", encoding="utf-8") as f:
                        for item in items:
                            f.write(json.dumps(item, ensure_ascii=False) + "\n")
                    print(f"Exported {len(items)} approved items to {args.output}")
                else:
                    _print_items(items)

            elif args.command == "stats":
                print(json.dumps(store.stats(), indent=2, ensure_ascii=False))

            elif args.command == "seed":
                ids = load_curated_knowledge_into_store(store, auto_review=args.approve)
                status = "approved & promoted" if args.approve else "pending review"
                print(f"Ingested {len(ids)} curated scientific facts ({status}). IDs: {ids}")

            elif args.command == "train":
                result = run_adaptation(
                    store=store,
                    registry=registry,
                    version_id=args.version,
                    dry_run=args.dry_run,
                    actor=args.by,
                )
                print(json.dumps(result, indent=2, ensure_ascii=False))

            elif args.command == "model":
                if args.model_action == "list":
                    active = registry.get_active_version()
                    print(f"Active Model: {active['version_id'] if active else 'None (Base Model)'}\n")
                    _print_items(registry.list_versions())
                elif args.model_action == "promote":
                    promoted = registry.promote_version(args.version_id, actor=args.by, store=store)
                    print(f"Model version '{args.version_id}' successfully promoted to ACTIVE.")
                elif args.model_action == "rollback":
                    rolled = registry.rollback(to_version_id=args.to, actor=args.by, store=store)
                    print(f"Rollback complete: {rolled['note']}")

            elif args.command == "diagnose":
                diag = check_resource_envelope()
                print(json.dumps(diag, indent=2, ensure_ascii=False))

        return 0
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"yukti: {exc}", file=sys.stderr)
        return 2


def _print_items(items: list[dict]) -> None:
    print(json.dumps(items, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
