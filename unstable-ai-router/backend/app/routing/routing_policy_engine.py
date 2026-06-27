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

MINIMUM_CONFIDENCE: Final[float] = 0.50
HIGH_CONFIDENCE:    Final[float] = 0.75


class RoutingPolicyEngine:

    def route(
        self,
        intent: str,
        confidence: float,
        secondary_intents: list[str] | None = None,
    ) -> dict:
        secondary = secondary_intents or []

        if confidence >= HIGH_CONFIDENCE:
            return {
                "routing_flow": ROUTING_MAP.get(intent, "General Support Queue"),
                "policy_applied": "direct_high_confidence",
                "confidence_band": "HIGH",
                "confidence_sufficient": True,
            }

        if confidence >= MINIMUM_CONFIDENCE:
            return {
                "routing_flow": ROUTING_MAP.get(intent, "General Support Queue"),
                "policy_applied": "direct_standard",
                "confidence_band": "MEDIUM",
                "confidence_sufficient": True,
            }

        candidates = [intent] + [s for s in secondary if s in ROUTING_MAP]
        best_intent = min(candidates, key=lambda x: INTENT_PRIORITY.get(x, 99))

        return {
            "routing_flow": ROUTING_MAP.get(best_intent, "General Support Queue"),
            "policy_applied": "priority_fallback",
            "confidence_band": "LOW",
            "confidence_sufficient": False,
            "resolved_via": best_intent,
        }
