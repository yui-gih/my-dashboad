import { z } from "zod";

export const TranscriptSourceSchema = z.enum([
  "manual_ja",
  "auto_ja",
  "manual_en",
  "auto_en",
  "description",
  "title_only",
]);
export type TranscriptSource = z.infer<typeof TranscriptSourceSchema>;

export const VideoSummarySchema = z.object({
  oneLiner: z.string(),
  keyPoints: z.array(z.string()).max(3),
  watchReason: z.string(),
});

export const VideoAnalysisSchema = z.object({
  id: z.string().uuid(),
  videoId: z.string(),
  title: z.string(),
  channelId: z.string(),
  channelTitle: z.string(),
  thumbnailUrl: z.string().url(),
  publishedAt: z.string().datetime(),
  priorityScore: z.number().min(0).max(1),
  summary: VideoSummarySchema,
  transcriptSource: TranscriptSourceSchema,
  analysisVersion: z.string(),
  llmTokensUsed: z.number().int(),
  analyzedAt: z.string().datetime(),
});

export type VideoAnalysis = z.infer<typeof VideoAnalysisSchema>;
export type VideoSummary = z.infer<typeof VideoSummarySchema>;
