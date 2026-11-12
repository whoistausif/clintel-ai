import pandas as pd
import pytest
from sklearn.model_selection import GroupShuffleSplit

from clinintel.cohort import FEATURES, LABEL, make_synthetic_cohort, validate_cohort
from clinintel.preprocessing import aggregate_temporal_observations


def test_synthetic_cohort_is_reproducible_and_valid():
    first = make_synthetic_cohort(100, seed=5)
    second = make_synthetic_cohort(100, seed=5)
    pd.testing.assert_frame_equal(first, second)
    assert len(validate_cohort(first)) == 100


def test_invalid_positive_label_horizon_is_rejected():
    frame = make_synthetic_cohort(40)
    frame.loc[0, "outcome_time"] = frame.loc[0, "index_time"] + pd.Timedelta(45, unit="D")
    frame.loc[0, LABEL] = 1
    with pytest.raises(ValueError, match="within 30 days"):
        validate_cohort(frame)


def test_missing_required_columns_are_rejected():
    frame = make_synthetic_cohort(40).drop(columns=["age"])
    with pytest.raises(ValueError, match="age"):
        validate_cohort(frame)


def test_features_recorded_after_index_time_are_rejected():
    frame = make_synthetic_cohort(40)
    frame.loc[0, "feature_cutoff_time"] = frame.loc[0, "index_time"] + pd.Timedelta(1, unit="D")
    with pytest.raises(ValueError, match="prevent leakage"):
        validate_cohort(frame)


def test_grouped_split_has_no_patient_overlap():
    frame = make_synthetic_cohort(200)
    y = frame[LABEL]
    groups = frame.patient_id
    splitter = GroupShuffleSplit(n_splits=1, test_size=.2, random_state=41)
    train_idx, test_idx = next(splitter.split(frame[FEATURES], y, groups=groups))
    assert set(groups.iloc[train_idx]).isdisjoint(set(groups.iloc[test_idx]))


def test_temporal_aggregation_excludes_observations_at_or_after_index():
    admissions = pd.DataFrame([{"admission_id":"A1", "patient_id":"P1", "index_time":"2024-01-02T00:00:00Z"}])
    observations = pd.DataFrame([
        {"admission_id":"A1", "observed_at":"2024-01-01T12:00:00Z", "heart_rate":70, "sbp":120, "creatinine":1.0},
        {"admission_id":"A1", "observed_at":"2024-01-02T00:00:00Z", "heart_rate":180, "sbp":200, "creatinine":9.0},
    ])
    result = aggregate_temporal_observations(observations, admissions).iloc[0]
    assert result.heart_rate_mean == 70
    assert result.sbp_mean == 120
    assert result.creatinine_max == 1
