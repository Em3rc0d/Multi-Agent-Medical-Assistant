from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .approval import ApprovalDecision, ApprovalRequest, ApprovalVerifier


class SQLiteApprovalStore:
    """Durable approval requests and immutable reviewer decisions."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS eak_approval_requests (id TEXT PRIMARY KEY, body_json TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS eak_approval_decisions (request_id TEXT PRIMARY KEY, body_json TEXT NOT NULL)"
            )

    def put_request(self, request: ApprovalRequest) -> None:
        body = self._request_to_json(request)
        with sqlite3.connect(self.path) as connection:
            existing = connection.execute(
                "SELECT body_json FROM eak_approval_requests WHERE id=?", (request.id,)
            ).fetchone()
            if existing is not None and existing[0] != body:
                raise ValueError("Approval request id collision")
            connection.execute(
                "INSERT OR IGNORE INTO eak_approval_requests(id, body_json) VALUES (?, ?)",
                (request.id, body),
            )

    def record_decision(self, decision: ApprovalDecision) -> None:
        request = self.get_request(decision.request_id)
        ApprovalVerifier.verify(request, decision)
        body = self._decision_to_json(decision)
        with sqlite3.connect(self.path) as connection:
            existing = connection.execute(
                "SELECT body_json FROM eak_approval_decisions WHERE request_id=?",
                (decision.request_id,),
            ).fetchone()
            if existing is not None:
                if existing[0] == body:
                    return
                raise ValueError("Approval decisions are immutable")
            connection.execute(
                "INSERT INTO eak_approval_decisions(request_id, body_json) VALUES (?, ?)",
                (decision.request_id, body),
            )

    def get_request(self, request_id: str) -> ApprovalRequest:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT body_json FROM eak_approval_requests WHERE id=?", (request_id,)
            ).fetchone()
        if row is None:
            raise KeyError("Approval request not found")
        value = json.loads(row[0])
        return ApprovalRequest(
            id=value["id"], execution_id=value["execution_id"], node_id=value["node_id"],
            profile=value["profile"], required_roles=tuple(value["required_roles"]),
            scope=tuple(value["scope"]),
        )

    def get_decision(self, request_id: str) -> ApprovalDecision | None:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT body_json FROM eak_approval_decisions WHERE request_id=?", (request_id,)
            ).fetchone()
        if row is None:
            return None
        value = json.loads(row[0])
        return ApprovalDecision(
            request_id=value["request_id"], execution_id=value["execution_id"],
            principal_ref=value["principal_ref"], authenticated_roles=tuple(value["authenticated_roles"]),
            decision=value["decision"], comment=value["comment"], timestamp=value["timestamp"],
            evidence=dict(value["evidence"]),
        )

    @staticmethod
    def _request_to_json(request: ApprovalRequest) -> str:
        return json.dumps({
            "id": request.id,
            "execution_id": request.execution_id,
            "node_id": request.node_id,
            "profile": request.profile,
            "required_roles": list(request.required_roles),
            "scope": list(request.scope),
        }, separators=(",", ":"), sort_keys=True)

    @staticmethod
    def _decision_to_json(decision: ApprovalDecision) -> str:
        return json.dumps({
            "request_id": decision.request_id,
            "execution_id": decision.execution_id,
            "principal_ref": decision.principal_ref,
            "authenticated_roles": list(decision.authenticated_roles),
            "decision": decision.decision,
            "comment": decision.comment,
            "timestamp": decision.timestamp,
            "evidence": dict(decision.evidence),
        }, separators=(",", ":"), sort_keys=True)
