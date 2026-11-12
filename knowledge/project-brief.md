# ClinIntel AI project brief

ClinIntel AI combines structured cohort data, a defined prediction target, model explanations, a patient timeline, and retrieval from permitted reference material. Its intended setting is research and education. It does not independently diagnose, prescribe, triage, or replace qualified clinicians.

Define the population, index time, prediction horizon, outcome, inclusion and exclusion criteria, and permitted feature timing before training. Features must be available at the prediction time. Split train, validation, and test partitions by patient. Record missingness, data provenance, cohort version, model version, and evaluation method.

The project architecture is approved data → cohort validation and extraction → preprocessing and temporal summaries → baseline risk model → evaluation and explanations → timeline/API/dashboard. A retrieval workflow should retrieve from approved source documents, filter for relevance, show evidence, and abstain when support is unavailable.
