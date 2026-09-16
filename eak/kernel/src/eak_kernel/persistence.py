from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from threading import Lock

from .model import Event


class SQLiteEventStore:
    """Durable, append-only, tamper-evident local event store.

    This adapter is suitable for engineering and single-node deployments. It is
    deliberately marked ``local-durable`` rather than ``production`` so the
    readiness gate cannot confuse a local SQLite database with a distributed
    production event store.
    """

    deployment_tier = "local-durable"

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._lock = Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS eak_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    occurred_at TEXT,
                    previous_hash TEXT,
                    event_hash TEXT
                )
                """
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(eak_events)")}
            for name, sql_type in (
                ("occurred_at", "TEXT"),
                ("previous_hash", "TEXT"),
                ("event_hash", "TEXT"),
            ):
                if name not in columns:
                    connection.execute(f"ALTER TABLE eak_events ADD COLUMN {name} {sql_type}")
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_eak_events_execution ON eak_events(execution_id, sequence)"
            )
        self._backfill_legacy_chain()

    @staticmethod
    def _event_hash(
        execution_id: str,
        event_type: str,
        payload_json: str,
        occurred_at: str,
        previous_hash: str,
    ) -> str:
        material = "\x1f".join(
            (execution_id, event_type, payload_json, occurred_at, previous_hash)
        ).encode("utf-8")
        return sha256(material).hexdigest()

    def _backfill_legacy_chain(self) -> None:
        """Backfill pre-chain rows once without rewriting existing hashes."""
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT sequence, execution_id, event_type, payload_json,
                       occurred_at, previous_hash, event_hash
                FROM eak_events ORDER BY execution_id, sequence
                """
            ).fetchall()
            previous_by_execution: dict[str, str] = {}
            for sequence, execution_id, event_type, payload_json, occurred_at, previous_hash, event_hash in rows:
                if event_hash:
                    previous_by_execution[execution_id] = event_hash
                    continue
                occurred_at = occurred_at or "1970-01-01T00:00:00+00:00"
                previous_hash = previous_by_execution.get(execution_id, "")
                event_hash = self._event_hash(
                    execution_id, event_type, payload_json, occurred_at, previous_hash
                )
                connection.execute(
                    """
                    UPDATE eak_events
                    SET occurred_at=?, previous_hash=?, event_hash=?
                    WHERE sequence=?
                    """,
                    (occurred_at, previous_hash, event_hash, sequence),
                )
                previous_by_execution[execution_id] = event_hash

    def append(self, event: Event) -> None:
        payload = json.dumps(dict(event.payload), separators=(",", ":"), sort_keys=True)
        occurred_at = datetime.now(timezone.utc).isoformat()
        with self._lock:
            connection = self._connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    """
                    SELECT event_hash FROM eak_events
                    WHERE execution_id=? ORDER BY sequence DESC LIMIT 1
                    """,
                    (event.execution_id,),
                ).fetchone()
                previous_hash = row[0] if row and row[0] else ""
                event_hash = self._event_hash(
                    event.execution_id, event.type, payload, occurred_at, previous_hash
                )
                connection.execute(
                    """
                    INSERT INTO eak_events(
                        execution_id, event_type, payload_json,
                        occurred_at, previous_hash, event_hash
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.execution_id,
                        event.type,
                        payload,
                        occurred_at,
                        previous_hash,
                        event_hash,
                    ),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()

    def stream(self, execution_id: str) -> tuple[Event, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT event_type, payload_json FROM eak_events WHERE execution_id=? ORDER BY sequence ASC",
                (execution_id,),
            ).fetchall()
        return tuple(Event(event_type, execution_id, json.loads(payload)) for event_type, payload in rows)

    def verify_chain(self, execution_id: str) -> bool:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_type, payload_json, occurred_at, previous_hash, event_hash
                FROM eak_events WHERE execution_id=? ORDER BY sequence ASC
                """,
                (execution_id,),
            ).fetchall()
        previous = ""
        for event_type, payload_json, occurred_at, previous_hash, event_hash in rows:
            if not occurred_at or previous_hash != previous or not event_hash:
                return False
            expected = self._event_hash(
                execution_id, event_type, payload_json, occurred_at, previous
            )
            if expected != event_hash:
                return False
            previous = event_hash
        return True
