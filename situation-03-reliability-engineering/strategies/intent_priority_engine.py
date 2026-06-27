"""
Strategy 2 — Intent Priority Engine
=====================================
Defines an explicit, deterministic priority hierarchy for conflict resolution.

Problem solved:
    When multiple intents compete with similar probability, the system has no
    principled way to choose. Without priority rules, the selection oscillates
    based on LLM non-determinism or random profile assignment.

Approach:
    Hard-coded business-logic priority:
        billing_issue > refund_request > cancel_order > shipping_issue > general_support

    Rationale:
        - billing_issue: Highest urgency — revenue impact, regulatory exposure
        - refund_request: Time-sensitive — SLA clocks run from first contact
        - cancel_order: Retention risk — requires immediate human review
        - shipping_issue: Operational — can be resolved asynchronously
        - general_support: Lowest — informational, no time pressure

    The engine applies when:
        (a) confidence is below the routing threshold
        (b) multiple intents have nearly equal probability mass
        (c) disambiguation layer detects MODERATE+ ambiguity
"""

from __future__ import annotations

PRIORITY_TABLE: dict[str, int] = {
    "billing_issue":   1,   # highest priority
    "refund_request":  2,
    "cancel_order":    3,
    "shipping_issue":  4,
    "general_support": 5,   # lowest priority
}

NEAR_TIE_THRESHOLD = 0.15   # intents within 15pp of each other are considered "tied"


class IntentPriorityEngine:
    def resolve(self, distribution: dict[str, float]) -> str:
        if not distribution:
            return "general_support"

        valid = {k: v for k, v in distribution.items() if k in PRIORITY_TABLE}
        if not valid:
            return "general_support"

        top_confidence = max(valid.values())
        candidates = [
            intent for intent, conf in valid.items()
            if conf >= top_confidence - NEAR_TIE_THRESHOLD
        ]

        return min(candidates, key=lambda x: PRIORITY_TABLE[x])

    def resolve_with_context(self, distribution: dict[str, float]) -> PriorityResult:
        if not distribution:
            return PriorityResult("general_support", False, False, {})

        valid = {k: v for k, v in distribution.items() if k in PRIORITY_TABLE}
        raw_winner = max(valid, key=valid.get) if valid else "general_support"
        top_confidence = valid.get(raw_winner, 0.0)

        candidates = [
            intent for intent, conf in valid.items()
            if conf >= top_confidence - NEAR_TIE_THRESHOLD
        ]
        near_tie = len(candidates) > 1
        priority_winner = min(candidates, key=lambda x: PRIORITY_TABLE[x])
        priority_applied = priority_winner != raw_winner

        return PriorityResult(
            winner=priority_winner,
            near_tie_detected=near_tie,
            priority_applied=priority_applied,
            candidates={k: valid[k] for k in candidates},
        )

    def rank(self, intents: list[str]) -> list[str]:
        return sorted([i for i in intents if i in PRIORITY_TABLE],
                      key=lambda x: PRIORITY_TABLE[x])


class PriorityResult:
    __slots__ = ("winner", "near_tie_detected", "priority_applied", "candidates")

    def __init__(
        self,
        winner: str,
        near_tie_detected: bool,
        priority_applied: bool,
        candidates: dict[str, float],
    ):
        self.winner = winner
        self.near_tie_detected = near_tie_detected
        self.priority_applied = priority_applied
        self.candidates = candidates

    def __repr__(self) -> str:
        return (
            f"PriorityResult(winner={self.winner!r}, "
            f"near_tie={self.near_tie_detected}, "
            f"priority_applied={self.priority_applied})"
        )


if __name__ == "__main__":
    engine = IntentPriorityEngine()

    distributions = [
        {"billing_issue": 0.35, "cancel_order": 0.32, "refund_request": 0.20, "shipping_issue": 0.08, "general_support": 0.05},
        {"cancel_order": 0.45, "billing_issue": 0.40, "refund_request": 0.10, "shipping_issue": 0.03, "general_support": 0.02},
        {"general_support": 0.30, "billing_issue": 0.28, "cancel_order": 0.22, "refund_request": 0.12, "shipping_issue": 0.08},
    ]

    for dist in distributions:
        result = engine.resolve_with_context(dist)
        raw_max = max(dist, key=dist.get)
        print(f"\nDistribution top: {raw_max} ({dist[raw_max]:.2f})")
        print(f"Priority resolved: {result.winner}")
        print(f"Near tie: {result.near_tie_detected} | Priority applied: {result.priority_applied}")
        print(f"Candidates: {result.candidates}")
