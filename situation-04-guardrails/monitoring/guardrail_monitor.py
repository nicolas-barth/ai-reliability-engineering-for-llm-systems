from typing import Dict, Any, List
from dataclasses import dataclass, field

from guardrails.guardrail_engine import EngineDecision
from policies.policy_engine import PolicyEngineResult
from .incident_detector import IncidentDetector, Incident


@dataclass
class MonitoringSnapshot:
    total_classifications: int = 0
    total_allowed: int = 0
    total_blocked: int = 0
    total_warnings: int = 0
    total_violations: int = 0
    guardrail_trigger_counts: Dict[str, int] = field(default_factory=dict)
    violation_type_counts: Dict[str, int] = field(default_factory=dict)
    policy_trigger_counts: Dict[str, int] = field(default_factory=dict)
    incidents: List[Incident] = field(default_factory=list)

    @property
    def block_rate_pct(self) -> float:
        if self.total_classifications == 0:
            return 0.0
        return round(self.total_blocked / self.total_classifications * 100, 2)

    @property
    def detection_rate_pct(self) -> float:
        detected = self.total_blocked + self.total_warnings
        if self.total_classifications == 0:
            return 0.0
        return round(detected / self.total_classifications * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_classifications": self.total_classifications,
            "total_allowed": self.total_allowed,
            "total_blocked": self.total_blocked,
            "total_warnings": self.total_warnings,
            "total_violations": self.total_violations,
            "block_rate_pct": self.block_rate_pct,
            "detection_rate_pct": self.detection_rate_pct,
            "guardrail_trigger_counts": self.guardrail_trigger_counts,
            "violation_type_counts": self.violation_type_counts,
            "policy_trigger_counts": self.policy_trigger_counts,
            "incidents": [i.to_dict() for i in self.incidents],
        }


class GuardrailMonitor:
    def __init__(self) -> None:
        self._snapshot = MonitoringSnapshot()
        self._incident_detector = IncidentDetector()

    def record(
        self,
        engine_decision: EngineDecision,
        policy_result: PolicyEngineResult,
    ) -> None:
        self._snapshot.total_classifications += 1

        is_blocked = not engine_decision.allowed or policy_result.blocked or policy_result.escalated
        if is_blocked:
            self._snapshot.total_blocked += 1
        else:
            self._snapshot.total_allowed += 1

        if engine_decision.warned_by:
            self._snapshot.total_warnings += 1

        self._snapshot.total_violations += engine_decision.total_violations

        for result in engine_decision.guardrail_results:
            if result.triggered:
                gname = result.guardrail_name
                self._snapshot.guardrail_trigger_counts[gname] = (
                    self._snapshot.guardrail_trigger_counts.get(gname, 0) + 1
                )
                if result.violation_type:
                    vt = result.violation_type.value
                    self._snapshot.violation_type_counts[vt] = (
                        self._snapshot.violation_type_counts.get(vt, 0) + 1
                    )

        for pname in policy_result.triggered_policies:
            self._snapshot.policy_trigger_counts[pname] = (
                self._snapshot.policy_trigger_counts.get(pname, 0) + 1
            )

    def check_incidents(
        self,
        consistency_rate: float,
        avg_reliability_score: float,
    ) -> List[Incident]:
        metrics = {
            "consistency_rate": consistency_rate,
            "avg_reliability_score": avg_reliability_score,
            "block_rate_pct": self._snapshot.block_rate_pct,
        }
        incidents = self._incident_detector.detect(metrics)
        self._snapshot.incidents.extend(incidents)
        return incidents

    def get_snapshot(self) -> MonitoringSnapshot:
        return self._snapshot
