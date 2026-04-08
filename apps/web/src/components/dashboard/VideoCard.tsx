"use client";

import type { VideoAnalysis } from "@repo/types";

const SOURCE_LABELS: Record<string, { label: string; color: string }> = {
  manual_ja: { label: "字幕(日本語)", color: "text-emerald-400" },
  auto_ja:   { label: "自動字幕(日)", color: "text-yellow-400" },
  manual_en: { label: "字幕(英語)",   color: "text-blue-400" },
  auto_en:   { label: "自動字幕(英)", color: "text-orange-400" },
  description: { label: "概要欄",     color: "text-zinc-400" },
  title_only:  { label: "タイトルのみ", color: "text-red-400" },
};

interface Props {
  video: VideoAnalysis;
}

export function VideoCard({ video }: Props) {
  const sourceInfo = SOURCE_LABELS[video.transcriptSource] ?? SOURCE_LABELS.title_only;
  const scorePercent = Math.round(video.priorityScore * 100);
  const scoreColor =
    scorePercent >= 70 ? "text-emerald-400" :
    scorePercent >= 40 ? "text-yellow-400" : "text-zinc-500";
  const scoreBg =
    scorePercent >= 70 ? "bg-emerald-500/20 border-emerald-500/40" :
    scorePercent >= 40 ? "bg-yellow-500/20 border-yellow-500/40" : "bg-black/60 border-zinc-700/40";

  return (
    <a
      href={`https://www.youtube.com/watch?v=${video.videoId}`}
      target="_blank"
      rel="noopener noreferrer"
      className="block rounded-xl border border-zinc-700/50 bg-gradient-to-b from-zinc-800/80 to-zinc-900 hover:border-zinc-600/70 hover:-translate-y-0.5 transition-all duration-200 overflow-hidden shadow-[0_4px_20px_rgba(0,0,0,0.4),inset_0_1px_0_rgba(255,255,255,0.06)] hover:shadow-[0_8px_32px_rgba(0,0,0,0.6),inset_0_1px_0_rgba(255,255,255,0.08)]"
    >
      <div className="flex gap-3 p-3">
        {/* サムネイル */}
        <div className="relative shrink-0 w-32 rounded-lg overflow-hidden bg-zinc-800 shadow-[0_2px_8px_rgba(0,0,0,0.5)]" style={{ height: "72px" }}>
          {video.thumbnailUrl && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={video.thumbnailUrl}
              alt={video.title}
              className="w-full h-full object-cover"
            />
          )}
          {/* グラデーションオーバーレイ */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
          {/* 優先度スコアバッジ */}
          <div className={`absolute top-1 right-1 text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${scoreBg} ${scoreColor}`}>
            {scorePercent}
          </div>
        </div>

        {/* コンテンツ */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-zinc-100 line-clamp-2 leading-snug">
            {video.title}
          </p>
          <p className="text-[11px] text-zinc-500 mt-0.5">{video.channelTitle}</p>

          {video.summary && (
            <div className="mt-2 space-y-1">
              <p className="text-xs text-zinc-300 font-medium leading-snug">{video.summary.oneLiner}</p>
              {video.summary.keyPoints.length > 0 && (
                <ul className="text-xs text-zinc-500 space-y-0.5 list-disc list-inside">
                  {video.summary.keyPoints.map((pt, i) => (
                    <li key={i}>{pt}</li>
                  ))}
                </ul>
              )}
              {video.summary.watchReason && (
                <p className="text-xs text-blue-400/80 mt-1">→ {video.summary.watchReason}</p>
              )}
            </div>
          )}

          <div className="flex items-center gap-2 mt-2">
            <span className={`text-[10px] font-mono ${sourceInfo.color}`}>
              [{sourceInfo.label}]
            </span>
            <span className="text-[10px] text-zinc-600" suppressHydrationWarning>
              {new Date(video.publishedAt).toLocaleDateString("ja-JP")}
            </span>
          </div>
        </div>
      </div>
    </a>
  );
}
