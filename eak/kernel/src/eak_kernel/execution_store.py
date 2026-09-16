from __future__ import annotations

import json
import sqlite3
from hashlib import sha256
from pathlib import Path
from threading import Lock
from typing import Any


class SQLiteExecutionStore:
    """Immutable durable store for compiled ExecutionContext snapshots."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._lock = Lock()
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS eak_execution_contexts (
                    execution_id TEXT PRIMARY KEY,
                    context_json TEXT NOT NULL,
                    digest TEXT NOT NULL
                )"""
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _canonical(context: dict[str, Any]) -> tuple[str, str]:
        encoded = json.dumps(context, separators=(",", ":"), sort_keys=True)
        return encoded, f"sha256:{sha256(encoded.encode('utf-8')).hexdigest()}"

    def save(self, context: dict[str, Any]) -> str:
        try:
            execution_id = str(context["spec"]["executionId"])
        except (KeyError, TypeError) as exc:
            raise ValueError("ExecutionContext requires spec.executionId") from exc
        encoded, digest = self._canonical(context)
        with self._lock, self._connect() as connection:
            existing = connection.execute(
                "SELECT context_json, digest FROM eak_execution_contexts WHERE execution_id=?",
                (execution_id,),
            ).fetchone()
            if existing is not None:
                if existing["digest"] != digest or existing["context_json"] != encoded:
                    raise ValueError("ExecutionContext snapshots are immutable")
                return digest
            connection.execute(
                "INSERT INTO eak_execution_contexts(execution_id, context_json, digest) VALUES (?, ?, ?)",
                (execution_id, encoded, digest),
            )
        return digest

    def load(self, execution_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT context_json FROM eak_execution_contexts WHERE execution_id=?",
                (execution_id,),
            ).fetchone()
        if row is None:
            raise KeyError("ExecutionContext not found")
        return json.loads(row["context_json"])

    def digest(self, execution_id: str) -> str:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT digest FROM eak_execution_contexts WHERE execution_id=?",
                (execution_id,),
            ).fetchone()
        if row is None:
            raise KeyError("ExecutionContext not found")
        return str(row["digest"])
