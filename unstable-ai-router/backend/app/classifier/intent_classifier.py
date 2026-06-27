import re
import random
import logging

from openai import AsyncOpenAI

from app.prompts.classification_prompt import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    PROFILE_INSTRUCTIONS,
    PROFILE_CONFIDENCE_RANGES,
)

logger = logging.getLogger(__name__)

VALID_INTENTS = [
    "cancel_order",
    "refund_request",
    "billing_issue",
    "shipping_issue",
    "general_support",
]

_FALLBACK_RESPONSES = {
    "cancel_order":    "Vou ajudar com o cancelamento da sua assinatura.",
    "refund_request":  "Encaminharei sua solicitação de reembolso para a equipe responsável.",
    "billing_issue":   "Identificamos um problema na sua cobrança. Vou verificar imediatamente.",
    "shipping_issue":  "Vou verificar o status da sua entrega junto à transportadora.",
    "general_support": "Recebi sua mensagem. Um agente especializado irá analisar seu caso.",
}

_UNIFORM_DISTRIBUTION = {intent: 0.20 for intent in VALID_INTENTS}


class IntentClassifier:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def classify(self, message: str, run_profile: int = 0) -> dict:
        user_content = USER_PROMPT_TEMPLATE.format(message=message)

        if run_profile > 0 and run_profile in PROFILE_INSTRUCTIONS:
            system_content = PROFILE_INSTRUCTIONS[run_profile] + "\n\n" + SYSTEM_PROMPT
        else:
            system_content = SYSTEM_PROMPT

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
            temperature=1.1,
            top_p=0.98,
            presence_penalty=0.4,
            max_tokens=300,
        )

        raw_text = response.choices[0].message.content or ""
        logger.debug("LLM raw output (profile=%d): %s", run_profile, raw_text)

        distribution = self._parse_distribution(raw_text)
        intent = self._parse_selected(raw_text, distribution)

        if run_profile > 0 and run_profile in PROFILE_CONFIDENCE_RANGES:
            low, high = PROFILE_CONFIDENCE_RANGES[run_profile]
            confidence = round(random.uniform(low, high), 2)
        else:
            confidence = round(distribution.get(intent, 0.50), 2)

        return {
            "predicted_intent": intent,
            "confidence": confidence,
            "intent_distribution": distribution,
            "generated_response": self._parse_response(raw_text, intent),
        }

    def _parse_distribution(self, text: str) -> dict:
        dist = {}
        for intent in VALID_INTENTS:
            match = re.search(rf"{re.escape(intent)}:\s*([\d.]+)", text, re.IGNORECASE)
            if match:
                try:
                    dist[intent] = min(1.0, max(0.0, float(match.group(1))))
                except ValueError:
                    dist[intent] = 0.0
            else:
                dist[intent] = 0.0

        total = sum(dist.values())
        if total > 0:
            dist = {k: round(v / total, 3) for k, v in dist.items()}
        else:
            dist = dict(_UNIFORM_DISTRIBUTION)

        return dist

    def _parse_selected(self, text: str, distribution: dict) -> str:
        match = re.search(r"Selected:\s*(\w+)", text, re.IGNORECASE)
        if match:
            candidate = match.group(1).lower()
            if candidate in VALID_INTENTS:
                return candidate

        if distribution:
            return max(distribution, key=distribution.get)

        return "general_support"

    def _parse_response(self, text: str, intent: str) -> str:
        match = re.search(r"Response:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
        if match:
            response = match.group(1).strip()
            response = " ".join(response.split())
            return response[:400]

        return _FALLBACK_RESPONSES.get(intent, "Encaminhando para o suporte adequado.")
