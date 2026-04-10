"use client";

import { useState } from "react";
import { useVideoFeed } from "@/hooks/useVideoFeed";
import { useAgentStream } from "@/hooks/useAgentStream";
import { VideoCard } from "@/components/dashboard/VideoCard";
import { AgentThoughtPanel } from "@/components/dashboard/AgentThoughtPanel";
import { QuotaIndicator } from "@/components/dashboard/QuotaIndicator";
import { NewsSection } from "@/components/dashboard/NewsSection";
import { PortfolioWidget } from "@/components/dashboard/PortfolioWidget";
import { MountainSection } from "@/components/dashboard/MountainSection";
import { AiNewsSection } from "@/components/dashboard/AiNewsSection";
import { HealthSection } from "@/components/dashboard/HealthSection";
import type { VideoAnalysis, NewsArticle, PortfolioSummary } from "@repo/types";
import type { MountainWeather, AiArticle, HealthRecord } from "@/app/page";

interface Props {
  initialData: {
    videos: VideoAnalysis[];
    articles: NewsArticle[];
    portfolio: {
      portfolio: PortfolioSummary;
      weather: { description: string; temp: number; location: string };
      advice: string;
      fxRate: number;
    };
    quota: {
      usedToday: number;
      remaining: number;
      limit: number;
      usagePercent: number;
    };
    mountains: MountainWeather[];
    aiArticles: AiArticle[];
    healthRecords: HealthRecord[];
  };
}

function SectionHeader({ icon, title, count }: { icon: string; title: string; count?: string }) {
  return (
    <div className="flex items-center gap-2 py-1">
      <span className="text-base leading-none">{icon}</span>
      <h2 className="text-sm font-semibold text-zinc-300">{title}</h2>
      {count && <span className="text-[10px] text-zinc-600 font-mono">{count}</span>}
      <div className="flex-1 h-px bg-gradient-to-r from-zinc-700/60 to-transparent" />
    </div>
  );
}

export function DashboardClient({ initialData }: Props) {
  const [runId, setRunId] = useState<string | null>(null);
  const [isTriggering, setIsTriggering] = useState(false);

  const { videos } = useVideoFeed(20);
  const { steps, done } = useAgentStream(runId);

  const displayVideos = videos.length > 0 ? videos : initialData.videos;
  const isRunning = !!runId && !done;

  async function handleRunAgent() {
    setIsTriggering(true);
    try {
      const res = await fetch(`/api/agent/youtube/run`, { method: "POST" });
      const data = await res.json();
      setRunId(data.runId);
    } catch (e) {
      console.error(e);
    } finally {
      setIsTriggering(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-57px)]">
      {/* 左ペイン: 縦スクロール */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-8">
          {/* ポートフォリオ */}
          <PortfolioWidget
            summary={initialData.portfolio.portfolio}
            weather={initialData.portfolio.weather}
            fxRate={initialData.portfolio.fxRate}
            advice={initialData.portfolio.advice}
          />

          {/* YouTube */}
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <SectionHeader icon="▶️" title="YouTube" count={`${displayVideos.length}件`} />
              <button
                onClick={handleRunAgent}
                disabled={isTriggering || isRunning}
                className="text-xs px-3 py-1.5 rounded-lg border border-zinc-700/50 bg-zinc-800 hover:bg-zinc-700 hover:border-zinc-600 disabled:opacity-40 transition-all shadow-[0_1px_4px_rgba(0,0,0,0.3)] shrink-0"
              >
                {isRunning ? "解析中..." : "今すぐ更新"}
              </button>
            </div>
            <div className="h-96 overflow-y-auto space-y-3 pr-1">
              {displayVideos.length === 0 ? (
                <div className="text-center py-8 text-zinc-600 text-sm">
                  <p>動画データがありません</p>
                  <p className="text-xs mt-1">「今すぐ更新」でエージェントを実行してください</p>
                </div>
              ) : (
                displayVideos.map((video) => (
                  <VideoCard key={video.videoId} video={video} />
                ))
              )}
            </div>
          </section>

          {/* ニュース */}
          <section className="space-y-3">
            <SectionHeader icon="📰" title="ニュース" count={`${initialData.articles.length}件`} />
            <div className="h-96 overflow-y-auto pr-1">
              <NewsSection articles={initialData.articles} />
            </div>
          </section>

          {/* 山情報 */}
          <section className="space-y-3">
            <SectionHeader icon="⛰️" title="山情報" count={`${initialData.mountains.length}山`} />
            <div className="h-96 overflow-y-auto pr-1">
              <MountainSection mountains={initialData.mountains} />
            </div>
          </section>

          {/* AI情報 */}
          <section className="space-y-3">
            <SectionHeader icon="🤖" title="AI 情報" count={`${initialData.aiArticles.length}件`} />
            <div className="h-96 overflow-y-auto pr-1">
              <AiNewsSection articles={initialData.aiArticles} />
            </div>
          </section>

          {/* 健康 */}
          <section className="space-y-3">
            <SectionHeader icon="❤️" title="健康" />
            <div className="h-96 overflow-y-auto pr-1">
              <HealthSection records={initialData.healthRecords} />
            </div>
          </section>
        </div>
      </div>

      {/* 右ペイン: エージェントログ + クォータ */}
      <div className="w-80 border-l border-zinc-800 flex flex-col p-4 gap-4 overflow-hidden shrink-0">
        <QuotaIndicator {...initialData.quota} />
        <div className="flex-1 overflow-hidden">
          <AgentThoughtPanel steps={steps} isRunning={isRunning} />
        </div>
      </div>
    </div>
  );
}
