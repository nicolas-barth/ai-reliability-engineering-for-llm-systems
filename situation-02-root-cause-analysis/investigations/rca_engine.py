from __future__ import annotations

from typing import Any


# Causal chain:
#   Prompt Ambiguity
# Root causes generate the problem.
# Contributing factors amplify it.
# Symptoms are observable consequences — not causes.

ROOT_CAUSES = [
    {
        "id": "RCA-01",
        "name": "Prompt Ambiguity",
        "rank": "primary",
        "category": "root_cause",
        "description": (
            "The input activates multiple distinct intents simultaneously. "
            "No disambiguation strategy is applied at the input layer — the LLM "
            "must resolve genuine semantic uncertainty at inference time. "
            "Controlled experiments proved this is the primary causal driver: "
            "removing the ambiguity produced near-perfect consistency."
        ),
        "situation_3_fix": (
            "Implement semantic disambiguation at the input layer. "
            "Detect multi-intent inputs and resolve them before classification."
        ),
    },
    {
        "id": "RCA-02",
        "name": "Intent Taxonomy Overlap",
        "rank": "secondary",
        "category": "root_cause",
        "description": (
            "billing_issue, cancel_order, and refund_request share significant "
            "semantic space. When an ambiguous input is presented, the classifier "
            "cannot distinguish between them cleanly — producing competing "
            "interpretations and split probability mass."
        ),
        "situation_3_fix": (
            "Redefine intent boundaries with mutually exclusive semantic criteria. "
            "Add explicit decision rules for overlapping domains."
        ),
    },
]

CONTRIBUTING_FACTORS = [
    {
        "id": "CF-01",
        "name": "Non-Deterministic Routing",
        "category": "contributing_factor",
        "description": (
            "When multiple intents compete, no routing priority hierarchy exists "
            "to resolve the ambiguity. The routing outcome is determined by whichever "
            "intent wins the probabilistic competition — which varies per run."
        ),
        "situation_3_fix": (
            "Add routing priority rules and confidence threshold guards. "
            "Define explicit tiebreakers when multiple intents are viable."
        ),
    },
]

OBSERVABLE_SYMPTOMS = [
    {
        "id": "SYM-01",
        "name": "Confidence Score Volatility",
        "category": "symptom",
        "explanation": (
            "When two intents hold near-equal probability mass, confidence collapses. "
            "The observed multimodal distribution is a consequence of intent competition, "
            "not an independent cause."
        ),
    },
    {
        "id": "SYM-02",
        "name": "Semantic Response Drift",
        "category": "symptom",
        "explanation": (
            "Responses drift because the selected intent changes per run. "
            "The LLM generates coherent responses per intent — but different intents "
            "produce structurally different responses."
        ),
    },
    {
        "id": "SYM-03",
        "name": "Routing Variance",
        "category": "symptom",
        "explanation": (
            "4 distinct routing flows activated from identical input. "
            "Routing variance is downstream of intent classification instability."
        ),
    },
    {
        "id": "SYM-04",
        "name": "Low Consistency Rate",
        "category": "symptom",
        "explanation": (
            "40% consistency is the aggregate result of all competing causal factors. "
            "It measures the problem, not its origin."
        ),
    },
]

SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


class RCAEngine:
    def compute(
        self,
        overlap_result: dict,
        ambiguity_result: dict,
        routing_result: dict,
        confidence_result: dict,
        experiment_result: dict | None = None,
    ) -> dict[str, Any]:
        scored_causes = self._score_root_causes(
            overlap_result, ambiguity_result, experiment_result
        )
        scored_factors = self._score_contributing_factors(routing_result)

        primary = scored_causes[0]
        secondary = scored_causes[1] if len(scored_causes) > 1 else None

        engineering_conclusion = self._build_conclusion(
            primary, secondary, ambiguity_result, routing_result, confidence_result, experiment_result
        )

        situation_3_priorities = (
            [rc["situation_3_fix"] for rc in scored_causes]
            + [cf["situation_3_fix"] for cf in scored_factors]
        )

        # Annotate symptoms with actual metric values
        symptoms = self._annotate_symptoms(confidence_result, routing_result)

        return {
            "primary_root_cause": {
                "name": primary["name"],
                "id": primary["id"],
                "severity": primary["severity"],
                "evidence": primary["evidence"],
                "score": primary["score"],
            },
            "secondary_root_cause": {
                "name": secondary["name"],
                "id": secondary["id"],
                "severity": secondary["severity"],
                "evidence": secondary["evidence"],
                "score": secondary["score"],
            } if secondary else None,
            "root_causes": scored_causes,
            "contributing_factors": scored_factors,
            "observable_symptoms": symptoms,
            "root_cause_ranking": scored_causes + scored_factors,
            "engineering_conclusion": engineering_conclusion,
            "confidence_level": (
                "HIGH" if experiment_result and experiment_result.get("comparison") else "MEDIUM"
            ),
            "overall_impact": "CRITICAL",
            "situation_3_priorities": situation_3_priorities,
            "causal_chain": [
                "Prompt Ambiguity",
                "Intent Taxonomy Overlap",
                "Non-Deterministic Routing",
                "Confidence Volatility / Routing Variance / Semantic Drift",
            ],
        }


    def _score_root_causes(
        self,
        overlap: dict,
        ambiguity: dict,
        experiments: dict | None,
    ) -> list[dict[str, Any]]:
        results = []

        # RCA-01: Prompt Ambiguity
        # Evidence strength driven by experiment results — this is causal, not correlational.
        level_base = {"LOW": 40, "MODERATE": 60, "HIGH": 80, "CRITICAL": 95}
        base = level_base.get(ambiguity["ambiguity_level"], 60)

        experiment_evidence = ""
        if experiments and experiments.get("comparison"):
            baseline = experiments.get("baseline_consistency", 40.0)
            deltas = [
                (c["label"], c["consistency_rate_pct"], c["delta_vs_baseline"])
                for c in experiments["comparison"]
                if c["id"] != "EXP-00"
            ]
            best_label, best_pct, best_delta = max(deltas, key=lambda x: x[2])
            if best_delta > 40:
                base = min(100, base + 15)
            experiment_evidence = (
                f"Controlled experiments confirmed causality: removing ambiguity raised "
                f"consistency from {baseline:.0f}% to {best_pct:.0f}% ({best_label}). "
                f"Delta: +{best_delta:.0f} percentage points."
            )

        severity = "CRITICAL" if base >= 85 else "HIGH" if base >= 65 else "MEDIUM"

        results.append({
            **ROOT_CAUSES[0],
            "score": round(float(base), 1),
            "severity": severity,
            "evidence": (
                f"Ambiguity level: {ambiguity['ambiguity_level']}. "
                f"{ambiguity['intent_count']} intents triggered simultaneously: "
                f"{', '.join(ambiguity['triggered_intents'])}. "
                + experiment_evidence
            ),
        })

        # RCA-02: Intent Taxonomy Overlap
        os_ = overlap["primary_overlap_score"]
        # Scale overlap score to reflect structural severity (min 40, max 95)
        scaled = round(min(95.0, max(40.0, os_ * 2.0)), 1)
        ov_severity = "CRITICAL" if scaled >= 85 else "HIGH" if scaled >= 60 else "MEDIUM"
        top_pair = overlap["top_competing_pairs"][0]

        results.append({
            **ROOT_CAUSES[1],
            "score": scaled,
            "severity": ov_severity,
            "evidence": (
                f"Primary competing pair: {overlap['primary_overlap']} "
                f"(overlap score {os_:.1f}%). "
                f"Top-2 co-occurrence: {top_pair['top2_cooccurrence_pct']:.1f}% of runs. "
                f"Pearson r={top_pair['pearson_r']:.3f}."
            ),
        })

        return sorted(results, key=lambda x: x["score"], reverse=True)


    def _score_contributing_factors(self, routing: dict) -> list[dict[str, Any]]:
        rs = routing["routing_instability_score"]
        sev = "HIGH" if routing["unique_flows"] >= 3 else "MEDIUM"

        return [{
            **CONTRIBUTING_FACTORS[0],
            "score": round(rs, 1),
            "severity": sev,
            "evidence": (
                f"{routing['unique_flows']} routing flows activated from identical input. "
                f"Collision rate: {routing['collision_rate_pct']:.1f}%. "
                f"Routing changed {routing['transition_count']} times across 50 runs."
            ),
        }]


    def _annotate_symptoms(self, confidence: dict, routing: dict) -> list[dict[str, Any]]:
        stats = confidence["overall_stats"]
        annotated = []
        for sym in OBSERVABLE_SYMPTOMS:
            entry = dict(sym)
            if sym["id"] == "SYM-01":
                entry["metric"] = (
                    f"σ={stats['std']:.3f}, "
                    f"range {stats['min']}–{stats['max']}, "
                    f"{confidence['cluster_count']} confidence clusters"
                )
            elif sym["id"] == "SYM-02":
                entry["metric"] = "mean drift 0.6425 (HIGH — from Situation 1)"
            elif sym["id"] == "SYM-03":
                entry["metric"] = (
                    f"{routing['unique_flows']} distinct flows from identical input"
                )
            elif sym["id"] == "SYM-04":
                entry["metric"] = "40.0% consistency rate (baseline — from Situation 1)"
            annotated.append(entry)
        return annotated


    def _build_conclusion(
        self,
        primary: dict,
        secondary: dict | None,
        ambiguity: dict,
        routing: dict,
        confidence: dict,
        experiments: dict | None,
    ) -> str:
        lines = [
            f"The primary driver of instability is prompt ambiguity. "
            f"The input activates {ambiguity['intent_count']} competing intents "
            f"simultaneously, providing no unambiguous signal for the classifier to resolve."
        ]

        if experiments and experiments.get("comparison"):
            baseline = experiments.get("baseline_consistency", 40.0)
            best = max(
                experiments["comparison"], key=lambda c: c["consistency_rate_pct"]
            )
            lines.append(
                f"Controlled experiments demonstrated that removing semantic ambiguity "
                f"raised consistency from {baseline:.0f}% to {best['consistency_rate_pct']:.0f}% "
                f"({best['label']}), confirming prompt ambiguity as the primary causal driver."
            )

        if secondary:
            lines.append(
                f"Intent taxonomy overlap further amplifies instability by creating "
                f"competing interpretations for the same user request — "
                f"billing_issue, cancel_order, and refund_request share significant semantic space."
            )

        lines.append(
            f"Confidence volatility and routing variance are observable symptoms "
            f"of these root causes — not independent causes themselves."
        )

        return " ".join(lines)
