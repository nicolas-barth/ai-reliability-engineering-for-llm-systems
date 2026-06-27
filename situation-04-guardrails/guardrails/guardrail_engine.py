from typing import Dict, Any, List
from dataclasses import dataclass, field

from .base_guardrail import BaseGuardrail, GuardrailResult, ActionType
from .intent_validation_guardrail import IntentValidationGuardrail
from .confidence_threshold_guardrail import ConfidenceThresholdGuardrail
from .ambiguity_detection_guardrail import AmbiguityDetectionGuardrail
from .routing_protection_guardrail import RoutingProtectionGuardrail
from .reliability_score_guardrail import ReliabilityScoreGuardrail


@dataclass
class EngineDecision:
    """Final routing decision after all guardrails have evaluated the classification."""

    allowed: bool
    blocked_by: List[str] = field(default_factory=list)
    warned_by: List[str] = field(default_factory=list)
    guardrail_results: List[GuardrailResult] = field(default_factory=list)
    total_violations: int = 0
    total_blocks: int = 0
    total_warnings: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "blocked_by": self.blocked_by,
            "warned_by": self.warned_by,
            "total_violations": self.total_violations,
            "total_blocks": self.total_blocks,
            "total_warnings": self.total_warnings,
            "guardrail_results": [r.to_dict() for r in self.guardrail_results],
        }


class GuardrailEngine:
    """Orchestrates all guardrails in the production safety pipeline.

    Evaluation order:
      1. IntentValidationGuardrail    — taxonomy and confidence gate
      2. ConfidenceThresholdGuardrail — confidence band enforcement
      3. AmbiguityDetectionGuardrail  — multi-intent detection
      4. RoutingProtectionGuardrail   — intent-to-flow consistency
      5. ReliabilityScoreGuardrail    — system health gate

    Pipeline contract:
      - All guardrails always run (no short-circuit), providing full audit coverage.
      - If any guardrail issues BLOCK or ESCALATE, routing is denied.
      - WARN violations are recorded but do not prevent routing.
    """

    def __init__(self) -> None:
        self._guardrails: List[BaseGuardrail] = [
            IntentValidationGuardrail(),
            ConfidenceThresholdGuardrail(),
            AmbiguityDetectionGuardrail(),
            RoutingProtectionGuardrail(),
            ReliabilityScoreGuardrail(),
        ]

    @property
    def guardrail_names(self) -> List[str]:
        return [g.name for g in self._guardrails]

    def evaluate(self, classification: Dict[str, Any]) -> EngineDecision:
        results: List[GuardrailResult] = []
        blocked_by: List[str] = []
        warned_by: List[str] = []

        for guardrail in self._guardrails:
            result = guardrail.evaluate(classification)
            results.append(result)

            if result.blocked:
                blocked_by.append(guardrail.name)
            elif result.triggered and result.action == ActionType.WARN:
                warned_by.append(guardrail.name)

        total_violations = sum(1 for r in results if r.triggered)
        total_blocks = len(blocked_by)
        total_warnings = len(warned_by)
        allowed = total_blocks == 0

        return EngineDecision(
            allowed=allowed,
            blocked_by=blocked_by,
            warned_by=warned_by,
            guardrail_results=results,
            total_violations=total_violations,
            total_blocks=total_blocks,
            total_warnings=total_warnings,
        )
