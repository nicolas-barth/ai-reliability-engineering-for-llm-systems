from typing import Dict, Tuple


ROUTING_POLICY: Dict[str, str] = {
    "billing_issue": "Billing Support Flow",
    "cancel_order": "Order Cancellation Flow",
    "refund_request": "Refund Processing Flow",
    "shipping_issue": "Shipping Support Flow",
    "general_support": "General Support Flow",
}


class RoutingValidator:
    def validate(self, intent: str, routing_flow: str) -> Tuple[bool, str]:
        """Returns (is_valid, reason_message)."""
        expected = ROUTING_POLICY.get(intent)
        if expected is None:
            return False, f"No routing policy defined for intent '{intent}'"
        if routing_flow != expected:
            return False, (
                f"Routing mismatch: intent='{intent}' expects '{expected}' "
                f"but received '{routing_flow}'"
            )
        return True, f"Routing valid: '{intent}' → '{routing_flow}'"

    def get_canonical_flow(self, intent: str) -> str:
        """Returns the canonical routing flow for a given intent."""
        return ROUTING_POLICY.get(intent, "General Support Flow")

    def all_policies(self) -> Dict[str, str]:
        return dict(ROUTING_POLICY)
