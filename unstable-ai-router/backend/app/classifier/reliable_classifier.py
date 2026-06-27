import json
import re
import logging

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

VALID_INTENTS = [
    "cancel_order",
    "refund_request",
    "billing_issue",
    "shipping_issue",
    "general_support",
]

# Priority hierarchy: lower number = higher priority
INTENT_PRIORITY = {
    "billing_issue": 1,
    "refund_request": 2,
    "cancel_order": 3,
    "shipping_issue": 4,
    "general_support": 5,
}

_RELIABLE_SYSTEM_PROMPT = """You are a precision customer intent classifier for a support routing system.

Your task: classify the customer message into EXACTLY ONE intent category.

AVAILABLE INTENTS:
- billing_issue: Charges, payments, invoices, billing errors, unexpected fees
- refund_request: Requests for money back, refunds, reimbursements, chargebacks
- cancel_order: Subscription cancellations, order cancellations, service termination
- shipping_issue: Delivery problems, tracking, shipping delays, missing packages
- general_support: General questions, account issues, anything that does not fit above

DISAMBIGUATION RULES — apply when multiple intents are detected:
1. billing_issue > all others when any charge/payment signal is present
2. refund_request > cancel_order when money-back language is explicit
3. cancel_order > general_support for any cancellation intent
4. shipping_issue only when delivery/shipment is the dominant concern
5. general_support is the fallback of last resort

OUTPUT — respond with valid JSON only, no extra text:
{
  "intent": "<one of the five intents above>",
  "confidence": <float 0.0-1.0>,
  "reasoning": "<one sentence>",
  "secondary_intents": ["<other detected intents>"],
  "disambiguation_applied": <true|false>,
  "signals_detected": ["<keywords or phrases that triggered the classification>"]
}"""

_LEVEL_1_SYSTEM_PROMPT = """You are a precision customer intent classifier for a support routing system.

Your task: classify the customer message into EXACTLY ONE intent category.

AVAILABLE INTENTS:
- billing_issue: Charges, payments, invoices, billing errors, unexpected fees
- refund_request: Requests for money back, refunds, reimbursements, chargebacks
- cancel_order: Subscription cancellations, order cancellations, service termination
- shipping_issue: Delivery problems, tracking, shipping delays, missing packages
- general_support: General questions, account issues, anything else

OUTPUT — respond with valid JSON only:
{
  "intent": "<one of the five intents above>",
  "confidence": <float 0.0-1.0>,
  "reasoning": "<one sentence>",
  "secondary_intents": [],
  "disambiguation_applied": false,
  "signals_detected": []
}"""

_USER_TEMPLATE = 'Classify this customer message:\n\n"{message}"\n\nRespond with JSON only.'

_FALLBACK_RESPONSES = {
    "cancel_order":    "Vou processar o cancelamento da sua assinatura agora.",
    "refund_request":  "Sua solicitação de reembolso será processada em 3-5 dias úteis.",
    "billing_issue":   "Identificamos o problema na sua cobrança. Vou corrigir imediatamente.",
    "shipping_issue":  "Vou verificar o rastreamento do seu pedido agora.",
    "general_support": "Recebemos sua solicitação e um especialista irá analisá-la.",
}


class ReliableIntentClassifier:

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def classify(self, message: str, strategy_level: int = 3) -> dict:
        system_prompt = (
            _LEVEL_1_SYSTEM_PROMPT if strategy_level == 1 else _RELIABLE_SYSTEM_PROMPT
        )
        user_content = _USER_TEMPLATE.format(message=message)

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
            top_p=0.95,
            presence_penalty=0.0,
            max_tokens=300,
            response_format={"type": "json_object"},
        )

        raw_text = response.choices[0].message.content or "{}"
        logger.debug("ReliableClassifier output (level=%d): %s", strategy_level, raw_text)

        return self._parse(raw_text, strategy_level)

    def _parse(self, raw_text: str, strategy_level: int) -> dict:
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            data = json.loads(match.group()) if match else {}

        intent = str(data.get("intent", "")).lower().strip()
        if intent not in VALID_INTENTS:
            intent = self._extract_intent_from_text(raw_text)

        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
        secondary = [s for s in data.get("secondary_intents", []) if s in VALID_INTENTS]

        if strategy_level >= 3 and confidence < 0.50 and secondary:
            intent, confidence = self._priority_fallback(intent, confidence, secondary)

        return {
            "predicted_intent": intent,
            "confidence": round(confidence, 3),
            "intent_distribution": self._build_distribution(intent, confidence, secondary),
            "generated_response": _FALLBACK_RESPONSES.get(
                intent, "Encaminhando para suporte especializado."
            ),
            "disambiguation_applied": bool(data.get("disambiguation_applied", False)),
            "secondary_intents": secondary,
            "reasoning": str(data.get("reasoning", "")),
            "signals_detected": list(data.get("signals_detected", [])),
            "strategy_level": strategy_level,
        }

    def _extract_intent_from_text(self, text: str) -> str:
        text_lower = text.lower()
        for intent in VALID_INTENTS:
            if intent in text_lower:
                return intent
        return "general_support"

    def _priority_fallback(self, intent: str, confidence: float, secondary: list) -> tuple:
        candidates = [intent] + secondary
        best = min(candidates, key=lambda x: INTENT_PRIORITY.get(x, 99))
        return best, max(confidence, 0.65)

    def _build_distribution(self, dominant: str, confidence: float, secondary: list) -> dict:
        dist = {i: 0.02 for i in VALID_INTENTS}
        dist[dominant] = confidence
        if secondary:
            share = round((1.0 - confidence) * 0.75 / len(secondary), 3)
            for s in secondary:
                if s in dist:
                    dist[s] = share
        total = sum(dist.values())
        return {k: round(v / total, 3) for k, v in dist.items()}
