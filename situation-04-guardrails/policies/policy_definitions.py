from dataclasses import dataclass
from typing import List
from enum import Enum


class PolicyAction(str, Enum):
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"
    REQUIRE_REVIEW = "REQUIRE_REVIEW"
    ALERT = "ALERT"
    LOG = "LOG"


@dataclass(frozen=True)
class Policy:
    name: str
    description: str
    trigger_violations: List[str]
    action: PolicyAction
    severity_threshold: str
    alert_on_trigger: bool = True

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "trigger_violations": list(self.trigger_violations),
            "action": self.action.value,
            "severity_threshold": self.severity_threshold,
            "alert_on_trigger": self.alert_on_trigger,
        }


LOW_CONFIDENCE_BLOCK = Policy(
    name="LOW_CONFIDENCE_BLOCK",
    description=(
        "Blocks routing for any classification with confidence below 0.50. "
        "Prevents unreliable predictions from reaching production flows."
    ),
    trigger_violations=["LOW_CONFIDENCE"],
    action=PolicyAction.BLOCK,
    severity_threshold="HIGH",
    alert_on_trigger=True,
)

MULTI_INTENT_ESCALATION = Policy(
    name="MULTI_INTENT_ESCALATION",
    description=(
        "Escalates ambiguous multi-intent classifications to human review. "
        "Triggered when secondary intent scores exceed the ambiguity threshold."
    ),
    trigger_violations=["MULTI_INTENT_DETECTED", "HIGH_AMBIGUITY"],
    action=PolicyAction.ESCALATE,
    severity_threshold="MEDIUM",
    alert_on_trigger=True,
)

ROUTING_MISMATCH_BLOCK = Policy(
    name="ROUTING_MISMATCH_BLOCK",
    description=(
        "Blocks any routing where the destination flow does not match "
        "the expected policy for the classified intent."
    ),
    trigger_violations=["ROUTING_MISMATCH"],
    action=PolicyAction.BLOCK,
    severity_threshold="HIGH",
    alert_on_trigger=True,
)

RELIABILITY_THRESHOLD = Policy(
    name="RELIABILITY_THRESHOLD",
    description=(
        "Enforces minimum reliability score of 70 for production routing. "
        "Scores below threshold indicate regression from Situation 3 production levels."
    ),
    trigger_violations=["RELIABILITY_BELOW_THRESHOLD"],
    action=PolicyAction.BLOCK,
    severity_threshold="HIGH",
    alert_on_trigger=True,
)

ALL_POLICIES: List[Policy] = [
    LOW_CONFIDENCE_BLOCK,
    MULTI_INTENT_ESCALATION,
    ROUTING_MISMATCH_BLOCK,
    RELIABILITY_THRESHOLD,
]
