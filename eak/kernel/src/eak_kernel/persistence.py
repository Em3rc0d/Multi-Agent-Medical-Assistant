from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Lock

from .model import Event


class SQLiteEventStore:
    """Durable append-only execution event store using stdlib SQLite."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._lock = Lock()
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS eak_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_eak_events_execution ON eak_events(execution_id, sequence)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def append(self, event: Event) -> None:
        payload = json.dumps(dict(event.payload), separators=(",", ":"), sort_keys=True)
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO eak_events(execution_id, event_type, payload_json) VALUES (?, ?, ?)",
                (event.execution_id, event.type, payload),
            )

    def stream(self, execution_id: str) -> tuple[Event, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT event_type, payload_json FROM eak_events WHERE execution_id=? ORDER BY sequence ASC",
                (execution_id,),
            ).fetchall()
        return tuple(Event(event_type, execution_id, json.loads(payload)) for event_type, payload in rows)
