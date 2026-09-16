from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Lock

from .evidence import EvidenceEdge, EvidenceGraph, EvidenceNode


class SQLiteEvidenceStore:
    """Durable execution-scoped EvidenceGraph persistence."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._lock = Lock()
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS eak_evidence_graphs (
                    execution_id TEXT NOT NULL,
                    graph_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    PRIMARY KEY(execution_id, graph_id)
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS eak_evidence_nodes (
                    execution_id TEXT NOT NULL,
                    graph_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    node_type TEXT NOT NULL,
                    attributes_json TEXT NOT NULL,
                    PRIMARY KEY(execution_id, graph_id, node_id),
                    FOREIGN KEY(execution_id, graph_id) REFERENCES eak_evidence_graphs(execution_id, graph_id) ON DELETE CASCADE
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS eak_evidence_edges (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    graph_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    FOREIGN KEY(execution_id, graph_id) REFERENCES eak_evidence_graphs(execution_id, graph_id) ON DELETE CASCADE
                )"""
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def save(self, *, execution_id: str, graph_id: str, graph: EvidenceGraph, version: str = "1.0.0") -> None:
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN")
            connection.execute(
                "INSERT OR REPLACE INTO eak_evidence_graphs(execution_id, graph_id, version) VALUES (?, ?, ?)",
                (execution_id, graph_id, version),
            )
            connection.execute(
                "DELETE FROM eak_evidence_edges WHERE execution_id=? AND graph_id=?",
                (execution_id, graph_id),
            )
            connection.execute(
                "DELETE FROM eak_evidence_nodes WHERE execution_id=? AND graph_id=?",
                (execution_id, graph_id),
            )
            connection.executemany(
                """INSERT INTO eak_evidence_nodes
                   (execution_id, graph_id, node_id, node_type, attributes_json) VALUES (?, ?, ?, ?, ?)""",
                [
                    (execution_id, graph_id, node.id, node.type, json.dumps(node.attributes, sort_keys=True))
                    for node in graph.nodes
                ],
            )
            connection.executemany(
                """INSERT INTO eak_evidence_edges
                   (execution_id, graph_id, source_id, target_id, relation) VALUES (?, ?, ?, ?, ?)""",
                [
                    (execution_id, graph_id, edge.source, edge.target, edge.relation)
                    for edge in graph.edges
                ],
            )
            connection.commit()

    def load(self, *, execution_id: str, graph_id: str) -> EvidenceGraph:
        with self._connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM eak_evidence_graphs WHERE execution_id=? AND graph_id=?",
                (execution_id, graph_id),
            ).fetchone()
            if exists is None:
                raise KeyError("Evidence graph not found")
            nodes = connection.execute(
                """SELECT node_id, node_type, attributes_json FROM eak_evidence_nodes
                   WHERE execution_id=? AND graph_id=? ORDER BY rowid ASC""",
                (execution_id, graph_id),
            ).fetchall()
            edges = connection.execute(
                """SELECT source_id, target_id, relation FROM eak_evidence_edges
                   WHERE execution_id=? AND graph_id=? ORDER BY sequence ASC""",
                (execution_id, graph_id),
            ).fetchall()
        graph = EvidenceGraph()
        for row in nodes:
            graph.add_node(
                EvidenceNode(row["node_id"], row["node_type"], json.loads(row["attributes_json"]))
            )
        for row in edges:
            graph.add_edge(EvidenceEdge(row["source_id"], row["target_id"], row["relation"]))
        return graph
