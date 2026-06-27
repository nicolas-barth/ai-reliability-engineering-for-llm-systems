from __future__ import annotations

import time
from typing import Any

import httpx


REQUEST_DELAY_S = 0.3
DEFAULT_URL = "http://localhost:8000/api/v1/classify"


class ControlledExperiments:
    def __init__(
        self,
        classify_url: str = DEFAULT_URL,
        runs_per_input: int = 15,
    ) -> None:
        self._url = classify_url
        self._runs = runs_per_input

    def run(self, experiment_inputs: list[dict]) -> dict[str, Any]:
        results_per_experiment: list[dict[str, Any]] = []

        with httpx.Client(timeout=30.0) as client:
            for exp in experiment_inputs:
                result = self._run_single(client, exp)
                results_per_experiment.append(result)

        baseline = next(
            (e for e in results_per_experiment if e.get("id") == "EXP-00"),
            results_per_experiment[0] if results_per_experiment else None,
        )
        baseline_consistency = baseline["consistency_rate_pct"] if baseline else 0.0

        return {
            "experiments": results_per_experiment,
            "baseline_consistency": baseline_consistency,
            "comparison": self._build_comparison(results_per_experiment, baseline_consistency),
        }

    def _run_single(self, client: httpx.Client, exp: dict) -> dict[str, Any]:
        raw: list[dict] = []
        message = exp["input"]
        print(f"      [{exp['id']}] {exp['label']}: {message[:55]}...")

        for i in range(self._runs):
            try:
                resp = client.post(self._url, json={"message": message})
                resp.raise_for_status()
                raw.append(resp.json())
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                print(f"        WARNING run {i + 1} failed: {exc}")
            if i < self._runs - 1:
                time.sleep(REQUEST_DELAY_S)

        if not raw:
            return {
                "id": exp["id"],
                "label": exp["label"],
                "input": message,
                "hypothesis": exp.get("hypothesis", ""),
                "error": "No results collected",
                "consistency_rate_pct": 0.0,
                "unique_intents": 0,
                "unique_routing_flows": 0,
                "total_runs": 0,
            }

        intents = [r["predicted_intent"] for r in raw]
        intent_counts: dict[str, int] = {}
        for intent in intents:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1

        dominant = max(intent_counts, key=lambda k: intent_counts[k])
        consistency_pct = round(intent_counts[dominant] / len(raw) * 100, 2)

        routing_flows = list({r["routing_flow"] for r in raw})
        confidences = [r["confidence"] for r in raw]
        conf_mean = round(sum(confidences) / len(confidences), 4)

        return {
            "id": exp["id"],
            "label": exp["label"],
            "input": message,
            "hypothesis": exp.get("hypothesis", ""),
            "total_runs": len(raw),
            "consistency_rate_pct": consistency_pct,
            "dominant_intent": dominant,
            "unique_intents": len(intent_counts),
            "intent_distribution": intent_counts,
            "unique_routing_flows": len(routing_flows),
            "routing_flows": routing_flows,
            "confidence_mean": conf_mean,
        }

    def _build_comparison(
        self,
        results: list[dict],
        baseline_consistency: float,
    ) -> list[dict[str, Any]]:
        comparison = []
        for exp in results:
            delta = round(exp.get("consistency_rate_pct", 0.0) - baseline_consistency, 2)
            comparison.append({
                "id": exp["id"],
                "label": exp["label"],
                "consistency_rate_pct": exp.get("consistency_rate_pct", 0.0),
                "unique_intents": exp.get("unique_intents", 0),
                "unique_routing_flows": exp.get("unique_routing_flows", 0),
                "confidence_mean": exp.get("confidence_mean", 0.0),
                "delta_vs_baseline": delta,
                "hypothesis_validated": delta > 10,
            })
        return comparison
