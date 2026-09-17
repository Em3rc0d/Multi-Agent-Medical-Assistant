from __future__ import annotations

import argparse
import json

from .readiness import ProductionReadinessChecker, load_profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate an EAK deployment profile")
    parser.add_argument("--profile", required=True)
    args = parser.parse_args()
    report = ProductionReadinessChecker.check(load_profile(args.profile))
    print(json.dumps({
        "ready": report.ready,
        "blockers": list(report.blockers),
        "warnings": list(report.warnings),
    }, indent=2, sort_keys=True))
    return 0 if report.ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
