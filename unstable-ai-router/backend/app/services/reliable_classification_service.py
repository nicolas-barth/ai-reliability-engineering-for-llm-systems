import uuid
from datetime import datetime, timezone

from app.classifier.reliable_classifier import ReliableIntentClassifier
from app.logs.logger import save_classification_log
from app.routing.routing_policy_engine import RoutingPolicyEngine


class ReliableClassificationService:

    def __init__(self, api_key: str, execution_mode: str):
        self._classifier = ReliableIntentClassifier(api_key=api_key)
        self._policy_engine = RoutingPolicyEngine()
        self._execution_mode = execution_mode

    async def classify(self, message: str, strategy_level: int = 3) -> dict:
        raw = await self._classifier.classify(message, strategy_level=strategy_level)

        intent = raw["predicted_intent"]
        confidence = raw["confidence"]
        secondary = raw.get("secondary_intents", [])

        routing_result = self._policy_engine.route(intent, confidence, secondary)
        reliability_score = self._compute_reliability_score(raw, routing_result)

        result = {
            "run_id": str(uuid.uuid4())[:8].upper(),
            "input": message,
            "predicted_intent": intent,
            "confidence": confidence,
            "intent_distribution": raw.get("intent_distribution", {}),
            "routing_flow": routing_result["routing_flow"],
            "generated_response": raw["generated_response"],
            "execution_mode": f"{self._execution_mode}_reliable_l{strategy_level}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "strategy_level": strategy_level,
            "reliability_score": reliability_score,
            "disambiguation_applied": raw.get("disambiguation_applied", False),
            "routing_policy": routing_result["policy_applied"],
            "secondary_intents": secondary,
            "reasoning": raw.get("reasoning", ""),
        }

        save_classification_log(result)
        return result

    def _compute_reliability_score(self, raw: dict, routing: dict) -> int:
        score = 0
        confidence = raw.get("confidence", 0.5)
        score += int(min(40, confidence * 40))
        score += 20
        if raw.get("disambiguation_applied"):
            score += 15
        else:
            score += 8
        band = routing.get("confidence_band", "LOW")
        score += {"HIGH": 15, "MEDIUM": 10, "LOW": 5}.get(band, 5)
        if raw.get("secondary_intents"):
            score += 10
        return min(100, max(0, score))
