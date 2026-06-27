export type Intent =
  | "cancel_order"
  | "refund_request"
  | "billing_issue"
  | "shipping_issue"
  | "general_support";

export type ClassificationResult = {
  run_id: string;
  input: string;
  predicted_intent: Intent;
  confidence: number;
  intent_distribution: Record<string, number>;
  routing_flow: string;
  generated_response: string;
  execution_mode: string;
  timestamp: string;
};

export type DatasetMessage = {
  id: number;
  message: string;
  hint: string;
};

export type ClassificationMetrics = {
  totalRuns: number;
  uniqueIntents: number;
  consistencyRate: number;
  avgConfidence: number;
  stabilityLabel: "STABLE" | "MODERATE" | "UNSTABLE" | "HIGH INSTABILITY";
  intentDistribution: Record<string, number>;
};

export type DriftMetric = {
  level: "LOW" | "MEDIUM" | "HIGH";
  score: number;
};

export type TransitionPair = {
  from: Intent;
  to: Intent;
  count: number;
};

export type TransitionDrift = {
  transitions: TransitionPair[];
  total: number;
};
