import { z } from "zod";

export const HoldingSchema = z.object({
  id: z.string().uuid(),
  ticker: z.string(),
  quantity: z.number(),
  averageCost: z.number(),
  currency: z.string().default("JPY"),
  isMock: z.boolean().default(true),
});

export const PortfolioSummarySchema = z.object({
  totalValue: z.number(),
  totalCost: z.number(),
  totalPnl: z.number(),
  totalPnlPercent: z.number(),
  topMover: z.object({
    ticker: z.string(),
    change: z.number(),
  }).nullable(),
  holdings: z.array(HoldingSchema),
  hasMockData: z.boolean(),
  updatedAt: z.string().datetime(),
});

export type Holding = z.infer<typeof HoldingSchema>;
export type PortfolioSummary = z.infer<typeof PortfolioSummarySchema>;
