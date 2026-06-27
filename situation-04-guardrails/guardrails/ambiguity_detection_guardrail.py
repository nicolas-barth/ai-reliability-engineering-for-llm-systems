from typing import Dict, Any, List
from .base_guardrail import BaseGuardrail, GuardrailResult, ViolationType, Severity, ActionType


AMBIGUITY_THRESHOLD = 0.30
STRONG_AMBIGUITY_THRESHOLD = 0.40


class AmbiguityDetectionGuardrail(BaseGuardrail):
    @property
    def name(self) -> str:
        return "AmbiguityDetectionGuardrail"

    @property
    def description(self) -> str:
        return "Detects multi-intent inputs and blocks or escalates ambiguous classifications."

    def evaluate(self, classification: Dict[str, Any]) -> GuardrailResult:
        distribution = classification.get("intent_distribution", {})
        predicted_intent = classification.get("predicted_intent", "")
        secondary_intents = classification.get("secondary_intents", [])

        if not distribution:
            return self._pass("No distribution data — ambiguity check skipped.")

        sorted_intents = sorted(distribution.items(), key=lambda x: x[1], reverse=True)

        if len(sorted_intents) < 2:
            return self._pass("Single intent in distribution — no ambiguity detected.")

        primary_score = sorted_intents[0][1]
        secondary_label = sorted_intents[1][0]
        secondary_score = sorted_intents[1][1]
        ambiguity_ratio = secondary_score / primary_score if primary_score > 0 else 0.0

        high_secondaries = [
            {"intent": lbl, "score": round(sc, 3)}
            for lbl, sc in sorted_intents[1:]
            if sc >= AMBIGUITY_THRESHOLD
        ]

        if secondary_score >= STRONG_AMBIGUITY_THRESHOLD:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                violation_type=ViolationType.MULTI_INTENT_DETECTED,
                severity=Severity.HIGH,
                action=ActionType.BLOCK,
                blocked=True,
                message=(
                    f"Strong multi-intent detected: primary='{predicted_intent}' ({primary_score:.2f}), "
                    f"secondary='{secondary_label}' ({secondary_score:.2f}). "
                    "Disambiguation required before routing."
                ),
                metadata={
                    "ambiguity_ratio": round(ambiguity_ratio, 3),
                    "primary_intent": predicted_intent,
                    "competing_intents": high_secondaries,
                },
            )

        if secondary_score >= AMBIGUITY_THRESHOLD:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                violation_type=ViolationType.HIGH_AMBIGUITY,
                severity=Severity.MEDIUM,
                action=ActionType.ESCALATE,
                blocked=True,
                message=(
                    f"Multi-intent signal: primary='{predicted_intent}' ({primary_score:.2f}), "
                    f"secondary='{secondary_label}' ({secondary_score:.2f}). "
                    "Escalation required."
                ),
                metadata={
                    "ambiguity_ratio": round(ambiguity_ratio, 3),
                    "primary_intent": predicted_intent,
                    "competing_intents": high_secondaries,
                },
            )

        if secondary_intents:
            return GuardrailResult(
                guardrail_name=self.name,
                triggered=True,
                violation_type=ViolationType.HIGH_AMBIGUITY,
                severity=Severity.LOW,
                action=ActionType.WARN,
                blocked=False,
                message=(
                    f"Weak secondary intent detected: {secondary_intents}. "
                    "Routing allowed with advisory."
                ),
                metadata={"secondary_intents": secondary_intents, "secondary_score": round(secondary_score, 3)},
            )

        return self._pass(
            f"No significant ambiguity (secondary={secondary_score:.2f} < {AMBIGUITY_THRESHOLD})."
        )
