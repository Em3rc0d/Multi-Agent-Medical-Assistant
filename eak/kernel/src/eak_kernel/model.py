from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


@dataclass(frozen=True, order=True)
class Ref:
    id: str
    version: str

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Ref":
        return cls(id=str(value["id"]), version=str(value["version"]))

    def as_dict(self) -> dict[str, str]:
        return {"id": self.id, "version": self.version}


class ExecutionState(StrEnum):
    CREATED = "CREATED"
    COMPILING = "COMPILING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


TERMINAL_STATES = {
    ExecutionState.SUCCEEDED,
    ExecutionState.FAILED,
    ExecutionState.CANCELLED,
}


@dataclass(frozen=True)
class PolicyDecision:
    effect: str
    reasons: tuple[str, ...] = ()
    obligations: tuple[str, ...] = ()
    constraints: Mapping[str, Any] = field(default_factory=dict)
    policy_version: str | None = None


@dataclass(frozen=True)
class CandidateSelection:
    provider: Ref
    rejected: Mapping[Ref, tuple[str, ...]]
    selection_profile: str


@dataclass(frozen=True)
class CertificationRecord:
    provider: Ref
    profile: str
    status: str = "CERTIFIED"
    domain: Ref | None = None


@dataclass(frozen=True)
class Event:
    type: str
    execution_id: str
    payload: Mapping[str, Any] = field(default_factory=dict)
