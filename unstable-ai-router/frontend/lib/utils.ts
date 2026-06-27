import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { ClassificationResult, ClassificationMetrics, Intent, DriftMetric, TransitionDrift } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function computeMetrics(history: ClassificationResult[]): ClassificationMetrics {
  if (history.length === 0) {
    return {
      totalRuns: 0,
      uniqueIntents: 0,
      consistencyRate: 0,
      avgConfidence: 0,
      stabilityLabel: "STABLE",
      intentDistribution: {},
    };
  }

  const distribution: Record<string, number> = {};
  for (const run of history) {
    distribution[run.predicted_intent] = (distribution[run.predicted_intent] ?? 0) + 1;
  }

  const uniqueIntents = Object.keys(distribution).length;
  const maxCount = Math.max(...Object.values(distribution));
  const consistencyRate = Math.round((maxCount / history.length) * 100);

  const avgConfidence = Math.round(
    (history.reduce((s, r) => s + r.confidence, 0) / history.length) * 100,
  );

  let stabilityLabel: ClassificationMetrics["stabilityLabel"];
  if (history.length < 2) {
    stabilityLabel = "STABLE";
  } else if (consistencyRate >= 90) {
    stabilityLabel = "STABLE";
  } else if (consistencyRate >= 70) {
    stabilityLabel = "MODERATE";
  } else if (consistencyRate >= 50) {
    stabilityLabel = "UNSTABLE";
  } else {
    stabilityLabel = "HIGH INSTABILITY";
  }

  return {
    totalRuns: history.length,
    uniqueIntents,
    consistencyRate,
    avgConfidence,
    stabilityLabel,
    intentDistribution: distribution,
  };
}

export function computeDrift(history: ClassificationResult[]): DriftMetric {
  if (history.length < 3) return { level: "LOW", score: 0 };

  const window = history.slice(-6);

  const uniqueIntents = new Set(window.map((r) => r.predicted_intent)).size;
  const intentVariance = (uniqueIntents - 1) / Math.max(window.length - 1, 1);

  const avgConf = window.reduce((s, r) => s + r.confidence, 0) / window.length;
  const confStd = Math.sqrt(
    window.reduce((s, r) => s + Math.pow(r.confidence - avgConf, 2), 0) / window.length,
  );

  const score = Math.min(1, intentVariance * 0.65 + confStd * 2.5 * 0.35);

  const level = score > 0.5 ? "HIGH" : score > 0.22 ? "MEDIUM" : "LOW";
  return { level, score };
}

export function computeTransitionDrift(history: ClassificationResult[]): TransitionDrift {
  if (history.length < 2) return { transitions: [], total: 0 };

  const counts: Record<string, number> = {};
  for (let i = 1; i < history.length; i++) {
    const from = history[i - 1].predicted_intent;
    const to = history[i].predicted_intent;
    if (from !== to) {
      const key = `${from}|||${to}`;
      counts[key] = (counts[key] ?? 0) + 1;
    }
  }

  const total = Object.values(counts).reduce((s, v) => s + v, 0);
  const transitions = Object.entries(counts)
    .map(([key, count]) => {
      const [from, to] = key.split("|||");
      return { from: from as Intent, to: to as Intent, count };
    })
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);

  return { transitions, total };
}

export const INTENT_CONFIG: Record<
  Intent,
  { color: string; bg: string; dot: string; bar: string; glow: string }
> = {
  cancel_order:    { color: "text-amber-400",   bg: "bg-amber-400/10",   dot: "bg-amber-400",   bar: "bg-amber-400",   glow: "rgba(251,191,36,0.15)" },
  refund_request:  { color: "text-blue-400",    bg: "bg-blue-400/10",    dot: "bg-blue-400",    bar: "bg-blue-400",    glow: "rgba(96,165,250,0.15)" },
  billing_issue:   { color: "text-red-400",     bg: "bg-red-400/10",     dot: "bg-red-400",     bar: "bg-red-400",     glow: "rgba(248,113,113,0.15)" },
  shipping_issue:  { color: "text-emerald-400", bg: "bg-emerald-400/10", dot: "bg-emerald-400", bar: "bg-emerald-400", glow: "rgba(52,211,153,0.15)" },
  general_support: { color: "text-purple-400",  bg: "bg-purple-400/10",  dot: "bg-purple-400",  bar: "bg-purple-400",  glow: "rgba(192,132,252,0.15)" },
};

export const STABILITY_CONFIG = {
  STABLE:            { color: "text-emerald-400", bg: "bg-emerald-400/10", border: "border-emerald-400/20", dot: "bg-emerald-400", glow: "rgba(52,211,153,0.12)" },
  MODERATE:          { color: "text-amber-400",   bg: "bg-amber-400/10",   border: "border-amber-400/20",   dot: "bg-amber-400",   glow: "rgba(251,191,36,0.12)" },
  UNSTABLE:          { color: "text-orange-400",  bg: "bg-orange-400/10",  border: "border-orange-400/20",  dot: "bg-orange-400",  glow: "rgba(251,146,60,0.18)" },
  "HIGH INSTABILITY":{ color: "text-red-400",     bg: "bg-red-400/10",     border: "border-red-400/20",     dot: "bg-red-400",     glow: "rgba(248,113,113,0.22)" },
} as const;

export const DRIFT_CONFIG = {
  LOW:    { color: "text-emerald-400", bg: "bg-emerald-400/10", dot: "bg-emerald-400", label: "LOW" },
  MEDIUM: { color: "text-amber-400",   bg: "bg-amber-400/10",   dot: "bg-amber-400",   label: "MEDIUM" },
  HIGH:   { color: "text-red-400",     bg: "bg-red-400/10",     dot: "bg-red-400",     label: "HIGH" },
} as const;

export const STATUS_MESSAGES: Record<ClassificationMetrics["stabilityLabel"], { title: string; detail: string }> = {
  STABLE:            { title: "CLASSIFICATION STABLE",              detail: "Model routing is consistent across recent runs." },
  MODERATE:          { title: "ROUTING VARIANCE DETECTED",          detail: "Classification is showing signs of non-determinism." },
  UNSTABLE:          { title: "HIGH ROUTING INSTABILITY",           detail: "Same input is being routed to different flows repeatedly." },
  "HIGH INSTABILITY":{ title: "SEVERE ROUTING FAILURE DETECTED",    detail: "Model cannot reliably determine customer intent — routing decisions are unsafe." },
};

export function formatTimestamp(iso: string): string {
  return (
    new Date(iso).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
      timeZone: "UTC",
    }) + " UTC"
  );
}

export function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.7) return "text-emerald-400";
  if (confidence >= 0.5) return "text-amber-400";
  return "text-red-400";
}

export function getConfidenceBarColor(confidence: number): string {
  if (confidence >= 0.7) return "bg-emerald-500";
  if (confidence >= 0.5) return "bg-amber-500";
  return "bg-red-500";
}

export function truncateResponse(text: string, maxLen = 60): string {
  if (!text) return "—";
  return text.length > maxLen ? text.slice(0, maxLen) + "…" : text;
}
