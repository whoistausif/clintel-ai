from __future__ import annotations

import pandas as pd

from .cohort import FEATURES, validate_cohort


def aggregate_temporal_observations(observations: pd.DataFrame, admissions: pd.DataFrame) -> pd.DataFrame:
    """Aggregate observations available by index_time into temporal summary features.

    Required observations columns: admission_id, observed_at, heart_rate, sbp,
    creatinine. Events at or after index_time are excluded to prevent leakage.
    """
    required_obs = {"admission_id", "observed_at", "heart_rate", "sbp", "creatinine"}
    required_adm = {"admission_id", "patient_id", "index_time"}
    if required_obs - set(observations) or required_adm - set(admissions):
        raise ValueError("Temporal input is missing required columns")
    obs = observations.copy()
    adm = admissions[list(required_adm)].copy()
    obs["observed_at"] = pd.to_datetime(obs.observed_at, utc=True, errors="coerce")
    adm["index_time"] = pd.to_datetime(adm.index_time, utc=True, errors="coerce")
    joined = obs.merge(adm, on="admission_id", how="inner", validate="many_to_one")
    eligible = joined[(joined.observed_at.notna()) & (joined.index_time.notna()) & (joined.observed_at < joined.index_time)]
    aggregates = eligible.groupby("admission_id").agg(
        heart_rate_mean=("heart_rate", "mean"), sbp_mean=("sbp", "mean"),
        creatinine_max=("creatinine", "max"), observation_count=("observed_at", "count"),
    ).reset_index()
    return adm.merge(aggregates, on="admission_id", how="left")


def prepare_model_table(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    cohort = validate_cohort(frame)
    table = cohort[["patient_id", "admission_id", "index_time", "feature_cutoff_time", "outcome_time", *FEATURES, "readmitted_30d"]].copy()
    return table, FEATURES.copy()
