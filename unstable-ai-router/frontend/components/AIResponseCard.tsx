"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Bot, Hash, Sparkles } from "lucide-react";
import { ClassificationResult, Intent } from "@/types";
import { INTENT_CONFIG, cn } from "@/lib/utils";

interface AIResponseCardProps {
  result: ClassificationResult | null;
  isLoading: boolean;
  previousResponse: string | null;
}

export function AIResponseCard({ result, isLoading, previousResponse }: AIResponseCardProps) {
  const hasChanged =
    result &&
    previousResponse !== null &&
    previousResponse !== result.generated_response;

  const intentCfg = result ? INTENT_CONFIG[result.predicted_intent as Intent] : null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="w-1 h-4 bg-indigo-500 rounded-full" />
        <span className="text-xs font-semibold text-[#A1A1AA] uppercase tracking-widest">
          AI Generated Response
        </span>
        {hasChanged && (
          <motion.span
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-[10px] font-mono font-semibold text-amber-400 bg-amber-400/10 border border-amber-400/20 px-1.5 py-0.5 rounded"
          >
            CHANGED
          </motion.span>
        )}
      </div>

      <div
        className={cn(
          "relative rounded-xl border overflow-hidden transition-all duration-500",
          result && intentCfg
            ? "border-[#27272A]"
            : "border-[#1C1C1E]",
        )}
        style={
          result && intentCfg
            ? { boxShadow: `0 0 20px ${intentCfg.glow}` }
            : undefined
        }
      >
        {result && intentCfg && (
          <div className={cn("absolute left-0 top-0 bottom-0 w-0.5", intentCfg.dot)} />
        )}

        <AnimatePresence mode="wait">
          {isLoading ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center gap-3 h-[130px]"
            >
              <div className="flex gap-1.5">
                {[0, 1, 2].map((i) => (
                  <motion.div
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-indigo-500"
                    animate={{ opacity: [0.3, 1, 0.3], y: [0, -4, 0] }}
                    transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.15 }}
                  />
                ))}
              </div>
              <span className="text-xs text-[#52525B] font-mono">Generating response...</span>
            </motion.div>
          ) : result ? (
            <motion.div
              key={result.run_id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className="p-5"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                    <Bot className="w-3.5 h-3.5 text-indigo-400" />
                  </div>
                  <span className="text-xs text-[#71717A] font-mono">support-agent-v1</span>
                </div>
                <div className="flex items-center gap-1.5 text-xs font-mono text-[#52525B]">
                  <Hash className="w-3 h-3" />
                  {result.run_id}
                </div>
              </div>

              <motion.p
                key={`text-${result.run_id}`}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: 0.1 }}
                className="text-[15px] text-[#E4E4E7] leading-relaxed"
              >
                &ldquo;{result.generated_response}&rdquo;
              </motion.p>

              <div className="mt-4 pt-3 border-t border-[#1C1C1E] flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Sparkles className="w-3 h-3 text-[#52525B]" />
                  <span className="text-[10px] text-[#52525B] font-mono">
                    routed via{" "}
                    <span className={cn("font-semibold", intentCfg?.color)}>
                      {result.predicted_intent}
                    </span>
                  </span>
                </div>
                {hasChanged && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-[10px] font-mono text-amber-400/70"
                  >
                    ↕ response drift detected
                  </motion.span>
                )}
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center gap-3 h-[130px]"
            >
              <Bot className="w-6 h-6 text-[#3F3F46]" />
              <span className="text-xs text-[#52525B]">Response will appear here</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
