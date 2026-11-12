from __future__ import annotations

import os

import pandas as pd
import psycopg

from clinintel.cohort import load_approved_csv


def main() -> None:
    source = os.getenv("CLINTEL_APPROVED_COHORT_CSV")
    database_url = os.getenv("CLINTEL_INGEST_DATABASE_URL")
    if not source or not database_url:
        raise SystemExit("Set CLINTEL_APPROVED_COHORT_CSV and a secured CLINTEL_INGEST_DATABASE_URL in the approved environment.")
    cohort_version = os.getenv("CLINTEL_COHORT_VERSION", "cohort-0.1.0")
    cohort = load_approved_csv(source)
    # This is a deliberate local, governed ingestion. Row-level data is never printed.
    patients_by_id = {}
    admissions = []
    features = []
    outcomes = []
    for row in cohort.to_dict(orient="records"):
        patient_id = str(row["patient_id"])
        admission_id = str(row["admission_id"])
        sex = str(row["sex"]) if pd.notna(row.get("sex")) else None
        index_time = row["index_time"].to_pydatetime()
        cutoff_time = row["feature_cutoff_time"].to_pydatetime()
        outcome_time = row["outcome_time"].to_pydatetime() if row["outcome_time"] is not None and str(row["outcome_time"]) != "NaT" else None
        origin = str(row.get("data_origin", "approved-cohort"))
        patients_by_id[patient_id] = (patient_id, int(row["age"]), sex, "approved-cohort")
        admissions.append((admission_id, patient_id, index_time, index_time, origin, cohort_version))
        numeric = lambda name: None if pd.isna(row[name]) else float(row[name])
        features.append((admission_id, patient_id, cutoff_time, numeric("heart_rate_mean"), numeric("sbp_mean"), numeric("creatinine_max"), numeric("prior_admissions"), numeric("length_of_stay"), cohort_version))
        outcomes.append((admission_id, "readmitted_30d", 30, outcome_time, int(row["readmitted_30d"]), cohort_version))

    with psycopg.connect(database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.executemany("INSERT INTO patients (patient_id, age, sex, dataset_tag) VALUES (%s, %s, %s, %s) ON CONFLICT (patient_id) DO UPDATE SET age = EXCLUDED.age, sex = COALESCE(EXCLUDED.sex, patients.sex), dataset_tag = EXCLUDED.dataset_tag", list(patients_by_id.values()))
            cursor.executemany("INSERT INTO admissions (admission_id, patient_id, index_time, discharge_time, data_origin, cohort_version) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (admission_id) DO UPDATE SET index_time = EXCLUDED.index_time, discharge_time = EXCLUDED.discharge_time, data_origin = EXCLUDED.data_origin, cohort_version = EXCLUDED.cohort_version", admissions)
            cursor.executemany("INSERT INTO admission_features (admission_id, patient_id, feature_cutoff_time, heart_rate_mean, sbp_mean, creatinine_max, prior_admissions, length_of_stay, cohort_version) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (admission_id) DO UPDATE SET feature_cutoff_time = EXCLUDED.feature_cutoff_time, heart_rate_mean = EXCLUDED.heart_rate_mean, sbp_mean = EXCLUDED.sbp_mean, creatinine_max = EXCLUDED.creatinine_max, prior_admissions = EXCLUDED.prior_admissions, length_of_stay = EXCLUDED.length_of_stay, cohort_version = EXCLUDED.cohort_version", features)
            cursor.executemany("INSERT INTO admission_outcomes (admission_id, outcome_name, horizon_days, outcome_time, label, cohort_version) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (admission_id, outcome_name, horizon_days) DO UPDATE SET outcome_time = EXCLUDED.outcome_time, label = EXCLUDED.label, cohort_version = EXCLUDED.cohort_version", outcomes)
    print(f"Imported {len(cohort)} approved, deidentified admissions for {cohort.patient_id.nunique()} patients. No patient-level values were printed.")


if __name__ == "__main__":
    main()
