from __future__ import annotations

import json
import sqlite3
from hashlib import sha256
from pathlib import Path
from threading import Lock

from .approval import ApprovalDecision, ApprovalRequest, ApprovalVerifier


class SQLiteApprovalStore:
    """Durable local store for authenticated approval records."""

    deployment_tier = "local-durable"

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._lock = Lock()
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS eak_approvals (
                    request_id TEXT PRIMARY KEY,
                    record_json TEXT NOT NULL,
                    record_hash TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=30)

    @staticmethod
    def _digest(record_json: str) -> str:
        return sha256(record_json.encode("utf-8")).hexdigest()

    @staticmethod
    def _serialize(request: ApprovalRequest, decision: ApprovalDecision) -> str:
        payload = {
            "request": {
                "id": request.id,
                "execution_id": request.execution_id,
                "node_id": request.node_id,
                "profile": request.profile,
                "required_roles": list(request.required_roles),
                "scope": list(request.scope),
            },
            "decision": {
                "request_id": decision.request_id,
                "execution_id": decision.execution_id,
                "principal_ref": decision.principal_ref,
                "authenticated_roles": list(decision.authenticated_roles),
                "decision": decision.decision,
                "comment": decision.comment,
                "timestamp": decision.timestamp,
                "evidence": decision.evidence,
            },
        }
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)

    def record(self, request: ApprovalRequest, decision: ApprovalDecision) -> None:
        ApprovalVerifier.verify(request, decision)
        record_json = self._serialize(request, decision)
        digest = self._digest(record_json)
        try:
            with self._lock, self._connect() as connection:
                connection.execute(
                    "INSERT INTO eak_approvals(request_id, record_json, record_hash) VALUES (?, ?, ?)",
                    (request.id, record_json, digest),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Approval request already recorded: {request.id}") from exc

    def load(self, request_id: str) -> tuple[ApprovalRequest, ApprovalDecision] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_json, record_hash FROM eak_approvals WHERE request_id=?",
                (request_id,),
            ).fetchone()
        if row is None:
            return None
        record_json, digest = row
        if self._digest(record_json) != digest:
            raise ValueError("Approval record integrity check failed")
        payload = json.loads(record_json)
        request_data = payload["request"]
        decision_data = payload["decision"]
        request = ApprovalRequest(
            id=request_data["id"],
            execution_id=request_data["execution_id"],
            node_id=request_data["node_id"],
            profile=request_data["profile"],
            required_roles=tuple(request_data["required_roles"]),
            scope=tuple(request_data["scope"]),
        )
        decision = ApprovalDecision(
            request_id=decision_data["request_id"],
            execution_id=decision_data["execution_id"],
            principal_ref=decision_data["principal_ref"],
            authenticated_roles=tuple(decision_data["authenticated_roles"]),
            decision=decision_data["decision"],
            comment=decision_data["comment"],
            timestamp=decision_data["timestamp"],
            evidence=dict(decision_data["evidence"]),
        )
        ApprovalVerifier.verify(request, decision)
        return request, decision
