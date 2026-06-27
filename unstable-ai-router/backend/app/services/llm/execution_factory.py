import logging

from app.classifier.intent_classifier import IntentClassifier
from app.config import Config
from app.services.llm.demo_llm_service import DemoLLMService
from app.services.llm.interfaces import LLMServiceInterface
from app.services.llm.real_llm_service import RealLLMService

logger = logging.getLogger(__name__)


def create_llm_service(config: Config) -> LLMServiceInterface:
    if config.execution_mode == "demo_mode":
        logger.info("Execution mode: DEMO — using pre-defined scenario cycling")
        return DemoLLMService(scenarios_path=config.demo_scenarios_path)

    logger.info("Execution mode: REAL_LLM — calling OpenAI API (temperature=0.9)")
    classifier = IntentClassifier(api_key=config.openai_api_key)
    return RealLLMService(classifier=classifier)
