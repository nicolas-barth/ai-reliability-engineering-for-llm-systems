import json
import logging
from pathlib import Path

from app.services.llm.interfaces import LLMServiceInterface

logger = logging.getLogger(__name__)

_FALLBACK_KEY = "_default"


class DemoLLMService(LLMServiceInterface):

    def __init__(self, scenarios_path: str) -> None:
        self._scenarios: dict[str, list[dict]] = self._load(scenarios_path)
        logger.info(
            "DemoLLMService loaded %d scenario(s) from %s",
            len(self._scenarios),
            scenarios_path,
        )

    def _load(self, path: str) -> dict[str, list[dict]]:
        with open(path, encoding="utf-8") as f:
            data: list[dict] = json.load(f)
        return {item["input"]: item["runs"] for item in data}

    async def classify(self, message: str, run_profile: int = 0) -> dict:
        runs = self._resolve(message)
        idx = (run_profile - 1) % len(runs) if run_profile > 0 else 0
        run = runs[idx]

        logger.debug(
            "DEMO profile=%d idx=%d/%d input=%r intent=%s confidence=%.0f%%",
            run_profile,
            idx + 1,
            len(runs),
            message[:60],
            run["intent"],
            run["confidence"] * 100,
        )

        return {
            "predicted_intent": run["intent"],
            "confidence": run["confidence"],
            "intent_distribution": run.get("distribution", {run["intent"]: run["confidence"]}),
            "generated_response": run["response"],
        }

    def _resolve(self, message: str) -> list[dict]:
        if message in self._scenarios:
            return self._scenarios[message]

        lower = message.lower()
        for key, runs in self._scenarios.items():
            if key != _FALLBACK_KEY and key.lower() == lower:
                return runs

        best_key, best_score = None, 0
        msg_words = set(lower.split())
        for key, runs in self._scenarios.items():
            if key == _FALLBACK_KEY:
                continue
            overlap = len(msg_words & set(key.lower().split()))
            if overlap > best_score:
                best_score, best_key = overlap, key

        if best_key and best_score >= 2:
            return self._scenarios[best_key]

        if _FALLBACK_KEY in self._scenarios:
            return self._scenarios[_FALLBACK_KEY]

        return [
            {
                "intent": "general_support",
                "confidence": 0.05,
                "distribution": {k: 0.20 for k in ["billing_issue", "cancel_order", "refund_request", "shipping_issue", "general_support"]},
                "response": "Vou encaminhar sua solicitação para o suporte adequado.",
            }
        ]
