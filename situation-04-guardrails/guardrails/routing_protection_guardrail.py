from typing import Dict, Any, List
from .base_guardrail import BaseGuardrail, GuardrailResult, ViolationType, Severity, ActionType


VALID_ROUTING_MAP: Dict[str, List[str]] = {
    "billing_issue": ["Billing Support Flow"],
    "cancel_order": ["Order Cancellation Flow"],
    "refund_request": ["Refund Processing Flow"],
    "shipping_issue": ["Shipping Support Flow"],
    "general_support": ["General Support Flow"],
}


class RoutingProtectionGuardrail(BaseGuardrail):
    @property
    def name(self) -> str:
        return "RoutingProtectionGuardrail"

    @property
    def description(self) -> str:
        return "Blocks inconsistent routing — enforces intent-to-flow mapping policies."

    def evaluate(self, classification: Dict[str, Any]) -> GuardrailResult:
        intent = classification.get("predicted_intent", "")
        routing_flow = classification.get("routing_flow", "")

        if not intent or not routing_flow:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                violation_type=ViolationType.ROUTING_MISMATCH,
                severity=Severity.CRITICAL,
                action=ActionType.BLOCK,
                blocked=True,
                message="Missing intent or routing_flow. Cannot validate routing consistency.",
                metadata={"intent": intent, "routing_flow": routing_flow},
            )

        valid_flows = VALID_ROUTING_MAP.get(intent, [])

        if not valid_flows:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                violation_type=ViolationType.ROUTING_MISMATCH,
                severity=Severity.HIGH,
                action=ActionType.BLOCK,
                blocked=True,
                message=f"No routing policy defined for intent '{intent}'. Routing blocked.",
                metadata={"intent": intent, "routing_flow": routing_flow},
            )

        if routing_flow not in valid_flows:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                violation_type=ViolationType.ROUTING_MISMATCH,
                severity=Severity.HIGH,
                action=ActionType.BLOCK,
                blocked=True,
                message=(
                    f"ROUTING MISMATCH: intent='{intent}' was sent to '{routing_flow}' "
                    f"but valid flow is '{valid_flows[0]}'. Guardrail triggered."
                ),
                metadata={
                    "intent": intent,
                    "routing_flow": routing_flow,
                    "expected_flow": valid_flows[0],
                },
            )

        return self._pass(
            f"Routing consistent: '{intent}' → '{routing_flow}'."
        )
