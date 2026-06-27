from typing import Dict, Any, List, Tuple, Set


REQUIRED_FIELDS: List[str] = [
    "run_id",
    "predicted_intent",
    "confidence",
    "intent_distribution",
    "routing_flow",
    "reliability_score",
]

VALID_INTENTS: Set[str] = {
    "billing_issue",
    "cancel_order",
    "refund_request",
    "shipping_issue",
    "general_support",
}


class ClassificationValidator:
    def validate(self, classification: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Returns (is_valid, list_of_errors)."""
        errors: List[str] = []

        for field in REQUIRED_FIELDS:
            if field not in classification or classification[field] is None:
                errors.append(f"Missing required field: '{field}'")

        confidence = classification.get("confidence")
        if confidence is not None:
            if not isinstance(confidence, (int, float)):
                errors.append(f"'confidence' must be numeric, got {type(confidence).__name__}")
            elif not (0.0 <= float(confidence) <= 1.0):
                errors.append(f"'confidence' out of range [0, 1]: {confidence}")

        intent = classification.get("predicted_intent", "")
        if intent and intent not in VALID_INTENTS:
            errors.append(f"Intent '{intent}' not in valid taxonomy: {sorted(VALID_INTENTS)}")

        dist = classification.get("intent_distribution", {})
        if dist and isinstance(dist, dict):
            total = sum(dist.values())
            if not (0.97 <= total <= 1.03):
                errors.append(f"intent_distribution sum deviates from 1.0 (sum={total:.4f})")

        score = classification.get("reliability_score")
        if score is not None:
            if not isinstance(score, (int, float)):
                errors.append("'reliability_score' must be numeric")
            elif not (0 <= float(score) <= 100):
                errors.append(f"'reliability_score' out of range [0, 100]: {score}")

        return len(errors) == 0, errors
