# Model card: 30-day readmission baseline

## Intended use

Educational and research engineering demonstration. Not for diagnosis, treatment, triage, prioritization, or individual care decisions.

## Target and index

Target: binary next-hospital-admission label within 30 days after the index discharge (all-cause proxy). Index time: discharge. The query does not distinguish unplanned from planned admissions. Study-specific outcome definitions and exclusions require review.

## Model

Median imputation, standard scaling, and class-weighted logistic regression. Input allowlist: age, heart-rate mean, systolic blood-pressure mean, maximum creatinine, prior admissions, and length of stay. The outcome time is not a feature. Splits are grouped by patient.

## Data and results

The included benchmark is generated synthetic data. Runtime training saves held-out synthetic metrics, AUROC confidence intervals, calibration statistics, and age-group descriptive metrics into the model artifact. Those values must be described as synthetic software checks, not clinical performance. No approved clinical cohort has been evaluated in this repository.

## Limitations

No clinical validation, external validation, temporal validation, subgroup fairness review, clinician review, prospective study, or impact study has been completed. The chosen threshold and risk labels are illustrative. Explanations are associations and not causal.
