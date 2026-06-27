"""
Reads project_metrics.json and generates the executive dashboard artifacts:
project_executive_dashboard.json, project_summary_report.md,
project_evolution.png, final_metrics_scorecard.png

Usage:
    python executive-dashboard/generate_executive_dashboard.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

ROOT      = Path(__file__).resolve().parent.parent
METRICS   = ROOT / "project_metrics.json"
OUT_DIR   = Path(__file__).resolve().parent / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DARK_BG  = "#0d1117"
GRID_COL = "#21262d"
TEXT_COL = "#e6edf3"
ACCENT   = "#58a6ff"
GREEN    = "#3fb950"
YELLOW   = "#d29922"
RED      = "#f85149"
ORANGE   = "#db6d28"
PURPLE   = "#bc8cff"
TEAL     = "#39d353"


def _load_metrics() -> dict:
    with open(METRICS, encoding="utf-8") as f:
        return json.load(f)


# 1. JSON dashboard
def generate_dashboard_json(m: dict) -> dict:
    base = m["baseline"]
    final = m["final_engineered"]
    guard = m["guardrails"]
    prod  = m["production_quality"]
    imp   = m["improvements"]
    prog  = m["situation_3_progression"]["experiments"]

    dashboard = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": "AI Quality Engineering Lab",
        "final_verdict": {
            "production_ready": prod["production_ready"],
            "deployment_recommendation": prod["deployment_recommendation"],
            "overall_quality_score": prod["overall_quality_score"],
            "overall_quality_grade": prod["overall_quality_grade"],
        },
        "evolution": {
            "consistency_rate": {
                "baseline": base["consistency_rate_pct"],
                "after_structured": prog[1]["consistency_rate_pct"],
                "after_disambiguation": prog[2]["consistency_rate_pct"],
                "final": final["consistency_rate_pct"],
                "delta_pp": imp["consistency_rate_delta_pp"],
                "pct_gain": imp["consistency_rate_pct_gain"],
            },
            "reliability_score": {
                "baseline": base["reliability_score"],
                "after_structured": prog[1]["reliability_score"],
                "after_disambiguation": prog[2]["reliability_score"],
                "final": final["reliability_score"],
                "delta_pts": imp["reliability_score_delta_pts"],
            },
            "entropy": {
                "baseline": base["entropy_normalized"],
                "baseline_level": base["entropy_level"],
                "final": final["entropy_normalized"],
                "final_level": final["entropy_level"],
                "delta_bits": imp["entropy_delta_bits"],
            },
            "readiness_progression": [e["readiness"] for e in prog],
        },
        "situation_results": {
            "situation_1": {
                "focus": "Evaluation",
                "key_finding": f"Baseline consistency {base['consistency_rate_pct']}% — CRITICAL instability confirmed",
                "consistency_rate_pct": base["consistency_rate_pct"],
                "reliability_score": base["reliability_score"],
                "readiness": base["readiness"],
            },
            "situation_2": {
                "focus": "Root Cause Analysis",
                "key_finding": "3 root causes identified: Prompt Ambiguity (CRITICAL), Taxonomy Overlap (HIGH), Non-Deterministic Routing (HIGH)",
                "primary_root_cause": "Prompt Ambiguity",
                "primary_root_cause_score": 95,
            },
            "situation_3": {
                "focus": "Reliability Engineering",
                "key_finding": f"Consistency improved from {base['consistency_rate_pct']}% to {final['consistency_rate_pct']}% through 6 strategy layers",
                "consistency_rate_pct": final["consistency_rate_pct"],
                "reliability_score": final["reliability_score"],
                "readiness": final["readiness"],
                "targets_met": "4/4",
            },
            "situation_4": {
                "focus": "Guardrails",
                "key_finding": "100% detection rate, 100% block rate, 0% false positives across 5 fault-injection experiments",
                "detection_rate_pct": guard["detection_rate_pct"],
                "block_rate_pct": guard["block_rate_pct"],
                "false_positive_rate_pct": guard["false_positive_rate_pct"],
            },
            "situation_5": {
                "focus": "Production Quality",
                "key_finding": f"Grade A ({prod['overall_quality_score']}/100), {prod['slos_passing']}/{prod['slos_total']} SLOs passing, deployment APPROVED",
                "overall_quality_score": prod["overall_quality_score"],
                "overall_quality_grade": prod["overall_quality_grade"],
                "slo_compliance_pct": prod["slo_compliance_pct"],
                "deployment_recommendation": prod["deployment_recommendation"],
            },
        },
        "key_metrics_summary": {
            "baseline_consistency": f"{base['consistency_rate_pct']}%",
            "final_consistency": f"{final['consistency_rate_pct']}%",
            "baseline_reliability": f"{base['reliability_score']}/100",
            "final_reliability": f"{final['reliability_score']}/100",
            "guardrail_detection": f"{guard['detection_rate_pct']}%",
            "guardrail_block": f"{guard['block_rate_pct']}%",
            "slo_compliance": f"{prod['slo_compliance_pct']}% ({prod['slos_passing']}/{prod['slos_total']})",
            "final_production_grade": f"{prod['overall_quality_grade']} ({prod['overall_quality_score']}/100)",
            "deploy_recommendation": prod["deployment_recommendation"],
        },
    }

    path = OUT_DIR / "project_executive_dashboard.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)
    print(f"  Saved {path.name}")
    return dashboard


# 2. Markdown summary report
def generate_summary_report(m: dict, dashboard: dict) -> None:
    base  = m["baseline"]
    final = m["final_engineered"]
    guard = m["guardrails"]
    prod  = m["production_quality"]
    imp   = m["improvements"]
    prog  = m["situation_3_progression"]["experiments"]
    ev    = dashboard["evolution"]

    lines = [
        "# AI Quality Engineering Lab — Project Summary Report",
        "",
        f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "---",
        "",
        "## Final Verdict",
        "",
        f"| Attribute | Value |",
        f"|-----------|-------|",
        f"| Production Ready | {'YES ✅' if prod['production_ready'] else 'NO ❌'} |",
        f"| Deployment Recommendation | **{prod['deployment_recommendation']}** |",
        f"| Overall Quality Score | **{prod['overall_quality_score']} / 100** |",
        f"| Overall Quality Grade | **{prod['overall_quality_grade']}** |",
        f"| SLO Compliance | {prod['slos_passing']}/{prod['slos_total']} ({prod['slo_compliance_pct']:.0f}%) |",
        "",
        "---",
        "",
        "## Project Evolution",
        "",
        "The system progressed through five engineering phases:",
        "",
        "```",
        f"  Consistency Rate                 Reliability Score",
        f"",
        f"  {base['consistency_rate_pct']:.0f}%  (Situation 1 — Baseline)      "
        f"{base['reliability_score']}/100  CRITICAL",
        f"   ↓",
        f"  {prog[1]['consistency_rate_pct']:.0f}%  (Situation 3 — Structured)    "
        f"{prog[1]['reliability_score']}/100  {prog[1]['readiness']}",
        f"   ↓",
        f"  {prog[2]['consistency_rate_pct']:.0f}%  (Situation 3 — Disambiguation) "
        f"{prog[2]['reliability_score']}/100  {prog[2]['readiness']}",
        f"   ↓",
        f"  {final['consistency_rate_pct']:.0f}%  (Situation 3 — Full Pipeline)  "
        f"{final['reliability_score']}/100  {final['readiness']}",
        f"   ↓",
        f"  {final['consistency_rate_pct']:.0f}%  (Situation 4 — Guardrails)     "
        f"{final['reliability_score']}/100  PROTECTED",
        f"   ↓",
        f"  {final['consistency_rate_pct']:.0f}%  (Situation 5 — Production)     "
        f"{prod['overall_quality_score']}/100  {prod['deployment_recommendation']}",
        "```",
        "",
        "---",
        "",
        "## Situation-by-Situation Results",
        "",
        "### Situation 1 — Evaluation",
        "",
        f"- **Consistency Rate:** {base['consistency_rate_pct']}% (target ≥ 85%)",
        f"- **Reliability Score:** {base['reliability_score']}/100",
        f"- **Entropy:** {base['entropy_normalized']} ({base['entropy_level']})",
        f"- **Routing Flows:** {base['routing_flows']}",
        f"- **Verdict:** {base['readiness']}",
        "",
        "Situation 1 proved mathematically that the system was unreliable.",
        "A consistency rate of 36% means that fewer than 4 out of 10 identical inputs",
        "were classified the same way. Entropy of 0.8269 (close to maximum) indicates",
        "the classification distribution was nearly uniform — the system was effectively guessing.",
        "",
        "### Situation 2 — Root Cause Analysis",
        "",
        "Three root causes identified and ranked:",
        "",
        "| Root Cause | Severity | Score |",
        "|------------|----------|-------|",
        "| Prompt Ambiguity | CRITICAL | 95/100 |",
        "| Intent Taxonomy Overlap | HIGH | 67/100 |",
        "| Non-Deterministic Routing | HIGH | 70/100 |",
        "",
        "Key evidence: removing ambiguity from the input raised consistency from 36% to 100%,",
        "confirming prompt ambiguity as the primary causal factor.",
        "",
        "### Situation 3 — Reliability Engineering",
        "",
        "Six strategies applied in a layered pipeline:",
        "",
        "| Experiment | Strategies | Consistency | Score | Readiness |",
        "|------------|------------|:-----------:|:-----:|-----------|",
    ]

    for exp in prog:
        lines.append(
            f"| {exp['label']} | {exp.get('strategies_active', exp['label'])} | "
            f"{exp['consistency_rate_pct']:.0f}% | {exp['reliability_score']}/100 | {exp['readiness']} |"
        )

    lines += [
        "",
        f"**Delta:** Consistency +{imp['consistency_rate_delta_pp']:.0f}pp | "
        f"Reliability Score +{imp['reliability_score_delta_pts']} pts | "
        f"Entropy {imp['entropy_delta_bits']:.4f} bits",
        "",
        "### Situation 4 — Guardrails",
        "",
        f"- **Detection Rate:** {guard['detection_rate_pct']}%",
        f"- **Block Rate:** {guard['block_rate_pct']}%",
        f"- **False Positive Rate:** {guard['false_positive_rate_pct']}%",
        f"- **Total Classifications:** {guard['total_classifications']} "
        f"({guard['total_allowed']} allowed, {guard['total_blocked']} blocked)",
        "",
        "5 fault-injection experiments confirmed the guardrails prevent any degraded",
        "classification from passing through, with zero false positives on healthy traffic.",
        "",
        "### Situation 5 — Production Quality",
        "",
        f"- **Overall Quality Score:** {prod['overall_quality_score']}/100 (Grade {prod['overall_quality_grade']})",
        f"- **SLO Compliance:** {prod['slos_passing']}/{prod['slos_total']} ({prod['slo_compliance_pct']:.0f}%)",
        f"- **Health Indicators:** {prod['health_indicators_healthy']}/{prod['health_indicators_total']} HEALTHY",
        f"- **Active Alerts:** {prod['alerts_firing']}/{prod['alerts_total']}",
        f"- **Open Incidents:** {prod['open_incidents']}",
        f"- **Deploy Recommendation:** {prod['deployment_recommendation']}",
        "",
        "---",
        "",
        "## Key Metrics Summary",
        "",
        "| Metric | Baseline | Final | Delta |",
        "|--------|----------|-------|-------|",
        f"| Consistency Rate | {base['consistency_rate_pct']}% | {final['consistency_rate_pct']}% | "
        f"+{imp['consistency_rate_delta_pp']:.0f}pp |",
        f"| Reliability Score | {base['reliability_score']}/100 | {final['reliability_score']}/100 | "
        f"+{imp['reliability_score_delta_pts']} pts |",
        f"| Entropy (normalized) | {base['entropy_normalized']} ({base['entropy_level']}) | "
        f"{final['entropy_normalized']} ({final['entropy_level']}) | "
        f"{imp['entropy_delta_bits']:.4f} bits |",
        f"| Routing Flows | {base['routing_flows']} | {final['routing_flows']} | "
        f"{imp['routing_flows_delta']} |",
        f"| Confidence Std Dev | {base['confidence_std']} | {final['confidence_std']} | "
        f"{imp['confidence_std_delta']} |",
        f"| Guardrail Detection | — | {guard['detection_rate_pct']}% | — |",
        f"| SLO Compliance | — | {prod['slo_compliance_pct']:.0f}% | — |",
        f"| Production Grade | — | {prod['overall_quality_grade']} ({prod['overall_quality_score']}/100) | — |",
        "",
        "---",
        "",
        "*AI Quality Engineering Lab — Executive Dashboard*",
    ]

    path = OUT_DIR / "project_summary_report.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Saved {path.name}")


# 3. Project evolution chart
def plot_project_evolution(m: dict) -> None:
    base  = m["baseline"]
    guard = m["guardrails"]
    prod  = m["production_quality"]
    prog  = m["situation_3_progression"]["experiments"]

    situations = [
        "Situation 1\n(Baseline)",
        "Situation 3\nExp 02",
        "Situation 3\nExp 03",
        "Situation 3\nExp 04",
        "Situation 4\n(Guardrails)",
        "Situation 5\n(Production)",
    ]

    consistency = [
        base["consistency_rate_pct"],
        prog[1]["consistency_rate_pct"],
        prog[2]["consistency_rate_pct"],
        prog[3]["consistency_rate_pct"],
        prog[3]["consistency_rate_pct"],
        prog[3]["consistency_rate_pct"],
    ]

    reliability = [
        base["reliability_score"],
        prog[1]["reliability_score"],
        prog[2]["reliability_score"],
        prog[3]["reliability_score"],
        prog[3]["reliability_score"],
        prod["overall_quality_score"],
    ]

    x = np.arange(len(situations))
    point_colors = [RED, YELLOW, YELLOW, GREEN, TEAL, ACCENT]

    fig = plt.figure(figsize=(16, 9), facecolor=DARK_BG)
    gs = gridspec.GridSpec(2, 1, figure=fig, hspace=0.55)

    ax1 = fig.add_subplot(gs[0])
    ax1.set_facecolor(DARK_BG)
    ax1.tick_params(colors=TEXT_COL, labelsize=9)
    ax1.spines[:].set_color(GRID_COL)
    ax1.grid(axis="y", color=GRID_COL, linewidth=0.7, alpha=0.6)
    ax1.set_axisbelow(True)

    ax1.plot(x, consistency, color=ACCENT, linewidth=2.5, zorder=2)
    ax1.fill_between(x, consistency, alpha=0.15, color=ACCENT)
    for xi, yi, col in zip(x, consistency, point_colors):
        ax1.scatter(xi, yi, s=100, color=col, zorder=3)
        ax1.text(xi, yi + 3, f"{yi:.0f}%", ha="center", color=TEXT_COL,
                 fontsize=9, fontweight="bold")

    ax1.axhline(85, color=GREEN, linestyle="--", linewidth=1.2, alpha=0.7)
    ax1.text(5.05, 85.5, "Target ≥ 85%", color=GREEN, fontsize=8, va="bottom")
    ax1.set_ylim(0, 110)
    ax1.set_xticks(x)
    ax1.set_xticklabels(situations, color=TEXT_COL, fontsize=9)
    ax1.set_ylabel("Consistency Rate (%)", color=TEXT_COL, fontsize=10)
    ax1.set_title("Consistency Rate Progression", color=TEXT_COL, fontsize=12,
                  fontweight="bold", pad=8)
    ax1.yaxis.label.set_color(TEXT_COL)

    ax2 = fig.add_subplot(gs[1])
    ax2.set_facecolor(DARK_BG)
    ax2.tick_params(colors=TEXT_COL, labelsize=9)
    ax2.spines[:].set_color(GRID_COL)
    ax2.grid(axis="y", color=GRID_COL, linewidth=0.7, alpha=0.6)
    ax2.set_axisbelow(True)

    ax2.plot(x, reliability, color=PURPLE, linewidth=2.5, zorder=2)
    ax2.fill_between(x, reliability, alpha=0.15, color=PURPLE)
    for xi, yi, col in zip(x, reliability, point_colors):
        ax2.scatter(xi, yi, s=100, color=col, zorder=3)
        ax2.text(xi, yi + 2.5, f"{yi:.0f}", ha="center", color=TEXT_COL,
                 fontsize=9, fontweight="bold")

    ax2.axhline(80, color=GREEN, linestyle="--", linewidth=1.2, alpha=0.7)
    ax2.text(5.05, 80.5, "Target ≥ 80", color=GREEN, fontsize=8, va="bottom")
    ax2.set_ylim(0, 110)
    ax2.set_xticks(x)
    ax2.set_xticklabels(situations, color=TEXT_COL, fontsize=9)
    ax2.set_ylabel("Score / Quality (0-100)", color=TEXT_COL, fontsize=10)
    ax2.set_title("Reliability Score / Quality Score Progression", color=TEXT_COL,
                  fontsize=12, fontweight="bold", pad=8)
    ax2.yaxis.label.set_color(TEXT_COL)

    fig.suptitle(
        "AI Quality Engineering Lab — Project Evolution",
        color=TEXT_COL, fontsize=15, fontweight="bold", y=0.98,
    )

    plt.savefig(OUT_DIR / "project_evolution.png", dpi=150,
                bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print("  Saved project_evolution.png")


# 4. Final metrics scorecard
def plot_final_metrics_scorecard(m: dict) -> None:
    base  = m["baseline"]
    final = m["final_engineered"]
    guard = m["guardrails"]
    prod  = m["production_quality"]
    imp   = m["improvements"]

    fig = plt.figure(figsize=(16, 9), facecolor=DARK_BG)
    gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.6, wspace=0.4)

    def _kpi_panel(ax, title, before_val, after_val, unit, target_line=None,
                   before_label="Baseline", after_label="Final",
                   lower_is_better=False):
        ax.set_facecolor(DARK_BG)
        ax.tick_params(colors=TEXT_COL, labelsize=9)
        ax.spines[:].set_color(GRID_COL)
        ax.grid(axis="y", color=GRID_COL, linewidth=0.5, alpha=0.6)
        ax.set_axisbelow(True)

        bars = ax.bar(
            [before_label, after_label],
            [before_val, after_val],
            color=[RED, GREEN],
            width=0.5, edgecolor=DARK_BG,
        )
        for bar, val in zip(bars, [before_val, after_val]):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + (abs(after_val) * 0.03 + 0.5),
                    f"{val}{unit}", ha="center", color=TEXT_COL,
                    fontsize=11, fontweight="bold")

        if target_line is not None:
            ax.axhline(target_line, color=GREEN, linestyle="--",
                       linewidth=1.2, alpha=0.7)

        ax.set_title(title, color=TEXT_COL, fontsize=11, fontweight="bold", pad=6)
        ax.xaxis.label.set_color(TEXT_COL)

    # Panel 1: Consistency Rate
    ax = fig.add_subplot(gs[0, 0])
    _kpi_panel(ax, "Consistency Rate",
               base["consistency_rate_pct"], final["consistency_rate_pct"],
               "%", target_line=85)
    ax.set_ylim(0, 110)

    # Panel 2: Reliability Score
    ax = fig.add_subplot(gs[0, 1])
    _kpi_panel(ax, "Reliability Score",
               base["reliability_score"], final["reliability_score"],
               "/100", target_line=80)
    ax.set_ylim(0, 110)

    # Panel 3: Entropy (lower is better)
    ax = fig.add_subplot(gs[0, 2])
    ax.set_facecolor(DARK_BG)
    ax.tick_params(colors=TEXT_COL, labelsize=9)
    ax.spines[:].set_color(GRID_COL)
    ax.grid(axis="y", color=GRID_COL, linewidth=0.5, alpha=0.6)
    ax.set_axisbelow(True)
    bars = ax.bar(["Baseline", "Final"],
                  [base["entropy_normalized"], final["entropy_normalized"]],
                  color=[RED, GREEN], width=0.5, edgecolor=DARK_BG)
    for bar, val in zip(bars, [base["entropy_normalized"], final["entropy_normalized"]]):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.02,
                f"{val:.3f}", ha="center", color=TEXT_COL,
                fontsize=11, fontweight="bold")
    ax.axhline(0.35, color=GREEN, linestyle="--", linewidth=1.2, alpha=0.7)
    ax.set_ylim(0, 1.1)
    ax.set_title("Entropy (normalized, ↓ better)", color=TEXT_COL,
                 fontsize=11, fontweight="bold", pad=6)

    # Panel 4: Guardrail rates
    ax = fig.add_subplot(gs[1, 0])
    ax.set_facecolor(DARK_BG)
    ax.tick_params(colors=TEXT_COL, labelsize=9)
    ax.spines[:].set_color(GRID_COL)
    ax.grid(axis="y", color=GRID_COL, linewidth=0.5, alpha=0.6)
    ax.set_axisbelow(True)
    rates = [guard["detection_rate_pct"], guard["block_rate_pct"],
             100 - guard["false_positive_rate_pct"]]
    rate_labels = ["Detection\nRate", "Block\nRate", "True\nNegative"]
    bars = ax.bar(rate_labels, rates, color=[GREEN, GREEN, TEAL],
                  width=0.45, edgecolor=DARK_BG)
    for bar, val in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                f"{val:.0f}%", ha="center", color=TEXT_COL,
                fontsize=11, fontweight="bold")
    ax.set_ylim(0, 115)
    ax.set_title("Guardrail Effectiveness", color=TEXT_COL,
                 fontsize=11, fontweight="bold", pad=6)

    # Panel 5: SLO Compliance
    ax = fig.add_subplot(gs[1, 1])
    ax.set_facecolor(DARK_BG)
    ax.tick_params(colors=TEXT_COL, labelsize=9)
    ax.spines[:].set_color(GRID_COL)
    ax.grid(axis="y", color=GRID_COL, linewidth=0.5, alpha=0.6)
    ax.set_axisbelow(True)
    slo_vals  = [prod["slos_passing"], prod["slos_total"] - prod["slos_passing"]]
    slo_cols  = [GREEN, GRID_COL]
    slo_labels = [f"Passing\n({prod['slos_passing']})", f"Failing\n(0)"]
    wedges, _ = ax.pie(slo_vals, colors=slo_cols, startangle=90,
                       wedgeprops={"edgecolor": DARK_BG, "linewidth": 2})
    ax.set_title(f"SLO Compliance\n{prod['slo_compliance_pct']:.0f}% ({prod['slos_passing']}/{prod['slos_total']})",
                 color=TEXT_COL, fontsize=11, fontweight="bold", pad=6)
    patches = [mpatches.Patch(color=c, label=l) for c, l in zip(slo_cols, slo_labels)]
    ax.legend(handles=patches, loc="lower center", facecolor=DARK_BG,
              edgecolor=GRID_COL, labelcolor=TEXT_COL, fontsize=8,
              bbox_to_anchor=(0.5, -0.15))

    # Panel 6: Final Grade
    ax = fig.add_subplot(gs[1, 2])
    ax.set_facecolor(DARK_BG)
    ax.axis("off")
    ax.text(0.5, 0.75, prod["overall_quality_grade"],
            ha="center", va="center", fontsize=72, fontweight="bold",
            color=GREEN, transform=ax.transAxes)
    ax.text(0.5, 0.45, f"{prod['overall_quality_score']}/100",
            ha="center", va="center", fontsize=22, fontweight="bold",
            color=TEXT_COL, transform=ax.transAxes)
    ax.text(0.5, 0.25, prod["deployment_recommendation"],
            ha="center", va="center", fontsize=16, fontweight="bold",
            color=TEAL, transform=ax.transAxes)
    ax.set_title("Production Grade", color=TEXT_COL,
                 fontsize=11, fontweight="bold", pad=6)

    fig.suptitle(
        "AI Quality Engineering Lab — Final Metrics Scorecard",
        color=TEXT_COL, fontsize=15, fontweight="bold", y=1.01,
    )

    plt.savefig(OUT_DIR / "final_metrics_scorecard.png", dpi=150,
                bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print("  Saved final_metrics_scorecard.png")


# MAIN
def main() -> None:
    sep = "=" * 60
    print(f"\n{sep}")
    print("  AI QUALITY ENGINEERING LAB")
    print("  EXECUTIVE DASHBOARD GENERATOR")
    print(sep)
    print()

    print("  Loading project_metrics.json...")
    m = _load_metrics()
    print("  OK\n")

    print("  Step 1 — Generating executive dashboard JSON...")
    dashboard = generate_dashboard_json(m)

    print("\n  Step 2 — Generating project summary report...")
    generate_summary_report(m, dashboard)

    print("\n  Step 3 — Generating project evolution chart...")
    plot_project_evolution(m)

    print("\n  Step 4 — Generating final metrics scorecard...")
    plot_final_metrics_scorecard(m)

    print(f"\n  Outputs: {OUT_DIR}")
    print(f"\n{sep}\n")


if __name__ == "__main__":
    main()
