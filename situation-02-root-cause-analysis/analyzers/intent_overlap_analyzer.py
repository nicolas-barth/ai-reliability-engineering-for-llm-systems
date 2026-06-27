from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


INTENTS = [
    "billing_issue",
    "cancel_order",
    "refund_request",
    "shipping_issue",
    "general_support",
]


class IntentOverlapAnalyzer:
    def __init__(self, results_path: Path) -> None:
        with results_path.open(encoding="utf-8") as f:
            self._results = json.load(f)

    def analyze(self) -> dict[str, Any]:
        distributions = [r["intent_distribution"] for r in self._results]
        n = len(distributions)

        prob_matrix = np.zeros((n, len(INTENTS)))
        for i, dist in enumerate(distributions):
            for j, intent in enumerate(INTENTS):
                prob_matrix[i, j] = dist.get(intent, 0.0)

        overlap_matrix: dict[str, dict[str, Any]] = {}
        pairs: list[dict[str, Any]] = []

        for ai, intent_a in enumerate(INTENTS):
            for bi, intent_b in enumerate(INTENTS):
                if ai >= bi:
                    continue

                pa = prob_matrix[:, ai]
                pb = prob_matrix[:, bi]

                avg_min = float(np.mean(np.minimum(pa, pb)))

                top2_count = 0
                for row in range(n):
                    sorted_idx = np.argsort(prob_matrix[row])[::-1][:2].tolist()
                    if ai in sorted_idx and bi in sorted_idx:
                        top2_count += 1
                top2_pct = round(top2_count / n * 100, 2)

                pa_c = pa - pa.mean()
                pb_c = pb - pb.mean()
                denom = float(np.sqrt((pa_c**2).sum() * (pb_c**2).sum()))
                pearson_r = float((pa_c * pb_c).sum() / denom) if denom > 1e-10 else 0.0

                overlap_score = round((avg_min * 0.5 + top2_pct / 100 * 0.5) * 100, 2)

                key = f"{intent_a}_vs_{intent_b}"
                entry = {
                    "intent_a": intent_a,
                    "intent_b": intent_b,
                    "avg_min_probability": round(avg_min, 4),
                    "top2_cooccurrence_pct": top2_pct,
                    "pearson_r": round(pearson_r, 4),
                    "overlap_score": overlap_score,
                }
                overlap_matrix[key] = entry
                pairs.append(entry)

        pairs_sorted = sorted(pairs, key=lambda x: x["overlap_score"], reverse=True)

        return {
            "overlap_matrix": overlap_matrix,
            "top_competing_pairs": pairs_sorted[:5],
            "primary_overlap": (
                pairs_sorted[0]["intent_a"] + " ↔ " + pairs_sorted[0]["intent_b"]
            ),
            "primary_overlap_score": pairs_sorted[0]["overlap_score"],
            "intents": INTENTS,
        }
