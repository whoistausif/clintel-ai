from __future__ import annotations

import os

from clinintel.cohort import load_approved_csv, make_synthetic_cohort
from clinintel.config import settings
from clinintel.modeling import train_and_save


def main() -> None:
    source = os.getenv("CLINTEL_APPROVED_COHORT_CSV")
    if source:
        cohort = load_approved_csv(source)
        print(f"Training from an explicitly supplied approved local CSV; rows={len(cohort)}. Keep this file private.")
    elif settings.environment == "development" and settings.data_mode == "synthetic":
        cohort = make_synthetic_cohort()
        print("Training on synthetic development data only; resulting metrics are not clinical evidence.")
    else:
        raise SystemExit("Set CLINTEL_APPROVED_COHORT_CSV to an approved local cohort; no synthetic training in this mode.")
    metadata = train_and_save(cohort, settings.model_path)
    print(f"Saved model artifact: {settings.model_path}")
    print(f"Model version: {metadata['model_version']} | data origin: {metadata['data_origin']}")
    print(f"Evaluation summary: {metadata['metrics']}")


if __name__ == "__main__":
    main()
