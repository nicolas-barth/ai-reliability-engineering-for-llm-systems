from __future__ import annotations

from typing import Any


KEYWORD_INTENT_MAP: dict[str, str] = {
    "cobrado": "billing_issue",
    "cobrança": "billing_issue",
    "indevida": "billing_issue",
    "indevido": "billing_issue",
    "errado": "billing_issue",
    "fatura": "billing_issue",
    "cancelar": "cancel_order",
    "cancelamento": "cancel_order",
    "assinatura": "cancel_order",
    "encerrar": "cancel_order",
    "reembolso": "refund_request",
    "estorno": "refund_request",
    "devolução": "refund_request",
    "devolver": "refund_request",
    "entrega": "shipping_issue",
    "envio": "shipping_issue",
    "rastreamento": "shipping_issue",
    "pacote": "shipping_issue",
    "frete": "shipping_issue",
}

AMBIGUITY_LEVELS = {1: "LOW", 2: "MODERATE", 3: "HIGH", 4: "CRITICAL"}


class PromptAmbiguityAnalyzer:
    def analyze(self, message: str) -> dict[str, Any]:
        text = message.lower()

        keyword_hits: dict[str, str] = {}
        intent_keywords: dict[str, list[str]] = {}

        for keyword, intent in KEYWORD_INTENT_MAP.items():
            if keyword in text:
                keyword_hits[keyword] = intent
                intent_keywords.setdefault(intent, []).append(keyword)

        triggered_intents = list(intent_keywords.keys())

        has_billing = "billing_issue" in triggered_intents
        has_cancel = "cancel_order" in triggered_intents
        if has_billing and has_cancel and "refund_request" not in triggered_intents:
            triggered_intents.append("refund_request")
            intent_keywords["refund_request"] = ["[implied: cobrança + cancelamento]"]

        intent_count = len(triggered_intents)
        ambiguity_level = AMBIGUITY_LEVELS.get(min(intent_count, 4), "CRITICAL")
        unique_intent_slots = len(set(KEYWORD_INTENT_MAP.values()))
        ambiguity_score = round(intent_count / unique_intent_slots * 100, 2)

        return {
            "message": message,
            "keyword_hits": keyword_hits,
            "intent_keywords": intent_keywords,
            "triggered_intents": triggered_intents,
            "intent_count": intent_count,
            "ambiguity_level": ambiguity_level,
            "ambiguity_score": ambiguity_score,
        }

    def analyze_batch(self, messages: list[dict]) -> list[dict[str, Any]]:
        results = []
        for msg_obj in messages:
            result = self.analyze(msg_obj["input"])
            result["id"] = msg_obj.get("id", "")
            result["label"] = msg_obj.get("label", "")
            results.append(result)
        return results
