from fastapi.testclient import TestClient

from clinintel.api import app


def test_demo_api_health_registry_prediction_and_explanation():
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["research_only"] is True

        registry = client.get("/api/patients")
        assert registry.status_code == 200
        demo = registry.json()["patients"][0]
        assert demo["synthetic"] is True
        assert 0 <= demo["prediction"]["probability"] <= 1

        scored = client.post("/api/predict-risk", json={
            "patient_id": "DEMO-TEST-1", "age": 55, "heart_rate_mean": 82,
            "sbp_mean": 124, "creatinine_max": 1.1, "prior_admissions": 1,
            "length_of_stay": 4.2,
        })
        assert scored.status_code == 200
        prediction_id = scored.json()["prediction_id"]
        explanation = client.get(f"/api/explanation/{prediction_id}")
        assert explanation.status_code == 200
        assert explanation.json()["causal"] is False


def test_frontend_does_not_expose_project_files():
    with TestClient(app) as client:
        assert client.get("/").status_code == 200
        assert client.get("/styles.css").status_code == 200
        assert client.get("/README.md").status_code == 404
        assert client.get("/.env.example").status_code == 404


def test_validation_errors_do_not_echo_note_text():
    marker = "private_note_marker_123"
    with TestClient(app) as client:
        response = client.post("/api/clinical-nlp/extract", json={"note": marker * 1000, "approved_deidentified": True})
        assert response.status_code == 422
        assert marker not in response.text
