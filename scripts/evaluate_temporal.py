from __future__ import annotations

import json
import os

from clinintel.cohort import load_approved_csv
from clinintel.modeling import temporal_validation


def main() -> None:
    source = os.getenv("CLINTEL_APPROVED_COHORT_CSV")
    if not source:
        raise SystemExit("Set CLINTEL_APPROVED_COHORT_CSV to an approved local cohort export.")
    cohort = load_approved_csv(source)
    report = temporal_validation(cohort)
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
