from typing import Dict, Any
from .base_guardrail import BaseGuardrail, GuardrailResult, ViolationType, Severity, ActionType


HIGH_THRESHOLD = 0.75
MEDIUM_THRESHOLD = 0.50


class ConfidenceThresholdGuardrail(BaseGuardrail):
    @property
    def name(self) -> str:
        return "ConfidenceThresholdGuardrail"

    @property
    def description(self) -> str:
        return "Blocks routing when model confidence falls below the minimum accepted threshold."

    def evaluate(self, classification: Dict[str, Any]) -> GuardrailResult:
        confidence = classification.get("confidence", 0.0)

        if confidence >= HIGH_THRESHOLD:
            return self._pass(
                f"HIGH confidence band ({confidence:.2f} >= {HIGH_THRESHOLD}). Direct routing authorized."
            )

        if confidence >= MEDIUM_THRESHOLD:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                violation_type=ViolationType.LOW_CONFIDENCE,
                severity=Severity.LOW,
                action=ActionType.WARN,
                blocked=False,
                message=(
                    f"MEDIUM confidence band ({confidence:.2f}). Routing allowed — "
                    "monitor classification stability."
                ),
                metadata={"confidence": confidence, "band": "MEDIUM", "threshold": MEDIUM_THRESHOLD},
            )

        return GuardrailResult(
            guardrail_name=self.name,
            triggered=True,
            violation_type=ViolationType.LOW_CONFIDENCE,
            severity=Severity.HIGH,
            action=ActionType.BLOCK,
            blocked=True,
            message=(
                f"LOW confidence ({confidence:.2f} < {MEDIUM_THRESHOLD}). "
                "Routing blocked. Fallback to human review required."
            ),
            metadata={"confidence": confidence, "band": "LOW", "threshold": MEDIUM_THRESHOLD},
        )
