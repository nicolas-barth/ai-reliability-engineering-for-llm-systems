from __future__ import annotations

import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure UTF-8 output on Windows (PowerShell defaults to cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import warnings
import time
import matplotlib
matplotlib.use("Agg")
warnings.filterwarnings("ignore", message=".*[Tt]ight.*[Ll]ayout.*", category=UserWarning)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

ROOT = Path(__file__).parent.parent
SIT1_OUTPUTS = ROOT.parent / "situation-01-evaluation" / "outputs"
OUTPUTS = ROOT / "outputs"
VIZ = ROOT / "visualizations"
REPORTS = ROOT / "reports"

sys.path.insert(0, str(ROOT))

from analyzers.intent_overlap_analyzer import IntentOverlapAnalyzer, INTENTS
from analyzers.prompt_ambiguity_analyzer import PromptAmbiguityAnalyzer
from analyzers.routing_collision_analyzer import RoutingCollisionAnalyzer
from analyzers.confidence_variance_analyzer import ConfidenceVarianceAnalyzer
from investigations.rca_engine import RCAEngine
from experiments.controlled_experiments import ControlledExperiments


BG     = "#0d1117"
SURF   = "#161b22"
BORDER = "#30363d"
GRID   = "#21262d"
ACCENT = "#58a6ff"
OK     = "#3fb950"
WARN   = "#d29922"
DANGER = "#f85149"
MUTED  = "#8b949e"
TEXT   = "#c9d1d9"

SEVERITY_COLORS = {
    "CRITICAL": DANGER,
    "HIGH":     WARN,
    "MEDIUM":   ACCENT,
    "LOW":      OK,
}

INTENT_COLORS = {
    "billing_issue":   "#58a6ff",
    "cancel_order":    "#f85149",
    "refund_request":  "#3fb950",
    "shipping_issue":  "#d29922",
    "general_support": "#a371f7",
}


def _style_axes(ax: plt.Axes) -> None:
    ax.set_facecolor(SURF)
    ax.tick_params(colors=TEXT, labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    ax.title.set_color(TEXT)


def _new_fig(figsize: tuple = (12, 7)) -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(BG)
    _style_axes(ax)
    return fig, ax


def _viz_overlap_matrix(overlap: dict) -> None:
    matrix = np.full((len(INTENTS), len(INTENTS)), np.nan)
    om = overlap["overlap_matrix"]
    for ai, ia in enumerate(INTENTS):
        for bi, ib in enumerate(INTENTS):
            if ai == bi:
                continue
            key = f"{ia}_vs_{ib}" if ai < bi else f"{ib}_vs_{ia}"
            if key in om:
                matrix[ai, bi] = om[key]["overlap_score"]

    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    masked = np.ma.masked_invalid(matrix)
    cmap = matplotlib.colormaps.get_cmap("YlOrRd")
    cmap.set_bad(color=SURF)

    im = ax.imshow(masked, cmap=cmap, vmin=0, vmax=60, aspect="auto")

    short = [i.replace("_", "\n") for i in INTENTS]
    ax.set_xticks(range(len(INTENTS)))
    ax.set_yticks(range(len(INTENTS)))
    ax.set_xticklabels(short, color=TEXT, fontsize=9)
    ax.set_yticklabels(short, color=TEXT, fontsize=9)

    for ai in range(len(INTENTS)):
        for bi in range(len(INTENTS)):
            val = matrix[ai, bi]
            if not np.isnan(val):
                color = "black" if val > 35 else TEXT
                ax.text(bi, ai, f"{val:.0f}%", ha="center", va="center",
                        color=color, fontsize=9, fontweight="bold")

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(colors=TEXT, labelsize=8)
    cbar.set_label("Overlap Score (%)", color=TEXT, fontsize=9)

    ax.set_title("Intent Overlap Matrix", color=TEXT, fontsize=13, fontweight="bold", pad=14)
    ax.set_xlabel("Intent B", color=TEXT, fontsize=10)
    ax.set_ylabel("Intent A", color=TEXT, fontsize=10)

    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
    ax.tick_params(colors=TEXT)

    primary = overlap["primary_overlap"]
    score = overlap["primary_overlap_score"]
    fig.text(0.5, 0.01,
             f"Primary overlap: {primary}  ({score:.1f}%)",
             ha="center", color=DANGER, fontsize=9)

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    out = VIZ / "intent_overlap_matrix.png"
    fig.savefig(out, dpi=150, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"    Saved: {out.name}")


def _viz_root_cause_ranking(rca: dict) -> None:
    ranking = rca["root_cause_ranking"]
    names = [r["name"] for r in reversed(ranking)]
    scores = [r["score"] for r in reversed(ranking)]
    severities = [r["severity"] for r in reversed(ranking)]
    colors = [SEVERITY_COLORS.get(s, ACCENT) for s in severities]

    fig, ax = _new_fig(figsize=(11, 6))

    bars = ax.barh(names, scores, color=colors, height=0.55, zorder=3)
    ax.set_xlim(0, 115)
    ax.set_xlabel("Root Cause Score (0–100)", color=TEXT, fontsize=10)
    ax.set_title("Root Cause Ranking", color=TEXT, fontsize=13, fontweight="bold")
    ax.grid(axis="x", color=GRID, linewidth=0.7, zorder=0)
    ax.tick_params(axis="y", labelsize=10)

    for bar, score, sev in zip(bars, scores, severities):
        ax.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height() / 2,
                f"{score:.0f}  [{sev}]",
                va="center", color=SEVERITY_COLORS.get(sev, TEXT), fontsize=9, fontweight="bold")

    legend_patches = [
        mpatches.Patch(color=DANGER, label="CRITICAL"),
        mpatches.Patch(color=WARN, label="HIGH"),
        mpatches.Patch(color=ACCENT, label="MEDIUM"),
        mpatches.Patch(color=OK, label="LOW"),
    ]
    ax.legend(handles=legend_patches, loc="lower right",
              facecolor=SURF, edgecolor=BORDER, labelcolor=TEXT, fontsize=8)

    fig.tight_layout()
    out = VIZ / "root_cause_ranking.png"
    fig.savefig(out, dpi=150, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"    Saved: {out.name}")


def _viz_ambiguity_contribution(ambiguity: dict) -> None:
    intent_kws = ambiguity["intent_keywords"]
    labels, sizes, colors_list = [], [], []

    for intent, kws in intent_kws.items():
        labels.append(f"{intent}\n({', '.join(kws[:3])})")
        sizes.append(len(kws))
        colors_list.append(INTENT_COLORS.get(intent, MUTED))

    if not sizes:
        return

    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        colors=colors_list,
        autopct="%1.0f%%",
        startangle=90,
        pctdistance=0.75,
        wedgeprops={"width": 0.5, "edgecolor": BG, "linewidth": 2},
    )
    for at in autotexts:
        at.set_color(BG)
        at.set_fontsize(11)
        at.set_fontweight("bold")

    ax.legend(
        wedges,
        labels,
        title="Triggered Intents",
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
        facecolor=SURF,
        edgecolor=BORDER,
        labelcolor=TEXT,
        fontsize=9,
        title_fontsize=9,
    )

    level = ambiguity["ambiguity_level"]
    level_color = SEVERITY_COLORS.get(level, TEXT)
    ax.set_title(
        f"Prompt Ambiguity Contribution\nAmbiguity Level: {level}",
        color=TEXT, fontsize=12, fontweight="bold",
    )
    ax.title.set_color(TEXT)

    fig.tight_layout()
    out = VIZ / "ambiguity_contribution.png"
    fig.savefig(out, dpi=150, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"    Saved: {out.name}")


def _viz_experiment_comparison(experiment_result: dict | None) -> None:
    if not experiment_result:
        print("    Skipped: no experiment data")
        return

    comparison = experiment_result.get("comparison", [])
    if not comparison:
        return

    labels = [c["label"] for c in comparison]
    consistencies = [c["consistency_rate_pct"] for c in comparison]
    unique_intents = [c["unique_intents"] for c in comparison]
    baseline_val = experiment_result.get("baseline_consistency", consistencies[0])

    x = np.arange(len(labels))
    width = 0.55

    fig, ax1 = _new_fig(figsize=(11, 6))
    ax2 = ax1.twinx()
    ax2.set_facecolor(SURF)

    bar_colors = []
    for c in comparison:
        delta = c["delta_vs_baseline"]
        if delta >= 15:
            bar_colors.append(OK)
        elif delta >= 0:
            bar_colors.append(ACCENT)
        else:
            bar_colors.append(DANGER)

    bars = ax1.bar(x, consistencies, width, color=bar_colors, alpha=0.85, zorder=3, label="Consistency %")
    ax2.plot(x, unique_intents, color=WARN, marker="o", linewidth=2,
             markersize=7, zorder=4, label="Unique Intents")

    ax1.axhline(y=baseline_val, color=MUTED, linestyle="--", linewidth=1.2,
                zorder=2, label=f"Baseline ({baseline_val:.0f}%)")

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, color=TEXT, fontsize=10)
    ax1.set_ylabel("Consistency Rate (%)", color=TEXT, fontsize=10)
    ax1.set_ylim(0, 115)
    ax1.set_title("Controlled Experiment Comparison", color=TEXT, fontsize=13, fontweight="bold")
    ax1.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)

    ax2.set_ylabel("Unique Intents", color=WARN, fontsize=10)
    ax2.tick_params(axis="y", colors=WARN, labelsize=9)
    ax2.set_ylim(0, 6)
    for spine in ax2.spines.values():
        spine.set_edgecolor(BORDER)

    for bar, val in zip(bars, consistencies):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                 f"{val:.0f}%", ha="center", color=TEXT, fontsize=9, fontweight="bold")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               loc="upper right", facecolor=SURF, edgecolor=BORDER,
               labelcolor=TEXT, fontsize=8)

    fig.tight_layout()
    out = VIZ / "experiment_comparison.png"
    fig.savefig(out, dpi=150, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"    Saved: {out.name}")


def _viz_confidence_distribution(confidence: dict) -> None:
    values = confidence.get("_raw_values", [])
    if not values:
        print("    Skipped: no raw confidence values in memory")
        return

    fig, ax = _new_fig(figsize=(11, 6))

    n_bins = 20
    counts, bin_edges, patches = ax.hist(
        values, bins=n_bins, range=(0, 1),
        color=ACCENT, alpha=0.7, edgecolor=BG, linewidth=0.5, zorder=3,
    )

    if confidence["multimodal_detected"]:
        cluster_palette = [DANGER, WARN, OK, ACCENT, "#a371f7"]
        for idx, cl in enumerate(confidence["confidence_clusters"]):
            color = cluster_palette[idx % len(cluster_palette)]
            ax.axvspan(cl["min"] - 0.005, cl["max"] + 0.005,
                       alpha=0.15, color=color, zorder=2,
                       label=cl.get("matched_profile") or f"Cluster {cl['cluster_id']}")

    mean_val = confidence["overall_stats"]["mean"]
    ax.axvline(x=mean_val, color=WARN, linewidth=1.5, linestyle="--", zorder=4,
               label=f"Mean = {mean_val:.3f}")

    ax.set_xlabel("Confidence Score", color=TEXT, fontsize=10)
    ax.set_ylabel("Frequency", color=TEXT, fontsize=10)
    ax.set_title(
        f"Confidence Score Distribution  (σ={confidence['overall_stats']['std']:.3f})",
        color=TEXT, fontsize=13, fontweight="bold",
    )
    ax.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)

    legend = ax.legend(facecolor=SURF, edgecolor=BORDER, labelcolor=TEXT, fontsize=8,
                       loc="upper left")

    interp = confidence["variance_interpretation"]
    fig.text(0.5, 0.01,
             f"Variance interpretation: {interp}  |  Clusters: {confidence['cluster_count']}  |  "
             f"Multimodal: {'YES' if confidence['multimodal_detected'] else 'NO'}",
             ha="center", color=SEVERITY_COLORS.get(interp, TEXT), fontsize=9)

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    out = VIZ / "confidence_distribution.png"
    fig.savefig(out, dpi=150, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"    Saved: {out.name}")


def _generate_report(
    overlap: dict,
    ambiguity: dict,
    routing: dict,
    confidence: dict,
    experiment_result: dict | None,
    rca: dict,
    timestamp: str,
) -> None:
    primary = rca["primary_root_cause"]
    secondary = rca.get("secondary_root_cause")
    root_causes = rca.get("root_causes", [])
    contributing_factors = rca.get("contributing_factors", [])
    symptoms = rca.get("observable_symptoms", [])

    lines: list[str] = []
    lines.append("# ROOT CAUSE ANALYSIS REPORT")
    lines.append("## Situation 2 — AI Quality Engineering Lab")
    lines.append("")
    lines.append(f"> Generated: {timestamp}")
    lines.append(f"> Primary Root Cause: **{primary['name']}** — Severity: **{primary['severity']}**")
    if secondary:
        lines.append(f"> Secondary Root Cause: **{secondary['name']}** — Severity: **{secondary['severity']}**")
    lines.append(f"> Overall Impact: **{rca['overall_impact']}**  |  Analysis Confidence: **{rca['confidence_level']}**")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Executive Summary")
    lines.append("")
    lines.append(rca["engineering_conclusion"])
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Evidence Base (Situation 1 Outputs)")
    lines.append("")
    lines.append("| Metric | Value | Threshold | Status |")
    lines.append("|--------|-------|-----------|--------|")
    lines.append(f"| Consistency Rate | 40.0% | >= 85% | FAILED |")
    lines.append(f"| Unique Intents | {len(confidence['per_intent_stats'])} | <= 2 | FAILED |")
    lines.append(f"| Routing Flows | {routing['unique_flows']} | 1 | FAILED |")
    lines.append(f"| Confidence Std Dev | {confidence['overall_stats']['std']:.3f} | < 0.05 | FAILED |")
    lines.append(f"| Confidence Range | {confidence['overall_stats']['min']}--{confidence['overall_stats']['max']} | -- | -- |")
    lines.append(f"| Confidence Clusters | {confidence['cluster_count']} | 1 | {'FAILED' if confidence['cluster_count'] > 1 else 'OK'} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Causal Chain")
    lines.append("")
    lines.append("```")
    for i, step in enumerate(rca.get("causal_chain", []), 1):
        prefix = "  " * (i - 1)
        arrow = "" if i == 1 else f"{'  ' * (i-2)}  └─► "
        lines.append(f"{arrow}{step}")
    lines.append("```")
    lines.append("")
    lines.append("> Root Causes generate the problem.")
    lines.append("> Contributing Factors amplify it.")
    lines.append("> Observable Symptoms are consequences — not causes.")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Root Cause Ranking")
    lines.append("")

    lines.append("### Root Causes")
    lines.append("")
    for i, rc in enumerate(root_causes, 1):
        rank_label = "Primary" if rc.get("rank") == "primary" else "Secondary"
        lines.append(f"#### #{i} — {rc['name']}  `[{rank_label} Root Cause]`")
        lines.append(f"**Severity:** {rc['severity']}  |  **Score:** {rc['score']}/100")
        lines.append("")
        lines.append(rc["description"])
        lines.append("")
        lines.append(f"**Evidence:** {rc['evidence']}")
        lines.append("")
        lines.append(f"**Situation 3 Fix:** {rc['situation_3_fix']}")
        lines.append("")

    lines.append("### Contributing Factors")
    lines.append("")
    for cf in contributing_factors:
        lines.append(f"#### {cf['name']}  `[Contributing Factor]`")
        lines.append(f"**Severity:** {cf['severity']}  |  **Score:** {cf['score']}/100")
        lines.append("")
        lines.append(cf["description"])
        lines.append("")
        lines.append(f"**Evidence:** {cf['evidence']}")
        lines.append("")
        lines.append(f"**Situation 3 Fix:** {cf['situation_3_fix']}")
        lines.append("")

    lines.append("### Observable Symptoms")
    lines.append("")
    lines.append("> These are measurable consequences of the root causes — not independent causes.")
    lines.append("")
    lines.append("| Symptom | Metric | Explanation |")
    lines.append("|---------|--------|-------------|")
    for sym in symptoms:
        lines.append(
            f"| {sym['name']} | {sym.get('metric', '--')} | {sym['explanation'][:80]}... |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Analyzer Findings")
    lines.append("")

    lines.append("### Intent Overlap Analysis")
    lines.append("")
    lines.append(f"Primary overlap: **{overlap['primary_overlap']}** (score: {overlap['primary_overlap_score']:.1f}%)")
    lines.append("")
    lines.append("| Pair | Overlap Score | Top-2 Co-occurrence | Pearson r |")
    lines.append("|------|--------------|--------------------|-----------| ")
    for pair in overlap["top_competing_pairs"]:
        lines.append(
            f"| {pair['intent_a']} vs {pair['intent_b']} "
            f"| {pair['overlap_score']:.1f}% "
            f"| {pair['top2_cooccurrence_pct']:.1f}% "
            f"| {pair['pearson_r']:.3f} |"
        )
    lines.append("")

    lines.append("### Prompt Ambiguity Analysis")
    lines.append("")
    lines.append(f"**Input:** `{ambiguity['message']}`")
    lines.append(f"**Ambiguity Level:** {ambiguity['ambiguity_level']}")
    lines.append(f"**Triggered Intents:** {', '.join(ambiguity['triggered_intents'])}")
    lines.append("")
    lines.append("| Keyword | Triggered Intent |")
    lines.append("|---------|-----------------|")
    for kw, intent in ambiguity["keyword_hits"].items():
        lines.append(f"| `{kw}` | {intent} |")
    lines.append("")

    lines.append("### Routing Collision Analysis")
    lines.append("")
    lines.append(f"**Unique routing flows:** {routing['unique_flows']}")
    lines.append(f"**Collision rate:** {routing['collision_rate_pct']:.1f}%")
    lines.append(f"**Routing instability score:** {routing['routing_instability_score']:.1f}/100")
    lines.append(f"**Routing transitions across 50 runs:** {routing['transition_count']}")
    lines.append("")
    lines.append("| Routing Flow | Count | % |")
    lines.append("|-------------|-------|---|")
    for flow, stats in routing["routing_distribution"].items():
        lines.append(f"| {flow} | {stats['count']} | {stats['pct']:.1f}% |")
    lines.append("")

    lines.append("### Confidence Variance Analysis")
    lines.append("")
    o = confidence["overall_stats"]
    lines.append(
        f"**Range:** {o['min']}--{o['max']}  |  **Mean:** {o['mean']}  |  "
        f"**Std Dev:** {o['std']}  |  **Interpretation:** {confidence['variance_interpretation']}"
    )
    lines.append("")
    lines.append(
        f"> Note: Confidence volatility is classified as an **Observable Symptom**, not a root cause. "
        f"It is a downstream consequence of intent competition caused by prompt ambiguity and taxonomy overlap."
    )
    lines.append("")
    if confidence["confidence_clusters"]:
        lines.append(f"**Clusters detected:** {confidence['cluster_count']}")
        lines.append("")
        lines.append("| Cluster | Count | Mean | Min | Max | Matched Profile |")
        lines.append("|---------|-------|------|-----|-----|-----------------|")
        for cl in confidence["confidence_clusters"]:
            lines.append(
                f"| {cl['cluster_id']} | {cl['count']} ({cl['pct']:.0f}%) "
                f"| {cl['mean']:.3f} | {cl['min']:.3f} | {cl['max']:.3f} "
                f"| {cl.get('matched_profile') or '--'} |"
            )
    lines.append("")
    lines.append("---")
    lines.append("")

    if experiment_result:
        lines.append("## Experiment Results")
        lines.append("")
        lines.append(
            f"Controlled experiment baseline: **{experiment_result['baseline_consistency']:.1f}%**"
            " *(15 controlled runs on ambiguous input — see Situation 1 for the 50-run live measurement)*"
        )
        lines.append("")
        lines.append(
            "> Experiments isolate the causal contribution of prompt ambiguity. "
            "If removing a semantic element dramatically increases consistency, "
            "that element is a primary causal factor."
        )
        lines.append("")
        lines.append("| Experiment | Input (truncated) | Consistency | Unique Intents | Delta vs Baseline | Validated |")
        lines.append("|-----------|-------------------|-------------|---------------|-------------------|----------|")
        for c in experiment_result["comparison"]:
            exp = next(
                (e for e in experiment_result["experiments"] if e["id"] == c["id"]), {}
            )
            inp = exp.get("input", "")[:40] + "..."
            validated = "YES" if c["hypothesis_validated"] else "NO"
            lines.append(
                f"| {c['id']} {c['label']} | `{inp}` "
                f"| {c['consistency_rate_pct']:.1f}% "
                f"| {c['unique_intents']} "
                f"| {c['delta_vs_baseline']:+.1f}% "
                f"| {validated} |"
            )
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Engineering Conclusion")
    lines.append("")
    lines.append(rca["engineering_conclusion"])
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Situation 3 Priorities")
    lines.append("")
    lines.append("The following interventions should be addressed in priority order:")
    lines.append("")
    for i, fix in enumerate(rca["situation_3_priorities"], 1):
        lines.append(f"{i}. {fix}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*AI Quality Engineering Lab — Root Cause Analysis Division*")

    report_path = REPORTS / "root_cause_analysis_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"    Saved: {report_path.name}")


def _wrap(text: str, width: int = 52, indent: str = "  ") -> None:
    words = text.split()
    line = indent
    for w in words:
        if len(line) + len(w) > width:
            print(line)
            line = indent + w + " "
        else:
            line += w + " "
    if line.strip():
        print(line)


def _print_summary(rca: dict, confidence: dict, routing: dict) -> None:
    primary = rca["primary_root_cause"]
    secondary = rca.get("secondary_root_cause")
    contributing = rca.get("contributing_factors", [])
    symptoms = rca.get("observable_symptoms", [])
    sep = "=" * 52

    print()
    print(sep)
    print("  ROOT CAUSE ANALYSIS REPORT")
    print(sep)
    print()
    print("  Primary Root Cause:")
    print(f"  {primary['name']}")
    print()
    if secondary:
        print("  Secondary Root Cause:")
        print(f"  {secondary['name']}")
        print()
    if contributing:
        print("  Contributing Factors:")
        for cf in contributing:
            print(f"  - {cf['name']}")
        print()
    if symptoms:
        print("  Observed Symptoms:")
        for sym in symptoms:
            print(f"  - {sym['name']}")
        print()
    print(f"  Impact:     {rca['overall_impact']}")
    print(f"  Confidence: {rca['confidence_level']}")
    print()
    print(sep)
    print()
    print("  Root Cause Ranking")
    print()
    root_causes = rca.get("root_causes", [])
    for i, rc in enumerate(root_causes, 1):
        rank = rc.get("rank", "").upper()
        rank_tag = f"[{rank}]" if rank else ""
        sev_pad = rc["severity"].ljust(8)
        print(f"  #{i}  {rc['name']}  {rank_tag}")
        print(f"       Severity: {sev_pad}  Score: {rc['score']:.0f}/100")
        print()
    if contributing:
        print("  Contributing Factors:")
        print()
        for cf in contributing:
            sev_pad = cf["severity"].ljust(8)
            print(f"  --  {cf['name']}  [Contributing Factor]")
            print(f"       Severity: {sev_pad}  Score: {cf['score']:.0f}/100")
            print()
    print("  Observable Symptoms (not causes):")
    print()
    for sym in symptoms:
        print(f"  --  {sym['name']}")
        if sym.get("metric"):
            print(f"       {sym['metric']}")
    print()
    print(sep)
    print()
    print("  Engineering Conclusion")
    print()
    _wrap(rca["engineering_conclusion"], width=54)
    print()
    print(sep)
    print()
    print("  Situation 3 Priorities:")
    for i, fix in enumerate(rca["situation_3_priorities"], 1):
        _wrap(f"{i}. {fix}", width=54, indent="  ")
    print()
    print(sep)


def main() -> None:
    _start = time.time()
    for d in (OUTPUTS, VIZ, REPORTS):
        d.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print("\n[STEP 1/5] Loading Situation 1 evidence...")
    results_path = SIT1_OUTPUTS / "evaluation_results.json"
    if not results_path.exists():
        print(f"  ERROR: {results_path} not found.")
        print("  Run situation-01-evaluation first to generate the evidence base.")
        sys.exit(1)

    with results_path.open(encoding="utf-8") as f:
        sit1_results = json.load(f)
    print(f"  Loaded {len(sit1_results)} runs from Situation 1.")

    print("\n[STEP 2/5] Running analyzers...")

    print("  >> Intent Overlap Analyzer")
    overlap = IntentOverlapAnalyzer(results_path).analyze()
    print(f"    Primary overlap: {overlap['primary_overlap']} ({overlap['primary_overlap_score']:.1f}%)")

    print("  >> Prompt Ambiguity Analyzer")
    datasets_path = ROOT / "datasets" / "experiment_inputs.json"
    with datasets_path.open(encoding="utf-8") as f:
        experiment_inputs = json.load(f)
    baseline_input = experiment_inputs[0]["input"]
    ambiguity = PromptAmbiguityAnalyzer().analyze(baseline_input)
    print(f"    Ambiguity level: {ambiguity['ambiguity_level']} ({ambiguity['intent_count']} intents)")

    print("  >> Routing Collision Analyzer")
    routing = RoutingCollisionAnalyzer(results_path).analyze()
    print(f"    Unique flows: {routing['unique_flows']}, Collision rate: {routing['collision_rate_pct']:.1f}%")

    print("  >> Confidence Variance Analyzer")
    confidence = ConfidenceVarianceAnalyzer(results_path).analyze()
    # Attach raw values for visualization
    confidence["_raw_values"] = [r["confidence"] for r in sit1_results]
    print(
        f"    σ={confidence['overall_stats']['std']:.3f}, "
        f"Clusters: {confidence['cluster_count']}, "
        f"Multimodal: {confidence['multimodal_detected']}"
    )

    print("\n[STEP 3/5] Running controlled experiments...")
    experiment_result: dict | None = None

    try:
        import httpx
        with httpx.Client(timeout=5.0) as probe:
            probe.get("http://localhost:8000/api/v1/health")
        print("  Backend reachable. Running 4 experiments × 15 runs each...")
        experiment_result = ControlledExperiments(runs_per_input=15).run(experiment_inputs)
        comparison = experiment_result.get("comparison", [])
        for c in comparison:
            validated = "✓" if c["hypothesis_validated"] else "✗"
            print(
                f"    {c['id']} {c['label']}: "
                f"{c['consistency_rate_pct']:.0f}% consistency  {validated}"
            )
    except Exception:
        print("  WARNING: Backend not reachable. Skipping experiments.")
        print("  Start unstable-ai-router/backend and rerun to include experiment data.")

    # Save intermediate outputs
    rca_results = {
        "timestamp": timestamp,
        "overlap": overlap,
        "ambiguity": ambiguity,
        "routing": routing,
        "confidence": {k: v for k, v in confidence.items() if k != "_raw_values"},
        "experiments": experiment_result,
    }
    (OUTPUTS / "rca_results.json").write_text(
        json.dumps(rca_results, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    rca = RCAEngine().compute(overlap, ambiguity, routing, confidence, experiment_result)
    (OUTPUTS / "rca_summary.json").write_text(
        json.dumps(
            {k: v for k, v in rca.items() if k != "root_cause_ranking"},
            indent=2, ensure_ascii=False
        ),
        encoding="utf-8"
    )
    (OUTPUTS / "rca_summary.json").write_text(
        json.dumps(rca, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )

    print("\n[STEP 4/5] Generating visualizations...")
    _viz_overlap_matrix(overlap)
    _viz_root_cause_ranking(rca)
    _viz_ambiguity_contribution(ambiguity)
    _viz_experiment_comparison(experiment_result)
    _viz_confidence_distribution(confidence)

    print("\n[STEP 5/5] Generating RCA report...")
    _generate_report(overlap, ambiguity, routing, confidence, experiment_result, rca, timestamp)

    _print_summary(rca, confidence, routing)

    _elapsed = time.time() - _start
    if _elapsed >= 60:
        _min = int(_elapsed // 60)
        _sec = _elapsed % 60
        _time_str = f"{_min} minute{'s' if _min != 1 else ''} {_sec:.1f} seconds"
    else:
        _time_str = f"{_elapsed:.1f} seconds"
    print()
    print("=" * 50)
    print("Situation 02 Completed")
    print(f"Execution Time: {_time_str}")
    print("=" * 50)


if __name__ == "__main__":
    main()
