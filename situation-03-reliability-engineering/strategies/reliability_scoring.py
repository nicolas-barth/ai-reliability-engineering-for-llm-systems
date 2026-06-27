"""
Strategy 6 — Reliability Scoring
===================================
Computes a 0-100 composite reliability score for each classification,
and an aggregate score across a batch of runs.

Problem solved:
    The baseline system had no internal signal of classification quality.
    All results were treated identically regardless of confidence, ambiguity,
    or routing policy certainty. There was no mechanism to self-monitor
    or surface degrading classification quality.

Approach:
    Per-call Reliability Score (0-100):
        Confidence Band:         0-40 pts  (primary quality signal)
        Structured Output:       0-20 pts  (schema validation passed)
        Disambiguation Resolved: 0-15 pts  (ambiguity was detected and handled)
        Routing Policy Certainty: 0-15 pts (confidence band determines routing policy)
        Secondary Intent Context: 0-10 pts (secondary intents were provided)
        Total:                   100 pts max

    Aggregate Reliability Score (0-100):
        Composite of mean per-call score adjusted by consistency rate.

    Readiness Classification:
        90-100: PRODUCTION READY
        80-89:  READY (minor risks)
        65-79:  PARTIALLY READY (review recommended)
        50-64:  NOT READY (significant issues)
        0-49:   CRITICAL (do not deploy)
"""

from __future__ import annotations

import math

READINESS_BANDS = [
    (90, "PRODUCTION READY",  "System is stable, consistent, and suitable for production load."),
    (80, "READY",             "System is reliable. Minor edge cases may require monitoring."),
    (65, "PARTIALLY READY",   "System is functional but has identifiable reliability risks."),
    (50, "NOT READY",         "Significant reliability issues. Engineering review required."),
    (0,  "CRITICAL",          "Severe instability. Do not deploy without remediation."),
]


class ReliabilityScorer:
    def score_call(
        self,
        confidence: float,
        structured_output: bool = True,
        disambiguation_applied: bool = False,
        confidence_band: str = "MEDIUM",
        secondary_intents_provided: bool = False,
    ) -> CallScore:
        confidence_pts = int(min(40, confidence * 40))
        structure_pts  = 20 if structured_output else 0
        disambig_pts   = 15 if disambiguation_applied else 8
        routing_pts    = {"HIGH": 15, "MEDIUM": 10, "LOW": 5}.get(confidence_band, 5)
        context_pts    = 10 if secondary_intents_provided else 0

        total = confidence_pts + structure_pts + disambig_pts + routing_pts + context_pts
        total = min(100, max(0, total))

        return CallScore(
            total=total,
            confidence_pts=confidence_pts,
            structure_pts=structure_pts,
            disambiguation_pts=disambig_pts,
            routing_pts=routing_pts,
            context_pts=context_pts,
        )

    def score_batch(self, call_scores: list[int], consistency_rate: float) -> AggregateScore:
        if not call_scores:
            return AggregateScore(0, 0.0, "CRITICAL", "No data")

        mean_score = sum(call_scores) / len(call_scores)
        std_score  = math.sqrt(sum((s - mean_score) ** 2 for s in call_scores) / len(call_scores))

        # Penalize low consistency — a consistent 80 is better than an inconsistent 90
        consistency_multiplier = 0.6 + (0.4 * consistency_rate)
        aggregate = int(mean_score * consistency_multiplier)
        aggregate = min(100, max(0, aggregate))

        band, label, description = self._classify_readiness(aggregate)
        return AggregateScore(
            score=aggregate,
            mean_call_score=round(mean_score, 1),
            std_call_score=round(std_score, 1),
            readiness_label=label,
            readiness_description=description,
            consistency_multiplier=round(consistency_multiplier, 3),
        )

    def _classify_readiness(self, score: int) -> tuple:
        for threshold, label, description in READINESS_BANDS:
            if score >= threshold:
                return threshold, label, description
        return 0, "CRITICAL", "Severe instability."


class CallScore:
    __slots__ = (
        "total", "confidence_pts", "structure_pts",
        "disambiguation_pts", "routing_pts", "context_pts",
    )

    def __init__(self, total, confidence_pts, structure_pts,
                 disambiguation_pts, routing_pts, context_pts):
        self.total             = total
        self.confidence_pts    = confidence_pts
        self.structure_pts     = structure_pts
        self.disambiguation_pts = disambiguation_pts
        self.routing_pts       = routing_pts
        self.context_pts       = context_pts

    def __repr__(self) -> str:
        return (
            f"CallScore(total={self.total}, "
            f"conf={self.confidence_pts}, struct={self.structure_pts}, "
            f"disambig={self.disambiguation_pts}, routing={self.routing_pts})"
        )


class AggregateScore:
    def __init__(
        self,
        score: int,
        mean_call_score: float = 0.0,
        std_call_score: float = 0.0,
        readiness_label: str = "CRITICAL",
        readiness_description: str = "",
        consistency_multiplier: float = 1.0,
    ):
        self.score = score
        self.mean_call_score = mean_call_score
        self.std_call_score = std_call_score
        self.readiness_label = readiness_label
        self.readiness_description = readiness_description
        self.consistency_multiplier = consistency_multiplier

    def __repr__(self) -> str:
        return (
            f"AggregateScore(score={self.score}/100, "
            f"readiness={self.readiness_label!r})"
        )


if __name__ == "__main__":
    scorer = ReliabilityScorer()

    # Baseline-like call
    baseline = scorer.score_call(confidence=0.54, structured_output=False,
                                 disambiguation_applied=False,
                                 confidence_band="MEDIUM", secondary_intents_provided=False)
    print(f"Baseline call score: {baseline.total}/100")

    # Reliable call
    reliable = scorer.score_call(confidence=0.87, structured_output=True,
                                 disambiguation_applied=True,
                                 confidence_band="HIGH", secondary_intents_provided=True)
    print(f"Reliable call score: {reliable.total}/100")

    # Aggregate batch
    baseline_batch = scorer.score_batch([baseline.total] * 50, consistency_rate=0.40)
    reliable_batch = scorer.score_batch([reliable.total] * 50, consistency_rate=0.92)

    print(f"\nBaseline aggregate: {baseline_batch.score}/100 — {baseline_batch.readiness_label}")
    print(f"Reliable aggregate: {reliable_batch.score}/100 — {reliable_batch.readiness_label}")
