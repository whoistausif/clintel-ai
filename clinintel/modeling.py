from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .cohort import FEATURES, LABEL, CohortSpec, make_synthetic_cohort, validate_cohort

MODEL_VERSION = "baseline-logistic-0.1.0"


def build_model() -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scale", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=41)),
    ])


def build_random_forest() -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("classifier", RandomForestClassifier(n_estimators=200, min_samples_leaf=5, class_weight="balanced_subsample", n_jobs=-1, random_state=41)),
    ])


def _bootstrap_auc_ci(y: np.ndarray, prob: np.ndarray, seed: int = 41, samples: int = 300) -> list[float] | None:
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(samples):
        idx = rng.integers(0, len(y), len(y))
        if len(np.unique(y[idx])) == 2:
            values.append(roc_auc_score(y[idx], prob[idx]))
    if not values:
        return None
    return [round(float(np.quantile(values, 0.025)), 4), round(float(np.quantile(values, 0.975)), 4)]


def _ece(y: np.ndarray, prob: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0, 1, bins + 1)
    error = 0.0
    for left, right in zip(edges[:-1], edges[1:]):
        mask = (prob >= left) & (prob < right if right < 1 else prob <= right)
        if mask.any():
            error += float(mask.mean()) * abs(float(y[mask].mean()) - float(prob[mask].mean()))
    return error


def evaluate(y: np.ndarray, prob: np.ndarray, threshold: float = 0.5) -> dict:
    pred = (prob >= threshold).astype(int)
    cm = confusion_matrix(y, pred, labels=[0, 1]).tolist()
    return {
        "n_test": int(len(y)),
        "prevalence": round(float(np.mean(y)), 4),
        "auroc": round(float(roc_auc_score(y, prob)), 4) if len(np.unique(y)) > 1 else None,
        "auroc_95ci": _bootstrap_auc_ci(y, prob),
        "auprc": round(float(average_precision_score(y, prob)), 4) if len(np.unique(y)) > 1 else None,
        "brier_score": round(float(brier_score_loss(y, prob)), 4),
        "expected_calibration_error_10bin": round(_ece(y, prob), 4),
        "threshold": threshold,
        "precision": round(float(precision_score(y, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y, pred, zero_division=0)), 4),
        "confusion_matrix_tn_fp_fn_tp": cm,
        "calibration_bins": calibration_bins(y, prob),
    }


def calibration_bins(y: np.ndarray, prob: np.ndarray, bins: int = 10) -> list[dict]:
    edges = np.linspace(0, 1, bins + 1)
    output = []
    for index, (left, right) in enumerate(zip(edges[:-1], edges[1:])):
        mask = (prob >= left) & (prob < right if index < bins - 1 else prob <= right)
        if mask.any():
            output.append({"bin": index + 1, "n": int(mask.sum()), "mean_predicted": round(float(prob[mask].mean()), 4), "observed_rate": round(float(y[mask].mean()), 4)})
    return output


def train_and_save(frame: pd.DataFrame | None = None, output: str | Path = "artifacts/readmission-demo.joblib") -> dict:
    cohort = validate_cohort(frame if frame is not None else make_synthetic_cohort())
    y = cohort[LABEL].astype(int).to_numpy()
    holdout_split = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=41)
    train_val_idx, test_idx = next(holdout_split.split(cohort[FEATURES], y, groups=cohort["patient_id"]))
    train_val = cohort.iloc[train_val_idx]
    validation_split = GroupShuffleSplit(n_splits=1, test_size=0.1765, random_state=42)
    train_rel, val_rel = next(validation_split.split(train_val[FEATURES], train_val[LABEL], groups=train_val["patient_id"]))
    train, validation, test = train_val.iloc[train_rel], train_val.iloc[val_rel], cohort.iloc[test_idx]
    if any(part[LABEL].nunique() < 2 for part in (train, validation, test)):
        raise ValueError("Train, validation, and test partitions must each contain both outcome classes")
    model = build_model().fit(train[FEATURES], train[LABEL].astype(int))
    validation_prob = model.predict_proba(validation[FEATURES])[:, 1]
    test_prob = model.predict_proba(test[FEATURES])[:, 1]
    metrics = evaluate(test[LABEL].astype(int).to_numpy(), test_prob)
    validation_metrics = evaluate(validation[LABEL].astype(int).to_numpy(), validation_prob)
    forest = build_random_forest().fit(train[FEATURES], train[LABEL].astype(int))
    forest_validation = evaluate(validation[LABEL].astype(int).to_numpy(), forest.predict_proba(validation[FEATURES])[:, 1])
    forest_test = evaluate(test[LABEL].astype(int).to_numpy(), forest.predict_proba(test[FEATURES])[:, 1])
    metadata = {
        "model_version": MODEL_VERSION,
        "model_family": "LogisticRegression with median imputation and standard scaling",
        "features": FEATURES,
        "cohort": CohortSpec().__dict__,
        "data_origin": str(cohort.get("data_origin", pd.Series(["approved_csv"])).iloc[0]),
        "n_rows": int(len(cohort)),
        "n_patients": int(cohort.patient_id.nunique()),
        "n_train": int(len(train)),
        "n_validation": int(len(validation)),
        "n_test": int(len(test)),
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "validation_metrics": validation_metrics,
        "model_comparison": {
            "baseline_logistic_regression": {"validation": validation_metrics, "test": metrics},
            "random_forest_candidate": {"validation": forest_validation, "test": forest_test, "selected": False},
            "selection_note": "The logistic baseline remains the served model. Do not select a model from the test metrics; conduct prespecified validation and review first.",
        },
        "subgroup_metrics_age": subgroup_metrics(test, test_prob),
        "limitations": "Research prototype only. Synthetic benchmark metrics are not clinical evidence and must not guide care.",
    }
    parameter_bytes = b"".join(array.astype("<f8", copy=False).tobytes() for array in (model.named_steps["scale"].mean_, model.named_steps["scale"].scale_, model.named_steps["classifier"].coef_, model.named_steps["classifier"].intercept_))
    metadata["model_parameter_digest_sha256"] = hashlib.sha256(parameter_bytes).hexdigest()
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": model, "metadata": metadata}, path)
    return metadata


def load_model(path: str | Path) -> dict:
    path = Path(path)
    if not path.exists():
        return {"pipeline": None, "metadata": {"model_version": "not-trained", "metrics": None, "limitations": "Train the baseline before requesting a model output."}}
    return joblib.load(path)


def predict(bundle: dict, features: dict) -> dict:
    if bundle.get("pipeline") is None:
        raise RuntimeError("Model artifact is not trained")
    row = pd.DataFrame([{name: features.get(name) for name in FEATURES}])
    probability = float(bundle["pipeline"].predict_proba(row)[0, 1])
    band = "Elevated" if probability >= 0.65 else "Moderate" if probability >= 0.35 else "Lower"
    # Contributions are feature-level directional associations from the linear model.
    pipeline = bundle["pipeline"]
    imputed = pipeline.named_steps["impute"].transform(row)
    scaled = pipeline.named_steps["scale"].transform(imputed)[0]
    coefs = pipeline.named_steps["classifier"].coef_[0]
    contributions = sorted([
        {"feature": str(name), "contribution": round(float(coef * value), 4), "interpretation": "positive association with this model output" if coef * value > 0 else "negative association with this model output"}
        for name, coef, value in zip(FEATURES, coefs, scaled)
    ], key=lambda item: abs(item["contribution"]), reverse=True)[:6]
    return {"probability": round(probability, 4), "risk_band": band, "model_version": bundle["metadata"]["model_version"], "feature_contributions": contributions, "explanation_note": "Associations with this model output only; not causal or clinical conclusions."}


def subgroup_metrics(cohort: pd.DataFrame, predictions: np.ndarray) -> dict:
    """Descriptive subgroup evaluation; synthetic results must never be presented as clinical validity."""
    rows = cohort.reset_index(drop=True).copy()
    rows["probability"] = predictions
    rows["age_group"] = pd.cut(rows.age, [17, 39, 59, 120], labels=["18-39", "40-59", "60+"])
    result = {}
    for dimension in ["age_group", *(["sex"] if "sex" in rows else [])]:
        result[dimension] = {}
        for name, group in rows.groupby(dimension, observed=True, dropna=False):
            y, prob = group[LABEL].astype(int).to_numpy(), group.probability.to_numpy()
            result[dimension][str(name)] = {"n": int(len(group)), "positive_rate": round(float(y.mean()), 4), "auroc": round(float(roc_auc_score(y, prob)), 4) if len(np.unique(y)) > 1 else None, "data_origin": str(group.get("data_origin", pd.Series(["unknown"])).iloc[0])}
    return result


def temporal_validation(frame: pd.DataFrame) -> dict:
    """Train on earlier time and evaluate on later unseen patients, without threshold tuning."""
    cohort = validate_cohort(frame).sort_values("index_time").reset_index(drop=True)
    unique_times = cohort.index_time.drop_duplicates().sort_values()
    if len(unique_times) < 5:
        raise ValueError("Temporal validation needs at least five distinct index times")
    cutoff = unique_times.iloc[int(len(unique_times) * 0.8)]
    later = cohort[cohort.index_time >= cutoff]
    later_patients = set(later.patient_id)
    earlier = cohort[(cohort.index_time < cutoff) & ~cohort.patient_id.isin(later_patients)]
    if len(earlier) < 20 or len(later) < 20 or later[LABEL].nunique() < 2:
        raise ValueError("Temporal validation needs at least 20 earlier and later rows and both outcome classes in the later set")
    model = build_model().fit(earlier[FEATURES], earlier[LABEL].astype(int))
    probabilities = model.predict_proba(later[FEATURES])[:, 1]
    return {"cutoff_utc": cutoff.isoformat(), "train_rows": int(len(earlier)), "test_rows": int(len(later)), "overlapping_patients_removed_from_train": int(cohort[cohort.index_time < cutoff].patient_id.isin(later_patients).sum()), "metrics": evaluate(later[LABEL].astype(int).to_numpy(), probabilities), "data_origin": str(cohort.get("data_origin", pd.Series(["approved_csv"])).iloc[0]), "method": "chronological holdout with patient overlap removed"}
