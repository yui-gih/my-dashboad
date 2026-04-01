"use client";

import { useEffect, useRef } from "react";
import type { AgentStep } from "@repo/types";

interface Props {
  steps: AgentStep[];
  isRunning: boolean;
}

const STATUS_COLOR = {
  running: "text-yellow-400",
  success: "text-green-400",
  error: "text-red-400",
};

export function AgentThoughtPanel({ steps, isRunning }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [steps.length]);

  return (
    <div className="h-full flex flex-col bg-zinc-950 rounded-xl border border-zinc-800 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-zinc-800">
        <span className="text-xs text-zinc-400 font-mono">AGENT LOG</span>
        {isRunning && (
          <span className="flex items-center gap-1 text-xs text-yellow-400">
            <span className="animate-pulse">●</span> running
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3 font-mono text-xs space-y-1">
        {steps.length === 0 && (
          <p className="text-zinc-600">エージェント実行待機中...</p>
        )}
        {steps.map((step, i) => (
          <div key={i} className="flex gap-2 leading-relaxed">
            <span className="text-zinc-600 shrink-0">
              {new Date(step.timestamp).toLocaleTimeString("ja-JP")}
            </span>
            <span className={`shrink-0 ${STATUS_COLOR[step.status] ?? "text-zinc-400"}`}>
              [{step.node}]
            </span>
            <span className="text-zinc-300">{step.message}</span>
            {step.quotaUsed && step.quotaUsed > 0 && (
              <span className="text-orange-400 shrink-0">-{step.quotaUsed}u</span>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
