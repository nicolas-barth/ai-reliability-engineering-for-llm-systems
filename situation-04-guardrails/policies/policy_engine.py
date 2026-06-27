from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .policy_definitions import Policy, PolicyAction, ALL_POLICIES
from guardrails.base_guardrail import GuardrailResult


@dataclass
class PolicyDecision:
    policy_name: str
    triggered: bool
    action: PolicyAction
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_name": self.policy_name,
            "triggered": self.triggered,
            "action": self.action.value,
            "message": self.message,
            "metadata": self.metadata,
        }


@dataclass
class PolicyEngineResult:
    decisions: List[PolicyDecision] = field(default_factory=list)
    final_action: Optional[PolicyAction] = None
    blocked: bool = False
    escalated: bool = False
    requires_review: bool = False
    triggered_policies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "final_action": self.final_action.value if self.final_action else "ALLOW",
            "blocked": self.blocked,
            "escalated": self.escalated,
            "requires_review": self.requires_review,
            "triggered_policies": self.triggered_policies,
            "decisions": [d.to_dict() for d in self.decisions],
        }


class PolicyEngine:
    def __init__(self, policies: Optional[List[Policy]] = None) -> None:
        self._policies = policies or ALL_POLICIES

    @property
    def policy_names(self) -> List[str]:
        return [p.name for p in self._policies]

    def evaluate(self, guardrail_results: List[GuardrailResult]) -> PolicyEngineResult:
        active_violations = {
            r.violation_type.value
            for r in guardrail_results
            if r.violation_type is not None
        }

        decisions: List[PolicyDecision] = []
        triggered_policies: List[str] = []
        final_action: Optional[PolicyAction] = None
        blocked = False
        escalated = False
        requires_review = False

        for policy in self._policies:
            matched_violations = [v for v in policy.trigger_violations if v in active_violations]
            is_triggered = len(matched_violations) > 0

            if is_triggered:
                triggered_policies.append(policy.name)
                decisions.append(PolicyDecision(
                    policy_name=policy.name,
                    triggered=True,
                    action=policy.action,
                    message=(
                        f"Policy '{policy.name}' triggered by violations: {matched_violations}. "
                        f"Action: {policy.action.value}."
                    ),
                    metadata={"matched_violations": matched_violations},
                ))

                if policy.action == PolicyAction.BLOCK:
                    blocked = True
                    final_action = PolicyAction.BLOCK
                elif policy.action == PolicyAction.ESCALATE and not blocked:
                    escalated = True
                    if final_action is None:
                        final_action = PolicyAction.ESCALATE
                elif policy.action == PolicyAction.REQUIRE_REVIEW and not blocked and not escalated:
                    requires_review = True
                    if final_action is None:
                        final_action = PolicyAction.REQUIRE_REVIEW
            else:
                decisions.append(PolicyDecision(
                    policy_name=policy.name,
                    triggered=False,
                    action=PolicyAction.LOG,
                    message=f"Policy '{policy.name}' — no matching violations.",
                ))

        if final_action is None:
            final_action = PolicyAction.LOG

        return PolicyEngineResult(
            decisions=decisions,
            final_action=final_action,
            blocked=blocked,
            escalated=escalated,
            requires_review=requires_review,
            triggered_policies=triggered_policies,
        )
