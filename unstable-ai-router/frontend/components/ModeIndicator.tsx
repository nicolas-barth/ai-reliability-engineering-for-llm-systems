"use client";

interface ModeIndicatorProps {
  executionMode: string;
}

export function ModeIndicator({ executionMode }: ModeIndicatorProps) {
  const isDemo = executionMode === "demo_mode";

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-semibold tracking-widest border
        ${isDemo
          ? "bg-amber-500/10 border-amber-500/20 text-amber-400"
          : "bg-indigo-500/10 border-indigo-500/20 text-indigo-400"
        }
      `}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${isDemo ? "bg-amber-400" : "bg-indigo-400"}`}
      />
      {isDemo ? "DEMO MODE" : "REAL LLM"}
    </span>
  );
}
