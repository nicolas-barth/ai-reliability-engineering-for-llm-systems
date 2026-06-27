"""
Repeated Runs Evaluator

Executes the classification system N times with a fixed input to expose
probabilistic instability. No mocking — hits the live API endpoint.
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).parent.parent
DATASETS_DIR = ROOT / "datasets"
OUTPUTS_DIR = ROOT / "outputs"

CLASSIFY_URL = "http://localhost:8000/api/v1/classify"
DEFAULT_RUNS = 50
REQUEST_DELAY_S = 0.3


class RepeatedRunsEvaluator:
    def __init__(
        self,
        runs: int = DEFAULT_RUNS,
        classify_url: str = CLASSIFY_URL,
        input_file: Path = DATASETS_DIR / "main_input.json",
    ) -> None:
        self.runs = runs
        self.classify_url = classify_url
        self.input_file = input_file
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_input(self) -> str:
        with open(self.input_file, "r", encoding="utf-8") as f:
            return json.load(f)[0]

    def _classify_once(self, client: httpx.Client, message: str) -> dict[str, Any]:
        response = client.post(
            self.classify_url,
            json={"message": message},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    def run(self) -> list[dict[str, Any]]:
        message = self._load_input()
        results: list[dict[str, Any]] = []

        print(f"\n{'='*60}")
        print("  REPEATED RUNS EVALUATOR")
        print(f"{'='*60}")
        print(f"  Input : {message!r}")
        print(f"  Runs  : {self.runs}")
        print(f"  URL   : {self.classify_url}")
        print(f"{'='*60}\n")

        with httpx.Client() as client:
            for i in range(1, self.runs + 1):
                try:
                    result = self._classify_once(client, message)
                    result["run_number"] = i
                    results.append(result)

                    intent = result.get("predicted_intent", "unknown")
                    confidence = result.get("confidence", 0.0)
                    print(
                        f"  Run {i:>3}/{self.runs}"
                        f"  intent={intent:<22}"
                        f"  confidence={confidence:.4f}"
                    )
                except httpx.ConnectError:
                    print(
                        f"  Run {i:>3}/{self.runs}  CONNECTION ERROR — "
                        "is the server running at localhost:8000?",
                        file=sys.stderr,
                    )
                    break
                except httpx.RequestError as exc:
                    print(f"  Run {i:>3}/{self.runs}  REQUEST ERROR: {exc}", file=sys.stderr)
                except httpx.HTTPStatusError as exc:
                    print(f"  Run {i:>3}/{self.runs}  HTTP {exc.response.status_code}", file=sys.stderr)

                if i < self.runs:
                    time.sleep(REQUEST_DELAY_S)

        print(f"\n  Collected {len(results)} results.\n")

        if results:
            self._save_json(results)
            self._save_csv(results)

        return results

    def _save_json(self, results: list[dict[str, Any]]) -> None:
        path = OUTPUTS_DIR / "evaluation_results.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"  [JSON] {path}")

    def _save_csv(self, results: list[dict[str, Any]]) -> None:
        path = OUTPUTS_DIR / "evaluation_results.csv"
        fieldnames = [
            "run_number", "run_id", "predicted_intent", "confidence",
            "routing_flow", "execution_mode", "timestamp",
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(results)
        print(f"  [CSV]  {path}")
