"use client";

import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, ShieldAlert, CheckCircle2, Activity } from "lucide-react";
import { ClassificationMetrics } from "@/types";
import { STABILITY_CONFIG, STATUS_MESSAGES, cn } from "@/lib/utils";

interface SystemStatusBadgeProps {
  metrics: ClassificationMetrics;
}

const ICONS = {
  STABLE:            CheckCircle2,
  MODERATE:          Activity,
  UNSTABLE:          AlertTriangle,
  "HIGH INSTABILITY": ShieldAlert,
};

export function SystemStatusBadge({ metrics }: SystemStatusBadgeProps) {
  if (metrics.totalRuns < 2) return null;

  const cfg = STABILITY_CONFIG[metrics.stabilityLabel];
  const msg = STATUS_MESSAGES[metrics.stabilityLabel];
  const Icon = ICONS[metrics.stabilityLabel];
  const isAlert = metrics.stabilityLabel === "UNSTABLE" || metrics.stabilityLabel === "HIGH INSTABILITY";

  const avgConfColor =
    metrics.avgConfidence >= 70 ? cfg.color
    : metrics.avgConfidence >= 50 ? "text-amber-400"
    : "text-red-400";

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={metrics.stabilityLabel}
        initial={{ opacity: 0, y: -8, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -8, scale: 0.98 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className={cn("w-full mb-6 rounded-xl border px-5 py-4", cfg.bg, cfg.border)}
        style={{ boxShadow: `0 0 32px ${cfg.glow}, 0 0 12px ${cfg.glow}` }}
      >
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <div className="relative flex-shrink-0">
              {isAlert && (
                <motion.div
                  className={cn("absolute inset-0 rounded-full", cfg.dot)}
                  animate={{ scale: [1, 1.8, 1], opacity: [0.6, 0, 0.6] }}
                  transition={{ duration: 1.8, repeat: Infinity, ease: "easeOut" }}
                />
              )}
              <div className={cn("w-2.5 h-2.5 rounded-full relative z-10", cfg.dot)} />
            </div>

            <Icon className={cn("w-4 h-4 flex-shrink-0", cfg.color)} />

            <div className="min-w-0">
              <span className={cn("text-sm font-bold font-mono tracking-widest", cfg.color)}>
                {msg.title}
              </span>
              <p className="text-xs text-[#71717A] mt-0.5 truncate">{msg.detail}</p>
            </div>
          </div>

          {/* Stats row */}
          <div className="hidden sm:flex items-center gap-4 flex-shrink-0 text-xs font-mono">
            <div className="text-right">
              <div className="text-[#52525B]">avg confidence</div>
              <div className={cn("font-bold", avgConfColor)}>{metrics.avgConfidence}%</div>
            </div>
            <div className="w-px h-8 bg-[#27272A]" />
            <div className="text-right">
              <div className="text-[#52525B]">consistency</div>
              <div className={cn("font-bold", cfg.color)}>{metrics.consistencyRate}%</div>
            </div>
            <div className="w-px h-8 bg-[#27272A]" />
            <div className="text-right">
              <div className="text-[#52525B]">unique intents</div>
              <div className={cn("font-bold", cfg.color)}>{metrics.uniqueIntents}</div>
            </div>
            <div className="w-px h-8 bg-[#27272A]" />
            <div className="text-right">
              <div className="text-[#52525B]">total runs</div>
              <div className={cn("font-bold", cfg.color)}>{metrics.totalRuns}</div>
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
