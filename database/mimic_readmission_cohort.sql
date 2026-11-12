-- TEMPLATE ONLY. Run only in an approved PhysioNet/MIMIC-IV environment and adapt
-- against the locally installed schema/version. Do not export row-level data.
-- Before running in psql, define the last date with complete follow-up, e.g.
--   \set observation_end 'YYYY-MM-DD HH:MI:SS'
-- Outcome proxy: any next hospital admission within 30 days of index discharge.
-- Feature values are summarized strictly before index discharge; later admissions
-- are used only for labels. Patient-level splitting is still required downstream.
WITH config AS (
  SELECT :'observation_end'::TIMESTAMP AS observation_end
), admissions AS (
  SELECT a.subject_id, a.hadm_id, a.admittime, a.dischtime, a.deathtime,
         p.anchor_age, p.gender AS sex,
         LEAD(a.admittime) OVER (PARTITION BY a.subject_id ORDER BY a.admittime) AS next_admittime
  FROM hosp.admissions a
  JOIN hosp.patients p USING (subject_id)
  CROSS JOIN config cfg
  WHERE a.admittime IS NOT NULL AND a.dischtime IS NOT NULL
    AND a.dischtime >= a.admittime
    AND p.anchor_age BETWEEN 18 AND 89
    AND COALESCE(a.discharge_location, '') NOT ILIKE '%hospice%'
    AND (a.deathtime IS NULL OR a.deathtime > a.dischtime + INTERVAL '30 days')
    AND a.dischtime <= cfg.observation_end - INTERVAL '30 days'
), cohort AS (
  SELECT *,
    CASE WHEN next_admittime > dischtime
           AND next_admittime <= dischtime + INTERVAL '30 days'
         THEN 1 ELSE 0 END AS readmitted_30d
  FROM admissions
), prior AS (
  SELECT c.subject_id, c.hadm_id,
         COUNT(p.hadm_id)::NUMERIC AS prior_admissions
  FROM cohort c
  LEFT JOIN hosp.admissions p ON p.subject_id = c.subject_id
    AND p.hadm_id <> c.hadm_id AND p.admittime < c.admittime
  GROUP BY c.subject_id, c.hadm_id
), vitals AS (
  SELECT c.hadm_id,
    AVG(ce.valuenum) FILTER (WHERE LOWER(di.label) = 'heart rate') AS heart_rate_mean,
    AVG(ce.valuenum) FILTER (WHERE LOWER(di.label) LIKE '%systolic%' AND LOWER(di.label) NOT LIKE '%alarm%') AS sbp_mean
  FROM cohort c
  LEFT JOIN icu.icustays s ON s.hadm_id = c.hadm_id
  LEFT JOIN icu.chartevents ce ON ce.stay_id = s.stay_id
    AND ce.charttime >= c.admittime AND ce.charttime < c.dischtime
  LEFT JOIN icu.d_items di ON di.itemid = ce.itemid
  GROUP BY c.hadm_id
), lab_features AS (
  SELECT c.hadm_id,
    MAX(CASE
      WHEN LOWER(TRIM(le.valueuom)) = 'mg/dl' THEN le.valuenum
      WHEN LOWER(TRIM(le.valueuom)) IN ('umol/l', 'µmol/l') THEN le.valuenum / 88.4
      ELSE NULL
    END) FILTER (WHERE LOWER(dli.label) LIKE '%creatinine%'
      AND LOWER(dli.label) NOT LIKE '%urine%'
      AND LOWER(dli.label) NOT LIKE '%body fluid%') AS creatinine_max
  FROM cohort c
  LEFT JOIN hosp.labevents le ON le.hadm_id = c.hadm_id
    AND le.charttime >= c.admittime AND le.charttime < c.dischtime
  LEFT JOIN hosp.d_labitems dli ON dli.itemid = le.itemid
  GROUP BY c.hadm_id
)
SELECT c.subject_id AS patient_id, c.hadm_id AS admission_id,
       c.dischtime AS index_time, c.dischtime AS feature_cutoff_time,
       c.next_admittime AS outcome_time,
       c.anchor_age AS age, c.sex, v.heart_rate_mean, v.sbp_mean,
       lf.creatinine_max, p.prior_admissions,
       EXTRACT(EPOCH FROM (c.dischtime - c.admittime)) / 86400.0 AS length_of_stay,
       c.readmitted_30d
FROM cohort c
JOIN prior p USING (subject_id, hadm_id)
LEFT JOIN vitals v USING (hadm_id)
LEFT JOIN lab_features lf USING (hadm_id)
WHERE c.dischtime IS NOT NULL;
