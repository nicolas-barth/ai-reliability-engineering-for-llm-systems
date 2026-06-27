"""
Usage:
    python scripts/run_full_reliability_engineering.py [--mode fast|standard|full] [--skip-api]

    --mode fast       10 runs/experiment  (~1 min)
    --mode standard   25 runs/experiment  (~3-5 min)
    --mode full       50 runs/experiment  (~10 min)
    --skip-api        Use synthetic data — no backend required
"""

import argparse
import json
import math
import os
import sys
import time
import warnings
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.patches as mpatches
warnings.filterwarnings("ignore", message=".*[Tt]ight.*[Ll]ayout.*", category=UserWarning)
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
S1_OUTPUTS = ROOT.parent / "situation-01-evaluation" / "outputs"
OUTPUTS_DIR = ROOT / "outputs"
VIZ_DIR = ROOT / "visualizations"
REPORTS_DIR = ROOT / "reports"

for d in (OUTPUTS_DIR, VIZ_DIR, REPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT))

from evaluations.reliability_evaluator import ReliabilityEvaluator
from evaluations.comparison_engine import ComparisonEngine
from experiments.experiment_runner import ExperimentRunner

DARK_BG   = "#0d1117"
GRID_COL  = "#21262d"
TEXT_COL  = "#e6edf3"
ACCENT    = "#58a6ff"
GREEN     = "#3fb950"
YELLOW    = "#d29922"
RED       = "#f85149"
ORANGE    = "#db6d28"
PURPLE    = "#bc8cff"

EXP_COLORS = [RED, YELLOW, ORANGE, GREEN]
EXP_LABELS_SHORT = ["Baseline", "Structured", "Disambiguation\n+ Priority", "All Strategies"]

MODES = {
    "fast": {
        "n_runs": 10,
        "label": "FAST",
        "description": "Rapid validation — 10 runs per experiment",
        "estimated_time": "~1 minute",
    },
    "standard": {
        "n_runs": 25,
        "label": "STANDARD",
        "description": "Normal workflow — 25 runs per experiment",
        "estimated_time": "~3-5 minutes",
    },
    "full": {
        "n_runs": 50,
        "label": "FULL",
        "description": "Official execution — 50 runs per experiment",
        "estimated_time": "~10 min sequential / ~2 min parallel",
    },
}


def load_baseline(runner: ExperimentRunner, evaluator: ReliabilityEvaluator) -> dict:
    print("  Loading Situation 1 baseline data...")
    runs = runner.run_baseline()
    metrics = evaluator.evaluate(runs)
    print(f"  Loaded {len(runs)} baseline runs. "
          f"Consistency: {metrics['consistency']['consistency_rate_pct']}%")
    return {"label": "Experiment 01 — Baseline", "strategies_active": "None (unstable system)",
            "level": 0, "runs": runs, "metrics": metrics}


def run_experiment(
    level: int,
    label: str,
    strategies_active: str,
    runner: ExperimentRunner,
    evaluator: ReliabilityEvaluator,
    n_runs: int,
    use_synthetic: bool,
) -> dict:
    print(f"  Running {label} ({n_runs} runs)...")
    runs = runner.run_api_experiment(level, n_runs=n_runs, use_synthetic=use_synthetic)
    metrics = evaluator.evaluate(runs)
    cr = metrics["consistency"]["consistency_rate_pct"]
    rs = metrics["reliability"]["reliability_score"]
    rl = metrics["reliability"]["readiness_label"]
    print(f"  Done. Consistency: {cr}% | Score: {rs}/100 | {rl}")
    return {"label": label, "strategies_active": strategies_active,
            "level": level, "runs": runs, "metrics": metrics}


# VISUALIZATION HELPERS
def _setup_fig(title: str, figsize=(12, 6)):
    fig, ax = plt.subplots(figsize=figsize, facecolor=DARK_BG)
    ax.set_facecolor(DARK_BG)
    ax.tick_params(colors=TEXT_COL, labelsize=10)
    ax.xaxis.label.set_color(TEXT_COL)
    ax.yaxis.label.set_color(TEXT_COL)
    ax.title.set_color(TEXT_COL)
    ax.spines[:].set_color(GRID_COL)
    ax.grid(axis="y", color=GRID_COL, linewidth=0.7, alpha=0.8)
    ax.set_axisbelow(True)
    fig.suptitle(title, color=TEXT_COL, fontsize=14, fontweight="bold", y=1.01)
    return fig, ax


def plot_consistency(experiments: list[dict]) -> None:
    values = [e["metrics"]["consistency"]["consistency_rate_pct"] for e in experiments]
    fig, ax = _setup_fig("Consistency Rate — Before vs After Each Strategy Layer")

    bars = ax.bar(EXP_LABELS_SHORT, values, color=EXP_COLORS, width=0.55,
                  edgecolor=DARK_BG, linewidth=0.5)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f"{val:.0f}%", ha="center", va="bottom",
                color=TEXT_COL, fontweight="bold", fontsize=12)

    ax.axhline(85, color=GREEN, linestyle="--", linewidth=1.5, alpha=0.8)
    ax.text(3.5, 86.5, "Target ≥ 85%", color=GREEN, fontsize=9, ha="right")
    ax.set_ylim(0, 105)
    ax.set_ylabel("Consistency Rate (%)", color=TEXT_COL)
    ax.set_xlabel("Experiment", color=TEXT_COL)

    plt.tight_layout(pad=2.0)
    path = VIZ_DIR / "before_vs_after_consistency.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"  Saved {path.name}")


def plot_entropy(experiments: list[dict]) -> None:
    values = [e["metrics"]["entropy"]["normalized_entropy"] for e in experiments]
    levels = [e["metrics"]["entropy"]["entropy_level"] for e in experiments]
    level_colors = {"LOW": GREEN, "MEDIUM": YELLOW, "HIGH": RED}
    bar_colors = [level_colors.get(lv, ACCENT) for lv in levels]

    fig, ax = _setup_fig("Entropy Reduction — Classification Unpredictability Over Time")
    bars = ax.bar(EXP_LABELS_SHORT, values, color=bar_colors, width=0.55,
                  edgecolor=DARK_BG, linewidth=0.5)

    for bar, val, lv in zip(bars, values, levels):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{val:.3f}\n({lv})", ha="center", va="bottom",
                color=TEXT_COL, fontsize=10, fontweight="bold")

    ax.axhline(0.35, color=GREEN, linestyle="--", linewidth=1.5, alpha=0.8)
    ax.text(3.5, 0.36, "Target < 0.35 (LOW)", color=GREEN, fontsize=9, ha="right")
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Normalized Shannon Entropy (0 = deterministic)", color=TEXT_COL)
    ax.set_xlabel("Experiment", color=TEXT_COL)

    patches = [mpatches.Patch(color=c, label=l) for l, c in level_colors.items()]
    ax.legend(handles=patches, facecolor=DARK_BG, edgecolor=GRID_COL,
              labelcolor=TEXT_COL, loc="upper right")

    plt.tight_layout(pad=2.0)
    path = VIZ_DIR / "entropy_reduction.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"  Saved {path.name}")


def plot_drift(experiments: list[dict]) -> None:
    routing_flows = [e["metrics"]["routing"]["unique_routing_flows"] for e in experiments]
    dominant_pcts = [e["metrics"]["routing"].get("dominant_flow_pct", 0) for e in experiments]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), facecolor=DARK_BG)
    fig.suptitle("Routing Drift Reduction — Flows and Dominance", color=TEXT_COL,
                 fontsize=14, fontweight="bold")

    for ax in (ax1, ax2):
        ax.set_facecolor(DARK_BG)
        ax.tick_params(colors=TEXT_COL, labelsize=9)
        ax.spines[:].set_color(GRID_COL)
        ax.grid(axis="y", color=GRID_COL, linewidth=0.7, alpha=0.8)
        ax.set_axisbelow(True)

    # Left: unique routing flows
    bars1 = ax1.bar(EXP_LABELS_SHORT, routing_flows, color=EXP_COLORS, width=0.55,
                    edgecolor=DARK_BG)
    for bar, val in zip(bars1, routing_flows):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                 str(val), ha="center", color=TEXT_COL, fontweight="bold", fontsize=13)
    ax1.axhline(2, color=GREEN, linestyle="--", linewidth=1.5, alpha=0.8)
    ax1.text(3.5, 2.08, "Target ≤ 2 flows", color=GREEN, fontsize=9, ha="right")
    ax1.set_ylim(0, 6)
    ax1.set_ylabel("Unique Routing Flows", color=TEXT_COL)
    ax1.set_xlabel("Experiment", color=TEXT_COL)
    ax1.set_title("Routing Variance (lower = better)", color=TEXT_COL, fontsize=11)

    # Right: dominant flow %
    bars2 = ax2.bar(EXP_LABELS_SHORT, dominant_pcts, color=EXP_COLORS, width=0.55,
                    edgecolor=DARK_BG)
    for bar, val in zip(bars2, dominant_pcts):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                 f"{val:.0f}%", ha="center", color=TEXT_COL, fontweight="bold", fontsize=12)
    ax2.axhline(85, color=GREEN, linestyle="--", linewidth=1.5, alpha=0.8)
    ax2.text(3.5, 86.5, "Target ≥ 85%", color=GREEN, fontsize=9, ha="right")
    ax2.set_ylim(0, 110)
    ax2.set_ylabel("Dominant Flow Concentration (%)", color=TEXT_COL)
    ax2.set_xlabel("Experiment", color=TEXT_COL)
    ax2.set_title("Flow Dominance (higher = more deterministic)", color=TEXT_COL, fontsize=11)

    plt.tight_layout(pad=2.0)
    path = VIZ_DIR / "drift_reduction.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"  Saved {path.name}")


def plot_reliability_score(experiments: list[dict]) -> None:
    scores = [e["metrics"]["reliability"]["reliability_score"] for e in experiments]
    labels = [e["metrics"]["reliability"]["readiness_label"] for e in experiments]
    readiness_colors = {
        "PRODUCTION READY": "#00d26a",
        "READY":            GREEN,
        "PARTIALLY READY":  YELLOW,
        "NOT READY":        ORANGE,
        "CRITICAL":         RED,
    }
    bar_colors = [readiness_colors.get(lbl, ACCENT) for lbl in labels]

    fig, ax = _setup_fig("Reliability Score Improvement — 0 to 100 Scale", figsize=(12, 7))

    x = np.arange(len(experiments))
    bars = ax.bar(x, scores, color=bar_colors, width=0.55, edgecolor=DARK_BG, linewidth=0.5)

    for bar, score, label in zip(bars, scores, labels):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{score}", ha="center", color=TEXT_COL, fontweight="bold", fontsize=14)
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() / 2,
                label, ha="center", va="center", color=DARK_BG,
                fontweight="bold", fontsize=8, rotation=0)

    ax.axhline(80, color=GREEN, linestyle="--", linewidth=1.5, alpha=0.8)
    ax.text(len(experiments) - 0.5, 81.5, "Target ≥ 80", color=GREEN, fontsize=9, ha="right")
    ax.set_ylim(0, 110)
    ax.set_xticks(x)
    ax.set_xticklabels(EXP_LABELS_SHORT)
    ax.set_ylabel("Reliability Score (0-100)", color=TEXT_COL)
    ax.set_xlabel("Experiment", color=TEXT_COL)

    plt.tight_layout(pad=2.0)
    path = VIZ_DIR / "reliability_score_improvement.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"  Saved {path.name}")


def generate_report(experiments: list[dict], comparison: dict) -> None:
    prog = comparison["progression"]
    impr = comparison["improvements"]
    verdict = comparison["verdict"]

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Reliability Engineering Report",
        f"> Situation 3 — AI Quality Engineering Lab  |  Generated: {now_str}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        verdict["summary"],
        "",
        "---",
        "",
        "## 1. Problem Statement",
        "",
        "Situation 1 measured an intent classification system producing:",
        "",
        f"- **Consistency Rate:** {impr['consistency_rate']['before']:.0f}%  "
        "(40 of 50 identical inputs classified as the same intent)",
        f"- **Entropy:** {impr['entropy']['before_level']}  "
        f"(normalized={impr['entropy']['before']:.3f})",
        f"- **Routing Variance:** {impr['routing_flows']['before']} distinct flows from identical input",
        f"- **Reliability Score:** {impr['reliability_score']['before']}/100",
        f"- **Production Readiness:** {impr['readiness']['before']}",
        "",
        "Situation 2 identified the root causes:",
        "",
        "1. **Prompt Ambiguity** (PRIMARY) — input simultaneously activates multiple intent categories",
        "2. **Intent Taxonomy Overlap** (SECONDARY) — billing, cancel, and refund share semantic space",
        "3. **Non-Deterministic Routing** (CONTRIBUTING) — no routing policy hierarchy",
        "",
        "---",
        "",
        "## 2. Engineering Interventions",
        "",
        "Six reliability strategies were designed and implemented as a layered pipeline:",
        "",
        "### Strategy 1 — Semantic Disambiguation Layer",
        "Pre-classification keyword analysis detects multi-intent inputs and identifies",
        "the primary intent before the LLM is called. Prevents the model from receiving",
        "inherently ambiguous context without guidance.",
        "",
        "### Strategy 2 — Intent Priority Engine",
        "Explicit business-logic priority hierarchy resolves near-tie situations:",
        "`billing_issue > refund_request > cancel_order > shipping_issue > general_support`",
        "Applied when multiple intents score within 15 percentage points of each other.",
        "",
        "### Strategy 3 — Confidence Thresholds",
        "Three confidence bands with distinct routing policies:",
        "- **HIGH** (≥ 0.75): Direct routing, full trust",
        "- **MEDIUM** (≥ 0.50): Direct routing, standard trust",
        "- **LOW** (< 0.50): Blocked — priority fallback applied before routing",
        "",
        "### Strategy 4 — Structured Classification",
        "LLM forced to output JSON schema-validated responses. Eliminates free-text parsing,",
        "silent parse failures, and argmax fallback on corrupted distributions.",
        "Temperature reduced from 1.1 → 0.1 for output stability.",
        "",
        "### Strategy 5 — Routing Determinism",
        "Routing Policy Engine replaces direct `intent → flow` lookup.",
        "All routing decisions are band-aware, priority-respecting, and auditable.",
        "Architecture: `LLM → Validation → Policy Engine → Routing`",
        "",
        "### Strategy 6 — Reliability Scoring",
        "Per-call 0-100 reliability score computed from: confidence band, structured output",
        "validation, disambiguation resolution, routing policy certainty, and context richness.",
        "Used for monitoring, alerting, and production readiness assessment.",
        "",
        "---",
        "",
        "## 3. Experimental Results",
        "",
        "Each experiment applies strategies incrementally on the same test input:",
        "> *\"Fui cobrado errado e quero cancelar minha assinatura\"*",
        "",
        "| Experiment | Strategies Active | Consistency | Entropy | Flows | Score | Readiness |",
        "|------------|-------------------|:-----------:|:-------:|:-----:|:-----:|-----------|",
    ]

    for row in prog:
        lines.append(
            f"| {row['label']} | {row['strategies_active']} | "
            f"{row['consistency_rate']:.0f}% | {row['entropy']} | "
            f"{row['routing_flows']} | {row['reliability_score']}/100 | {row['readiness']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 4. Before vs After Comparison",
        "",
        "```",
        "═══════════════════════════════════════════════════════════════════════",
        "  RELIABILITY IMPROVEMENT REPORT",
        "═══════════════════════════════════════════════════════════════════════",
        "",
        f"  Metric                  Before          After           Delta",
        f"  ─────────────────────────────────────────────────────────────────",
        f"  Consistency Rate        {impr['consistency_rate']['before']:.0f}%             "
        f"{impr['consistency_rate']['after']:.0f}%             "
        f"+{impr['consistency_rate']['delta']:.0f}pp",
        f"  Entropy Level           {impr['entropy']['before_level']:<15} "
        f"{impr['entropy']['after_level']:<15} ↓",
        f"  Normalized Entropy      {impr['entropy']['before']:.3f}           "
        f"{impr['entropy']['after']:.3f}           "
        f"{impr['entropy']['delta']:+.3f}",
        f"  Dominant Flow Pct       {impr['routing_flows']['dominant_flow_pct_before']:.0f}%             "
        f"{impr['routing_flows']['dominant_flow_pct_after']:.0f}%             "
        f"+{impr['routing_flows']['dominant_flow_pct_after'] - impr['routing_flows']['dominant_flow_pct_before']:.0f}pp",
        f"  Reliability Score       {impr['reliability_score']['before']}/100          "
        f"{impr['reliability_score']['after']}/100          "
        f"+{impr['reliability_score']['delta']}",
        f"  Production Readiness    {impr['readiness']['before']:<15} "
        f"{impr['readiness']['after']:<15} ↑",
        "",
        "═══════════════════════════════════════════════════════════════════════",
        "```",
        "",
        "---",
        "",
        "## 5. Root Cause Remediation",
        "",
        "| Root Cause | Status | Fix Applied |",
        "|------------|:------:|-------------|",
        "| Prompt Ambiguity (RCA-01) | RESOLVED | Strategy 1 (Disambiguation) + Strategy 4 (Structured) |",
        "| Intent Taxonomy Overlap (RCA-02) | RESOLVED | Strategy 2 (Priority Engine) |",
        "| Non-Deterministic Routing (CF-01) | RESOLVED | Strategy 3 (Thresholds) + Strategy 5 (Policy Engine) |",
        "",
        "---",
        "",
        "## 6. Verdict",
        "",
        f"**Targets Met:** {verdict['targets_met_count']}/{verdict['targets_total']}",
        "",
        f"**Final Reliability Score:** {verdict['final_score']}/100",
        "",
        f"**Production Readiness:** `{verdict['final_readiness']}`",
        "",
        "> " + verdict["summary"],
        "",
        "---",
        "",
        "*AI Quality Engineering Lab — Situation 3: Reliability Engineering*",
    ]

    report_path = REPORTS_DIR / "reliability_engineering_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Saved {report_path.name}")


def print_executive_summary(experiments: list[dict], comparison: dict) -> None:
    prog = comparison["progression"]
    impr = comparison["improvements"]
    verdict = comparison["verdict"]
    sep = "=" * 70

    print(f"\n{sep}")
    print("  SITUATION 3 — RELIABILITY ENGINEERING")
    print("  EXECUTIVE SUMMARY")
    print(sep)
    print()
    print("  EXPERIMENT PROGRESSION")
    print(f"  {'Experiment':<40} {'Consistency':>12} {'Score':>8} {'Readiness'}")
    print(f"  {'-'*40} {'-'*12} {'-'*8} {'-'*20}")
    for row in prog:
        print(f"  {row['label']:<40} {row['consistency_rate']:>11.0f}% "
              f"{row['reliability_score']:>7}/100  {row['readiness']}")

    print()
    print("  BEFORE vs AFTER")
    print(f"  {'-'*65}")

    def delta_str(val):
        return f"+{val}" if val > 0 else str(val)

    b_cons = impr["consistency_rate"]["before"]
    a_cons = impr["consistency_rate"]["after"]
    b_ent  = impr["entropy"]["before_level"]
    a_ent  = impr["entropy"]["after_level"]
    b_flow = impr["routing_flows"]["dominant_flow_pct_before"]
    a_flow = impr["routing_flows"]["dominant_flow_pct_after"]
    b_scr  = impr["reliability_score"]["before"]
    a_scr  = impr["reliability_score"]["after"]
    b_read = impr["readiness"]["before"]
    a_read = impr["readiness"]["after"]

    rows = [
        ("Consistency Rate", f"{b_cons:.0f}%",    f"{a_cons:.0f}%",   f"+{a_cons - b_cons:.0f}pp"),
        ("Entropy Level",    b_ent,                a_ent,              "improved"),
        ("Dominant Flow %",  f"{b_flow:.0f}%",      f"{a_flow:.0f}%",   f"+{a_flow - b_flow:.0f}pp"),
        ("Reliability Score",f"{b_scr}/100",       f"{a_scr}/100",     delta_str(a_scr - b_scr)),
        ("Readiness",        b_read,               a_read,             "improved"),
    ]
    for metric, before, after, delta in rows:
        print(f"  {metric:<22} {before:<18} {after:<18} {delta}")

    print()
    print("  VERDICT")
    print(f"  {'-'*65}")
    print(f"  Targets met:    {verdict['targets_met_count']}/{verdict['targets_total']}")
    print(f"  Final score:    {verdict['final_score']}/100")
    print(f"  Readiness:      {verdict['final_readiness']}")
    print()
    # Wrap verdict summary at 66 chars
    summary = verdict["summary"]
    words = summary.split()
    line = "  "
    for word in words:
        if len(line) + len(word) + 1 > 68:
            print(line)
            line = "  " + word + " "
        else:
            line += word + " "
    if line.strip():
        print(line)
    print()
    print(sep)


# MAIN
def _parse_args():
    parser = argparse.ArgumentParser(
        prog="run_full_reliability_engineering",
        description="Situation 3 — AI Reliability Engineering Platform",
    )
    parser.add_argument(
        "--mode",
        choices=["fast", "standard", "full"],
        default="full",
        help="Execution mode: fast=10 runs, standard=25 runs, full=50 runs (default: full)",
    )
    parser.add_argument(
        "--skip-api",
        action="store_true",
        help="Use deterministic synthetic data instead of calling the backend",
    )
    return parser.parse_args()


def _print_header(mode_cfg: dict, use_synthetic: bool) -> None:
    data_source = "OFFLINE -- synthetic data (--skip-api)" if use_synthetic else "LIVE -- backend at localhost:8000"
    print(f"\n{'='*70}")
    print("  SITUATION 3 -- RELIABILITY ENGINEERING")
    print(f"  AI Quality Engineering Lab")
    print(f"{'='*70}")
    print(f"  Mode:             {mode_cfg['label']}  |  {mode_cfg['description']}")
    print(f"  Runs/Experiment:  {mode_cfg['n_runs']}")
    print(f"  Experiments:      4  (Baseline + 3 strategy layers)")
    print(f"  Data source:      {data_source}")
    print(f"  Estimated time:   {mode_cfg['estimated_time']}")
    print(f"{'='*70}")
    print()


def main():
    _start = time.time()
    args = _parse_args()
    mode_cfg = MODES[args.mode]
    n_runs = mode_cfg["n_runs"]
    use_synthetic = args.skip_api

    runner    = ExperimentRunner(S1_OUTPUTS, OUTPUTS_DIR)
    evaluator = ReliabilityEvaluator()
    engine    = ComparisonEngine()

    _print_header(mode_cfg, use_synthetic)

    sep = "-" * 70

    print(f"{sep}")
    print("  Step 1 -- Loading baseline (Situation 1 data)")
    print(sep)
    baseline = load_baseline(runner, evaluator)
    experiments = [baseline]

    experiment_configs = [
        (1, "Experiment 02 -- Structured Classification",
         "Structured Output + Low Temperature"),
        (2, "Experiment 03 -- Disambiguation + Priority Engine",
         "Strategies 1-2-3: Disambiguation + Priority + Thresholds"),
        (3, "Experiment 04 -- Full Reliability Engineering",
         "All 6 Strategies: Complete Reliability Pipeline"),
    ]

    for i, (level, label, strategies) in enumerate(experiment_configs, start=2):
        print(f"{sep}")
        print(f"  Step {i + 1} -- {label}")
        print(sep)
        exp = run_experiment(level, label, strategies, runner, evaluator, n_runs, use_synthetic)
        experiments.append(exp)

    print(f"{sep}")
    print("  Step 5 -- Computing before/after comparison")
    print(sep)
    comparison = engine.compare(experiments)

    print(f"{sep}")
    print("  Step 6 -- Saving outputs")
    print(sep)
    improvement_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "execution_mode": args.mode,
        "data_source": "synthetic" if use_synthetic else "live",
        "runs_per_experiment": n_runs,
        "comparison": comparison,
        "experiments": [
            {"label": e["label"], "metrics": e["metrics"]} for e in experiments
        ],
    }
    out_path = OUTPUTS_DIR / "reliability_improvement_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(improvement_report, f, indent=2, ensure_ascii=False)
    print(f"  Saved {out_path.name}")

    print(f"{sep}")
    print("  Step 7 -- Generating visualizations")
    print(sep)
    plot_consistency(experiments)
    plot_entropy(experiments)
    plot_drift(experiments)
    plot_reliability_score(experiments)

    print(f"{sep}")
    print("  Step 8 -- Generating reliability engineering report")
    print(sep)
    generate_report(experiments, comparison)

    print_executive_summary(experiments, comparison)

    print(f"  Outputs:        {OUTPUTS_DIR}")
    print(f"  Visualizations: {VIZ_DIR}")
    print(f"  Reports:        {REPORTS_DIR}")
    print(f"\n{'='*70}\n")

    _elapsed = time.time() - _start
    if _elapsed >= 60:
        _min = int(_elapsed // 60)
        _sec = _elapsed % 60
        _time_str = f"{_min} minute{'s' if _min != 1 else ''} {_sec:.1f} seconds"
    else:
        _time_str = f"{_elapsed:.1f} seconds"
    print("=" * 50)
    print("Situation 03 Completed")
    print(f"Execution Time: {_time_str}")
    print("=" * 50)


if __name__ == "__main__":
    main()
