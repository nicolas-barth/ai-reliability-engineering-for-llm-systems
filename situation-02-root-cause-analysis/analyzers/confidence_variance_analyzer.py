from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


CLUSTER_GAP = 0.12

KNOWN_PROFILES = [
    (0.03, 0.08, "Profile 1 — Critical Uncertainty"),
    (0.25, 0.35, "Profile 2 — Weak Interpretation"),
    (0.50, 0.58, "Profile 3 — Moderate Interpretation"),
    (0.68, 0.74, "Profile 4 — Fairly Confident"),
    (0.82, 0.92, "Profile 5 — High Confidence"),
]


class ConfidenceVarianceAnalyzer:
    def __init__(self, results_path: Path) -> None:
        with results_path.open(encoding="utf-8") as f:
            self._results = json.load(f)

    def analyze(self) -> dict[str, Any]:
        confidences = np.array([r["confidence"] for r in self._results])
        intents = [r["predicted_intent"] for r in self._results]
        n = len(confidences)

        overall = {
            "min": round(float(confidences.min()), 4),
            "max": round(float(confidences.max()), 4),
            "mean": round(float(confidences.mean()), 4),
            "std": round(float(confidences.std()), 4),
            "range": round(float(confidences.max() - confidences.min()), 4),
        }

        sorted_conf = np.sort(confidences)
        raw_clusters: list[list[float]] = []
        current: list[float] = [float(sorted_conf[0])]
        for i in range(1, n):
            if float(sorted_conf[i]) - float(sorted_conf[i - 1]) > CLUSTER_GAP:
                raw_clusters.append(current)
                current = [float(sorted_conf[i])]
            else:
                current.append(float(sorted_conf[i]))
        raw_clusters.append(current)

        cluster_info = []
        for idx, cl in enumerate(raw_clusters):
            arr = np.array(cl)
            cl_mean = float(arr.mean())
            matched = next(
                (label for lo, hi, label in KNOWN_PROFILES if lo - 0.06 <= cl_mean <= hi + 0.06),
                None,
            )
            cluster_info.append({
                "cluster_id": idx + 1,
                "count": len(cl),
                "pct": round(len(cl) / n * 100, 1),
                "mean": round(cl_mean, 4),
                "min": round(float(arr.min()), 4),
                "max": round(float(arr.max()), 4),
                "matched_profile": matched,
            })

        multimodal_detected = len(raw_clusters) >= 3

        unique_intents = sorted(set(intents))
        per_intent: dict[str, Any] = {}
        for intent in unique_intents:
            vals = np.array([
                r["confidence"] for r in self._results
                if r["predicted_intent"] == intent
            ])
            per_intent[intent] = {
                "count": int(len(vals)),
                "mean": round(float(vals.mean()), 4),
                "std": round(float(vals.std()), 4),
                "min": round(float(vals.min()), 4),
                "max": round(float(vals.max()), 4),
            }

        if multimodal_detected and len(raw_clusters) >= 4:
            root_cause = (
                f"Multimodal confidence distribution detected with {len(raw_clusters)} "
                "distinct clusters. This pattern is inconsistent with natural LLM confidence "
                "variation and strongly suggests external randomization or profile-based "
                "confidence steering injected at the service layer."
            )
            interpretation = "CRITICAL"
        elif overall["std"] > 0.25:
            root_cause = (
                f"High confidence volatility (σ={overall['std']:.3f}) caused by intent "
                "competition. When two intents carry near-equal probability mass, the "
                "selected confidence collapses to near-zero."
            )
            interpretation = "HIGH"
        else:
            root_cause = (
                "Moderate confidence variance. Intent competition partially explains volatility."
            )
            interpretation = "MODERATE"

        return {
            "overall_stats": overall,
            "confidence_clusters": cluster_info,
            "cluster_count": len(raw_clusters),
            "multimodal_detected": multimodal_detected,
            "per_intent_stats": per_intent,
            "variance_root_cause": root_cause,
            "variance_interpretation": interpretation,
        }
