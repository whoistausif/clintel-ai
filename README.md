# ClinIntel AI

ClinIntel AI is a clinical risk and patient-intelligence **research prototype**. The repository now contains a full-stack scaffold for cohort validation, leakage-aware feature preparation, a patient-grouped logistic-regression baseline, evaluation, model explanations, a transparent clinical-note entity demo, evidence retrieval, API routes, PostgreSQL schema, audit metadata, monitoring hooks, Docker, and tests.

## Safety and data status

- The included development dataset is generated synthetic data. Its predictions and evaluation metrics are **not clinical evidence** and must not guide patient care.
- No MIMIC-IV credentials or restricted patient data are included. MIMIC-IV is access-controlled. Use it only after completing its current access, training, and data-use requirements, and comply with its terms.
- The sample SQL is a template. Review it against the installed MIMIC-IV version, dictionary item IDs, cohort policy, and local governance before running it. Keep data in the approved environment.
- The note extractor is a small lexicon/negation demonstration, not validated clinical NLP. The evidence assistant uses TF-IDF retrieval and extractive snippets from local project notes; it is not a medical advice generator.
- All model contributions describe associations with a model output, not causal or clinical conclusions. The software does not diagnose, prescribe, triage, or replace qualified clinicians.
- This is not a production-ready clinical system. Complete security review, access control integration, threat modeling, validation, privacy review, and operational governance before any sensitive or clinical use.

## Start with Docker

1. Copy `.env.example` to `.env`.
2. Set long random values for `CLINTEL_API_KEY`, `POSTGRES_PASSWORD`, `CLINTEL_APP_PASSWORD`, and `CLINTEL_INGEST_PASSWORD`. The app, database administrator, and ingestion tool use separate credentials.
3. Start the API and PostgreSQL:

   ```powershell
   docker compose up --build
   ```

4. Open `http://localhost:8000`. API docs are at `http://localhost:8000/docs`.

For a TLS-terminated deployment, place a trusted certificate/key at `certs/fullchain.pem` and `certs/privkey.pem`, set `CLINTEL_ENV=production`, set `CLINTEL_DATA_MODE=approved_csv`, point `CLINTEL_MODEL_PATH` at a reviewed non-synthetic artifact, update allowed origins, and start with `docker compose --profile tls up --build`. The API port and PostgreSQL port bind to loopback; Nginx is the public TLS entry point. The browser can pass a service key using **Connect API**. This is shared-key authentication, not per-user role authorization.

The container starts in development mode and trains a baseline on deterministic synthetic data if no artifact exists. The API refuses synthetic auto-training when `CLINTEL_ENV=production`; production requires a reviewed model artifact and an explicitly approved data workflow. The public Render demo uses development mode with synthetic data only; never point it at real or approved patient data. Never put an API secret in browser code.

## Deploy a public synthetic demo

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/whoistausif/clintel-ai)

The included `render.yaml` creates one free Docker web service for a **synthetic-data demo only**. It does not provision a database; predictions and audit events are temporary and may be lost when the service restarts. Free Render services can spin down while idle. This configuration is for portfolio demonstration, not production or real patient information. Do not submit PHI, credentials, or approved cohort data to the public demo. For production, use the governed deployment workflow above with reviewed artifacts, authentication, database, and institutional approvals.

## Start locally

Use Python 3.11+ and PostgreSQL 16 if you want persistence. Create a virtual environment, install `requirements.txt`, copy `.env.example` to `.env`, then run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m scripts.train_model
uvicorn clinintel.api:app --env-file .env --reload --port 8000
```

The API can run without a database URL for local exploration; JSONL audit metadata is written under `artifacts/`. PostgreSQL schema is in `database/schema.sql`. Keep `.env`, model artifacts, cohort files, exports, notes, and logs private. The dashboard's **Connect API** control keeps a verified key in `sessionStorage` for the current tab only. API keys are shared service credentials; configure user-level identity/roles at an approved gateway for multi-user use.

## Approved cohort workflow

The required CSV columns are:

`patient_id, admission_id, index_time, feature_cutoff_time, outcome_time, age, heart_rate_mean, sbp_mean, creatinine_max, prior_admissions, length_of_stay, readmitted_30d`

Optional `data_origin` and `sex` columns label provenance and support subgroup review. The CSV loader validates required columns, identifiers, binary labels, adult age, dates, positive-label timing, and a feature cutoff no later than the index time. Features are restricted to the documented pre-index allowlist in `clinintel/cohort.py`; outcome timestamps are labels only and are never model inputs. Keep the approved local file out of Git and set `CLINTEL_APPROVED_COHORT_CSV` only inside its governed environment. Cohort definition fields and model version are recorded with the artifact.

`database/mimic_readmission_cohort.sql` is an adaptation template, not a turnkey query. It requires a psql `observation_end` date to avoid labeling admissions without complete 30-day follow-up. Validate the data dictionary and item IDs before use, define exclusions with a clinician/research lead, document missingness, and retain patient-level identifiers only where approved.

For a governed, approved export, set `CLINTEL_APPROVED_COHORT_CSV` and `CLINTEL_DATA_MODE=approved_csv` in the protected environment, then run `python -m scripts.train_model`. Do temporal holdout evaluation with `python -m scripts.evaluate_temporal`. To import the prepared table into PostgreSQL, provide a separate migration/ingestion-role URL in `CLINTEL_INGEST_DATABASE_URL` and run `python -m scripts.import_approved_cohort`. The importer validates first and writes patients, admissions, pre-index features, and outcome labels in one database transaction; it does not print row-level data. Do not use the runtime API role as the importer.

## Baseline and evaluation

`python -m scripts.train_model` creates a scikit-learn imputation + standardization + logistic-regression baseline and evaluates a random-forest comparison candidate on the same patient-grouped train, validation, and test partitions. The logistic baseline remains the served model; the test scores are not used for model selection. The artifact includes its cohort definition, feature allowlist, data origin, model version and parameter digest. Evaluation reports AUROC with bootstrap 95% CI, AUPRC, Brier score, 10-bin expected calibration error, calibration bins, precision, recall, F1, confusion matrix, and descriptive age/sex subgroups. The threshold is a research default, not a care threshold.

For external or temporal evaluation, prepare a separately governed cohort and document its time window and provenance. Do not tune on the final test set. Synthetic benchmark numbers must remain labeled synthetic.

`python -m scripts.evaluate_temporal` runs a chronological holdout and removes patients from the earlier partition if they appear in the later partition. It requires enough distinct dates, rows, and both outcome classes. It prints a report and does not store the supplied cohort.

## API overview

Protected routes require `X-API-Key` whenever `CLINTEL_API_KEY` is configured; outside development, missing keys fail closed.

| Route | Purpose |
|---|---|
| `GET /api/health` | Service, environment, data mode and safety flags |
| `GET /api/patients` | Synthetic demo registry in development; approved cohort list requires a key outside development |
| `GET /api/patients/{id}/timeline` | Synthetic or authenticated approved-research timeline |
| `POST /api/predict-risk` | Baseline output and feature associations |
| `GET /api/predictions/{id}` | Retrieve a prediction |
| `GET /api/explanation/{id}` | Retrieve feature contributions |
| `POST /api/clinical-question` | Retrieve project-note evidence and abstain if unsupported |
| `GET /api/evidence/{id}` | Read a curated evidence source |
| `POST /api/clinical-nlp/extract` | Opt-in processing of an approved, deidentified note; note text is not persisted |
| `POST /api/clinical-nlp/evaluate` | Exact-span NLP precision/recall/F1 against an approved annotated sample |
| `POST /api/cohort/validate` | Validate an approved, deidentified cohort payload without storing its rows |
| `POST /api/models/train-baseline` | Development-only synthetic baseline training |
| `GET /api/models/readmission` | Model card and benchmark metrics |
| `GET /api/monitoring/summary` | Request latency counters and monitoring status |
| `POST /api/monitoring/input-drift` | Numeric feature PSI against synthetic reference; no universal threshold asserted |
| `POST /api/monitoring/outcome-evaluation` | Evaluate approved labeled follow-up data |
| `GET /api/audit/summary` | Audit storage/privacy summary |

## Project layout

```text
clinintel/       cohort, preprocessing, model, NLP, retrieval, API, security, monitoring
database/        PostgreSQL schema and MIMIC-IV extraction template
knowledge/       permitted local project-note evidence corpus
scripts/         reproducible model training entry point
tests/           cohort, leakage, metrics, NLP, retrieval and security tests
docs/            architecture, governance, model card, API and operations notes
```

## Tests

```powershell
python -m pytest
```

Tests use synthetic fixtures only. They verify cohort validation, feature timing, group splits, evaluation output, NLP negation cues, evidence abstention, and fail-closed key behavior. They do not validate clinical safety or model utility.

## Remaining governance work before real research data

Secure dataset authorization and institutional review; validate and version cohort SQL; define event/label semantics with the study team; review feature validity and missingness; independently audit leakage; run temporal/external and subgroup validation; compare baselines; validate calibration; annotate and score NLP extraction; approve each retrieval source; productionize secrets/authentication, TLS, authorization and database least privilege; review audit retention; add operational alerts and rollback; and obtain applicable clinical, privacy, security, and ethics review. This repository is a substantial implementation scaffold, not an assertion that these reviews or clinical validations have occurred.
