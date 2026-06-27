from typing import Dict, Any, Set
from .base_guardrail import BaseGuardrail, GuardrailResult, ViolationType, Severity, ActionType


VALID_INTENTS: Set[str] = {
    "billing_issue",
    "cancel_order",
    "refund_request",
    "shipping_issue",
    "general_support",
}


class IntentValidationGuardrail(BaseGuardrail):
    @property
    def name(self) -> str:
        return "IntentValidationGuardrail"

    @property
    def description(self) -> str:
        return "Rejects classifications with intents outside the valid taxonomy or insufficient confidence."

    def evaluate(self, classification: Dict[str, Any]) -> GuardrailResult:
        intent = classification.get("predicted_intent", "")
        confidence = classification.get("confidence", 0.0)

        if not intent:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                violation_type=ViolationType.INVALID_INTENT,
                severity=Severity.CRITICAL,
                action=ActionType.BLOCK,
                blocked=True,
                message="No intent present in classification result. Cannot validate.",
                metadata={"intent": intent},
            )

        if intent not in VALID_INTENTS:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                violation_type=ViolationType.INVALID_INTENT,
                severity=Severity.CRITICAL,
                action=ActionType.BLOCK,
                blocked=True,
                message=(
                    f"Intent '{intent}' is not in the valid taxonomy. Classification blocked."
                ),
                metadata={"intent": intent, "valid_intents": sorted(VALID_INTENTS)},
            )

        if confidence < 0.50:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                violation_type=ViolationType.LOW_CONFIDENCE,
                severity=Severity.HIGH,
                action=ActionType.BLOCK,
                blocked=True,
                message=(
                    f"Intent '{intent}' is valid but confidence {confidence:.2f} is insufficient "
                    "for direct routing. Fallback to human review required."
                ),
                metadata={"intent": intent, "confidence": confidence, "minimum_required": 0.50},
            )

        return self._pass(f"Intent '{intent}' validated (confidence={confidence:.2f}).")
