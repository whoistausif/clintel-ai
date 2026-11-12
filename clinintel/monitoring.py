from __future__ import annotations

import numpy as np
import pandas as pd

from .cohort import FEATURES


def population_stability_index(reference: pd.Series, current: pd.Series, bins: int = 10) -> float | None:
    """Numeric PSI for monitoring only; thresholds need domain review before use."""
    ref = pd.to_numeric(reference, errors="coerce").dropna().to_numpy()
    cur = pd.to_numeric(current, errors="coerce").dropna().to_numpy()
    if len(ref) < 20 or len(cur) < 20:
        return None
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return None
    edges[0], edges[-1] = -np.inf, np.inf
    ref_counts, _ = np.histogram(ref, bins=edges)
    cur_counts, _ = np.histogram(cur, bins=edges)
    ref_pct = np.clip(ref_counts / len(ref), 1e-6, None)
    cur_pct = np.clip(cur_counts / len(cur), 1e-6, None)
    return round(float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))), 4)


def drift_report(reference: pd.DataFrame, current: pd.DataFrame) -> dict:
    return {name: {"psi": population_stability_index(reference[name], current[name]), "reference_n": int(reference[name].notna().sum()), "current_n": int(current[name].notna().sum())} for name in FEATURES}
