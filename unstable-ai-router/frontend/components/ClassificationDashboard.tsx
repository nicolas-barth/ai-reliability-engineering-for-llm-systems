"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertCircle } from "lucide-react";
import { Header } from "./Header";
import { InputSection } from "./InputSection";
import { ResultCard } from "./ResultCard";
import { AIResponseCard } from "./AIResponseCard";
import { RunHistory } from "./RunHistory";
import { MetricsPanel } from "./MetricsPanel";
import { SystemStatusBadge } from "./SystemStatusBadge";
import { classifyMessage, fetchDataset, fetchExecutionMode } from "@/services/api";
import { ClassificationResult, DatasetMessage } from "@/types";
import { computeMetrics, computeDrift, computeTransitionDrift } from "@/lib/utils";

export function ClassificationDashboard() {
  const FIXED_MESSAGE = "Fui cobrado errado e quero cancelar minha assinatura";
  const [message, setMessage] = useState(FIXED_MESSAGE);
  const [history, setHistory] = useState<ClassificationResult[]>([]);
  const [currentResult, setCurrentResult] = useState<ClassificationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dataset, setDataset] = useState<DatasetMessage[]>([]);
  const [executionMode, setExecutionMode] = useState<string>("");

  const previousResponseRef = useRef<string | null>(null);

  useEffect(() => {
    fetchDataset()
      .then(setDataset)
      .catch(() => {});
    fetchExecutionMode()
      .then(setExecutionMode)
      .catch(() => {});
  }, []);

  const handleClassify = async (msg: string) => {
    setIsLoading(true);
    setError(null);

    if (currentResult) {
      previousResponseRef.current = currentResult.generated_response;
    }

    try {
      const result = await classifyMessage(msg);
      setCurrentResult(result);
      setHistory((prev) => [...prev, result]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Classification failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setHistory([]);
    setCurrentResult(null);
    previousResponseRef.current = null;
  };

  const metrics = computeMetrics(history);
  const drift = computeDrift(history);
  const transitionDrift = computeTransitionDrift(history);

  return (
    <div className="min-h-screen bg-[#09090B]">
      <Header executionMode={executionMode} />

      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-8">
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-6 overflow-hidden"
            >
              <div className="flex items-center gap-3 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400 font-mono">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <SystemStatusBadge metrics={metrics} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          <div className="space-y-6">
            <InputSection
              onClassify={handleClassify}
              isLoading={isLoading}
              hasRun={history.length > 0}
              dataset={dataset}
              currentMessage={message}
              onMessageChange={setMessage}
            />
            <ResultCard result={currentResult} isLoading={isLoading} />
            <AIResponseCard
              result={currentResult}
              isLoading={isLoading}
              previousResponse={previousResponseRef.current}
            />
          </div>

          <div className="lg:col-span-2 space-y-6">
            <RunHistory history={history} onClear={handleClear} />
            <MetricsPanel metrics={metrics} drift={drift} transitionDrift={transitionDrift} />
          </div>
        </div>
      </div>
    </div>
  );
}
