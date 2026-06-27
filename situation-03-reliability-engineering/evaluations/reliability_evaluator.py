from __future__ import annotations

import math
from collections import Counter


VALID_INTENTS = [
    "billing_issue", "cancel_order", "refund_request",
    "shipping_issue", "general_support",
]


class ReliabilityEvaluator:
    def evaluate(self, runs: list[dict]) -> dict:
        if not runs:
            return {}

        intents     = [r["predicted_intent"] for r in runs]
        confidences = [float(r["confidence"]) for r in runs]
        flows       = [r.get("routing_flow", "Unknown") for r in runs]

        intent_counts = Counter(intents)
        flow_counts   = Counter(flows)

        dominant_intent = intent_counts.most_common(1)[0][0]
        dominant_count  = intent_counts[dominant_intent]
        consistency_rate = dominant_count / len(runs)

        dominant_flow     = flow_counts.most_common(1)[0][0]
        dominant_flow_pct = flow_counts[dominant_flow] / len(runs)

        conf_mean = sum(confidences) / len(confidences)
        conf_std  = math.sqrt(
            sum((c - conf_mean) ** 2 for c in confidences) / len(confidences)
        )
        conf_min  = min(confidences)
        conf_max  = max(confidences)

        entropy = self._normalized_entropy(intent_counts, len(runs))
        reliability_score = self._reliability_score(
            consistency_rate, entropy, dominant_flow_pct, conf_std
        )
        readiness = self._readiness_label(reliability_score)

        disambig_rate = (
            sum(1 for r in runs if r.get("disambiguation_applied", False)) / len(runs)
        )

        return {
            "total_runs": len(runs),
            "consistency": {
                "dominant_intent":      dominant_intent,
                "dominant_count":       dominant_count,
                "consistency_rate":     round(consistency_rate, 4),
                "consistency_rate_pct": round(consistency_rate * 100, 1),
            },
            "unique_intents": {
                "unique_intent_count": len(intent_counts),
                "intent_counts": dict(intent_counts),
            },
            "routing": {
                "unique_routing_flows": len(flow_counts),
                "dominant_flow":        dominant_flow,
                "dominant_flow_pct":    round(dominant_flow_pct * 100, 1),
                "routing_distribution": {
                    flow: {"count": cnt, "pct": round(cnt / len(runs) * 100, 1)}
                    for flow, cnt in flow_counts.items()
                },
            },
            "confidence": {
                "min":   round(conf_min, 3),
                "max":   round(conf_max, 3),
                "mean":  round(conf_mean, 3),
                "std":   round(conf_std, 3),
                "range": round(conf_max - conf_min, 3),
            },
            "entropy": {
                "normalized_entropy": round(entropy, 4),
                "entropy_level":      self._entropy_level(entropy),
            },
            "reliability": {
                "reliability_score":    reliability_score,
                "readiness_label":      readiness,
                "disambiguation_rate":  round(disambig_rate * 100, 1),
                "dominant_flow_pct":    round(dominant_flow_pct * 100, 1),
            },
        }

    def _normalized_entropy(self, counts: Counter, total: int) -> float:
        entropy = 0.0
        for count in counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        max_entropy = math.log2(len(VALID_INTENTS))
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def _reliability_score(
        self,
        consistency_rate: float,
        entropy: float,
        dominant_flow_pct: float,
        conf_std: float,
    ) -> int:
        score = 0.0
        score += consistency_rate * 40
        score += (1.0 - entropy) * 25
        score += dominant_flow_pct * 20
        score += max(0.0, (0.30 - conf_std) / 0.30) * 15
        return min(100, max(0, int(round(score))))

    def _entropy_level(self, entropy: float) -> str:
        if entropy < 0.35:
            return "LOW"
        if entropy < 0.65:
            return "MEDIUM"
        return "HIGH"

    def _readiness_label(self, score: int) -> str:
        if score >= 90:
            return "PRODUCTION READY"
        if score >= 80:
            return "READY"
        if score >= 65:
            return "PARTIALLY READY"
        if score >= 50:
            return "NOT READY"
        return "CRITICAL"
