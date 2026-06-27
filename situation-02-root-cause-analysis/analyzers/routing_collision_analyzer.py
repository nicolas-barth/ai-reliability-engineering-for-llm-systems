from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RoutingCollisionAnalyzer:
    def __init__(self, results_path: Path) -> None:
        with results_path.open(encoding="utf-8") as f:
            self._results = json.load(f)

    def analyze(self) -> dict[str, Any]:
        flows = [r["routing_flow"] for r in self._results]
        n = len(flows)

        flow_counts: dict[str, int] = {}
        for f in flows:
            flow_counts[f] = flow_counts.get(f, 0) + 1

        dominant_flow = max(flow_counts, key=lambda k: flow_counts[k])
        collision_count = n - flow_counts[dominant_flow]
        collision_rate_pct = round(collision_count / n * 100, 2)

        all_flows = sorted(set(flows))
        transition_matrix: dict[str, dict[str, int]] = {
            f: {g: 0 for g in all_flows} for f in all_flows
        }
        transition_count = 0
        for i in range(n - 1):
            src, dst = flows[i], flows[i + 1]
            transition_matrix[src][dst] += 1
            if src != dst:
                transition_count += 1

        max_streak = 0
        current_streak = 0
        for i in range(1, n):
            if flows[i] != flows[i - 1]:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        unique_flows = len(all_flows)
        max_possible_flows = 5
        routing_instability_score = round(
            ((unique_flows / max_possible_flows) * 0.4 + (collision_rate_pct / 100) * 0.6) * 100,
            2,
        )

        return {
            "routing_distribution": {
                f: {"count": c, "pct": round(c / n * 100, 1)}
                for f, c in sorted(flow_counts.items(), key=lambda x: x[1], reverse=True)
            },
            "dominant_flow": dominant_flow,
            "unique_flows": unique_flows,
            "collision_rate_pct": collision_rate_pct,
            "transition_count": transition_count,
            "max_consecutive_switches": max_streak,
            "routing_instability_score": routing_instability_score,
            "transition_matrix": transition_matrix,
        }
