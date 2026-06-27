from typing import Dict, Any
from .base_guardrail import BaseGuardrail, GuardrailResult, ViolationType, Severity, ActionType


PRODUCTION_READY_THRESHOLD = 70
DEGRADED_THRESHOLD = 50


class ReliabilityScoreGuardrail(BaseGuardrail):
    @property
    def name(self) -> str:
        return "ReliabilityScoreGuardrail"

    @property
    def description(self) -> str:
        return "Blocks classifications where reliability score falls below production thresholds."

    def evaluate(self, classification: Dict[str, Any]) -> GuardrailResult:
        score = classification.get("reliability_score")

        if score is None:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                violation_type=ViolationType.RELIABILITY_BELOW_THRESHOLD,
                severity=Severity.HIGH,
                action=ActionType.BLOCK,
                blocked=True,
                message="Reliability score absent. Cannot verify system health. Routing blocked.",
                metadata={"reliability_score": None},
            )

        if score < DEGRADED_THRESHOLD:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                violation_type=ViolationType.RELIABILITY_BELOW_THRESHOLD,
                severity=Severity.CRITICAL,
                action=ActionType.BLOCK,
                blocked=True,
                message=(
                    f"CRITICAL: Reliability score {score} < {DEGRADED_THRESHOLD}. "
                    "System operating in fully degraded state — regression to pre-Situation-3 levels. "
                    "Classification blocked."
                ),
                metadata={"reliability_score": score, "threshold": DEGRADED_THRESHOLD, "status": "CRITICAL"},
            )

        if score < PRODUCTION_READY_THRESHOLD:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                violation_type=ViolationType.RELIABILITY_BELOW_THRESHOLD,
                severity=Severity.HIGH,
                action=ActionType.BLOCK,
                blocked=True,
                message=(
                    f"Reliability score {score} < {PRODUCTION_READY_THRESHOLD}. "
                    "System does not meet production-ready standard. "
                    "Classification blocked pending remediation."
                ),
                metadata={"reliability_score": score, "threshold": PRODUCTION_READY_THRESHOLD, "status": "DEGRADED"},
            )

        return self._pass(
            f"Reliability score {score} meets production threshold (>= {PRODUCTION_READY_THRESHOLD})."
        )
