"use client";

import { useEffect, useState } from "react";
import type { AgentStep } from "@repo/types";

const AGENT_URL = process.env.NEXT_PUBLIC_AGENT_URL ?? "http://localhost:8000";

export function useAgentStream(runId: string | null) {
  const [steps, setSteps] = useState<AgentStep[]>([]);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!runId) return;
    setSteps([]);
    setDone(false);

    const es = new EventSource(`${AGENT_URL}/api/agent/stream/${runId}`);

    es.onmessage = (e) => {
      const step = JSON.parse(e.data) as AgentStep & { node?: string };
      if (step.node === "DONE") {
        setDone(true);
        es.close();
        return;
      }
      setSteps((prev) => [...prev, step]);
    };

    es.onerror = () => {
      setDone(true);
      es.close();
    };

    return () => es.close();
  }, [runId]);

  return { steps, done };
}
