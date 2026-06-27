# Evaluation Report — Situation 1
**AI Quality Engineering Lab** · Probabilistic Instability Analysis

> Generated: 2026-06-27 16:43:09 UTC
> Total Runs: 50 · Input: Fixed single message · Evaluation type: Repeated identical input

---

## Executive Summary

This evaluation was conducted to mathematically characterize the behavioral
instability of the AI intent classification system under deterministic input
conditions. The same customer message was submitted **50 times**, and the
system's output distribution, routing decisions, and confidence signals were
recorded and analyzed.

The results demonstrate **HIGH**
probabilistic dispersion with a consistency rate of
**34.0%** — meaning the system disagreed with its
own dominant prediction in **66.0% of runs**.
This level of variance renders the system unreliable for deterministic
production routing.

---

## Methodology

| Parameter | Value |
|-----------|-------|
| Total Runs | 50 |
| Input Fixture | Single fixed message (repeated 50×) |
| Evaluation Strategy | Repeated identical input |
| API Endpoint | `POST /api/v1/classify` |
| Metrics Computed | 6 (consistency, uniqueness, routing, confidence, entropy, drift) |

---

## Results

### 1. Consistency Rate

| Metric | Value |
|--------|-------|
| Dominant Intent | `billing_issue` |
| Dominant Count | 17 / 50 runs |
| **Consistency Rate** | **34.00%** |
| Instability Rate | 66.00% |

A consistency rate of **34.00%** means the system
converges on the same intent in fewer than 34%
of executions. Production-grade classifiers typically require ≥ 85%
consistency for deterministic routing.

---

### 2. Intent Distribution

50 runs produced **4 distinct intent
classifications** from a single input:

| Intent | Count | Share |
|--------|-------|-------|
| `billing_issue` | 17 | 34.0% |
| `general_support` | 14 | 28.0% |
| `cancel_order` | 11 | 22.0% |
| `refund_request` | 8 | 16.0% |

---

### 3. Routing Variance

**4 unique routing flows** were activated by the
same input:

| Routing Flow | Count | Percentage |
|-------------|-------|------------|
| `Billing Support Flow` | 17 | 34.0% |
| `General Support Queue` | 14 | 28.0% |
| `Order Cancellation Flow` | 11 | 22.0% |
| `Refund Flow` | 8 | 16.0% |

Every unique routing flow represents a different downstream execution path.
A customer experiencing the same billing issue would be routed to
4 different support queues across consecutive
interactions.

---

### 4. Confidence Analysis

| Metric | Value |
|--------|-------|
| Minimum | 0.0300 |
| Maximum | 0.9000 |
| Mean | 0.4534 |
| **Std Deviation** | **0.3061** |
| Range | 0.8700 |

Confidence standard deviation of **0.3061** and a peak-to-trough
range of **0.8700** demonstrate high signal volatility.
A reliable classifier should exhibit σ < 0.05 and range < 0.15 under
identical inputs.

---

### 5. Intent Entropy (Shannon)

| Metric | Value |
|--------|-------|
| Shannon Entropy H | 1.9470 bits |
| Maximum Possible H | 2.3219 bits |
| **Normalized Entropy** | **0.8385** |
| Interpretation | HIGH — significant probabilistic dispersion |

Normalized Shannon entropy of **0.8385** (scale 0–1)
measures the information-theoretic dispersion of predicted intents.
Values approaching 1.0 indicate near-uniform distribution — the classifier
is statistically indistinguishable from a random selector.

---

### 6. Response Drift

| Metric | Value |
|--------|-------|
| Mean Similarity to Baseline | 0.3617 |
| **Mean Drift** | **0.6383** |
| Min Similarity | 0.1508 |
| Max Similarity | 0.6721 |
| Interpretation | HIGH |

Response drift of **0.6383** was measured via sequential
character-level similarity against the first-run baseline response.
**high semantic variation** across identical
inputs creates inconsistent customer experiences and undermines trust in
downstream automation.

---

## Technical Conclusion

> The system demonstrated **severe probabilistic instability** under identical
> inputs.
>
> Multiple competing intent interpretations were observed across
> **4 distinct categories**, with
> **4 active routing destinations** activated from a
> single fixed message. Confidence oscillated between 0.0300 and
> 0.9000 (σ = 0.3061), and normalized Shannon entropy
> reached **0.8385** — indicating substantial
> information-theoretic dispersion.
>
> At a consistency rate of **34.0%**, the system
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
| `outputs/evaluation_results.json` | Raw results from all 50 runs |
| `outputs/evaluation_results.csv` | Tabular format for spreadsheet analysis |
| `outputs/metrics_summary.json` | Computed metrics (machine-readable) |
| `visualizations/confidence_variance.png` | Confidence signal over time |
| `visualizations/intent_distribution.png` | Intent frequency breakdown |
| `visualizations/routing_variance.png` | Routing flow distribution |
| `visualizations/consistency_rate.png` | Summary dashboard — key metrics |

---

*Generated automatically by the Situation 1 Evaluation Pipeline.*
*AI Quality Engineering Lab — Evaluation Engineering Division*
