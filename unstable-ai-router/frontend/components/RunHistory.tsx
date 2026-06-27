"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Trash2 } from "lucide-react";
import { ClassificationResult, Intent } from "@/types";
import { INTENT_CONFIG, formatTimestamp, getConfidenceColor, truncateResponse, cn } from "@/lib/utils";

function IntentCell({ intent }: { intent: Intent }) {
  const cfg = INTENT_CONFIG[intent];
  return (
    <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium whitespace-nowrap", cfg.bg, cfg.color)}>
      <span className={cn("w-1 h-1 rounded-full flex-shrink-0", cfg.dot)} />
      {intent}
    </span>
  );
}

interface RunHistoryProps {
  history: ClassificationResult[];
  onClear: () => void;
}

export function RunHistory({ history, onClear }: RunHistoryProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-1 h-4 bg-indigo-500 rounded-full" />
          <span className="text-xs font-semibold text-[#A1A1AA] uppercase tracking-widest">
            Run History
          </span>
          {history.length > 0 && (
            <span className="text-[10px] font-mono text-[#52525B] bg-[#18181B] px-1.5 py-0.5 rounded">
              {history.length}
            </span>
          )}
        </div>
        {history.length > 0 && (
          <button
            onClick={onClear}
            className="flex items-center gap-1.5 text-xs text-[#52525B] hover:text-[#A1A1AA] transition-colors py-1"
          >
            <Trash2 className="w-3 h-3" />
            Clear
          </button>
        )}
      </div>

      <div className="bg-[#111113] border border-[#27272A] rounded-lg overflow-hidden">
        {history.length === 0 ? (
          <div className="flex items-center justify-center h-40 text-xs text-[#52525B] font-mono">
            No runs yet — start classifying messages
          </div>
        ) : (
          <div className="overflow-auto max-h-[380px]">
            <table className="w-full border-collapse">
              <thead className="sticky top-0 bg-[#0D0D0F] border-b border-[#1C1C1E]">
                <tr>
                  {["#", "Intent", "Conf.", "Flow", "Response Preview", "Time"].map((h) => (
                    <th
                      key={h}
                      className="text-left px-3 py-3 text-[10px] text-[#52525B] font-semibold uppercase tracking-widest whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <AnimatePresence initial={false}>
                  {[...history].reverse().map((run, idx) => {
                    const runNumber = history.length - idx;
                    return (
                      <motion.tr
                        key={run.run_id}
                        initial={{ opacity: 0, backgroundColor: "rgba(99,102,241,0.12)" }}
                        animate={{ opacity: 1, backgroundColor: "rgba(0,0,0,0)" }}
                        transition={{ duration: 0.6 }}
                        className="border-b border-[#1C1C1E] last:border-0 hover:bg-[#18181B]/60 transition-colors"
                      >
                        <td className="px-3 py-3 text-xs font-mono text-[#52525B] w-8">
                          {runNumber}
                        </td>
                        <td className="px-3 py-3">
                          <IntentCell intent={run.predicted_intent} />
                        </td>
                        <td className="px-3 py-3 w-14">
                          <span className={cn("text-xs font-mono font-bold", getConfidenceColor(run.confidence))}>
                            {(run.confidence * 100).toFixed(0)}%
                          </span>
                        </td>
                        <td className="px-3 py-3 text-[11px] font-mono text-[#71717A] whitespace-nowrap">
                          {run.routing_flow}
                        </td>
                        <td className="px-3 py-3 max-w-[220px]">
                          <span className="text-[11px] text-[#71717A] italic leading-snug block truncate">
                            {truncateResponse(run.generated_response, 55)}
                          </span>
                        </td>
                        <td className="px-3 py-3 text-[10px] font-mono text-[#52525B] whitespace-nowrap">
                          {formatTimestamp(run.timestamp)}
                        </td>
                      </motion.tr>
                    );
                  })}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
