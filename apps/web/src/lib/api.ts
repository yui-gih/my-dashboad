const AGENT_URL = process.env.NEXT_PUBLIC_AGENT_URL ?? "http://localhost:8000";

export async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${AGENT_URL}/api${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<T>;
}

export async function triggerAgent(agent: "youtube" | "news"): Promise<void> {
  await fetch(`${AGENT_URL}/api/agent/${agent}/run`, { method: "POST" });
}
