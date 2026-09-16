from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Lock

from .approval import ApprovalDecision, ApprovalRequest, ApprovalVerifier


class SQLiteApprovalStore:
    """Durable approval requests and immutable decisions."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._lock = Lock()
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS eak_approval_requests (
                    id TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    profile TEXT NOT NULL,
                    required_roles_json TEXT NOT NULL,
                    scope_json TEXT NOT NULL
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS eak_approval_decisions (
                    request_id TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL,
                    principal_ref TEXT NOT NULL,
                    authenticated_roles_json TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    comment TEXT,
                    timestamp TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    FOREIGN KEY(request_id) REFERENCES eak_approval_requests(id)
                )"""
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def create(self, request: ApprovalRequest) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO eak_approval_requests
                   (id, execution_id, node_id, profile, required_roles_json, scope_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    request.id,
                    request.execution_id,
                    request.node_id,
                    request.profile,
                    json.dumps(request.required_roles),
                    json.dumps(request.scope),
                ),
            )

    def get_request(self, request_id: str) -> ApprovalRequest:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM eak_approval_requests WHERE id=?", (request_id,)
            ).fetchone()
        if row is None:
            raise KeyError("Approval request not found")
        return ApprovalRequest(
            id=row["id"],
            execution_id=row["execution_id"],
            node_id=row["node_id"],
            profile=row["profile"],
            required_roles=tuple(json.loads(row["required_roles_json"])),
            scope=tuple(json.loads(row["scope_json"])),
        )

    def decide(self, decision: ApprovalDecision) -> None:
        request = self.get_request(decision.request_id)
        ApprovalVerifier.verify(request, decision)
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO eak_approval_decisions
                   (request_id, execution_id, principal_ref, authenticated_roles_json, decision, comment, timestamp, evidence_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    decision.request_id,
                    decision.execution_id,
                    decision.principal_ref,
                    json.dumps(decision.authenticated_roles),
                    decision.decision,
                    decision.comment,
                    decision.timestamp,
                    json.dumps(decision.evidence, sort_keys=True),
                ),
            )

    def get_decision(self, request_id: str) -> ApprovalDecision | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM eak_approval_decisions WHERE request_id=?", (request_id,)
            ).fetchone()
        if row is None:
            return None
        return ApprovalDecision(
            request_id=row["request_id"],
            execution_id=row["execution_id"],
            principal_ref=row["principal_ref"],
            authenticated_roles=tuple(json.loads(row["authenticated_roles_json"])),
            decision=row["decision"],
            comment=row["comment"],
            timestamp=row["timestamp"],
            evidence=json.loads(row["evidence_json"]),
        )
