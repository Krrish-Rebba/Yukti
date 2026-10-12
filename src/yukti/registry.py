"""Model version registry, multi-task benchmark gating, and rollback manager for Yukti."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .store import Store, utc_now


class ModelRegistry:
    def __init__(self, registry_file: str | Path = "models/registry.json"):
        self.path = Path(registry_file)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._save_data({"active_version": None, "versions": []})

    def _load_data(self) -> dict[str, Any]:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_data(self, data: dict[str, Any]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def register_candidate(
        self,
        version_id: str,
        adapter_path: str,
        base_model: str,
        training_knowledge_ids: list[int],
        control_perplexity: float,
        novel_perplexity: float,
        prior_control_perplexity: float | None = None,
        max_degradation_pct: float = 10.0,
    ) -> dict[str, Any]:
        """Registers a candidate trained adapter and evaluates the benchmark gate."""
        data = self._load_data()
        now = utc_now()

        # Gate Evaluation: check if prior task perplexity degraded beyond threshold
        gate_pass = True
        gate_notes = "Control baseline perplexity within acceptable retention threshold."

        if prior_control_perplexity is not None and prior_control_perplexity > 0:
            pct_change = ((control_perplexity - prior_control_perplexity) / prior_control_perplexity) * 100.0
            if pct_change > max_degradation_pct:
                gate_pass = False
                gate_notes = (
                    f"Catastrophic forgetting detected: control baseline perplexity degraded by "
                    f"{pct_change:.1f}% (exceeds allowed {max_degradation_pct:.1f}% ceiling)."
                )

        manifest = {
            "version_id": version_id,
            "created_at": now,
            "base_model": base_model,
            "adapter_path": str(adapter_path),
            "parent_version": data.get("active_version"),
            "training_knowledge_ids": training_knowledge_ids,
            "metrics": {
                "control_perplexity": round(control_perplexity, 4),
                "novel_perplexity": round(novel_perplexity, 4),
                "prior_control_perplexity": round(prior_control_perplexity, 4) if prior_control_perplexity else None,
            },
            "gate_passed": gate_pass,
            "gate_notes": gate_notes,
            "status": "candidate" if gate_pass else "rejected",
        }

        # Check if version already exists
        versions = [v for v in data["versions"] if v["version_id"] != version_id]
        versions.append(manifest)
        data["versions"] = versions
        self._save_data(data)
        return manifest

    def list_versions(self) -> list[dict[str, Any]]:
        return self._load_data().get("versions", [])

    def get_active_version(self) -> dict[str, Any] | None:
        data = self._load_data()
        active_id = data.get("active_version")
        if not active_id:
            return None
        for v in data["versions"]:
            if v["version_id"] == active_id:
                return v
        return None

    def promote_version(self, version_id: str, actor: str = "researcher", store: Store | None = None) -> dict[str, Any]:
        """Promote a passing candidate version to active status."""
        data = self._load_data()
        target = None
        for v in data["versions"]:
            if v["version_id"] == version_id:
                target = v
                break

        if target is None:
            raise ValueError(f"Version '{version_id}' does not exist in registry.")
        if not target.get("gate_passed", False):
            raise ValueError(f"Cannot promote '{version_id}': Failed benchmark gate ({target.get('gate_notes')}).")

        target["status"] = "active"
        target["promoted_at"] = utc_now()
        target["promoted_by"] = actor
        data["active_version"] = version_id
        self._save_data(data)

        if store:
            store.record(None, "model_promoted", actor, f"Promoted model version {version_id} to active.")

        return target

    def rollback(self, to_version_id: str | None = None, actor: str = "researcher", store: Store | None = None) -> dict[str, Any]:
        """Rollback active model to a previous version or designated version."""
        data = self._load_data()
        current_active = data.get("active_version")
        if not current_active:
            raise ValueError("No active model version to roll back from.")

        if to_version_id is None:
            # Revert to parent of current active
            for v in data["versions"]:
                if v["version_id"] == current_active:
                    to_version_id = v.get("parent_version")
                    break

        if not to_version_id:
            # Revert to base model (no active adapter)
            data["active_version"] = None
            note = f"Rolled back from {current_active} to unadapted base model."
            self._save_data(data)
            if store:
                store.record(None, "model_rollback", actor, note)
            return {"active_version": None, "note": note}

        # Find target version
        target = None
        for v in data["versions"]:
            if v["version_id"] == to_version_id:
                target = v
                break

        if target is None:
            raise ValueError(f"Target rollback version '{to_version_id}' not found.")

        target["status"] = "active"
        data["active_version"] = to_version_id
        self._save_data(data)

        note = f"Rolled back active model from {current_active} to {to_version_id}."
        if store:
            store.record(None, "model_rollback", actor, note)

        return {"active_version": to_version_id, "note": note}
