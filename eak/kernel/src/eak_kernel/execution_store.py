from __future__ import annotations

import json
import sqlite3
from hashlib import sha256
from pathlib import Path
from threading import Lock
from typing import Any, Mapping, Protocol


class ExecutionContextStore(Protocol):
    def save(self, context: Mapping[str, Any]) -> str: ...
    def load(self, execution_id: str) -> dict[str, Any]: ...
    def digest(self, execution_id: str) -> str: ...


class SQLiteExecutionStore:
    """Immutable durable reference store for compiled ExecutionContext snapshots."""

    deployment_tier = "local-durable"

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._lock = Lock()
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS eak_execution_contexts (
                    execution_id TEXT PRIMARY KEY,
                    context_json TEXT NOT NULL,
                    digest TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _canonical(context: Mapping[str, Any]) -> tuple[str, str]:
        encoded = json.dumps(dict(context), separators=(",", ":"), sort_keys=True)
        return encoded, f"sha256:{sha256(encoded.encode('utf-8')).hexdigest()}"

    def save(self, context: Mapping[str, Any]) -> str:
        try:
            execution_id = str(context["spec"]["executionId"])
        except (KeyError, TypeError) as exc:
            raise ValueError("ExecutionContext requires spec.executionId") from exc
        if not execution_id:
            raise ValueError("ExecutionContext executionId is required")
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
        value = json.loads(row["context_json"])
        encoded, digest = self._canonical(value)
        if encoded != row["context_json"] or digest != self.digest(execution_id):
            raise ValueError("ExecutionContext integrity check failed")
        return value

    def digest(self, execution_id: str) -> str:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT digest FROM eak_execution_contexts WHERE execution_id=?",
                (execution_id,),
            ).fetchone()
        if row is None:
            raise KeyError("ExecutionContext not found")
        return str(row["digest"])

    def backup_to(self, destination: str | Path) -> Path:
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        with self._lock, self._connect() as source, sqlite3.connect(target) as backup:
            source.backup(backup)
        return target
