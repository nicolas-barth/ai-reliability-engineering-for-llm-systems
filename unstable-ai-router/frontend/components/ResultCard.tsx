"use client";

import { motion, AnimatePresence } from "framer-motion";
import { GitBranch, Clock, Hash, Zap, AlertCircle } from "lucide-react";
import { ClassificationResult, Intent } from "@/types";
import {
  INTENT_CONFIG,
  formatTimestamp,
  getConfidenceColor,
  getConfidenceBarColor,
  cn,
} from "@/lib/utils";

function IntentBadge({ intent }: { intent: Intent }) {
  const cfg = INTENT_CONFIG[intent];
  return (
    <span className={cn("inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-mono font-semibold", cfg.bg, cfg.color)}>
      <span className={cn("w-1.5 h-1.5 rounded-full flex-shrink-0", cfg.dot)} />
      {intent}
    </span>
  );
}

interface ResultCardProps {
  result: ClassificationResult | null;
  isLoading: boolean;
}

export function ResultCard({ result, isLoading }: ResultCardProps) {
  const isUnstable = result && result.confidence < 0.65;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="w-1 h-4 bg-indigo-500 rounded-full" />
        <span className="text-xs font-semibold text-[#A1A1AA] uppercase tracking-widest">
          Current Result
        </span>
        {isUnstable && (
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-1 text-[10px] font-mono font-semibold text-red-400 bg-red-400/10 border border-red-400/20 px-1.5 py-0.5 rounded"
          >
            <AlertCircle className="w-2.5 h-2.5" />
            LOW CONFIDENCE
          </motion.span>
        )}
      </div>

      <div className="bg-[#111113] border border-[#27272A] rounded-lg overflow-hidden min-h-[200px]">
        <AnimatePresence mode="wait">
          {isLoading ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center gap-3 h-[200px]"
            >
              <div className="w-8 h-8 rounded-full border-2 border-indigo-500/20 border-t-indigo-500 animate-spin" />
              <span className="text-xs text-[#52525B] font-mono">Routing through LLM...</span>
            </motion.div>
          ) : result ? (
            <motion.div
              key={result.run_id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="p-5 space-y-5"
            >
              <div className="flex items-center justify-between text-xs font-mono text-[#52525B]">
                <div className="flex items-center gap-1.5">
                  <Hash className="w-3 h-3" />
                  {result.run_id}
                </div>
                <div className="flex items-center gap-1.5">
                  <Clock className="w-3 h-3" />
                  {formatTimestamp(result.timestamp)}
                </div>
              </div>

              <div className="space-y-2">
                <span className="text-[11px] text-[#71717A] uppercase tracking-wider font-medium">
                  Selected Intent
                </span>
                <IntentBadge intent={result.predicted_intent} />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-[#71717A] uppercase tracking-wider font-medium">
                    Confidence
                  </span>
                  <div className="flex items-center gap-2">
                    {result.confidence < 0.65 && (
                      <span className="text-[10px] font-mono text-red-400/70">UNCERTAIN</span>
                    )}
                    <span className={cn("text-sm font-mono font-bold", getConfidenceColor(result.confidence))}>
                      {(result.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                <div className="h-1.5 bg-[#1C1C1E] rounded-full overflow-hidden">
                  <motion.div
                    className={cn("h-full rounded-full", getConfidenceBarColor(result.confidence))}
                    initial={{ width: 0 }}
                    animate={{ width: `${result.confidence * 100}%` }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                  />
                </div>
              </div>

              {result.intent_distribution && Object.keys(result.intent_distribution).length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-[#71717A] uppercase tracking-wider font-medium">
                      Interpretation Split
                    </span>
                    <span className="text-[10px] text-[#3F3F46] font-mono">probability mass</span>
                  </div>
                  <div className="space-y-1.5">
                    {Object.entries(result.intent_distribution)
                      .sort(([, a], [, b]) => b - a)
                      .map(([intent, prob]) => {
                        const cfg = INTENT_CONFIG[intent as Intent];
                        const pct = Math.round(prob * 100);
                        const isSelected = intent === result.predicted_intent;
                        return (
                          <div key={intent} className="flex items-center gap-2">
                            <span
                              className={cn(
                                "text-[10px] font-mono w-28 flex-shrink-0 truncate",
                                isSelected ? cfg?.color : "text-[#3F3F46]",
                              )}
                            >
                              {intent}
                            </span>
                            <div className="flex-1 h-1 bg-[#1C1C1E] rounded-full overflow-hidden">
                              <motion.div
                                className={cn("h-full rounded-full", isSelected ? cfg?.bar : "bg-[#2E2E33]")}
                                initial={{ width: 0 }}
                                animate={{ width: `${pct}%` }}
                                transition={{ duration: 0.4, ease: "easeOut", delay: 0.1 }}
                              />
                            </div>
                            <span
                              className={cn(
                                "text-[10px] font-mono w-7 text-right flex-shrink-0",
                                isSelected ? cfg?.color : "text-[#3F3F46]",
                              )}
                            >
                              {pct}%
                            </span>
                          </div>
                        );
                      })}
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <span className="text-[11px] text-[#71717A] uppercase tracking-wider font-medium">
                  Routing Flow
                </span>
                <div className="flex items-center gap-2 px-3 py-2 bg-indigo-500/5 border border-indigo-500/20 rounded-md">
                  <GitBranch className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                  <span className="text-sm text-indigo-300 font-mono">{result.routing_flow}</span>
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center gap-3 h-[200px]"
            >
              <div className="w-10 h-10 rounded-xl bg-[#18181B] border border-[#27272A] flex items-center justify-center">
                <Zap className="w-5 h-5 text-[#3F3F46]" />
              </div>
              <span className="text-xs text-[#52525B]">
                Run a classification to see results
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
