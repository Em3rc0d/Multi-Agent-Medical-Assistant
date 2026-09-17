from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .evidence import EvidenceEdge, EvidenceGraph, EvidenceNode


class SQLiteEvidenceStore:
    """Execution-scoped durable EvidenceGraph persistence."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS eak_evidence_nodes (
                    execution_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    node_type TEXT NOT NULL,
                    attributes_json TEXT NOT NULL,
                    PRIMARY KEY (execution_id, node_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS eak_evidence_edges (
                    execution_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    PRIMARY KEY (execution_id, source_id, target_id, relation)
                )
                """
            )

    def save(self, execution_id: str, graph: EvidenceGraph) -> None:
        with sqlite3.connect(self.path) as connection:
            for node in graph.nodes:
                body = json.dumps(node.attributes, separators=(",", ":"), sort_keys=True)
                existing = connection.execute(
                    "SELECT node_type, attributes_json FROM eak_evidence_nodes WHERE execution_id=? AND node_id=?",
                    (execution_id, node.id),
                ).fetchone()
                if existing is not None and existing != (node.type, body):
                    raise ValueError(f"Evidence node id collision: {node.id}")
                connection.execute(
                    "INSERT OR IGNORE INTO eak_evidence_nodes(execution_id, node_id, node_type, attributes_json) VALUES (?, ?, ?, ?)",
                    (execution_id, node.id, node.type, body),
                )
            for edge in graph.edges:
                connection.execute(
                    "INSERT OR IGNORE INTO eak_evidence_edges(execution_id, source_id, target_id, relation) VALUES (?, ?, ?, ?)",
                    (execution_id, edge.source, edge.target, edge.relation),
                )

    def load(self, execution_id: str) -> EvidenceGraph:
        graph = EvidenceGraph()
        with sqlite3.connect(self.path) as connection:
            node_rows = connection.execute(
                "SELECT node_id, node_type, attributes_json FROM eak_evidence_nodes WHERE execution_id=? ORDER BY node_id",
                (execution_id,),
            ).fetchall()
            edge_rows = connection.execute(
                "SELECT source_id, target_id, relation FROM eak_evidence_edges WHERE execution_id=? ORDER BY source_id, target_id, relation",
                (execution_id,),
            ).fetchall()
        for node_id, node_type, attributes_json in node_rows:
            graph.add_node(EvidenceNode(str(node_id), str(node_type), json.loads(attributes_json)))
        for source_id, target_id, relation in edge_rows:
            graph.add_edge(EvidenceEdge(str(source_id), str(target_id), str(relation)))
        return graph
