import numpy as np

from clinintel.modeling import evaluate, temporal_validation, train_and_save
from clinintel.cohort import make_synthetic_cohort


def test_evaluation_returns_discrimination_calibration_and_threshold_metrics():
    y = np.array([0, 0, 1, 1, 0, 1])
    probability = np.array([.1, .3, .6, .9, .2, .7])
    result = evaluate(y, probability)
    for field in ("auroc", "auprc", "auroc_95ci", "brier_score", "expected_calibration_error_10bin", "precision", "recall", "f1", "confusion_matrix_tn_fp_fn_tp", "calibration_bins"):
        assert field in result
    assert result["auroc"] == 1.0


def test_training_tracks_group_splits_and_synthetic_provenance(tmp_path):
    metadata = train_and_save(make_synthetic_cohort(300), tmp_path / "model.joblib")
    assert metadata["n_train"] + metadata["n_validation"] + metadata["n_test"] == 300
    assert metadata["data_origin"] == "synthetic"
    assert metadata["subgroup_metrics_age"]
    assert "random_forest_candidate" in metadata["model_comparison"]
    assert metadata["model_comparison"]["random_forest_candidate"]["selected"] is False
    assert (tmp_path / "model.joblib").exists()


def test_temporal_validation_uses_later_holdout_and_reports_provenance():
    report = temporal_validation(make_synthetic_cohort(300))
    assert report["train_rows"] >= 20
    assert report["test_rows"] >= 20
    assert report["overlapping_patients_removed_from_train"] == 0
    assert report["data_origin"] == "synthetic"
