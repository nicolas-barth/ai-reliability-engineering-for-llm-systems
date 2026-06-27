from __future__ import annotations

import math
from collections import Counter
from difflib import SequenceMatcher
from typing import Any

import numpy as np


class MetricsEngine:
    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results
        self.n = len(results)

    def consistency_rate(self) -> dict[str, Any]:
        intents = [r["predicted_intent"] for r in self.results]
        counter = Counter(intents)
        dominant_intent, dominant_count = counter.most_common(1)[0]
        rate = dominant_count / self.n
        return {
            "dominant_intent": dominant_intent,
            "dominant_count": dominant_count,
            "total_runs": self.n,
            "consistency_rate": round(rate, 4),
            "consistency_rate_pct": round(rate * 100, 2),
        }

    def unique_intents(self) -> dict[str, Any]:
        intents = [r["predicted_intent"] for r in self.results]
        counter = Counter(intents)
        return {
            "unique_intent_count": len(counter),
            "intent_counts": dict(counter.most_common()),
        }

    def routing_variance(self) -> dict[str, Any]:
        flows = [r["routing_flow"] for r in self.results]
        counter = Counter(flows)
        return {
            "unique_routing_flows": len(counter),
            "routing_distribution": {
                flow: {"count": cnt, "pct": round(cnt / self.n * 100, 2)}
                for flow, cnt in counter.most_common()
            },
        }

    def confidence_metrics(self) -> dict[str, Any]:
        confidences = [r["confidence"] for r in self.results]
        arr = np.array(confidences, dtype=float)
        return {
            "min": round(float(arr.min()), 4),
            "max": round(float(arr.max()), 4),
            "mean": round(float(arr.mean()), 4),
            "std": round(float(arr.std()), 4),
            "range": round(float(arr.max() - arr.min()), 4),
            "values": [round(float(c), 4) for c in confidences],
        }

    def intent_entropy(self) -> dict[str, Any]:
        intents = [r["predicted_intent"] for r in self.results]
        counter = Counter(intents)
        total = sum(counter.values())
        probs = [cnt / total for cnt in counter.values()]

        H = -sum(p * math.log2(p) for p in probs if p > 0)
        max_H = math.log2(5)  # 5 possible intent categories
        normalized_H = H / max_H

        return {
            "shannon_entropy": round(H, 4),
            "max_possible_entropy": round(max_H, 4),
            "normalized_entropy": round(normalized_H, 4),
            "interpretation": _entropy_label(normalized_H),
        }

    def response_drift(self) -> dict[str, Any]:
        responses = [r.get("generated_response", "") for r in self.results]
        if len(responses) < 2:
            return {
                "mean_similarity_to_baseline": 1.0,
                "mean_drift": 0.0,
                "min_similarity": 1.0,
                "max_similarity": 1.0,
                "drift_interpretation": "INSUFFICIENT DATA",
            }

        baseline = responses[0]
        similarities = [
            SequenceMatcher(None, baseline, r).ratio()
            for r in responses[1:]
        ]
        mean_sim = sum(similarities) / len(similarities)
        mean_drift = 1.0 - mean_sim

        return {
            "mean_similarity_to_baseline": round(mean_sim, 4),
            "mean_drift": round(mean_drift, 4),
            "min_similarity": round(min(similarities), 4),
            "max_similarity": round(max(similarities), 4),
            "drift_interpretation": _drift_label(mean_drift),
        }

    def compute_all(self) -> dict[str, Any]:
        return {
            "total_runs": self.n,
            "consistency": self.consistency_rate(),
            "unique_intents": self.unique_intents(),
            "routing": self.routing_variance(),
            "confidence": self.confidence_metrics(),
            "entropy": self.intent_entropy(),
            "drift": self.response_drift(),
        }


def _entropy_label(normalized: float) -> str:
    if normalized < 0.30:
        return "LOW — system converges on dominant intent"
    if normalized < 0.60:
        return "MODERATE — partial instability detected"
    if normalized < 0.85:
        return "HIGH — significant probabilistic dispersion"
    return "CRITICAL — near-uniform distribution (classifier is effectively random)"


def _drift_label(drift: float) -> str:
    if drift < 0.15:
        return "MINIMAL"
    if drift < 0.40:
        return "MODERATE"
    if drift < 0.65:
        return "HIGH"
    return "SEVERE"
