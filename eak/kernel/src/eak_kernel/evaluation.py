from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class MetricGate:
    metric: str
    operator: str
    threshold: float

    def passes(self, value: float) -> bool:
        if self.operator == ">=":
            return value >= self.threshold
        if self.operator == "<=":
            return value <= self.threshold
        if self.operator == ">":
            return value > self.threshold
        if self.operator == "<":
            return value < self.threshold
        raise ValueError(f"Unsupported metric gate operator: {self.operator}")


@dataclass(frozen=True)
class EvaluationResult:
    passed: bool
    failures: tuple[str, ...]


class EvaluationGate:
    """Deterministic production-eligibility gate over versioned metrics."""

    def __init__(self, gates: tuple[MetricGate, ...]) -> None:
        self.gates = gates

    def evaluate(self, metrics: Mapping[str, float]) -> EvaluationResult:
        failures: list[str] = []
        for gate in self.gates:
            if gate.metric not in metrics:
                failures.append(f"missing:{gate.metric}")
                continue
            if not gate.passes(float(metrics[gate.metric])):
                failures.append(
                    f"failed:{gate.metric}:{metrics[gate.metric]}{gate.operator}{gate.threshold}"
                )
        return EvaluationResult(passed=not failures, failures=tuple(failures))
