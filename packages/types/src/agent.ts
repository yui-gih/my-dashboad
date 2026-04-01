import { z } from "zod";

export const AgentStepSchema = z.object({
  node: z.string(),
  message: z.string(),
  quotaUsed: z.number().optional(),
  timestamp: z.string().datetime(),
  status: z.enum(["running", "success", "error"]),
});

export const AgentStatusSchema = z.object({
  isRunning: z.boolean(),
  lastRunAt: z.string().datetime().nullable(),
  quotaUsed: z.number(),
  quotaLimit: z.number(),
  nextRunAt: z.string().datetime().nullable(),
});

export type AgentStep = z.infer<typeof AgentStepSchema>;
export type AgentStatus = z.infer<typeof AgentStatusSchema>;
