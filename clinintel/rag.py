from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
STOPWORDS = {"how", "what", "why", "when", "where", "who", "does", "should", "would", "could", "can", "is", "are", "the", "a", "an", "be", "do", "did", "of", "for", "in", "on", "to", "and", "or", "at", "as", "about", "this", "that", "me", "tell", "explain", "please", "work", "within", "after", "before"}


@dataclass
class EvidenceDocument:
    document_id: str
    title: str
    text: str
    source: str


def load_knowledge(path: Path = ROOT / "knowledge") -> list[EvidenceDocument]:
    documents = []
    if not path.exists():
        return documents
    for file in sorted(path.glob("*.md")):
        text = file.read_text(encoding="utf-8")
        title = next((line.lstrip("# ") for line in text.splitlines() if line.startswith("#")), file.stem)
        documents.append(EvidenceDocument(file.stem, title, text, file.name))
    return documents


def retrieve(question: str, documents: list[EvidenceDocument] | None = None, limit: int = 3) -> list[dict]:
    docs = documents if documents is not None else load_knowledge()
    if not question.strip() or not docs:
        return []
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform([d.text for d in docs] + [question])
    scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    query_terms = set(re.findall(r"[a-z0-9]{3,}", question.lower())) - STOPWORDS
    ranked = []
    for index, score in enumerate(scores):
        doc_terms = set(re.findall(r"[a-z0-9]{3,}", docs[index].text.lower())) - STOPWORDS
        overlap = len(query_terms & doc_terms) / max(1, len(query_terms))
        ranked.append((index, float(score) + 0.25 * overlap))
    ranked.sort(key=lambda item: item[1], reverse=True)
    output = []
    for index, score in ranked[:limit]:
        if score < 0.15:
            continue
        doc = docs[index]
        snippets = [line.strip("# ") for line in doc.text.splitlines() if line.strip() and not line.startswith("#")]
        output.append({"document_id": doc.document_id, "title": doc.title, "source": doc.source, "score": round(float(score), 4), "excerpt": " ".join(snippets[:3])[:650]})
    return output


def answer(question: str) -> dict:
    evidence = retrieve(question)
    if not evidence:
        return {"answer": "I could not find supporting information in the curated project notes, so I cannot provide a grounded answer.", "evidence": [], "abstained": True}
    # Extractive response: no generative model, no free-form medical advice.
    return {"answer": evidence[0]["excerpt"], "evidence": evidence, "abstained": False, "mode": "extractive_tfidf"}
