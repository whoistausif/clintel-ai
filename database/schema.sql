-- ClinIntel AI schema: research prototype only; do not load restricted data without approvals.
CREATE TABLE IF NOT EXISTS patients (
  patient_id TEXT PRIMARY KEY,
  age SMALLINT CHECK (age BETWEEN 0 AND 120),
  sex TEXT,
  dataset_tag TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS admissions (
  admission_id TEXT PRIMARY KEY,
  patient_id TEXT NOT NULL REFERENCES patients(patient_id),
  index_time TIMESTAMPTZ NOT NULL,
  discharge_time TIMESTAMPTZ,
  data_origin TEXT NOT NULL,
  cohort_version TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS admissions_patient_time_idx ON admissions(patient_id, index_time);
CREATE TABLE IF NOT EXISTS admission_features (
  admission_id TEXT PRIMARY KEY REFERENCES admissions(admission_id) ON DELETE CASCADE,
  patient_id TEXT NOT NULL REFERENCES patients(patient_id),
  feature_cutoff_time TIMESTAMPTZ NOT NULL,
  heart_rate_mean NUMERIC,
  sbp_mean NUMERIC,
  creatinine_max NUMERIC,
  prior_admissions NUMERIC,
  length_of_stay NUMERIC,
  cohort_version TEXT NOT NULL,
  imported_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS admission_features_patient_idx ON admission_features(patient_id);
CREATE TABLE IF NOT EXISTS admission_outcomes (
  admission_id TEXT NOT NULL REFERENCES admissions(admission_id) ON DELETE CASCADE,
  outcome_name TEXT NOT NULL,
  horizon_days SMALLINT NOT NULL CHECK (horizon_days > 0),
  outcome_time TIMESTAMPTZ,
  label SMALLINT NOT NULL CHECK (label IN (0, 1)),
  cohort_version TEXT NOT NULL,
  PRIMARY KEY (admission_id, outcome_name, horizon_days)
);
CREATE TABLE IF NOT EXISTS vitals (
  observation_id BIGSERIAL PRIMARY KEY,
  admission_id TEXT NOT NULL REFERENCES admissions(admission_id) ON DELETE CASCADE,
  observed_at TIMESTAMPTZ NOT NULL,
  heart_rate NUMERIC,
  systolic_bp NUMERIC,
  respiratory_rate NUMERIC,
  temperature_c NUMERIC,
  oxygen_saturation NUMERIC,
  source_id TEXT
);
CREATE INDEX IF NOT EXISTS vitals_admission_time_idx ON vitals(admission_id, observed_at);
CREATE TABLE IF NOT EXISTS labs (
  lab_id BIGSERIAL PRIMARY KEY,
  admission_id TEXT NOT NULL REFERENCES admissions(admission_id) ON DELETE CASCADE,
  observed_at TIMESTAMPTZ NOT NULL,
  test_code TEXT NOT NULL,
  value NUMERIC,
  unit TEXT,
  source_id TEXT
);
CREATE INDEX IF NOT EXISTS labs_admission_time_idx ON labs(admission_id, observed_at);
CREATE TABLE IF NOT EXISTS medications (
  medication_id BIGSERIAL PRIMARY KEY,
  admission_id TEXT NOT NULL REFERENCES admissions(admission_id) ON DELETE CASCADE,
  event_time TIMESTAMPTZ NOT NULL,
  medication_code TEXT NOT NULL,
  event_type TEXT,
  source_id TEXT
);
CREATE TABLE IF NOT EXISTS diagnoses (
  diagnosis_id BIGSERIAL PRIMARY KEY,
  admission_id TEXT NOT NULL REFERENCES admissions(admission_id) ON DELETE CASCADE,
  code_system TEXT NOT NULL,
  diagnosis_code TEXT NOT NULL,
  diagnosis_rank SMALLINT,
  source_id TEXT
);
CREATE TABLE IF NOT EXISTS procedures (
  procedure_id BIGSERIAL PRIMARY KEY,
  admission_id TEXT NOT NULL REFERENCES admissions(admission_id) ON DELETE CASCADE,
  event_time TIMESTAMPTZ,
  code_system TEXT NOT NULL,
  procedure_code TEXT NOT NULL,
  source_id TEXT
);
CREATE TABLE IF NOT EXISTS clinical_notes (
  note_id TEXT PRIMARY KEY,
  admission_id TEXT NOT NULL REFERENCES admissions(admission_id) ON DELETE CASCADE,
  note_time TIMESTAMPTZ NOT NULL,
  note_type TEXT NOT NULL,
  deidentified BOOLEAN NOT NULL DEFAULT FALSE,
  content TEXT NOT NULL,
  source_id TEXT,
  CHECK (deidentified = TRUE)
);
CREATE TABLE IF NOT EXISTS predictions (
  prediction_id UUID PRIMARY KEY,
  patient_id TEXT NOT NULL REFERENCES patients(patient_id),
  model_version TEXT NOT NULL,
  outcome_name TEXT NOT NULL,
  horizon_days SMALLINT NOT NULL CHECK (horizon_days > 0),
  probability NUMERIC NOT NULL CHECK (probability BETWEEN 0 AND 1),
  risk_band TEXT NOT NULL CHECK (risk_band IN ('Lower', 'Moderate', 'Elevated')),
  data_origin TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS predictions_patient_time_idx ON predictions(patient_id, created_at DESC);
CREATE TABLE IF NOT EXISTS explanations (
  explanation_id BIGSERIAL PRIMARY KEY,
  prediction_id UUID NOT NULL REFERENCES predictions(prediction_id) ON DELETE CASCADE,
  method TEXT NOT NULL,
  feature_contributions JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS knowledge_documents (
  document_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  source_name TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  permitted_use TEXT NOT NULL,
  indexed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS audit_logs (
  audit_id BIGSERIAL PRIMARY KEY,
  action TEXT NOT NULL,
  status TEXT NOT NULL,
  model_version TEXT,
  event_time TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS audit_logs_time_idx ON audit_logs(event_time DESC);

-- Suggested least-privilege deployment: create separate migration and runtime roles,
-- grant the runtime role only the SELECT/INSERT operations needed by its endpoints.
