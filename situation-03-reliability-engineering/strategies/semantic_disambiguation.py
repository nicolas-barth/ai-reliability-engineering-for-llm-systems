"""
Strategy 1 — Semantic Disambiguation Layer
==========================================
Detects multi-intent inputs and resolves to a single primary intent
before any routing decision is made.

Problem solved:
    Input "Fui cobrado errado e quero cancelar minha assinatura" carries
    BOTH billing_issue AND cancel_order signals simultaneously. Without
    disambiguation, the classifier races between these interpretations
    across repeated calls — producing inconsistent routing.

Approach:
    1. Keyword scanning maps each signal to its intent category
    2. Ambiguity score quantifies how many intents are activated
    3. Priority hierarchy breaks ties deterministically

This runs PRE-CLASSIFICATION — before the LLM is called.
"""

from __future__ import annotations

INTENT_SIGNALS: dict[str, list[str]] = {
    "billing_issue": [
        "cobrado", "cobrança", "fatura", "valor", "pagamento", "débito",
        "tarifa", "taxa", "plano", "mensalidade", "desconto", "cobranç",
        "errado", "indevido", "incorreto",
    ],
    "refund_request": [
        "reembolso", "devolver", "estorno", "ressarcimento", "devolução",
        "reembolsar", "reaver", "restituir",
    ],
    "cancel_order": [
        "cancelar", "cancelamento", "cancelei", "assinatura", "encerrar",
        "encerramento", "desativar", "desativação", "rescisão",
    ],
    "shipping_issue": [
        "entrega", "envio", "prazo", "rastreamento", "frete", "transportadora",
        "atraso", "extraviado", "não chegou", "código de rastreio",
    ],
    "general_support": [
        "dúvida", "ajuda", "informação", "suporte", "pergunta", "problema",
        "como faço", "preciso de ajuda",
    ],
}

INTENT_PRIORITY: dict[str, int] = {
    "billing_issue":   1,
    "refund_request":  2,
    "cancel_order":    3,
    "shipping_issue":  4,
    "general_support": 5,
}

AMBIGUITY_THRESHOLDS = {
    "LOW":      (0, 1),
    "MODERATE": (2, 2),
    "HIGH":     (3, 3),
    "CRITICAL": (4, 99),
}


class SemanticDisambiguationLayer:
    def analyze(self, message: str) -> DisambiguationResult:
        message_lower = message.lower()
        signal_counts: dict[str, int] = {}
        matched_signals: dict[str, list[str]] = {}

        for intent, signals in INTENT_SIGNALS.items():
            matches = [s for s in signals if s in message_lower]
            if matches:
                signal_counts[intent] = len(matches)
                matched_signals[intent] = matches

        activated = sorted(signal_counts.keys(), key=lambda x: INTENT_PRIORITY[x])
        ambiguity_level = self._classify_ambiguity(len(activated))
        primary_intent = activated[0] if activated else "general_support"
        disambiguation_applied = len(activated) > 1

        return DisambiguationResult(
            primary_intent=primary_intent,
            activated_intents=activated,
            ambiguity_level=ambiguity_level,
            disambiguation_applied=disambiguation_applied,
            signal_counts=signal_counts,
            matched_signals=matched_signals,
        )

    def _classify_ambiguity(self, count: int) -> str:
        for level, (lo, hi) in AMBIGUITY_THRESHOLDS.items():
            if lo <= count <= hi:
                return level
        return "CRITICAL"


class DisambiguationResult:
    __slots__ = (
        "primary_intent",
        "activated_intents",
        "ambiguity_level",
        "disambiguation_applied",
        "signal_counts",
        "matched_signals",
    )

    def __init__(
        self,
        primary_intent: str,
        activated_intents: list[str],
        ambiguity_level: str,
        disambiguation_applied: bool,
        signal_counts: dict[str, int],
        matched_signals: dict[str, list[str]],
    ):
        self.primary_intent = primary_intent
        self.activated_intents = activated_intents
        self.ambiguity_level = ambiguity_level
        self.disambiguation_applied = disambiguation_applied
        self.signal_counts = signal_counts
        self.matched_signals = matched_signals

    def __repr__(self) -> str:
        return (
            f"DisambiguationResult("
            f"primary={self.primary_intent!r}, "
            f"activated={self.activated_intents}, "
            f"ambiguity={self.ambiguity_level})"
        )


if __name__ == "__main__":
    layer = SemanticDisambiguationLayer()
    test_messages = [
        "Fui cobrado errado e quero cancelar minha assinatura",
        "Quero solicitar reembolso da minha última fatura",
        "Onde está minha entrega? Já passou do prazo",
        "Tenho uma dúvida sobre minha conta",
    ]
    for msg in test_messages:
        result = layer.analyze(msg)
        print(f"\n[INPUT]  {msg}")
        print(f"[OUTPUT] primary={result.primary_intent} | ambiguity={result.ambiguity_level}")
        print(f"         activated={result.activated_intents}")
        print(f"         signals={result.matched_signals}")
