from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any


@dataclass(frozen=True)
class WorkItem:
    id: str
    queue: str
    payload: dict[str, Any]
    attempts: int
    lease_owner: str | None = None
    lease_expires_at: float | None = None


class SQLiteWorkQueue:
    """Durable at-least-once work queue with leases and idempotent enqueue."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._lock = Lock()
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS eak_work_items (
                    id TEXT PRIMARY KEY,
                    queue_name TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    idempotency_key TEXT,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    available_at REAL NOT NULL,
                    lease_owner TEXT,
                    lease_expires_at REAL,
                    last_error TEXT,
                    UNIQUE(queue_name, idempotency_key)
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_eak_work_claim ON eak_work_items(queue_name, status, available_at)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        return connection

    def enqueue(
        self,
        *,
        queue: str,
        payload: dict[str, Any],
        idempotency_key: str | None = None,
        available_at: float | None = None,
    ) -> str:
        if not queue:
            raise ValueError("queue is required")
        item_id = f"work_{uuid.uuid4().hex}"
        available = time.time() if available_at is None else float(available_at)
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if idempotency_key is not None:
                existing = connection.execute(
                    "SELECT id FROM eak_work_items WHERE queue_name=? AND idempotency_key=?",
                    (queue, idempotency_key),
                ).fetchone()
                if existing:
                    connection.commit()
                    return str(existing["id"])
            connection.execute(
                """INSERT INTO eak_work_items
                   (id, queue_name, payload_json, idempotency_key, status, available_at)
                   VALUES (?, ?, ?, ?, 'READY', ?)""",
                (item_id, queue, encoded, idempotency_key, available),
            )
            connection.commit()
        return item_id

    def claim(self, *, queue: str, worker: str, lease_seconds: float = 30.0, now: float | None = None) -> WorkItem | None:
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        current = time.time() if now is None else float(now)
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """UPDATE eak_work_items SET status='READY', lease_owner=NULL, lease_expires_at=NULL
                   WHERE status='LEASED' AND lease_expires_at <= ?""",
                (current,),
            )
            row = connection.execute(
                """SELECT * FROM eak_work_items
                   WHERE queue_name=? AND status='READY' AND available_at <= ?
                   ORDER BY available_at ASC, rowid ASC LIMIT 1""",
                (queue, current),
            ).fetchone()
            if row is None:
                connection.commit()
                return None
            expires = current + lease_seconds
            connection.execute(
                """UPDATE eak_work_items
                   SET status='LEASED', attempts=attempts+1, lease_owner=?, lease_expires_at=?
                   WHERE id=?""",
                (worker, expires, row["id"]),
            )
            connection.commit()
            return WorkItem(
                id=str(row["id"]),
                queue=str(row["queue_name"]),
                payload=json.loads(row["payload_json"]),
                attempts=int(row["attempts"]) + 1,
                lease_owner=worker,
                lease_expires_at=expires,
            )

    def ack(self, *, item_id: str, worker: str) -> None:
        self._finish(item_id=item_id, worker=worker, status="DONE", error=None)

    def fail(
        self,
        *,
        item_id: str,
        worker: str,
        error: str,
        retry_delay: float = 0.0,
        now: float | None = None,
    ) -> None:
        current = time.time() if now is None else float(now)
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT status, lease_owner FROM eak_work_items WHERE id=?", (item_id,)
            ).fetchone()
            if row is None:
                raise KeyError("Work item not found")
            if row["status"] != "LEASED" or row["lease_owner"] != worker:
                raise PermissionError("Worker does not own the active lease")
            connection.execute(
                """UPDATE eak_work_items SET status='READY', available_at=?, lease_owner=NULL,
                   lease_expires_at=NULL, last_error=? WHERE id=?""",
                (current + max(0.0, retry_delay), error, item_id),
            )
            connection.commit()

    def _finish(self, *, item_id: str, worker: str, status: str, error: str | None) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT status, lease_owner FROM eak_work_items WHERE id=?", (item_id,)
            ).fetchone()
            if row is None:
                raise KeyError("Work item not found")
            if row["status"] != "LEASED" or row["lease_owner"] != worker:
                raise PermissionError("Worker does not own the active lease")
            connection.execute(
                """UPDATE eak_work_items SET status=?, lease_owner=NULL, lease_expires_at=NULL,
                   last_error=? WHERE id=?""",
                (status, error, item_id),
            )
            connection.commit()
