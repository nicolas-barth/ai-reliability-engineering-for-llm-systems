from typing import Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class IncidentSeverity(str, Enum):
    P1 = "P1"  # Critical — immediate action required
    P2 = "P2"  # High — action required within 1 hour
    P3 = "P3"  # Medium — action required within 24 hours


@dataclass
class Incident:
    incident_id: str
    severity: IncidentSeverity
    title: str
    description: str
    triggered_by: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "triggered_by": self.triggered_by,
            "metadata": self.metadata,
            "resolved": self.resolved,
        }


class IncidentDetector:
    CONSISTENCY_P1 = 60.0
    CONSISTENCY_P2 = 80.0
    RELIABILITY_P1 = 50.0
    RELIABILITY_P2 = 70.0
    BLOCK_RATE_P1 = 60.0
    BLOCK_RATE_P2 = 30.0

    def __init__(self) -> None:
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"INC-{self._counter:04d}"

    def detect(self, metrics: Dict[str, Any]) -> List[Incident]:
        incidents: List[Incident] = []
        consistency = metrics.get("consistency_rate", 100.0)
        avg_score = metrics.get("avg_reliability_score", 100.0)
        block_rate = metrics.get("block_rate_pct", 0.0)

        if consistency < self.CONSISTENCY_P1:
            incidents.append(Incident(
                incident_id=self._next_id(),
                severity=IncidentSeverity.P1,
                title="CRITICAL: Classification consistency collapsed",
                description=(
                    f"Consistency rate {consistency:.1f}% is below P1 threshold ({self.CONSISTENCY_P1}%). "
                    "System has regressed to pre-Situation-3 levels. Immediate rollback required."
                ),
                triggered_by="IncidentDetector.consistency_check",
                metadata={"consistency_rate": consistency, "threshold": self.CONSISTENCY_P1},
            ))
        elif consistency < self.CONSISTENCY_P2:
            incidents.append(Incident(
                incident_id=self._next_id(),
                severity=IncidentSeverity.P2,
                title="Consistency degradation detected",
                description=(
                    f"Consistency rate {consistency:.1f}% below P2 threshold ({self.CONSISTENCY_P2}%). "
                    "Investigate recent changes to disambiguation or classification pipelines."
                ),
                triggered_by="IncidentDetector.consistency_check",
                metadata={"consistency_rate": consistency, "threshold": self.CONSISTENCY_P2},
            ))

        if avg_score < self.RELIABILITY_P1:
            incidents.append(Incident(
                incident_id=self._next_id(),
                severity=IncidentSeverity.P1,
                title="CRITICAL: Reliability score critical",
                description=(
                    f"Average reliability score {avg_score:.1f} below P1 threshold ({self.RELIABILITY_P1}). "
                    "Full regression to unstable baseline state detected."
                ),
                triggered_by="IncidentDetector.reliability_score_check",
                metadata={"avg_reliability_score": avg_score, "threshold": self.RELIABILITY_P1},
            ))
        elif avg_score < self.RELIABILITY_P2:
            incidents.append(Incident(
                incident_id=self._next_id(),
                severity=IncidentSeverity.P2,
                title="Reliability score below production threshold",
                description=(
                    f"Average reliability score {avg_score:.1f} below P2 threshold ({self.RELIABILITY_P2}). "
                    "System does not meet Situation 3 production standards."
                ),
                triggered_by="IncidentDetector.reliability_score_check",
                metadata={"avg_reliability_score": avg_score, "threshold": self.RELIABILITY_P2},
            ))

        if block_rate > self.BLOCK_RATE_P1:
            incidents.append(Incident(
                incident_id=self._next_id(),
                severity=IncidentSeverity.P1,
                title="CRITICAL: Guardrail block rate critical",
                description=(
                    f"Block rate {block_rate:.1f}% exceeds P1 threshold ({self.BLOCK_RATE_P1}%). "
                    "System is rejecting the majority of classifications. Immediate investigation required."
                ),
                triggered_by="IncidentDetector.block_rate_check",
                metadata={"block_rate_pct": block_rate, "threshold": self.BLOCK_RATE_P1},
            ))
        elif block_rate > self.BLOCK_RATE_P2:
            incidents.append(Incident(
                incident_id=self._next_id(),
                severity=IncidentSeverity.P2,
                title="Elevated guardrail block rate",
                description=(
                    f"Block rate {block_rate:.1f}% exceeds P2 threshold ({self.BLOCK_RATE_P2}%). "
                    "Review guardrail configuration and recent classification quality."
                ),
                triggered_by="IncidentDetector.block_rate_check",
                metadata={"block_rate_pct": block_rate, "threshold": self.BLOCK_RATE_P2},
            ))

        return incidents
