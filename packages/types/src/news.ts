import { z } from "zod";

export const NewsImpactSchema = z.object({
  score: z.number().min(0).max(1),
  direction: z.enum(["positive", "negative", "neutral"]),
  affectedSectors: z.array(z.string()),
  reasoning: z.string(),
});

export const NewsArticleSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  url: z.string().url(),
  source: z.string(),
  publishedAt: z.string().datetime().nullable(),
  summaryLines: z.array(z.string()).max(3),
  japanMarketImpact: NewsImpactSchema,
  urgency: z.enum(["breaking", "today", "background"]),
  createdAt: z.string().datetime(),
});

export type NewsArticle = z.infer<typeof NewsArticleSchema>;
export type NewsImpact = z.infer<typeof NewsImpactSchema>;
