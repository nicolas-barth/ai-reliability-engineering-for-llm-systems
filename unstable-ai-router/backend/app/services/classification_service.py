import random
import uuid
from datetime import datetime, timezone

from app.logs.logger import save_classification_log
from app.routing.router import get_routing_flow
from app.services.llm.interfaces import LLMServiceInterface


class ClassificationService:
    def __init__(self, llm: LLMServiceInterface, execution_mode: str):
        self._llm = llm
        self._execution_mode = execution_mode

    async def classify(self, message: str) -> dict:
        run_profile = random.choices(range(1, 6), weights=[16, 21, 29, 17, 17])[0]

        raw = await self._llm.classify(message, run_profile=run_profile)

        intent = raw["predicted_intent"]
        result = {
            "run_id": str(uuid.uuid4())[:8].upper(),
            "input": message,
            "predicted_intent": intent,
            "confidence": raw["confidence"],
            "intent_distribution": raw.get("intent_distribution", {}),
            "routing_flow": get_routing_flow(intent),
            "generated_response": raw["generated_response"],
            "execution_mode": self._execution_mode,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        save_classification_log(result)
        return result
