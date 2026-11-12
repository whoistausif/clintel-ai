from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

FEATURES = ["age", "heart_rate_mean", "sbp_mean", "creatinine_max", "prior_admissions", "length_of_stay"]
LABEL = "readmitted_30d"
REQUIRED = {"patient_id", "admission_id", "index_time", "feature_cutoff_time", LABEL, *FEATURES}


@dataclass(frozen=True)
class CohortSpec:
    name: str = "demo_readmission_30d"
    population: str = "Synthetic adult demo admissions"
    index_time: str = "discharge time"
    horizon_days: int = 30
    outcome: str = "Next hospital admission within 30 days after index discharge (all-cause proxy)"
    inclusion: str = "Synthetic adults age 18 or older with complete admission identifiers"
    exclusion: str = "Rows with missing identifiers, invalid dates, or outcome outside the 30-day horizon"


def validate_cohort(frame: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED - set(frame.columns)
    if missing:
        raise ValueError(f"Cohort is missing required columns: {', '.join(sorted(missing))}")
    data = frame.copy()
    if data["patient_id"].isna().any() or data["admission_id"].isna().any():
        raise ValueError("Patient and admission identifiers are required")
    if data["admission_id"].duplicated().any():
        raise ValueError("admission_id must be unique")
    if data[LABEL].isna().any():
        raise ValueError("readmitted_30d labels cannot be missing")
    for feature in FEATURES:
        data[feature] = pd.to_numeric(data[feature], errors="coerce")
    data["index_time"] = pd.to_datetime(data["index_time"], errors="coerce", utc=True)
    data["outcome_time"] = pd.to_datetime(data["outcome_time"], errors="coerce", utc=True)
    data["feature_cutoff_time"] = pd.to_datetime(data["feature_cutoff_time"], errors="coerce", utc=True)
    if data[["index_time", "feature_cutoff_time"]].isna().any().any():
        raise ValueError("Invalid index_time or feature_cutoff_time")
    if (data["feature_cutoff_time"] > data["index_time"]).any():
        raise ValueError("feature_cutoff_time must be at or before index_time to prevent leakage")
    if not set(data[LABEL].dropna().unique()).issubset({0, 1, False, True}):
        raise ValueError("readmitted_30d must be binary")
    if data["age"].isna().any() or ((data["age"] < 18) | (data["age"] > 120)).any():
        raise ValueError("The adult demo cohort excludes ages under 18")
    for feature, minimum, maximum in (("heart_rate_mean", 20, 300), ("sbp_mean", 30, 300), ("creatinine_max", 0, 100), ("prior_admissions", 0, 100), ("length_of_stay", 0, 365)):
        if ((data[feature] < minimum) | (data[feature] > maximum)).fillna(False).any():
            raise ValueError(f"{feature} has values outside the permitted validation range")
    # Labels are required to be temporally consistent with the documented horizon.
    horizon = (data["outcome_time"] - data["index_time"]).dt.total_seconds() / 86400
    positive = data[LABEL].astype(int) == 1
    if (positive & (data["outcome_time"].isna() | (horizon < 0) | (horizon > 30))).any():
        raise ValueError("Positive outcome_time must be within 30 days after index_time")
    if ((~positive) & data["outcome_time"].notna() & (horizon <= 30)).any():
        raise ValueError("Negative labels cannot have an outcome_time within 30 days after index_time")
    # Explicit guard against known post-index fields in the model input.
    forbidden = {"outcome_time", "readmitted_at", "discharge_disposition_after_index"} & set(FEATURES)
    if forbidden:
        raise ValueError(f"Post-index leakage columns found in FEATURES: {sorted(forbidden)}")
    return data


def load_approved_csv(path: str | Path) -> pd.DataFrame:
    """Load a locally approved, deidentified cohort export; never uploads or logs row values."""
    return validate_cohort(pd.read_csv(path))


def make_synthetic_cohort(n_patients: int = 1200, seed: int = 41) -> pd.DataFrame:
    """Create reproducible fictional rows only; synthetic labels are not clinical evidence."""
    rng = np.random.default_rng(seed)
    patient_num = np.arange(n_patients)
    age = rng.integers(18, 91, n_patients)
    hr = np.clip(rng.normal(79, 13, n_patients), 45, 145)
    sbp = np.clip(rng.normal(126, 19, n_patients), 75, 210)
    creat = np.clip(rng.lognormal(-0.05, 0.45, n_patients), 0.35, 5.8)
    prior = rng.poisson(0.75, n_patients)
    los = np.clip(rng.gamma(2.0, 2.1, n_patients), 0.5, 30)
    logits = -3.0 + 0.027 * (age - 55) + 0.22 * prior + 0.16 * (los - 4) + 0.38 * (creat - 1.1) + 0.012 * (hr - 78) - 0.006 * (sbp - 125)
    probability = 1 / (1 + np.exp(-logits))
    labels = rng.binomial(1, probability)
    index = pd.Timestamp("2024-01-01", tz="UTC") + pd.to_timedelta(rng.integers(0, 700, n_patients), unit="D")
    outcome_days = np.where(labels == 1, rng.integers(1, 31, n_patients), rng.integers(31, 91, n_patients))
    return pd.DataFrame({
        "patient_id": [f"SYN-P-{i:05d}" for i in patient_num],
        "admission_id": [f"SYN-A-{i:05d}" for i in patient_num],
        "index_time": index,
        "outcome_time": index + pd.to_timedelta(outcome_days, unit="D"),
        "feature_cutoff_time": index,
        "age": age,
        "heart_rate_mean": hr.round(1),
        "sbp_mean": sbp.round(1),
        "creatinine_max": creat.round(2),
        "prior_admissions": prior,
        "length_of_stay": los.round(1),
        LABEL: labels,
        "data_origin": "synthetic",
        "sex": rng.choice(["F", "M"], n_patients),
    })
