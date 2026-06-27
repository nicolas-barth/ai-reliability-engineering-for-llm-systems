"""
Strategy 4 — Structured Classification
========================================
Eliminates free-text LLM output in favour of JSON schema-validated responses.

Problem solved:
    The baseline classifier parsed intent, confidence, and distribution from
    unstructured text using regex. Parsing failures silently degraded quality:
    if "Selected:" was missing, the system fell back to argmax(distribution),
    which amplified variance from the unstable distribution values.

    Free-text output also allowed the LLM to output partial or malformed
    responses that introduced silent errors downstream.

Approach:
    Force the LLM to output a JSON object matching a strict schema via
    OpenAI's response_format={"type": "json_object"} parameter.

    Schema enforced:
    {
        "intent":                 str (one of 5 valid values),
        "confidence":             float (0.0 - 1.0),
        "reasoning":              str,
        "secondary_intents":      list[str],
        "disambiguation_applied": bool,
        "signals_detected":       list[str]
    }

    Validation guarantees:
        - intent is always a valid enum value (or corrected to nearest match)
        - confidence is always in [0.0, 1.0]
        - secondary_intents contains only valid enum values
        - No parsing ambiguity — the structure is always present

    LLM parameters changed:
        temperature:      1.1  →  0.1   (output stability)
        top_p:            0.98 →  0.95  (less tail diversity)
        presence_penalty: 0.4  →  0.0   (no novelty incentive)
        response_format:  text →  json  (structural enforcement)
"""

from __future__ import annotations

VALID_INTENTS = frozenset({
    "cancel_order",
    "refund_request",
    "billing_issue",
    "shipping_issue",
    "general_support",
})

SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": list(VALID_INTENTS),
            "description": "The single most relevant intent category",
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Model confidence in the selected intent",
        },
        "reasoning": {
            "type": "string",
            "description": "One sentence explaining the classification decision",
        },
        "secondary_intents": {
            "type": "array",
            "items": {"type": "string", "enum": list(VALID_INTENTS)},
            "description": "Other intents detected in the message, if any",
        },
        "disambiguation_applied": {
            "type": "boolean",
            "description": "True if multiple intents were detected and priority rules were applied",
        },
        "signals_detected": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Keywords or phrases that triggered the classification",
        },
    },
    "required": ["intent", "confidence", "reasoning", "secondary_intents",
                 "disambiguation_applied", "signals_detected"],
    "additionalProperties": False,
}


class StructuredOutputValidator:
    def validate(self, data: dict) -> ValidationResult:
        errors: list[str] = []

        intent = str(data.get("intent", "")).lower().strip()
        if intent not in VALID_INTENTS:
            errors.append(f"invalid intent: {intent!r}")
            intent = self._closest_intent(intent, data)

        confidence = data.get("confidence")
        if not isinstance(confidence, (int, float)):
            errors.append(f"confidence not numeric: {confidence!r}")
            confidence = 0.5
        confidence = float(max(0.0, min(1.0, confidence)))

        secondary = [
            s.lower() for s in data.get("secondary_intents", [])
            if isinstance(s, str) and s.lower() in VALID_INTENTS
        ]

        return ValidationResult(
            intent=intent,
            confidence=round(confidence, 3),
            reasoning=str(data.get("reasoning", "")),
            secondary_intents=secondary,
            disambiguation_applied=bool(data.get("disambiguation_applied", False)),
            signals_detected=list(data.get("signals_detected", [])),
            validation_errors=errors,
            is_valid=len(errors) == 0,
        )

    def _closest_intent(self, raw: str, data: dict) -> str:
        for intent in VALID_INTENTS:
            if intent in raw:
                return intent
        raw_text = str(data)
        for intent in VALID_INTENTS:
            if intent in raw_text.lower():
                return intent
        return "general_support"


class ValidationResult:
    __slots__ = (
        "intent", "confidence", "reasoning", "secondary_intents",
        "disambiguation_applied", "signals_detected",
        "validation_errors", "is_valid",
    )

    def __init__(self, intent, confidence, reasoning, secondary_intents,
                 disambiguation_applied, signals_detected, validation_errors, is_valid):
        self.intent = intent
        self.confidence = confidence
        self.reasoning = reasoning
        self.secondary_intents = secondary_intents
        self.disambiguation_applied = disambiguation_applied
        self.signals_detected = signals_detected
        self.validation_errors = validation_errors
        self.is_valid = is_valid

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "secondary_intents": self.secondary_intents,
            "disambiguation_applied": self.disambiguation_applied,
            "signals_detected": self.signals_detected,
        }


if __name__ == "__main__":
    validator = StructuredOutputValidator()

    test_outputs = [
        {"intent": "billing_issue", "confidence": 0.87, "reasoning": "...",
         "secondary_intents": ["cancel_order"], "disambiguation_applied": True,
         "signals_detected": ["cobrado", "errado"]},
        {"intent": "BILLING_ISSUE", "confidence": 1.2, "reasoning": "...",
         "secondary_intents": [], "disambiguation_applied": False, "signals_detected": []},
        {"intent": "unknown_intent", "confidence": "high", "reasoning": "...",
         "secondary_intents": ["billing_issue"], "disambiguation_applied": False, "signals_detected": []},
    ]

    for output in test_outputs:
        result = validator.validate(output)
        print(f"\nInput intent:  {output['intent']}")
        print(f"Valid intent:  {result.intent} (is_valid={result.is_valid})")
        print(f"Confidence:    {result.confidence}")
        if result.validation_errors:
            print(f"Errors fixed:  {result.validation_errors}")
