from typing import Final

ROUTING_MAP: Final[dict[str, str]] = {
    "cancel_order": "Order Cancellation Flow",
    "refund_request": "Refund Flow",
    "billing_issue": "Billing Support Flow",
    "shipping_issue": "Shipping Support Flow",
    "general_support": "General Support Queue",
}


def get_routing_flow(intent: str) -> str:
    return ROUTING_MAP.get(intent, "General Support Queue")
