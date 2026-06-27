from app.classifier.intent_classifier import IntentClassifier
from app.services.llm.interfaces import LLMServiceInterface


class RealLLMService(LLMServiceInterface):

    def __init__(self, classifier: IntentClassifier) -> None:
        self._classifier = classifier

    async def classify(self, message: str, run_profile: int = 0) -> dict:
        return await self._classifier.classify(message, run_profile=run_profile)
