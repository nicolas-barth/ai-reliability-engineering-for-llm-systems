"use client";

import { motion } from "framer-motion";
import { Cpu } from "lucide-react";
import { ModeIndicator } from "./ModeIndicator";

interface HeaderProps {
  executionMode?: string;
}

export function Header({ executionMode }: HeaderProps) {
  return (
    <header className="border-b border-[#1C1C1E] bg-[#09090B]/90 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-[1400px] mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center flex-shrink-0">
            <Cpu className="w-4 h-4 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-[#F4F4F5] tracking-tight leading-none mb-0.5">
              AI Quality Engineering Lab
            </h1>
            <p className="text-xs text-[#71717A] leading-none">
              Intent Classification &amp; Routing Instability Simulator
            </p>
          </div>
        </div>

        <div className="flex items-center gap-5">
          <div className="hidden sm:flex items-center gap-3 text-xs text-[#52525B] font-mono">
            <span className="px-2 py-0.5 bg-[#111113] border border-[#27272A] rounded text-[#71717A]">
              GPT-4o-mini
            </span>
            <span className="px-2 py-0.5 bg-[#111113] border border-[#27272A] rounded text-[#71717A]">
              temp=1.1
            </span>
            <span className="px-2 py-0.5 bg-[#111113] border border-[#27272A] rounded text-[#71717A]">
              top_p=0.98
            </span>
          </div>

          {executionMode && <ModeIndicator executionMode={executionMode} />}

          <div className="flex items-center gap-2">
            <motion.div
              className="w-2 h-2 rounded-full bg-emerald-400"
              animate={{ opacity: [1, 0.3, 1] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            />
            <span className="text-xs text-emerald-400 font-semibold tracking-wide">LIVE</span>
          </div>
        </div>
      </div>
    </header>
  );
}
