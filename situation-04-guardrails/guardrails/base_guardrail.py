from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class ViolationType(str, Enum):
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    HIGH_AMBIGUITY = "HIGH_AMBIGUITY"
    MULTI_INTENT_DETECTED = "MULTI_INTENT_DETECTED"
    ROUTING_MISMATCH = "ROUTING_MISMATCH"
    RELIABILITY_BELOW_THRESHOLD = "RELIABILITY_BELOW_THRESHOLD"
    INVALID_INTENT = "INVALID_INTENT"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActionType(str, Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    REQUIRE_REVIEW = "REQUIRE_REVIEW"
    ESCALATE = "ESCALATE"
    BLOCK = "BLOCK"


@dataclass
class GuardrailResult:
    guardrail_name: str
    triggered: bool
    violation_type: Optional[ViolationType] = None
    severity: Optional[Severity] = None
    message: str = ""
    action: ActionType = ActionType.ALLOW
    blocked: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "guardrail_name": self.guardrail_name,
            "triggered": self.triggered,
            "violation_type": self.violation_type.value if self.violation_type else None,
            "severity": self.severity.value if self.severity else None,
            "message": self.message,
            "action": self.action.value,
            "blocked": self.blocked,
            "metadata": self.metadata,
        }


class BaseGuardrail(ABC):
    """Abstract base for all guardrails in the production safety pipeline."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def evaluate(self, classification: Dict[str, Any]) -> GuardrailResult: ...

    def _pass(self, message: str = "Guardrail passed — no violations detected.") -> GuardrailResult:
        return GuardrailResult(
            guardrail_name=self.name,
            triggered=False,
            action=ActionType.ALLOW,
            blocked=False,
            message=message,
        )
