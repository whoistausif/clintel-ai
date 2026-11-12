from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .cohort import FEATURES, make_synthetic_cohort, validate_cohort
from .config import ROOT, settings
from .database import execute, fetch_all
from .modeling import load_model, predict, train_and_save
from .modeling import evaluate
from .monitoring import drift_report
from .nlp import extract_clinical_entities, score_extraction
from .rag import answer, retrieve
from .security import audit, check_api_key

model_bundle: dict = {"pipeline": None, "metadata": {"model_version": "not-trained", "metrics": None}}
demo_cohort = make_synthetic_cohort(1200)
prediction_records: dict[str, dict] = {}
latencies: list[float] = []


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global model_bundle
    if settings.environment == "production" or settings.data_mode != "synthetic":
        model_bundle = load_model(settings.model_path)
        origin = model_bundle.get("metadata", {}).get("data_origin")
        if model_bundle.get("pipeline") is None or (settings.environment == "production" and origin == "synthetic"):
            raise RuntimeError("Production requires a reviewed, non-synthetic model artifact; synthetic auto-training is disabled")
    elif not settings.model_path.exists():
        metadata = train_and_save(demo_cohort, settings.model_path)
        model_bundle = load_model(settings.model_path)
        audit("model_train_synthetic", "completed", metadata["model_version"])
    else:
        model_bundle = load_model(settings.model_path)
    yield


app = FastAPI(title="ClinIntel AI Research API", version="0.2.0", description="Research-only API. Not for clinical diagnosis, treatment, triage, or care decisions.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins), allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-API-Key"])


class PredictRequest(BaseModel):
    patient_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
    age: float = Field(ge=18, le=120)
    heart_rate_mean: float | None = Field(default=None, ge=20, le=300)
    sbp_mean: float | None = Field(default=None, ge=30, le=300)
    creatinine_max: float | None = Field(default=None, ge=0, le=100)
    prior_admissions: float | None = Field(default=None, ge=0, le=100)
    length_of_stay: float | None = Field(default=None, ge=0, le=365)

    def feature_dict(self) -> dict:
        return {name: getattr(self, name) for name in FEATURES}


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class NoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=10000)
    # Explicit acknowledgement that the note is approved and deidentified.
    approved_deidentified: bool = False


class NlpEvaluationRequest(BaseModel):
    examples: list[dict] = Field(min_length=1, max_length=500)
    approved_annotated_sample: bool = False


class CohortCheckRequest(BaseModel):
    rows: list[dict] = Field(min_length=10, max_length=10000)
    approved_deidentified: bool = False


class DriftRequest(BaseModel):
    rows: list[dict] = Field(min_length=20, max_length=10000)
    approved_deidentified: bool = False


class OutcomeEvaluationRequest(BaseModel):
    labels: list[int] = Field(min_length=20, max_length=100000)
    probabilities: list[float] = Field(min_length=20, max_length=100000)
    approved_deidentified: bool = False


def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    if not check_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Valid X-API-Key required")


@app.middleware("http")
async def request_metrics(request: Request, call_next):
    started = time.perf_counter()
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > 1_048_576:
        return JSONResponse(status_code=413, content={"detail": "Request body exceeds the 1 MiB research API limit"})
    response = await call_next(request)
    elapsed = (time.perf_counter() - started) * 1000
    if request.url.path.startswith("/api/"):
        latencies.append(elapsed)
        if len(latencies) > 1000:
            del latencies[:-1000]
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/") else "no-cache"
    return response


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    # Keep exception details and request payloads out of responses and logs.
    return JSONResponse(status_code=500, content={"detail": "Internal research API error"})


@app.exception_handler(RequestValidationError)
async def request_validation_error(request: Request, exc: RequestValidationError):
    # Pydantic errors may include the rejected input (including note text); omit it.
    safe_errors = [{"location": error.get("loc"), "message": error.get("msg"), "type": error.get("type")} for error in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": safe_errors})


@app.get("/api/health")
def health():
    return {"status": "ok", "environment": settings.environment, "data_mode": settings.data_mode, "model_version": model_bundle.get("metadata", {}).get("model_version"), "research_only": True, "clinical_use": False}


@app.get("/api/patients")
def patients(x_api_key: Annotated[str | None, Header()] = None):
    if settings.environment != "development" and not check_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Valid X-API-Key required")
    if settings.environment != "development":
        rows = fetch_all("SELECT DISTINCT ON (p.patient_id) p.patient_id, p.age, p.sex, f.heart_rate_mean, f.sbp_mean, f.creatinine_max, f.prior_admissions, f.length_of_stay FROM patients p JOIN admission_features f USING (patient_id) JOIN admissions a USING (admission_id) WHERE p.dataset_tag = 'approved-cohort' ORDER BY p.patient_id, a.index_time DESC LIMIT 200")
        output = []
        for row in rows:
            features = {name: float(row[name]) if row[name] is not None else None for name in FEATURES}
            scored = predict(model_bundle, features)
            output.append({"patient_id": row["patient_id"], "age": row["age"], "sex": row["sex"], "condition": "Approved research record", "features": features, "prediction": scored, "synthetic": False})
        counts = {level: sum(item["prediction"]["risk_band"] == level for item in output) for level in ("Lower", "Moderate", "Elevated")}
        total = len(output)
        return {"data_origin": "approved research cohort", "cohort_size": total, "elevated_percent": round(100 * counts["Elevated"] / total, 1) if total else None, "risk_distribution": {key: round(100 * value / total, 1) for key, value in counts.items()} if total else {}, "patients": output}
    cohort_probabilities = model_bundle["pipeline"].predict_proba(demo_cohort[FEATURES])[:, 1] if model_bundle.get("pipeline") is not None else None
    cohort_levels = ["Elevated" if value >= 0.65 else "Moderate" if value >= 0.35 else "Lower" for value in cohort_probabilities] if cohort_probabilities is not None else []
    output = []
    for index, row in demo_cohort.head(200).iterrows():
        features = {name: float(row[name]) for name in FEATURES}
        risk = predict(model_bundle, features) if model_bundle.get("pipeline") is not None else None
        output.append({"patient_id": f"DEMO-{1042 + index}", "age": int(row.age), "sex": "F" if index % 2 == 0 else "M", "condition": ["Heart failure", "Type 2 diabetes", "Chronic kidney disease", "COPD"][index % 4], "features": features, "prediction": risk, "synthetic": True})
    counts = {level: cohort_levels.count(level) for level in ("Lower", "Moderate", "Elevated")}
    denominator = len(cohort_levels)
    distribution = {level: round(100 * count / denominator, 1) for level, count in counts.items()} if denominator else {}
    return {"data_origin": "synthetic", "cohort_size": int(len(demo_cohort)), "elevated_percent": distribution.get("Elevated"), "risk_distribution": distribution, "patients": output}


@app.get("/api/patients/{patient_id}/timeline")
def patient_timeline(patient_id: str, x_api_key: Annotated[str | None, Header()] = None):
    if settings.environment != "development":
        if not check_api_key(x_api_key):
            raise HTTPException(status_code=401, detail="Valid X-API-Key required")
        rows = fetch_all("SELECT 'Index admission' AS event_type, a.index_time AS event_time, 'Approved research admission' AS summary FROM admissions a JOIN patients p USING (patient_id) WHERE p.patient_id = %s UNION ALL SELECT 'Risk estimate' AS event_type, pr.created_at AS event_time, 'Research model output' AS summary FROM predictions pr WHERE pr.patient_id = %s ORDER BY event_time DESC LIMIT 200", (patient_id, patient_id))
        if not rows:
            raise HTTPException(status_code=404, detail="Research record not found")
        return {"patient_id": patient_id, "synthetic": False, "events": rows}
    if not patient_id.startswith(("DEMO-", "SYN-P-")):
        raise HTTPException(status_code=404, detail="Only synthetic demo records are available")
    match = next((i for i in range(len(demo_cohort)) if patient_id == f"DEMO-{1042 + i}" or patient_id == f"SYN-P-{i:05d}"), None)
    if match is None:
        raise HTTPException(status_code=404, detail="Synthetic record not found")
    row = demo_cohort.iloc[match]
    return {"patient_id": patient_id, "synthetic": True, "events": [{"event_type": "index_discharge", "event_time": row.index_time.isoformat(), "summary": "Synthetic index discharge"}, {"event_type": "cohort_outcome_window", "event_time": row.outcome_time.isoformat(), "summary": "Synthetic label observation time"}]}


@app.post("/api/predict-risk", dependencies=[Depends(require_api_key)])
def predict_risk(payload: PredictRequest):
    if model_bundle.get("pipeline") is None:
        raise HTTPException(status_code=503, detail="No reviewed model artifact is configured")
    try:
        result = predict(model_bundle, payload.feature_dict())
    except Exception:
        audit("risk_prediction", "failed", model_bundle.get("metadata", {}).get("model_version"))
        raise HTTPException(status_code=422, detail="Could not score these feature values")
    prediction_id = str(uuid.uuid4())
    data_origin = "synthetic-demo-api" if settings.environment == "development" else "approved-research-api"
    record = {"prediction_id": prediction_id, "patient_id": payload.patient_id, "created_at": datetime.now(timezone.utc).isoformat(), **result, "data_origin": data_origin}
    prediction_records[prediction_id] = record
    try:
        execute("INSERT INTO patients (patient_id, age, dataset_tag) VALUES (%s, %s, %s) ON CONFLICT (patient_id) DO NOTHING", (payload.patient_id, payload.age, data_origin))
        execute("INSERT INTO predictions (prediction_id, patient_id, model_version, outcome_name, horizon_days, probability, risk_band, data_origin, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (prediction_id, payload.patient_id, result["model_version"], "readmitted_30d", 30, result["probability"], result["risk_band"], data_origin, record["created_at"]))
        execute("INSERT INTO explanations (prediction_id, method, feature_contributions) VALUES (%s, %s, %s::jsonb)", (prediction_id, "standardized logistic-regression contributions", __import__("json").dumps(result["feature_contributions"])))
    except Exception:
        pass
    audit("risk_prediction", "completed", result["model_version"])
    return {**record, "research_only": True, "warning": "Synthetic demo model output. Not clinically validated; do not use for care decisions."}


@app.get("/api/predictions/{prediction_id}", dependencies=[Depends(require_api_key)])
def get_prediction(prediction_id: str):
    record = prediction_records.get(prediction_id)
    if not record:
        rows = fetch_all("SELECT prediction_id, patient_id, model_version, outcome_name, horizon_days, probability, risk_band, data_origin, created_at FROM predictions WHERE prediction_id = %s", (prediction_id,))
        record = rows[0] if rows else None
    if not record:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return {**record, "research_only": True}


@app.get("/api/explanation/{prediction_id}", dependencies=[Depends(require_api_key)])
def get_explanation(prediction_id: str):
    record = prediction_records.get(prediction_id)
    if record:
        return {"prediction_id": prediction_id, "model_version": record["model_version"], "feature_contributions": record["feature_contributions"], "interpretation": record["explanation_note"], "method": "standardized logistic-regression coefficient contributions", "causal": False}
    rows = fetch_all("SELECT e.prediction_id, e.method, e.feature_contributions, p.model_version FROM explanations e JOIN predictions p USING (prediction_id) WHERE e.prediction_id = %s", (prediction_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Explanation not found")
    return {**rows[0], "interpretation": "Associations with this model output only; not causal or clinical conclusions.", "causal": False}


@app.post("/api/clinical-question", dependencies=[Depends(require_api_key)])
def clinical_question(payload: QuestionRequest):
    # The evidence assistant is restricted to project methodology and safety notes.
    result = answer(payload.question)
    audit("evidence_question", "abstained" if result["abstained"] else "answered")
    return {**result, "research_only": True, "medical_advice": False, "knowledge_scope": "curated ClinIntel project notes only"}


@app.get("/api/evidence/{evidence_id}", dependencies=[Depends(require_api_key)])
def evidence(evidence_id: str):
    match = next((item for item in retrieve("", limit=10) if item["document_id"] == evidence_id), None)
    if match is None:
        # Return a curated document by ID without exposing filesystem paths.
        from .rag import load_knowledge
        doc = next((item for item in load_knowledge() if item.document_id == evidence_id), None)
        if doc is None:
            raise HTTPException(status_code=404, detail="Evidence source not found")
        match = {"document_id": doc.document_id, "title": doc.title, "source": doc.source, "excerpt": doc.text[:2000]}
    return match


@app.post("/api/clinical-nlp/extract", dependencies=[Depends(require_api_key)])
def clinical_nlp(payload: NoteRequest):
    if not payload.approved_deidentified:
        raise HTTPException(status_code=400, detail="Confirm the note is approved and deidentified before processing")
    entities = extract_clinical_entities(payload.note)
    audit("clinical_nlp_extract", "completed")
    return {"entities": entities, "note_persisted": False, "method": "transparent demo lexicon with negation cues", "limitations": "Not validated for clinical use; assess against an annotated sample before research deployment."}


@app.post("/api/clinical-nlp/evaluate", dependencies=[Depends(require_api_key)])
def clinical_nlp_evaluate(payload: NlpEvaluationRequest):
    if not payload.approved_annotated_sample:
        raise HTTPException(status_code=400, detail="Confirm that this annotated sample is approved and deidentified")
    gold, predicted = [], []
    for example in payload.examples:
        text = example.get("text")
        expected = example.get("entities")
        if not isinstance(text, str) or not isinstance(expected, list):
            raise HTTPException(status_code=422, detail="Each example needs text and an entities list")
        gold.extend(expected)
        predicted.extend(extract_clinical_entities(text))
    audit("clinical_nlp_evaluation", "completed")
    return {**score_extraction(gold, predicted), "examples": len(payload.examples), "research_only": True, "note_text_persisted": False}


@app.post("/api/cohort/validate", dependencies=[Depends(require_api_key)])
def cohort_validate(payload: CohortCheckRequest):
    if not payload.approved_deidentified:
        raise HTTPException(status_code=400, detail="Confirm this cohort is approved and deidentified")
    try:
        cohort = validate_cohort(pd.DataFrame(payload.rows))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    audit("cohort_validate", "completed")
    return {"valid": True, "rows": int(len(cohort)), "patients": int(cohort.patient_id.nunique()), "features": FEATURES, "cohort_definition": "Synthetic adult readmission cohort; see CohortSpec", "rows_persisted": False}


@app.post("/api/models/train-baseline", dependencies=[Depends(require_api_key)])
def train_baseline():
    global model_bundle
    if settings.environment == "production":
        raise HTTPException(status_code=403, detail="Training is disabled through the production API")
    metadata = train_and_save(demo_cohort, settings.model_path)
    model_bundle = load_model(settings.model_path)
    audit("model_train_synthetic", "completed", metadata["model_version"])
    return {**metadata, "research_only": True}


@app.get("/api/models/readmission")
def model_card():
    metadata = model_bundle.get("metadata", {})
    return {"model_version": metadata.get("model_version"), "model_family": metadata.get("model_family", "not configured"), "target": "next hospital admission within 30 days after index discharge (all-cause proxy)", "features": metadata.get("features", FEATURES), "data_origin": metadata.get("data_origin", "not trained"), "metrics": metadata.get("metrics"), "model_comparison": metadata.get("model_comparison"), "cohort": metadata.get("cohort"), "limitations": metadata.get("limitations"), "research_only": True}


@app.get("/api/monitoring/summary", dependencies=[Depends(require_api_key)])
def monitoring_summary():
    sorted_ms = sorted(latencies)
    percentile = sorted_ms[min(int(0.95 * (len(sorted_ms) - 1)), len(sorted_ms) - 1)] if sorted_ms else None
    return {"model_version": model_bundle.get("metadata", {}).get("model_version"), "request_count_window": len(sorted_ms), "latency_p50_ms": round(sorted_ms[len(sorted_ms)//2], 2) if sorted_ms else None, "latency_p95_ms": round(percentile, 2) if percentile is not None else None, "input_drift": "not calculated until an approved current cohort is explicitly supplied", "prediction_drift": "not calculated", "clinical_performance_monitoring": "requires approved outcome follow-up; no clinical data connected", "research_only": True}


@app.post("/api/monitoring/input-drift", dependencies=[Depends(require_api_key)])
def input_drift(payload: DriftRequest):
    if not payload.approved_deidentified:
        raise HTTPException(status_code=400, detail="Confirm the cohort is approved and deidentified")
    current = pd.DataFrame(payload.rows)
    missing = set(FEATURES) - set(current.columns)
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing feature columns: {', '.join(sorted(missing))}")
    report = drift_report(demo_cohort, current)
    audit("input_drift_report", "completed", model_bundle.get("metadata", {}).get("model_version"))
    return {"reference_origin": "synthetic development cohort", "current_rows": int(len(current)), "features": report, "thresholds": "No automatic alert threshold configured; PSI requires dataset-specific review.", "research_only": True}


@app.post("/api/monitoring/outcome-evaluation", dependencies=[Depends(require_api_key)])
def outcome_evaluation(payload: OutcomeEvaluationRequest):
    if not payload.approved_deidentified:
        raise HTTPException(status_code=400, detail="Confirm outcomes are approved and deidentified")
    if len(payload.labels) != len(payload.probabilities) or set(payload.labels) - {0, 1} or any(value < 0 or value > 1 for value in payload.probabilities):
        raise HTTPException(status_code=422, detail="Labels must be binary and paired with probabilities in [0, 1]")
    metrics = evaluate(pd.Series(payload.labels).to_numpy(), pd.Series(payload.probabilities).to_numpy())
    audit("outcome_performance_evaluation", "completed", model_bundle.get("metadata", {}).get("model_version"))
    return {"model_version": model_bundle.get("metadata", {}).get("model_version"), "metrics": metrics, "data_origin": "approved user-supplied outcomes; provenance must be documented outside this API", "research_only": True}


@app.get("/api/audit/summary", dependencies=[Depends(require_api_key)])
def audit_summary():
    return {"storage": "metadata-only JSONL with optional PostgreSQL mirror", "includes_patient_values": False, "note_text_persisted": False, "audit_file_exists": settings.audit_path.exists()}


# Serve only the three public UI assets. Never mount the project root: that would
# expose private data, environment files, model artifacts, and source files.
@app.get("/", include_in_schema=False)
def frontend_index():
    return FileResponse(ROOT / "index.html")


@app.get("/styles.css", include_in_schema=False)
def frontend_styles():
    return FileResponse(ROOT / "styles.css", media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def frontend_script():
    return FileResponse(ROOT / "app.js", media_type="text/javascript")
