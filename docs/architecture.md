# Architecture

```text
Approved local cohort CSV / synthetic development generator
        ↓
cohort validation → pre-index temporal summaries → patient-grouped split
        ↓
logistic-regression baseline → held-out evaluation → coefficient contributions
        ↓
FastAPI risk, timeline, NLP, evidence, evaluation and monitoring endpoints
        ↓
responsive dashboard + PostgreSQL persistence + metadata-only audit trail
```

The current data generator is explicitly synthetic. No real clinical data source is connected. The MIMIC-IV SQL is an adaptation template requiring local dictionary review. PostgreSQL is optional for local development; its schema includes the documented entity tables. JSONL audit events contain action/status/model version only.

## Interfaces

- Preprocessing receives raw temporal observations and admissions, joins by admission, and filters to `observed_at < index_time` before aggregation.
- Modeling is a scikit-learn pipeline with an explicit feature allowlist and `GroupShuffleSplit` by patient.
- Explanations use standardized logistic-regression contributions and are labeled associative.
- NLP is a local lexicon matcher with negation cues, not a validated clinical model.
- Evidence retrieval uses TF-IDF over permitted local project notes and abstains on weak matches. There is no LLM in this implementation.
- FastAPI protects sensitive or write/evaluation endpoints with `X-API-Key`; production fails closed. Only public synthetic demo registry/timeline routes are unprotected.

## Known deployment gaps

TLS termination, user identity/role-based authorization, database role provisioning, managed secret storage, durable experiment tracking, model registry/rollback, alert routing, full database-backed timeline ingestion, comprehensive request-rate/body limits, and formal privacy/security assessment require deployment-specific integration.
