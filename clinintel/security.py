from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone

from .config import settings
from .database import execute


def check_api_key(candidate: str | None) -> bool:
    """Fail closed outside development; compare secrets in constant time."""
    if not settings.api_key:
        return settings.environment == "development"
    return bool(candidate) and hmac.compare_digest(candidate.encode(), settings.api_key.encode())


def audit(action: str, status: str, model_version: str | None = None) -> None:
    """Log metadata only; never store note text, feature values, tokens, or patient identifiers."""
    event = {"timestamp": datetime.now(timezone.utc).isoformat(), "action": action, "status": status, "model_version": model_version}
    settings.audit_path.parent.mkdir(parents=True, exist_ok=True)
    with settings.audit_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, separators=(",", ":")) + "\n")
    try:
        execute("INSERT INTO audit_logs (action, status, model_version, event_time) VALUES (%s, %s, %s, %s)", (action, status, model_version, event["timestamp"]))
    except Exception:
        # Local JSONL remains the fallback if PostgreSQL is unavailable.
        pass
