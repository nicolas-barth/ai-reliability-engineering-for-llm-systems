"use client";

import { motion } from "framer-motion";
import { Activity, GitBranch, TrendingDown, BarChart2, Gauge, ArrowRight } from "lucide-react";
import { ClassificationMetrics, Intent, DriftMetric, TransitionDrift } from "@/types";
import { INTENT_CONFIG, STABILITY_CONFIG, DRIFT_CONFIG, cn } from "@/lib/utils";

interface MetricTileProps {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  suffix?: string;
  valueColor?: string;
}

function MetricTile({ label, value, icon: Icon, suffix, valueColor }: MetricTileProps) {
  return (
    <div className="bg-[#111113] border border-[#27272A] rounded-lg p-4 space-y-2">
      <div className="flex items-center gap-1.5 text-[10px] text-[#71717A] uppercase tracking-widest font-semibold">
        <Icon className="w-3 h-3" />
        {label}
      </div>
      <div className={cn("text-2xl font-bold font-mono leading-none", valueColor ?? "text-[#F4F4F5]")}>
        {value}
        {suffix && <span className="text-sm text-[#71717A] ml-1 font-normal">{suffix}</span>}
      </div>
    </div>
  );
}

interface MetricsPanelProps {
  metrics: ClassificationMetrics;
  drift: DriftMetric;
  transitionDrift: TransitionDrift;
}

export function MetricsPanel({ metrics, drift, transitionDrift }: MetricsPanelProps) {
  const stability = STABILITY_CONFIG[metrics.stabilityLabel];
  const driftCfg = DRIFT_CONFIG[drift.level];

  const avgConfColor =
    metrics.avgConfidence >= 70 ? "text-emerald-400"
    : metrics.avgConfidence >= 50 ? "text-amber-400"
    : "text-red-400";

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="w-1 h-4 bg-indigo-500 rounded-full" />
        <span className="text-xs font-semibold text-[#A1A1AA] uppercase tracking-widest">
          Metrics
        </span>
      </div>

      {metrics.totalRuns >= 2 && (
        <div className="grid grid-cols-2 gap-3">
          <motion.div
            key={metrics.stabilityLabel}
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className={cn("flex items-center gap-2.5 px-3 py-2.5 rounded-lg border", stability.bg, stability.border)}
            style={{ boxShadow: `0 0 16px ${stability.glow}` }}
          >
            <motion.div
              className={cn("w-2 h-2 rounded-full flex-shrink-0", stability.dot)}
              animate={metrics.stabilityLabel !== "STABLE" ? { opacity: [1, 0.3, 1] } : {}}
              transition={{ duration: 1.2, repeat: Infinity }}
            />
            <div>
              <div className={cn("text-[10px] font-mono font-bold tracking-wide", stability.color)}>
                {metrics.stabilityLabel}
              </div>
              <div className="text-[10px] text-[#52525B]">routing</div>
            </div>
          </motion.div>

          <motion.div
            key={drift.level}
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className={cn("flex items-center gap-2.5 px-3 py-2.5 rounded-lg border", driftCfg.bg, "border-transparent")}
          >
            <Gauge className={cn("w-3.5 h-3.5 flex-shrink-0", driftCfg.color)} />
            <div>
              <div className={cn("text-[10px] font-mono font-bold tracking-wide", driftCfg.color)}>
                {drift.level} DRIFT
              </div>
              <div className="text-[10px] text-[#52525B]">model decision</div>
            </div>
          </motion.div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <MetricTile label="Total Runs" value={metrics.totalRuns || "—"} icon={Activity} />
        <MetricTile
          label="Unique Intents"
          value={metrics.totalRuns > 0 ? metrics.uniqueIntents : "—"}
          icon={GitBranch}
          valueColor={metrics.uniqueIntents > 2 ? "text-orange-400" : metrics.uniqueIntents > 1 ? "text-amber-400" : "text-[#F4F4F5]"}
        />
        <MetricTile
          label="Consistency Rate"
          value={metrics.totalRuns > 0 ? metrics.consistencyRate : "—"}
          suffix={metrics.totalRuns > 0 ? "%" : undefined}
          icon={TrendingDown}
          valueColor={
            metrics.totalRuns === 0 ? "text-[#F4F4F5]"
            : metrics.consistencyRate >= 80 ? "text-emerald-400"
            : metrics.consistencyRate >= 60 ? "text-amber-400"
            : "text-red-400"
          }
        />
        <MetricTile
          label="Avg Confidence"
          value={metrics.totalRuns > 0 ? metrics.avgConfidence : "—"}
          suffix={metrics.totalRuns > 0 ? "%" : undefined}
          icon={BarChart2}
          valueColor={metrics.totalRuns === 0 ? "text-[#F4F4F5]" : avgConfColor}
        />
      </div>

      {metrics.totalRuns > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-[#111113] border border-[#27272A] rounded-lg p-4 space-y-3"
        >
          <span className="text-[10px] text-[#71717A] uppercase tracking-widest font-semibold">
            Intent Distribution
          </span>
          <div className="space-y-2.5">
            {Object.entries(metrics.intentDistribution)
              .sort(([, a], [, b]) => b - a)
              .map(([intent, count]) => {
                const cfg = INTENT_CONFIG[intent as Intent];
                const pct = Math.round((count / metrics.totalRuns) * 100);
                return (
                  <div key={intent} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className={cn("text-xs font-mono", cfg?.color ?? "text-[#A1A1AA]")}>
                        {intent}
                      </span>
                      <span className="text-xs font-mono text-[#52525B]">
                        {count}× &nbsp;{pct}%
                      </span>
                    </div>
                    <div className="h-1 bg-[#1C1C1E] rounded-full overflow-hidden">
                      <motion.div
                        className={cn("h-full rounded-full", cfg?.bar ?? "bg-[#71717A]")}
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.4, ease: "easeOut" }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        </motion.div>
      )}

      {transitionDrift.total > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-[#111113] border border-[#27272A] rounded-lg p-4 space-y-3"
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-[#71717A] uppercase tracking-widest font-semibold">
              Transition Drift
            </span>
            <span className="text-[10px] font-mono text-[#52525B]">
              {transitionDrift.total} shift{transitionDrift.total !== 1 ? "s" : ""}
            </span>
          </div>
          <div className="space-y-2">
            {transitionDrift.transitions.map(({ from, to, count }) => {
              const fromCfg = INTENT_CONFIG[from];
              const toCfg = INTENT_CONFIG[to];
              return (
                <motion.div
                  key={`${from}-${to}`}
                  initial={{ opacity: 0, x: -4 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center justify-between"
                >
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className={cn("text-[11px] font-mono truncate", fromCfg?.color ?? "text-[#A1A1AA]")}>
                      {from}
                    </span>
                    <ArrowRight className="w-3 h-3 text-[#3F3F46] flex-shrink-0" />
                    <span className={cn("text-[11px] font-mono truncate", toCfg?.color ?? "text-[#A1A1AA]")}>
                      {to}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-[#52525B] flex-shrink-0 ml-2">
                    {count}×
                  </span>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      )}
    </div>
  );
}
