from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SnapshotEntry:
    path: str
    sha256: str
    size: int


@dataclass(frozen=True)
class SnapshotManifest:
    entries: tuple[SnapshotEntry, ...]

    def to_json(self) -> str:
        return json.dumps(
            {"entries": [asdict(entry) for entry in self.entries]},
            separators=(",", ":"),
            sort_keys=True,
        )

    @classmethod
    def from_json(cls, value: str) -> "SnapshotManifest":
        data = json.loads(value)
        return cls(tuple(SnapshotEntry(**entry) for entry in data["entries"]))


def build_manifest(root: str | Path, paths: Iterable[str | Path]) -> SnapshotManifest:
    base = Path(root).resolve()
    entries: list[SnapshotEntry] = []
    for raw in paths:
        path = Path(raw).resolve()
        if base != path and base not in path.parents:
            raise ValueError("Snapshot path escaped root")
        if not path.is_file():
            raise FileNotFoundError(path)
        relative = path.relative_to(base).as_posix()
        data = path.read_bytes()
        entries.append(SnapshotEntry(relative, sha256(data).hexdigest(), len(data)))
    return SnapshotManifest(tuple(sorted(entries, key=lambda entry: entry.path)))


def verify_manifest(root: str | Path, manifest: SnapshotManifest) -> tuple[str, ...]:
    base = Path(root).resolve()
    failures: list[str] = []
    for entry in manifest.entries:
        path = (base / entry.path).resolve()
        if base not in path.parents and path != base:
            failures.append(f"path-escape:{entry.path}")
            continue
        if not path.is_file():
            failures.append(f"missing:{entry.path}")
            continue
        data = path.read_bytes()
        if len(data) != entry.size:
            failures.append(f"size:{entry.path}")
            continue
        if sha256(data).hexdigest() != entry.sha256:
            failures.append(f"digest:{entry.path}")
    return tuple(failures)
