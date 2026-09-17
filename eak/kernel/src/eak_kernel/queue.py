from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class WorkItem:
    id: str
    execution_id: str
    node_id: str
    payload: Mapping[str, Any]
    state: str
    attempts: int
    max_attempts: int
    available_at: float
    leased_by: str | None = None
    lease_expires_at: float | None = None


class WorkQueue(Protocol):
    def enqueue(
        self,
        *,
        execution_id: str,
        node_id: str,
        payload: Mapping[str, Any],
        max_attempts: int = 3,
        available_at: float | None = None,
    ) -> WorkItem: ...

    def lease(self, *, worker_id: str, lease_seconds: float = 30.0) -> WorkItem | None: ...
    def ack(self, *, item_id: str, worker_id: str) -> None: ...
    def nack(self, *, item_id: str, worker_id: str, delay_seconds: float = 0.0) -> None: ...


class SQLiteWorkQueue:
    """Small durable at-least-once queue with explicit leases and bounded retries."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS eak_work_items (
                    id TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    state TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    max_attempts INTEGER NOT NULL,
                    available_at REAL NOT NULL,
                    leased_by TEXT,
                    lease_expires_at REAL,
                    created_at REAL NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_eak_work_ready ON eak_work_items(state, available_at, created_at)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=30.0, isolation_level=None)

    def enqueue(
        self,
        *,
        execution_id: str,
        node_id: str,
        payload: Mapping[str, Any],
        max_attempts: int = 3,
        available_at: float | None = None,
    ) -> WorkItem:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        now = time.time()
        item = WorkItem(
            id=f"work_{uuid.uuid4().hex}",
            execution_id=execution_id,
            node_id=node_id,
            payload=dict(payload),
            state="QUEUED",
            attempts=0,
            max_attempts=max_attempts,
            available_at=now if available_at is None else float(available_at),
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO eak_work_items(
                    id, execution_id, node_id, payload_json, state, attempts,
                    max_attempts, available_at, leased_by, lease_expires_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)
                """,
                (
                    item.id, item.execution_id, item.node_id,
                    json.dumps(dict(item.payload), separators=(",", ":"), sort_keys=True),
                    item.state, item.attempts, item.max_attempts, item.available_at, now,
                ),
            )
        return item

    def lease(self, *, worker_id: str, lease_seconds: float = 30.0) -> WorkItem | None:
        if not worker_id:
            raise ValueError("worker_id is required")
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        now = time.time()
        expiry = now + lease_seconds
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                UPDATE eak_work_items
                   SET state='QUEUED', leased_by=NULL, lease_expires_at=NULL
                 WHERE state='LEASED' AND lease_expires_at IS NOT NULL AND lease_expires_at <= ?
                   AND attempts < max_attempts
                """,
                (now,),
            )
            connection.execute(
                """
                UPDATE eak_work_items
                   SET state='DEAD', leased_by=NULL, lease_expires_at=NULL
                 WHERE state='LEASED' AND lease_expires_at IS NOT NULL AND lease_expires_at <= ?
                   AND attempts >= max_attempts
                """,
                (now,),
            )
            row = connection.execute(
                """
                SELECT id FROM eak_work_items
                 WHERE state='QUEUED' AND available_at <= ? AND attempts < max_attempts
                 ORDER BY created_at ASC, id ASC LIMIT 1
                """,
                (now,),
            ).fetchone()
            if row is None:
                connection.commit()
                return None
            item_id = str(row[0])
            connection.execute(
                """
                UPDATE eak_work_items
                   SET state='LEASED', leased_by=?, lease_expires_at=?, attempts=attempts+1
                 WHERE id=? AND state='QUEUED'
                """,
                (worker_id, expiry, item_id),
            )
            leased = self._fetch_row(connection, item_id)
            connection.commit()
            return leased
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def ack(self, *, item_id: str, worker_id: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE eak_work_items
                   SET state='DONE', leased_by=NULL, lease_expires_at=NULL
                 WHERE id=? AND state='LEASED' AND leased_by=?
                """,
                (item_id, worker_id),
            )
            if cursor.rowcount != 1:
                raise PermissionError("Work item is not leased by this worker")

    def nack(self, *, item_id: str, worker_id: str, delay_seconds: float = 0.0) -> None:
        if delay_seconds < 0:
            raise ValueError("delay_seconds must be >= 0")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT attempts, max_attempts, state, leased_by FROM eak_work_items WHERE id=?",
                (item_id,),
            ).fetchone()
            if row is None:
                raise KeyError("Work item not found")
            attempts, max_attempts, state, leased_by = row
            if state != "LEASED" or leased_by != worker_id:
                raise PermissionError("Work item is not leased by this worker")
            next_state = "DEAD" if int(attempts) >= int(max_attempts) else "QUEUED"
            connection.execute(
                """
                UPDATE eak_work_items
                   SET state=?, available_at=?, leased_by=NULL, lease_expires_at=NULL
                 WHERE id=?
                """,
                (next_state, time.time() + delay_seconds, item_id),
            )

    def get(self, item_id: str) -> WorkItem:
        with self._connect() as connection:
            item = self._fetch_row(connection, item_id)
        if item is None:
            raise KeyError("Work item not found")
        return item

    @staticmethod
    def _fetch_row(connection: sqlite3.Connection, item_id: str) -> WorkItem | None:
        row = connection.execute(
            """
            SELECT id, execution_id, node_id, payload_json, state, attempts,
                   max_attempts, available_at, leased_by, lease_expires_at
              FROM eak_work_items WHERE id=?
            """,
            (item_id,),
        ).fetchone()
        if row is None:
            return None
        return WorkItem(
            id=str(row[0]), execution_id=str(row[1]), node_id=str(row[2]),
            payload=json.loads(row[3]), state=str(row[4]), attempts=int(row[5]),
            max_attempts=int(row[6]), available_at=float(row[7]),
            leased_by=None if row[8] is None else str(row[8]),
            lease_expires_at=None if row[9] is None else float(row[9]),
        )
