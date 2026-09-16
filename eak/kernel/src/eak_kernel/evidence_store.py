from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from threading import Lock
from typing import Any

from .evidence import EvidenceGraph


@dataclass(frozen=True)
class EvidenceSnapshot:
    execution_id: str
    graph_id: str
    version: str
    digest: str


class SQLiteEvidenceStore:
    """Durable local persistence for execution-scoped evidence graphs."""

    deployment_tier = "local-durable"

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._lock = Lock()
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS eak_evidence_graphs (
                    execution_id TEXT NOT NULL,
                    graph_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    contract_json TEXT NOT NULL,
                    digest TEXT NOT NULL,
                    PRIMARY KEY(execution_id, graph_id, version)
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=30)

    @staticmethod
    def _digest(contract_json: str) -> str:
        return sha256(contract_json.encode("utf-8")).hexdigest()

    def save(
        self,
        *,
        execution_id: str,
        graph: EvidenceGraph,
        graph_id: str,
        version: str = "1.0.0",
    ) -> EvidenceSnapshot:
        contract = graph.to_contract(graph_id=graph_id, version=version)
        contract_json = json.dumps(contract, separators=(",", ":"), sort_keys=True)
        digest = self._digest(contract_json)
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO eak_evidence_graphs(
                    execution_id, graph_id, version, contract_json, digest
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (execution_id, graph_id, version, contract_json, digest),
            )
        return EvidenceSnapshot(execution_id, graph_id, version, f"sha256:{digest}")

    def load(self, *, execution_id: str, graph_id: str, version: str = "1.0.0") -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT contract_json, digest FROM eak_evidence_graphs
                WHERE execution_id=? AND graph_id=? AND version=?
                """,
                (execution_id, graph_id, version),
            ).fetchone()
        if row is None:
            return None
        contract_json, digest = row
        if self._digest(contract_json) != digest:
            raise ValueError("Evidence graph integrity check failed")
        return json.loads(contract_json)
