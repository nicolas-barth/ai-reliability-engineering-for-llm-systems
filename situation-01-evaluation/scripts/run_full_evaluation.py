from __future__ import annotations

import json
import sys
import textwrap
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Make sibling packages importable
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Ensure UTF-8 output on Windows (PowerShell defaults to cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import warnings
import time
import matplotlib
matplotlib.use("Agg")
warnings.filterwarnings("ignore", message=".*[Tt]ight.*[Ll]ayout.*", category=UserWarning)
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from evaluators.repeated_runs_evaluator import RepeatedRunsEvaluator
from metrics.metrics_engine import MetricsEngine

OUTPUTS_DIR = ROOT / "outputs"
REPORTS_DIR = ROOT / "reports"
VIZ_DIR = ROOT / "visualizations"
RUNS = 50

BG = "#0d1117"
SURFACE = "#161b22"
BORDER = "#30363d"
GRID = "#21262d"
ACCENT = "#58a6ff"
SUCCESS = "#3fb950"
WARNING = "#d29922"
DANGER = "#f85149"
MUTED = "#8b949e"
TEXT = "#c9d1d9"

INTENT_COLORS: dict[str, str] = {
    "cancel_order": "#f85149",
    "refund_request": "#ff7b72",
    "billing_issue": "#d29922",
    "shipping_issue": "#3fb950",
    "general_support": "#58a6ff",
}
BAR_PALETTE = [ACCENT, WARNING, DANGER, SUCCESS, MUTED]


def _style_axes(ax: plt.Axes) -> None:
    ax.set_facecolor(SURFACE)
    ax.tick_params(colors=MUTED, labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
    ax.grid(True, color=GRID, linewidth=0.5, alpha=0.8, zorder=0)


def _annotate(ax: plt.Axes, text: str, color: str) -> None:
    ax.annotate(
        text,
        xy=(0.98, 0.96), xycoords="axes fraction",
        ha="right", va="top", fontsize=9, fontstyle="italic", color=color,
        bbox=dict(boxstyle="round,pad=0.3", facecolor=BG, edgecolor=color, alpha=0.85),
        zorder=10,
    )


def plot_confidence_variance(metrics: dict[str, Any]) -> Path:
    conf = metrics["confidence"]
    values: list[float] = conf["values"]
    mean: float = conf["mean"]
    std: float = conf["std"]
    x = list(range(1, len(values) + 1))

    fig, ax = plt.subplots(figsize=(14, 5))
    fig.patch.set_facecolor(BG)
    _style_axes(ax)
    ax.grid(axis="both", color=GRID, linewidth=0.5, alpha=0.8)

    ax.fill_between(x, mean - std, mean + std, color=WARNING, alpha=0.08)
    ax.plot(x, values, color=ACCENT, linewidth=1.5, alpha=0.9, zorder=3)
    ax.scatter(x, values, color=ACCENT, s=22, alpha=0.75, zorder=4)
    ax.axhline(mean, color=SUCCESS, linewidth=1.5, linestyle="--", alpha=0.85,
               label=f"Mean: {mean:.4f}")
    ax.axhline(mean + std, color=WARNING, linewidth=1.0, linestyle=":", alpha=0.7,
               label=f"+1σ: {mean + std:.4f}")
    ax.axhline(mean - std, color=WARNING, linewidth=1.0, linestyle=":", alpha=0.7,
               label=f"−1σ: {mean - std:.4f}")

    ax.set_title("Confidence Variance Across Runs", color=TEXT, fontsize=14,
                 fontweight="bold", pad=14)
    ax.set_xlabel("Run Number", color=MUTED, fontsize=10)
    ax.set_ylabel("Confidence Score", color=MUTED, fontsize=10)
    ax.set_xlim(0.5, len(values) + 0.5)
    ax.set_ylim(0.0, 1.05)
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.2f"))

    legend = ax.legend(facecolor=SURFACE, edgecolor=BORDER,
                       labelcolor=TEXT, fontsize=9)

    _annotate(ax, f"σ = {std:.4f}  |  range = {conf['range']:.4f}", DANGER)

    fig.tight_layout(pad=2)
    out = VIZ_DIR / "confidence_variance.png"
    fig.savefig(out, dpi=150, facecolor=BG)
    plt.close(fig)
    print(f"  [VIZ] {out.name}")
    return out


def plot_intent_distribution(metrics: dict[str, Any]) -> Path:
    counts_map: dict[str, int] = metrics["unique_intents"]["intent_counts"]
    total = sum(counts_map.values())
    intents = list(counts_map.keys())
    counts = list(counts_map.values())
    colors = [INTENT_COLORS.get(k, ACCENT) for k in intents]

    fig, ax = plt.subplots(figsize=(11, 5))
    fig.patch.set_facecolor(BG)
    _style_axes(ax)
    ax.grid(axis="x", color=GRID, linewidth=0.5, alpha=0.8)

    bars = ax.barh(intents, counts, color=colors, alpha=0.85,
                   height=0.55, edgecolor=BG, zorder=3)

    for bar, cnt in zip(bars, counts):
        pct = cnt / total * 100
        ax.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{cnt}  ({pct:.1f}%)",
            va="center", color=TEXT, fontsize=9,
        )

    ax.set_title("Intent Distribution Across Runs", color=TEXT,
                 fontsize=14, fontweight="bold", pad=14)
    ax.set_xlabel("Occurrences", color=MUTED, fontsize=10)
    ax.set_xlim(0, max(counts) * 1.28)
    ax.tick_params(axis="y", labelcolor=TEXT)

    fig.tight_layout(pad=2)
    out = VIZ_DIR / "intent_distribution.png"
    fig.savefig(out, dpi=150, facecolor=BG)
    plt.close(fig)
    print(f"  [VIZ] {out.name}")
    return out


def plot_routing_variance(metrics: dict[str, Any]) -> Path:
    routing_dist: dict[str, dict] = metrics["routing"]["routing_distribution"]
    flows = list(routing_dist.keys())
    counts = [routing_dist[f]["count"] for f in flows]
    pcts = [routing_dist[f]["pct"] for f in flows]
    colors = BAR_PALETTE[: len(flows)]

    fig, ax = plt.subplots(figsize=(11, 5))
    fig.patch.set_facecolor(BG)
    _style_axes(ax)
    ax.grid(axis="y", color=GRID, linewidth=0.5, alpha=0.8)

    x = list(range(len(flows)))
    bars = ax.bar(x, counts, color=colors, alpha=0.85, width=0.55,
                  edgecolor=BG, zorder=3)

    for bar, cnt, pct in zip(bars, counts, pcts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.25,
            f"{cnt}\n({pct:.1f}%)",
            ha="center", va="bottom", color=TEXT, fontsize=9,
        )

    ax.set_title("Routing Flow Variance", color=TEXT, fontsize=14,
                 fontweight="bold", pad=14)
    ax.set_ylabel("Occurrences", color=MUTED, fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels([f.replace(" ", "\n") for f in flows],
                       color=TEXT, fontsize=8)
    ax.set_ylim(0, max(counts) * 1.30)

    unique = metrics["routing"]["unique_routing_flows"]
    color = DANGER if unique >= 3 else WARNING
    _annotate(ax, f"{unique} unique routing flows detected", color)

    fig.tight_layout(pad=2)
    out = VIZ_DIR / "routing_variance.png"
    fig.savefig(out, dpi=150, facecolor=BG)
    plt.close(fig)
    print(f"  [VIZ] {out.name}")
    return out


def plot_consistency_rate(metrics: dict[str, Any]) -> Path:
    c = metrics["consistency"]
    e = metrics["entropy"]
    conf = metrics["confidence"]
    d = metrics["drift"]

    panels = [
        (
            "Consistency\nRate",
            f"{c['consistency_rate_pct']:.1f}%",
            c["dominant_intent"].replace("_", " "),
            _rate_color(c["consistency_rate_pct"]),
        ),
        (
            "Normalized\nEntropy",
            f"{e['normalized_entropy']:.4f}",
            e["interpretation"].split("—")[0].strip(),
            _entropy_color(e["normalized_entropy"]),
        ),
        (
            "Confidence\nStd Dev",
            f"{conf['std']:.4f}",
            f"range  {conf['range']:.4f}",
            _std_color(conf["std"]),
        ),
        (
            "Response\nDrift",
            f"{d['mean_drift']:.4f}",
            d["drift_interpretation"],
            _drift_color(d["mean_drift"]),
        ),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(16, 5))
    fig.patch.set_facecolor(BG)

    for ax, (title, value, subtitle, color) in zip(axes, panels):
        ax.set_facecolor(SURFACE)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        ax.text(0.5, 0.83, title, ha="center", va="center",
                color=MUTED, fontsize=11, fontweight="bold")
        ax.text(0.5, 0.50, value, ha="center", va="center",
                color=color, fontsize=28, fontweight="bold")
        ax.text(0.5, 0.18, subtitle, ha="center", va="center",
                color=MUTED, fontsize=9)

        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_edgecolor(BORDER)
            spine.set_linewidth(1.5)

    fig.suptitle(
        "Evaluation Summary — Key Instability Metrics",
        color=TEXT, fontsize=14, fontweight="bold", y=1.02,
    )
    fig.tight_layout(pad=1.5)
    out = VIZ_DIR / "consistency_rate.png"
    fig.savefig(out, dpi=150, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  [VIZ] {out.name}")
    return out


def _rate_color(pct: float) -> str:
    return SUCCESS if pct >= 70 else (WARNING if pct >= 40 else DANGER)

def _entropy_color(normalized: float) -> str:
    return SUCCESS if normalized < 0.30 else (WARNING if normalized < 0.60 else DANGER)

def _std_color(std: float) -> str:
    return SUCCESS if std < 0.10 else (WARNING if std < 0.25 else DANGER)

def _drift_color(drift: float) -> str:
    return SUCCESS if drift < 0.15 else (WARNING if drift < 0.40 else DANGER)


def generate_report(metrics: dict[str, Any], timestamp: str) -> Path:
    c = metrics["consistency"]
    u = metrics["unique_intents"]
    r = metrics["routing"]
    conf = metrics["confidence"]
    e = metrics["entropy"]
    d = metrics["drift"]
    n = metrics["total_runs"]

    intent_rows = "\n".join(
        f"| `{intent}` | {count} | {count / n * 100:.1f}% |"
        for intent, count in u["intent_counts"].items()
    )
    routing_rows = "\n".join(
        f"| `{flow}` | {data['count']} | {data['pct']}% |"
        for flow, data in r["routing_distribution"].items()
    )

    report = f"""# Evaluation Report — Situation 1
**AI Quality Engineering Lab** · Probabilistic Instability Analysis

> Generated: {timestamp}
> Total Runs: {n} · Input: Fixed single message · Evaluation type: Repeated identical input

---

## Executive Summary

This evaluation was conducted to mathematically characterize the behavioral
instability of the AI intent classification system under deterministic input
conditions. The same customer message was submitted **{n} times**, and the
system's output distribution, routing decisions, and confidence signals were
recorded and analyzed.

The results demonstrate **{e['interpretation'].split('—')[0].strip()}**
probabilistic dispersion with a consistency rate of
**{c['consistency_rate_pct']:.1f}%** — meaning the system disagreed with its
own dominant prediction in **{100 - c['consistency_rate_pct']:.1f}% of runs**.
This level of variance renders the system unreliable for deterministic
production routing.

---

## Methodology

| Parameter | Value |
|-----------|-------|
| Total Runs | {n} |
| Input Fixture | Single fixed message (repeated {n}×) |
| Evaluation Strategy | Repeated identical input |
| API Endpoint | `POST /api/v1/classify` |
| Metrics Computed | 6 (consistency, uniqueness, routing, confidence, entropy, drift) |

---

## Results

### 1. Consistency Rate

| Metric | Value |
|--------|-------|
| Dominant Intent | `{c['dominant_intent']}` |
| Dominant Count | {c['dominant_count']} / {n} runs |
| **Consistency Rate** | **{c['consistency_rate_pct']:.2f}%** |
| Instability Rate | {100 - c['consistency_rate_pct']:.2f}% |

A consistency rate of **{c['consistency_rate_pct']:.2f}%** means the system
converges on the same intent in fewer than {c['consistency_rate_pct']:.0f}%
of executions. Production-grade classifiers typically require ≥ 85%
consistency for deterministic routing.

---

### 2. Intent Distribution

{n} runs produced **{u['unique_intent_count']} distinct intent
classifications** from a single input:

| Intent | Count | Share |
|--------|-------|-------|
{intent_rows}

---

### 3. Routing Variance

**{r['unique_routing_flows']} unique routing flows** were activated by the
same input:

| Routing Flow | Count | Percentage |
|-------------|-------|------------|
{routing_rows}

Every unique routing flow represents a different downstream execution path.
A customer experiencing the same billing issue would be routed to
{r['unique_routing_flows']} different support queues across consecutive
interactions.

---

### 4. Confidence Analysis

| Metric | Value |
|--------|-------|
| Minimum | {conf['min']:.4f} |
| Maximum | {conf['max']:.4f} |
| Mean | {conf['mean']:.4f} |
| **Std Deviation** | **{conf['std']:.4f}** |
| Range | {conf['range']:.4f} |

Confidence standard deviation of **{conf['std']:.4f}** and a peak-to-trough
range of **{conf['range']:.4f}** demonstrate high signal volatility.
A reliable classifier should exhibit σ < 0.05 and range < 0.15 under
identical inputs.

---

### 5. Intent Entropy (Shannon)

| Metric | Value |
|--------|-------|
| Shannon Entropy H | {e['shannon_entropy']:.4f} bits |
| Maximum Possible H | {e['max_possible_entropy']:.4f} bits |
| **Normalized Entropy** | **{e['normalized_entropy']:.4f}** |
| Interpretation | {e['interpretation']} |

Normalized Shannon entropy of **{e['normalized_entropy']:.4f}** (scale 0–1)
measures the information-theoretic dispersion of predicted intents.
Values approaching 1.0 indicate near-uniform distribution — the classifier
is statistically indistinguishable from a random selector.

---

### 6. Response Drift

| Metric | Value |
|--------|-------|
| Mean Similarity to Baseline | {d['mean_similarity_to_baseline']:.4f} |
| **Mean Drift** | **{d['mean_drift']:.4f}** |
| Min Similarity | {d['min_similarity']:.4f} |
| Max Similarity | {d['max_similarity']:.4f} |
| Interpretation | {d['drift_interpretation']} |

Response drift of **{d['mean_drift']:.4f}** was measured via sequential
character-level similarity against the first-run baseline response.
**{d['drift_interpretation'].lower()} semantic variation** across identical
inputs creates inconsistent customer experiences and undermines trust in
downstream automation.

---

## Technical Conclusion

> The system demonstrated **severe probabilistic instability** under identical
> inputs.
>
> Multiple competing intent interpretations were observed across
> **{u['unique_intent_count']} distinct categories**, with
> **{r['unique_routing_flows']} active routing destinations** activated from a
> single fixed message. Confidence oscillated between {conf['min']:.4f} and
> {conf['max']:.4f} (σ = {conf['std']:.4f}), and normalized Shannon entropy
> reached **{e['normalized_entropy']:.4f}** — indicating substantial
> information-theoretic dispersion.
>
> At a consistency rate of **{c['consistency_rate_pct']:.1f}%**, the system
> cannot be trusted to produce deterministic routing in a production
> environment. Any downstream process dependent on predicted intent —
> escalation logic, billing workflows, support triage — would be exposed to
> unacceptable stochastic variance.
>
> **The current system does not yet provide sufficient predictability for safe
> production usage.**

---

## Artifacts

| File | Description |
|------|-------------|
| `outputs/evaluation_results.json` | Raw results from all {n} runs |
| `outputs/evaluation_results.csv` | Tabular format for spreadsheet analysis |
| `outputs/metrics_summary.json` | Computed metrics (machine-readable) |
| `visualizations/confidence_variance.png` | Confidence signal over time |
| `visualizations/intent_distribution.png` | Intent frequency breakdown |
| `visualizations/routing_variance.png` | Routing flow distribution |
| `visualizations/consistency_rate.png` | Summary dashboard — key metrics |

---

*Generated automatically by the Situation 1 Evaluation Pipeline.*
*AI Quality Engineering Lab — Evaluation Engineering Division*
"""

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "evaluation_report.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  [RPT] {out.name}")
    return out


def _reliability_score(metrics: dict[str, Any]) -> int:
    c_pct   = metrics["consistency"]["consistency_rate_pct"]
    entropy = metrics["entropy"]["normalized_entropy"]
    drift   = metrics["drift"]["mean_drift"]
    std     = metrics["confidence"]["std"]

    c_score = min(1.0, c_pct  / 85.0) * 40
    e_score = max(0.0, 1.0 - entropy / 0.85) * 25
    d_score = max(0.0, 1.0 - drift   / 0.65) * 20
    s_score = max(0.0, 1.0 - std     / 0.25) * 15

    return max(0, min(100, round(c_score + e_score + d_score + s_score)))


def _readiness_label(score: int) -> str:
    if score >= 75:
        return "PRONTO"
    if score >= 55:
        return "PARCIALMENTE PRONTO"
    if score >= 35:
        return "ALTO RISCO"
    return "NÃO PRONTO"


def _instability_label(metrics: dict[str, Any]) -> str:
    c_pct   = metrics["consistency"]["consistency_rate_pct"]
    entropy = metrics["entropy"]["normalized_entropy"]
    if c_pct >= 85 and entropy < 0.30:
        return "ESTÁVEL"
    if c_pct >= 65 or entropy < 0.50:
        return "MODERADAMENTE INSTÁVEL"
    if c_pct >= 40 or entropy < 0.70:
        return "ALTAMENTE INSTÁVEL"
    return "SEVERAMENTE INSTÁVEL"


def _detect_behaviors(metrics: dict[str, Any]) -> list[tuple[bool, str]]:
    return [
        (metrics["unique_intents"]["unique_intent_count"] > 2,  "Interpretações semânticas concorrentes"),
        (metrics["routing"]["unique_routing_flows"] > 1,        "Inconsistência de roteamento"),
        (metrics["confidence"]["std"] > 0.20,                   "Oscilação de confiança"),
        (metrics["drift"]["mean_drift"] > 0.30,                 "Deriva de resposta"),
        (metrics["entropy"]["normalized_entropy"] > 0.50,       "Incerteza operacional"),
    ]


def _top_transitions(results: list[dict[str, Any]]) -> list[tuple[tuple[str, str], int]]:
    intents = [r["predicted_intent"] for r in results]
    pairs   = [(intents[i], intents[i + 1]) for i in range(len(intents) - 1)]
    return Counter(pairs).most_common(5)


def _risk_categories(
    results: list[dict[str, Any]], metrics: dict[str, Any]
) -> list[tuple[str, str]]:
    intent_counts = metrics["unique_intents"]["intent_counts"]
    n             = metrics["total_runs"]
    dominant      = metrics["consistency"]["dominant_intent"]
    consistency   = metrics["consistency"]["consistency_rate"]

    buckets: dict[str, list[float]] = {}
    for r in results:
        buckets.setdefault(r["predicted_intent"], []).append(r.get("confidence", 0.5))
    avg_conf = {k: sum(v) / len(v) for k, v in buckets.items()}

    _CATEGORIA = {
        "billing_issue":   "Roteamento — Cobrança",
        "cancel_order":    "Roteamento — Cancelamento",
        "refund_request":  "Classificação — Reembolso",
        "general_support": "Escalonamento — Suporte",
        "shipping_issue":  "Roteamento — Entrega",
    }

    def _level(intent: str) -> str:
        pct = intent_counts.get(intent, 0) / n
        ac  = avg_conf.get(intent, 0.5)
        if intent == dominant:
            score = (1 - ac) * 0.4 + (1 - consistency) * 0.6
        else:
            score = (1 - ac) * 0.4 + pct * 0.6
        if score >= 0.55: return "CRÍTICO"
        if score >= 0.35: return "ALTO"
        if score >= 0.18: return "MÉDIO"
        return "BAIXO"

    return [
        (_CATEGORIA.get(intent, intent), _level(intent))
        for intent in intent_counts
    ]


def _stability_timeline(results: list[dict[str, Any]]) -> list[tuple[str, str]]:
    windows = []
    for start in range(0, len(results), 10):
        chunk = results[start : start + 10]
        end   = start + len(chunk)
        label = f"Execuções {start + 1:>2}–{end:>2}"
        unique_in = len({r["predicted_intent"] for r in chunk})
        avg_c     = sum(r.get("confidence", 0.5) for r in chunk) / len(chunk)
        if unique_in >= 4 or avg_c < 0.30:
            level = "SEVERO"
        elif unique_in >= 3 or avg_c < 0.45:
            level = "ALTO"
        elif unique_in >= 2 or avg_c < 0.60:
            level = "MODERADO"
        else:
            level = "ESTÁVEL"
        windows.append((label, level))
    return windows


def _confidence_buckets(results: list[dict[str, Any]]) -> list[tuple[str, int]]:
    ranges = [
        ("0,00 – 0,20", 0.00, 0.20),
        ("0,20 – 0,40", 0.20, 0.40),
        ("0,40 – 0,60", 0.40, 0.60),
        ("0,60 – 0,80", 0.60, 0.80),
        ("0,80 – 1,00", 0.80, 1.01),
    ]
    return [
        (label, sum(1 for r in results if lo <= r.get("confidence", 0.0) < hi))
        for label, lo, hi in ranges
    ]


def _auto_conclusion(
    metrics: dict[str, Any],
    instability: str,
    readiness: str,
) -> str:
    c    = metrics["consistency"]
    u    = metrics["unique_intents"]
    ro   = metrics["routing"]
    conf = metrics["confidence"]
    e    = metrics["entropy"]

    _adj = {
        "ESTÁVEL":                 "baixa",
        "MODERADAMENTE INSTÁVEL":  "moderada",
        "ALTAMENTE INSTÁVEL":      "elevada",
        "SEVERAMENTE INSTÁVEL":    "severa",
    }
    adj        = _adj.get(instability, "significativa")
    dispersao  = "substancial" if e["normalized_entropy"] > 0.60 else "moderada"

    return (
        f"O sistema demonstrou instabilidade probabilística {adj} sob entradas "
        f"idênticas. Múltiplas interpretações concorrentes emergiram em "
        f"{u['unique_intent_count']} categorias distintas, com "
        f"{ro['unique_routing_flows']} destinos de roteamento ativados a partir de "
        f"uma entrada fixa. A confiança oscilou entre {conf['min']:.4f} e "
        f"{conf['max']:.4f} (σ = {conf['std']:.4f}), e a entropia de Shannon "
        f"normalizada atingiu {e['normalized_entropy']:.4f} — indicando "
        f"dispersão informacional {dispersao}. Com taxa de consistência de "
        f"{c['consistency_rate_pct']:.1f}%, o sistema é classificado como "
        f"{readiness} para implantação em produção."
    )


def _verdict_text(score: int, readiness: str) -> str:
    if score < 35:
        return (
            "O sistema de roteamento apresenta instabilidade severa e comportamento "
            "determinístico insuficiente para implantação segura em produção. "
            f"Classificado como {readiness}: intervenção de engenharia é obrigatória "
            "antes de qualquer promoção ao ambiente produtivo."
        )
    if score < 55:
        return (
            "O sistema apresenta instabilidade significativa e não atende aos requisitos "
            f"mínimos de determinismo para workflows críticos. Classificado como "
            f"{readiness}: mitigações técnicas são necessárias antes da promoção."
        )
    if score < 75:
        return (
            "O sistema demonstra instabilidade moderada e requer validação adicional. "
            f"Classificado como {readiness}: recomenda-se monitoramento contínuo e "
            "mecanismos de fallback antes da promoção ao ambiente produtivo."
        )
    return (
        "O sistema demonstrou comportamento predominantemente estável. "
        f"Classificado como {readiness}: pode ser promovido com monitoramento ativo "
        "e alertas configurados para desvios de confiança."
    )


def print_executive_summary(
    results: list[dict[str, Any]],
    metrics: dict[str, Any],
    input_text: str,
) -> None:
    consistency = metrics["consistency"]
    unique      = metrics["unique_intents"]
    routing     = metrics["routing"]
    conf        = metrics["confidence"]
    entropy     = metrics["entropy"]
    drift       = metrics["drift"]
    n           = metrics["total_runs"]

    score        = _reliability_score(metrics)
    readiness    = _readiness_label(score)
    instability  = _instability_label(metrics)
    behaviors    = _detect_behaviors(metrics)
    worst        = min(results, key=lambda x: x.get("confidence", 1.0))
    transitions  = _top_transitions(results)
    risks        = _risk_categories(results, metrics)
    timeline     = _stability_timeline(results)
    conf_buckets = _confidence_buckets(results)

    low_conf  = sum(1 for x in results if x.get("confidence", 1.0) < 0.40)
    high_conf = sum(1 for x in results if x.get("confidence", 0.0) >= 0.80)

    W   = 62
    SEP = "=" * W
    DIV = "  " + "─" * (W - 4)

    def sec(title: str) -> None:
        print()
        print(f"  {title}")
        print(DIV)

    _ENTROPIA_PT = {"LOW": "BAIXA", "MODERATE": "MODERADA", "HIGH": "ALTA", "CRITICAL": "CRÍTICA"}
    _DERIVA_PT   = {"MINIMAL": "MÍNIMA", "MODERATE": "MODERADA", "HIGH": "ALTA", "SEVERE": "SEVERA"}

    entropy_level = _ENTROPIA_PT.get(entropy["interpretation"].split("—")[0].strip(),
                                     entropy["interpretation"].split("—")[0].strip())
    drift_level   = _DERIVA_PT.get(drift["drift_interpretation"], drift["drift_interpretation"])

    def _ebadge(v: float, t1: float, t2: float, t3: float) -> str:
        if v < t1: return "[BAIXO]"
        if v < t2: return "[MÉDIO]"
        if v < t3: return "[ALTO]"
        return "[CRÍTICO]"

    badge_consistency = _ebadge(100 - consistency["consistency_rate_pct"], 15, 35, 60)
    badge_routing     = _ebadge(routing["unique_routing_flows"] - 1, 1, 2, 3)
    badge_entropy     = _ebadge(entropy["normalized_entropy"], 0.30, 0.60, 0.85)
    badge_drift       = _ebadge(drift["mean_drift"], 0.15, 0.40, 0.65)
    badge_readiness   = {
        "PRONTO":              "[BAIXO]",
        "PARCIALMENTE PRONTO": "[MÉDIO]",
        "ALTO RISCO":          "[ALTO]",
        "NÃO PRONTO":          "[CRÍTICO]",
    }.get(readiness, "[CRÍTICO]")

    print()
    print(SEP)
    print("  SUMÁRIO EXECUTIVO DE AVALIAÇÃO")
    print(SEP)

    print()
    print("  INPUT ANALISADO:")
    print(f'  "{input_text}"')
    print()
    print(f"  TOTAL DE EXECUÇÕES: {n}")

    sec("MÉTRICAS PRINCIPAIS")
    print()
    L = 28
    print(f"  {'Taxa de Consistência':<{L}}  {consistency['consistency_rate_pct']:.2f}%"
          f"{'':>12}{badge_consistency}")
    print(f"  {'Variância de Roteamento':<{L}}  {routing['unique_routing_flows']} fluxos únicos"
          f"{'':>7}{badge_routing}")
    print(f"  {'Entropia de Intenção':<{L}}  {entropy['normalized_entropy']:.4f}"
          f"  ({entropy_level}){'':>4}{badge_entropy}")
    print(f"  {'Deriva Semântica':<{L}}  {drift['mean_drift']:.4f}"
          f"  ({drift_level}){'':>4}{badge_drift}")
    print(f"  {'Desvio Padrão de Confiança':<{L}}  {conf['std']:.4f}")

    sec("DISTRIBUIÇÃO DE INTENÇÕES")
    print()
    intent_counts = unique["intent_counts"]
    total     = sum(intent_counts.values())
    max_count = max(intent_counts.values()) if intent_counts else 1
    for rank, (intent, count) in enumerate(intent_counts.items(), 1):
        pct     = count / total * 100
        bar_len = round(count / max_count * 20)
        bar     = "█" * bar_len
        print(f"  #{rank:<3}  {intent:<22}  {count:>3} exec.  {pct:>5.1f}%  {bar}")

    sec("ANÁLISE DE CONFIANÇA")
    print()
    print(f"  {'Confiança Mínima':<{L}}  {conf['min']:.4f}")
    print(f"  {'Confiança Máxima':<{L}}  {conf['max']:.4f}")
    print(f"  {'Confiança Média':<{L}}  {conf['mean']:.4f}")
    print(f"  {'Desvio Padrão':<{L}}  {conf['std']:.4f}")
    print()
    print(f"  {'Execuções de Baixa Confiança':<{L}}  {low_conf:<4}  (limite < 0,40)")
    print(f"  {'Execuções de Alta Confiança':<{L}}  {high_conf:<4}  (limite >= 0,80)")

    sec("DISTRIBUIÇÃO DE CONFIANÇA POR FAIXA")
    print()
    for label, count in conf_buckets:
        bar_len = round(count / n * 20) if n else 0
        bar     = "█" * bar_len
        print(f"  {label}   →   {count:>3} exec.   {bar}")

    sec("ANÁLISE DE INSTABILIDADE")
    print()
    print("  Comportamentos Detectados:")
    print()
    for active, label in behaviors:
        marker = "[+]" if active else "[ ]"
        print(f"  {marker} {label}")

    sec("AVALIAÇÃO DE RISCO OPERACIONAL")
    print()
    for cat, level in risks:
        print(f"  {cat:<38}  {level}")

    sec("LINHA DO TEMPO DE INSTABILIDADE")
    print()
    for label, level in timeline:
        print(f"  {label}   →   {level}")

    sec("EXEMPLO DE PIOR FALHA")
    print()
    run_num    = worst.get("run_number", "?")
    intent_w   = worst.get("predicted_intent", "N/A")
    conf_w     = worst.get("confidence", 0.0)
    response_w = worst.get("generated_response") or "N/A"
    if len(response_w) > 72:
        response_w = response_w[:69] + "..."
    print(f"  Execução     #{run_num}")
    print(f"  Intenção     {intent_w}")
    print(f"  Confiança    {conf_w:.4f}")
    print(f'  Resposta     "{response_w}"')

    sec("TRANSIÇÕES MAIS FREQUENTES")
    print()
    if transitions:
        for (a, b), count in transitions:
            label = f"{a}  →  {b}"
            print(f"  {label:<48}  {count}x")
    else:
        print("  Dados de transição não disponíveis.")

    sec("AVALIAÇÃO DE CONFIABILIDADE DO SISTEMA")
    print()
    print(f"  {'Score de Confiabilidade':<{L}}  {score} / 100")
    print(f"  {'Prontidão para Produção':<{L}}  {readiness}   {badge_readiness}")
    print(f"  {'Nível de Instabilidade':<{L}}  {instability}")

    sec("CONCLUSÃO TÉCNICA")
    print()
    for line in textwrap.wrap(_auto_conclusion(metrics, instability, readiness), width=56):
        print(f"  {line}")

    sec("VEREDICTO FINAL")
    print()
    for line in textwrap.wrap(_verdict_text(score, readiness), width=56):
        print(f"  {line}")

    sec("ARTEFATOS")
    print()
    print(f"  Saídas       →  {OUTPUTS_DIR.name}/")
    print(f"  Gráficos     →  {VIZ_DIR.name}/")
    print(f"  Relatório    →  {REPORTS_DIR.name}/evaluation_report.md")
    print()
    print(SEP)
    print()


def main() -> None:
    _start = time.time()
    print("\n" + "=" * 60)
    print("  SITUATION 1 — FULL EVALUATION PIPELINE")
    print("=" * 60)

    dataset_path = ROOT / "datasets" / "main_input.json"
    try:
        with open(dataset_path, encoding="utf-8") as f:
            input_text = json.load(f)[0]
    except Exception:
        input_text = "N/A"

    print("\n[STEP 1/4] Executing repeated runs...")
    evaluator = RepeatedRunsEvaluator(runs=RUNS)
    results = evaluator.run()

    if not results:
        print(
            "\nERROR: No results collected.\n"
            "Ensure the backend is running:  uvicorn main:app --reload --port 8000\n"
            "(cd unstable-ai-router/backend first)",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\n[STEP 2/4] Computing instability metrics...")
    engine = MetricsEngine(results)
    metrics = engine.compute_all()

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    metrics_path = OUTPUTS_DIR / "metrics_summary.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"  [JSON] {metrics_path.name}")

    c, e, conf = metrics["consistency"], metrics["entropy"], metrics["confidence"]
    print(f"  consistency_rate : {c['consistency_rate_pct']:.2f}%")
    print(f"  unique_intents   : {metrics['unique_intents']['unique_intent_count']}")
    print(f"  routing_flows    : {metrics['routing']['unique_routing_flows']}")
    print(f"  entropy          : {e['normalized_entropy']:.4f}  ({e['interpretation'].split('—')[0].strip()})")
    print(f"  confidence_std   : {conf['std']:.4f}")
    print(f"  drift            : {metrics['drift']['mean_drift']:.4f}  ({metrics['drift']['drift_interpretation']})")

    print("\n[STEP 3/4] Generating visualizations...")
    VIZ_DIR.mkdir(parents=True, exist_ok=True)
    plot_confidence_variance(metrics)
    plot_intent_distribution(metrics)
    plot_routing_variance(metrics)
    plot_consistency_rate(metrics)

    print("\n[STEP 4/4] Generating evaluation report...")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    generate_report(metrics, ts)

    print_executive_summary(results, metrics, input_text)

    _elapsed = time.time() - _start
    if _elapsed >= 60:
        _min = int(_elapsed // 60)
        _sec = _elapsed % 60
        _time_str = f"{_min} minute{'s' if _min != 1 else ''} {_sec:.1f} seconds"
    else:
        _time_str = f"{_elapsed:.1f} seconds"
    print()
    print("=" * 50)
    print("Situation 01 Completed")
    print(f"Execution Time: {_time_str}")
    print("=" * 50)


if __name__ == "__main__":
    main()
