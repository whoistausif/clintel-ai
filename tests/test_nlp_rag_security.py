from clinintel.nlp import extract_clinical_entities, score_extraction
from clinintel.rag import answer
from clinintel.security import check_api_key


def test_nlp_finds_entities_and_negation_cues():
    entities = extract_clinical_entities("Patient denies chest pain. Taking metformin.")
    assert any(item["text"] == "chest pain" and item["assertion"] == "negated" for item in entities)
    assert any(item["text"] == "metformin" and item["category"] == "medication" for item in entities)


def test_nlp_annotation_evaluation_reports_exact_match_scores():
    entities = extract_clinical_entities("No cough. Taking aspirin.")
    result = score_extraction(entities, entities)
    assert result["precision"] == result["recall"] == result["f1"] == 1.0


def test_evidence_assistant_abstains_when_support_is_missing():
    result = answer("What does the project say about lunar eclipses?")
    assert result["abstained"] is True
    assert result["evidence"] == []


def test_evidence_assistant_retrieves_relevant_cohort_and_metric_notes():
    cohort = answer("How should the cohort be split?")
    metrics = answer("What metrics should be reported?")
    assert cohort["abstained"] is False
    assert metrics["abstained"] is False
    assert cohort["evidence"][0]["source"]
    assert metrics["evidence"][0]["source"]


def test_development_key_policy_fails_closed_outside_development(monkeypatch):
    from types import SimpleNamespace
    from clinintel import security
    monkeypatch.setattr(security, "settings", SimpleNamespace(environment="production", api_key="secret-value"))
    assert not check_api_key(None)
    assert not check_api_key("wrong")
    assert check_api_key("secret-value")


def test_protected_endpoint_key_guard_returns_401_without_secret(monkeypatch):
    from types import SimpleNamespace
    from fastapi import HTTPException
    from clinintel import api, security
    protected_settings = SimpleNamespace(environment="production", api_key="secret-value")
    monkeypatch.setattr(security, "settings", protected_settings)
    try:
        api.require_api_key(None)
        assert False, "Expected an authentication error"
    except HTTPException as error:
        assert error.status_code == 401
