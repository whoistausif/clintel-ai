from __future__ import annotations

import re

# Minimal, transparent demo lexicons. This is not a clinical-grade NLP model.
LEXICONS = {
    "symptom": ["shortness of breath", "chest pain", "cough", "fatigue", "dizziness", "nausea"],
    "diagnosis": ["heart failure", "type 2 diabetes", "chronic kidney disease", "copd", "pneumonia", "hypertension"],
    "medication": ["metformin", "furosemide", "lisinopril", "insulin", "albuterol", "aspirin"],
    "procedure": ["chest x-ray", "echocardiogram", "dialysis", "electrocardiogram", "blood culture"],
}
NEGATION = re.compile(r"\b(no|not|denies|without|negative for|rule out)\b", re.I)


def extract_clinical_entities(text: str) -> list[dict]:
    """Return lexicon matches with local character offsets and negation cues."""
    entities = []
    normalized = text.lower()
    for category, phrases in LEXICONS.items():
        for phrase in phrases:
            for match in re.finditer(rf"(?<!\w){re.escape(phrase)}(?!\w)", normalized):
                prefix = text[max(0, match.start() - 48):match.start()]
                cue = list(NEGATION.finditer(prefix))
                negated = bool(cue and len(prefix) - cue[-1].end() < 24)
                entities.append({"category": category, "text": text[match.start():match.end()], "start": match.start(), "end": match.end(), "assertion": "negated" if negated else "mentioned"})
    return sorted(entities, key=lambda item: item["start"])


def score_extraction(gold_entities: list[dict], predicted_entities: list[dict]) -> dict:
    """Exact-span/category micro evaluation against a locally annotated sample."""
    key = lambda item: (item.get("category"), item.get("start"), item.get("end"), item.get("assertion", "mentioned"))
    gold = {key(item) for item in gold_entities}
    predicted = {key(item) for item in predicted_entities}
    true_positive = len(gold & predicted)
    precision = true_positive / len(predicted) if predicted else 0.0
    recall = true_positive / len(gold) if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"gold_count": len(gold), "predicted_count": len(predicted), "true_positive": true_positive, "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4), "method": "exact span, category, and assertion match"}
