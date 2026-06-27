"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Play, RotateCcw, Loader2, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import { DatasetMessage } from "@/types";

interface InputSectionProps {
  onClassify: (message: string) => void;
  isLoading: boolean;
  hasRun: boolean;
  dataset: DatasetMessage[];
  currentMessage: string;
  onMessageChange: (msg: string) => void;
}

export function InputSection({
  onClassify,
  isLoading,
  hasRun,
  currentMessage,
}: InputSectionProps) {
  const handleRun = () => {
    if (currentMessage.trim() && !isLoading) {
      onClassify(currentMessage.trim());
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-1 h-4 bg-indigo-500 rounded-full" />
          <span className="text-xs font-semibold text-[#A1A1AA] uppercase tracking-widest">
            Classification Input
          </span>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-1 bg-amber-400/10 border border-amber-400/25 rounded-md">
          <Lock className="w-2.5 h-2.5 text-amber-400" />
          <span className="text-[10px] font-semibold text-amber-400 uppercase tracking-wider">
            Fixed Evaluation Scenario
          </span>
        </div>
      </div>

      <div className="relative">
        <textarea
          value={currentMessage}
          readOnly
          rows={5}
          className={cn(
            "w-full bg-[#0D0D10] border border-amber-400/20 rounded-lg px-4 py-3",
            "text-sm text-[#D4D4D8] font-mono leading-relaxed",
            "resize-none outline-none cursor-default select-all",
            "ring-0",
          )}
        />
        <div className="absolute bottom-3 right-3 flex items-center gap-1 text-[10px] text-amber-400/60 font-mono select-none">
          <Lock className="w-2.5 h-2.5" />
          read-only
        </div>
      </div>

      <p className="text-[11px] text-[#52525B] font-mono leading-relaxed px-0.5">
        Input locked — run repeatedly to observe routing instability across identical inputs.
      </p>

      <div className="flex gap-2">
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={handleRun}
          disabled={isLoading}
          className={cn(
            "flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg",
            "text-sm font-semibold transition-all duration-200",
            isLoading
              ? "bg-[#18181B] text-[#52525B] cursor-not-allowed"
              : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20",
          )}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Classifying...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Run Classification
            </>
          )}
        </motion.button>

        <AnimatePresence>
          {hasRun && (
            <motion.button
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
              exit={{ opacity: 0, width: 0 }}
              whileTap={{ scale: 0.97 }}
              onClick={handleRun}
              disabled={isLoading}
              className={cn(
                "flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg",
                "bg-[#18181B] hover:bg-[#1F1F23] border border-[#27272A] hover:border-indigo-500/30",
                "text-sm font-medium text-[#A1A1AA] hover:text-[#F4F4F5]",
                "transition-all duration-200 whitespace-nowrap",
                "disabled:opacity-40 disabled:cursor-not-allowed",
              )}
            >
              <RotateCcw className="w-4 h-4" />
              Run Again
            </motion.button>
          )}
        </AnimatePresence>
      </div>

      {hasRun && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-[11px] text-[#52525B] text-center font-mono"
        >
          Same input — observe how intent, confidence, and routing change each run
        </motion.p>
      )}
    </div>
  );
}
