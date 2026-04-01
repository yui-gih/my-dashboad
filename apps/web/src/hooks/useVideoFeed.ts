"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import type { VideoAnalysis } from "@repo/types";

export function useVideoFeed(limit = 20) {
  const [videos, setVideos] = useState<VideoAnalysis[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const supabase = createClient();

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    function toVideoAnalysis(v: any): VideoAnalysis {
      return {
        id: v.id,
        videoId: v.video_id,
        channelId: v.channel_id,
        channelTitle: v.channel_title ?? "",
        title: v.title,
        publishedAt: v.published_at,
        thumbnailUrl: v.thumbnail_url ?? "",
        priorityScore: v.priority_score ?? 0,
        summary: v.summary ?? { oneLiner: v.title, keyPoints: [], watchReason: "" },
        transcriptSource: v.transcript_source ?? "title_only",
        analyzedAt: v.analyzed_at ?? v.published_at ?? "",
      };
    }

    supabase
      .from("youtube_videos")
      .select("*")
      .order("priority_score", { ascending: false })
      .limit(limit)
      .then(({ data, error }) => {
        if (!error && data) setVideos(data.map(toVideoAnalysis));
        setLoading(false);
      });

    // Supabase Realtime: エージェントがINSERTするたびにUIに即時反映
    const channel = supabase
      .channel("youtube_videos_feed")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "youtube_videos" },
        (payload) => {
          setVideos((prev) =>
            [toVideoAnalysis(payload.new), ...prev]
              .sort((a, b) => b.priorityScore - a.priorityScore)
              .slice(0, limit)
          );
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [limit]);

  return { videos, loading };
}
