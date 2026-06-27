"""
Strategy 5 — Routing Determinism
===================================
Introduces a policy-driven routing engine between the classifier and the
routing layer, replacing direct intent→flow mapping with explicit policies.

Problem solved:
    The baseline architecture was:
        LLM output → intent string → ROUTING_MAP lookup → flow

    This meant all routing decisions, including low-confidence and ambiguous ones,
    flowed through identically. A 0.20-confidence "billing_issue" and a
    0.90-confidence "billing_issue" took exactly the same path.

    Result: routing variance tracked LLM output variance 1:1.

New architecture:
        LLM output → Classification Validation → Routing Policy Engine → flow

    The Routing Policy Engine applies band-based policies:
        HIGH  (≥ 0.75): DIRECT  → immediate routing, full trust
        MED   (≥ 0.50): DIRECT  → immediate routing, standard
        LOW   (< 0.50): FALLBACK → priority resolution before routing

    Impact:
        Routing flows collapse from 4 (observed in baseline) to 1-2,
        because the dominant confident intent wins consistently.
"""

from __future__ import annotations

from typing import Final

ROUTING_MAP: Final[dict[str, str]] = {
    "cancel_order":    "Order Cancellation Flow",
    "refund_request":  "Refund Flow",
    "billing_issue":   "Billing Support Flow",
    "shipping_issue":  "Shipping Support Flow",
    "general_support": "General Support Queue",
}

INTENT_PRIORITY: Final[dict[str, int]] = {
    "billing_issue":   1,
    "refund_request":  2,
    "cancel_order":    3,
    "shipping_issue":  4,
    "general_support": 5,
}

HIGH_BAND:   Final[float] = 0.75
MEDIUM_BAND: Final[float] = 0.50


class RoutingPolicyEngine:
    def route(
        self,
        intent: str,
        confidence: float,
        secondary_intents: list[str] | None = None,
        distribution: dict[str, float] | None = None,
    ) -> RoutingDecision:
        band = self._classify_band(confidence)

        if band in ("HIGH", "MEDIUM"):
            return RoutingDecision(
                routing_flow=ROUTING_MAP.get(intent, "General Support Queue"),
                resolved_intent=intent,
                confidence_band=band,
                policy_applied="direct_routing",
                priority_override=False,
            )

        resolved = self._priority_resolve(intent, secondary_intents or [], distribution or {})
        return RoutingDecision(
            routing_flow=ROUTING_MAP.get(resolved, "General Support Queue"),
            resolved_intent=resolved,
            confidence_band=band,
            policy_applied="priority_fallback",
            priority_override=resolved != intent,
        )

    def _classify_band(self, confidence: float) -> str:
        if confidence >= HIGH_BAND:
            return "HIGH"
        if confidence >= MEDIUM_BAND:
            return "MEDIUM"
        return "LOW"

    def _priority_resolve(
        self,
        intent: str,
        secondary: list[str],
        distribution: dict[str, float],
    ) -> str:
        candidates = [intent] + [s for s in secondary if s in ROUTING_MAP]

        # Also include distribution intents with >10% probability
        for d_intent, d_conf in distribution.items():
            if d_intent in ROUTING_MAP and d_conf > 0.10 and d_intent not in candidates:
                candidates.append(d_intent)

        return min(candidates, key=lambda x: INTENT_PRIORITY.get(x, 99))


class RoutingDecision:
    __slots__ = (
        "routing_flow",
        "resolved_intent",
        "confidence_band",
        "policy_applied",
        "priority_override",
    )

    def __init__(
        self,
        routing_flow: str,
        resolved_intent: str,
        confidence_band: str,
        policy_applied: str,
        priority_override: bool,
    ):
        self.routing_flow = routing_flow
        self.resolved_intent = resolved_intent
        self.confidence_band = confidence_band
        self.policy_applied = policy_applied
        self.priority_override = priority_override

    def __repr__(self) -> str:
        return (
            f"RoutingDecision("
            f"flow={self.routing_flow!r}, "
            f"intent={self.resolved_intent!r}, "
            f"band={self.confidence_band!r}, "
            f"policy={self.policy_applied!r})"
        )


if __name__ == "__main__":
    engine = RoutingPolicyEngine()

    cases = [
        ("billing_issue", 0.87, [], {}),
        ("cancel_order", 0.62, ["billing_issue"], {}),
        ("cancel_order", 0.31, ["billing_issue"], {"billing_issue": 0.35, "cancel_order": 0.31}),
        ("general_support", 0.22, [], {}),
    ]

    print("\n=== ROUTING POLICY ENGINE — TEST CASES ===\n")
    for intent, conf, secondary, dist in cases:
        decision = engine.route(intent, conf, secondary, dist)
        print(f"Input: {intent} (conf={conf})")
        print(f"  Flow:   {decision.routing_flow}")
        print(f"  Band:   {decision.confidence_band} | Policy: {decision.policy_applied}")
        if decision.priority_override:
            print(f"  ↳ Priority override applied → {decision.resolved_intent}")
        print()
