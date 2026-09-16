from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Mapping


@dataclass(frozen=True)
class WorkItem:
    id: str
    tenant: str
    kind: str
    payload: Mapping[str, Any]
    status: str
    attempts: int
    max_attempts: int
    lease_owner: str | None = None
    available_at: float = 0.0
    leased_until: float | None = None


class SQLiteWorkQueue:
    """Durable reference queue with explicit leases and bounded retries.

    This backend is intended for local/single-node deployments and conformance.
    Larger deployments can replace it behind the same semantics with a managed
    queue or broker without changing workflow contracts.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._lock = Lock()
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS eak_work_queue (
                    id TEXT PRIMARY KEY,
                    tenant TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    max_attempts INTEGER NOT NULL,
                    available_at REAL NOT NULL,
                    leased_until REAL,
                    lease_owner TEXT
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_eak_work_available "
                "ON eak_work_queue(status, available_at, leased_until)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        return connection

    def enqueue(
        self,
        *,
        id: str,
        tenant: str,
        kind: str,
        payload: Mapping[str, Any],
        max_attempts: int = 3,
        available_at: float | None = None,
    ) -> WorkItem:
        if not id or not tenant or not kind:
            raise ValueError("id, tenant, and kind are required")
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        when = time.time() if available_at is None else float(available_at)
        payload_json = json.dumps(dict(payload), separators=(",", ":"), sort_keys=True)
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """
                    INSERT INTO eak_work_queue(
                        id, tenant, kind, payload_json, status, attempts,
                        max_attempts, available_at, leased_until, lease_owner
                    ) VALUES (?, ?, ?, ?, 'QUEUED', 0, ?, ?, NULL, NULL)
                    """,
                    (id, tenant, kind, payload_json, max_attempts, when),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self.get(id)

    def claim(
        self,
        *,
        worker: str,
        lease_seconds: float = 60.0,
        now: float | None = None,
    ) -> WorkItem | None:
        if not worker:
            raise ValueError("worker is required")
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be > 0")
        current = time.time() if now is None else float(now)
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    """
                    SELECT *
                    FROM eak_work_queue
                    WHERE attempts < max_attempts
                      AND available_at <= ?
                      AND (
                        status = 'QUEUED'
                        OR (status = 'RUNNING' AND leased_until IS NOT NULL AND leased_until <= ?)
                      )
                    ORDER BY available_at ASC, rowid ASC
                    LIMIT 1
                    """,
                    (current, current),
                ).fetchone()
                if row is None:
                    connection.commit()
                    return None
                attempts = int(row["attempts"]) + 1
                leased_until = current + lease_seconds
                connection.execute(
                    """
                    UPDATE eak_work_queue
                    SET status='RUNNING', attempts=?, leased_until=?, lease_owner=?
                    WHERE id=?
                    """,
                    (attempts, leased_until, worker, row["id"]),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self.get(str(row["id"]))

    def ack(self, *, id: str, worker: str) -> WorkItem:
        return self._finish(id=id, worker=worker, status="SUCCEEDED")

    def nack(
        self,
        *,
        id: str,
        worker: str,
        retry_delay: float = 0.0,
        now: float | None = None,
    ) -> WorkItem:
        if retry_delay < 0:
            raise ValueError("retry_delay must be >= 0")
        current = time.time() if now is None else float(now)
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    "SELECT attempts, max_attempts, status, lease_owner FROM eak_work_queue WHERE id=?",
                    (id,),
                ).fetchone()
                self._assert_lease(row, worker)
                next_status = "FAILED" if int(row["attempts"]) >= int(row["max_attempts"]) else "QUEUED"
                connection.execute(
                    """
                    UPDATE eak_work_queue
                    SET status=?, available_at=?, leased_until=NULL, lease_owner=NULL
                    WHERE id=?
                    """,
                    (next_status, current + retry_delay, id),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self.get(id)

    def get(self, id: str) -> WorkItem:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM eak_work_queue WHERE id=?", (id,)
            ).fetchone()
        if row is None:
            raise KeyError("Work item not found")
        return self._row_to_item(row)

    def _finish(self, *, id: str, worker: str, status: str) -> WorkItem:
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    "SELECT status, lease_owner FROM eak_work_queue WHERE id=?", (id,)
                ).fetchone()
                self._assert_lease(row, worker)
                connection.execute(
                    """
                    UPDATE eak_work_queue
                    SET status=?, leased_until=NULL, lease_owner=NULL
                    WHERE id=?
                    """,
                    (status, id),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self.get(id)

    @staticmethod
    def _assert_lease(row: sqlite3.Row | None, worker: str) -> None:
        if row is None:
            raise KeyError("Work item not found")
        if row["status"] != "RUNNING" or row["lease_owner"] != worker:
            raise PermissionError("Work item is not leased by this worker")

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> WorkItem:
        return WorkItem(
            id=str(row["id"]),
            tenant=str(row["tenant"]),
            kind=str(row["kind"]),
            payload=json.loads(str(row["payload_json"])),
            status=str(row["status"]),
            attempts=int(row["attempts"]),
            max_attempts=int(row["max_attempts"]),
            lease_owner=row["lease_owner"],
            available_at=float(row["available_at"]),
            leased_until=None if row["leased_until"] is None else float(row["leased_until"]),
        )
