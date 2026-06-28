# ROOT CAUSE ANALYSIS REPORT
## Situation 2 — AI Quality Engineering Lab

> Generated: 2026-06-27T18:31:47Z
> Primary Root Cause: **Intent Taxonomy Overlap** — Severity: **CRITICAL**
> Secondary Root Cause: **Prompt Ambiguity** — Severity: **HIGH**
> Overall Impact: **CRITICAL**  |  Analysis Confidence: **MEDIUM**

---

## Executive Summary

The primary driver of instability is prompt ambiguity. The input activates 3 competing intents simultaneously, providing no unambiguous signal for the classifier to resolve. Intent taxonomy overlap further amplifies instability by creating competing interpretations for the same user request — billing_issue, cancel_order, and refund_request share significant semantic space. Confidence volatility and routing variance are observable symptoms of these root causes — not independent causes themselves.

---

## Evidence Base (Situation 1 Outputs)

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Consistency Rate | 40.0% | >= 85% | FAILED |
| Unique Intents | 4 | <= 2 | FAILED |
| Routing Flows | 4 | 1 | FAILED |
| Confidence Std Dev | 0.306 | < 0.05 | FAILED |
| Confidence Range | 0.03--0.9 | -- | -- |
| Confidence Clusters | 4 | 1 | FAILED |

---

## Causal Chain

```
Prompt Ambiguity
  └─► Intent Taxonomy Overlap
    └─► Non-Deterministic Routing
      └─► Confidence Volatility / Routing Variance / Semantic Drift
```

> Root Causes generate the problem.
> Contributing Factors amplify it.
> Observable Symptoms are consequences — not causes.

---

## Root Cause Ranking

### Root Causes

#### #1 — Intent Taxonomy Overlap  `[Secondary Root Cause]`
**Severity:** CRITICAL  |  **Score:** 91.2/100

billing_issue, cancel_order, and refund_request share significant semantic space. When an ambiguous input is presented, the classifier cannot distinguish between them cleanly — producing competing interpretations and split probability mass.

**Evidence:** Primary competing pair: billing_issue ↔ cancel_order (overlap score 45.6%). Top-2 co-occurrence: 64.0% of runs. Pearson r=-0.151.

**Situation 3 Fix:** Redefine intent boundaries with mutually exclusive semantic criteria. Add explicit decision rules for overlapping domains.

#### #2 — Prompt Ambiguity  `[Primary Root Cause]`
**Severity:** HIGH  |  **Score:** 80.0/100

The input activates multiple distinct intents simultaneously. No disambiguation strategy is applied at the input layer — the LLM must resolve genuine semantic uncertainty at inference time. Controlled experiments proved this is the primary causal driver: removing the ambiguity produced near-perfect consistency.

**Evidence:** Ambiguity level: HIGH. 3 intents triggered simultaneously: billing_issue, cancel_order, refund_request. 

**Situation 3 Fix:** Implement semantic disambiguation at the input layer. Detect multi-intent inputs and resolve them before classification.

### Contributing Factors

#### Non-Deterministic Routing  `[Contributing Factor]`
**Severity:** HIGH  |  **Score:** 71.6/100

When multiple intents compete, no routing priority hierarchy exists to resolve the ambiguity. The routing outcome is determined by whichever intent wins the probabilistic competition — which varies per run.

**Evidence:** 4 routing flows activated from identical input. Collision rate: 66.0%. Routing changed 36 times across 50 runs.

**Situation 3 Fix:** Add routing priority rules and confidence threshold guards. Define explicit tiebreakers when multiple intents are viable.

### Observable Symptoms

> These are measurable consequences of the root causes — not independent causes.

| Symptom | Metric | Explanation |
|---------|--------|-------------|
| Confidence Score Volatility | σ=0.306, range 0.03–0.9, 4 confidence clusters | When two intents hold near-equal probability mass, confidence collapses. The obs... |
| Semantic Response Drift | mean drift 0.6425 (HIGH — from Situation 1) | Responses drift because the selected intent changes per run. The LLM generates c... |
| Routing Variance | 4 distinct flows from identical input | 4 distinct routing flows activated from identical input. Routing variance is dow... |
| Low Consistency Rate | 40.0% consistency rate (baseline — from Situation 1) | 40% consistency is the aggregate result of all competing causal factors. It meas... |

---

## Analyzer Findings

### Intent Overlap Analysis

Primary overlap: **billing_issue ↔ cancel_order** (score: 45.6%)

| Pair | Overlap Score | Top-2 Co-occurrence | Pearson r |
|------|--------------|--------------------|-----------| 
| billing_issue vs cancel_order | 45.6% | 64.0% | -0.151 |
| shipping_issue vs general_support | 19.2% | 32.0% | 0.947 |
| billing_issue vs refund_request | 6.2% | 4.0% | -0.784 |
| cancel_order vs refund_request | 4.2% | 0.0% | -0.361 |
| billing_issue vs general_support | 3.7% | 0.0% | -0.809 |

### Prompt Ambiguity Analysis

**Input:** `Fui cobrado errado e quero cancelar minha assinatura`
**Ambiguity Level:** HIGH
**Triggered Intents:** billing_issue, cancel_order, refund_request

| Keyword | Triggered Intent |
|---------|-----------------|
| `cobrado` | billing_issue |
| `errado` | billing_issue |
| `cancelar` | cancel_order |
| `assinatura` | cancel_order |

### Routing Collision Analysis

**Unique routing flows:** 4
**Collision rate:** 66.0%
**Routing instability score:** 71.6/100
**Routing transitions across 50 runs:** 36

| Routing Flow | Count | % |
|-------------|-------|---|
| Billing Support Flow | 17 | 34.0% |
| General Support Queue | 14 | 28.0% |
| Order Cancellation Flow | 11 | 22.0% |
| Refund Flow | 8 | 16.0% |

### Confidence Variance Analysis

**Range:** 0.03--0.9  |  **Mean:** 0.4534  |  **Std Dev:** 0.3061  |  **Interpretation:** CRITICAL

> Note: Confidence volatility is classified as an **Observable Symptom**, not a root cause. It is a downstream consequence of intent competition caused by prompt ambiguity and taxonomy overlap.

**Clusters detected:** 4

| Cluster | Count | Mean | Min | Max | Matched Profile |
|---------|-------|------|-----|-----|-----------------|
| 1 | 13 (26%) | 0.053 | 0.030 | 0.070 | Profile 1 — Critical Uncertainty |
| 2 | 10 (20%) | 0.286 | 0.250 | 0.340 | Profile 2 — Weak Interpretation |
| 3 | 10 (20%) | 0.537 | 0.510 | 0.560 | Profile 3 — Moderate Interpretation |
| 4 | 17 (34%) | 0.809 | 0.690 | 0.900 | Profile 5 — High Confidence |

---

## Engineering Conclusion

The primary driver of instability is prompt ambiguity. The input activates 3 competing intents simultaneously, providing no unambiguous signal for the classifier to resolve. Intent taxonomy overlap further amplifies instability by creating competing interpretations for the same user request — billing_issue, cancel_order, and refund_request share significant semantic space. Confidence volatility and routing variance are observable symptoms of these root causes — not independent causes themselves.

---

## Situation 3 Priorities

The following interventions should be addressed in priority order:

1. Redefine intent boundaries with mutually exclusive semantic criteria. Add explicit decision rules for overlapping domains.
2. Implement semantic disambiguation at the input layer. Detect multi-intent inputs and resolve them before classification.
3. Add routing priority rules and confidence threshold guards. Define explicit tiebreakers when multiple intents are viable.

---

*AI Quality Engineering Lab — Root Cause Analysis Division*