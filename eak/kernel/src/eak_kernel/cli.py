from __future__ import annotations

import argparse
import json
from pathlib import Path

from .conformance import PaperConformanceHarness


def main() -> int:
    parser = argparse.ArgumentParser(description="Run EAK v0.2 cross-domain conformance")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    results = PaperConformanceHarness(args.root).run_all()
    print(json.dumps(results, indent=2))
    return 0 if all(item["pass"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
