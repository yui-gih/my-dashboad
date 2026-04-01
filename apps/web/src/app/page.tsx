import { Suspense } from "react";
import { fetchApi } from "@/lib/api";
import { DashboardClient } from "./dashboard-client";
import type { VideoAnalysis, NewsArticle, PortfolioSummary } from "@repo/types";

export type MountainWeather = {
  name: string;
  elevation: number;
  prefecture: string;
  temp: number;
  windSpeed: number;
  description: string;
  humidity: number;
  icon: string;
};

export type AiArticle = {
  id: string;
  title: string;
  url: string;
  source: string;
  publishedAt: string | null;
  summary: string;
};

export type HealthRecord = {
  date: string;
  steps: number | null;
  sleepHours: number | null;
  heartRateAvg: number | null;
  activeCalories: number | null;
  exerciseMinutes: number | null;
  standHours: number | null;
  weight: number | null;
};

type PortfolioResponse = {
  portfolio: PortfolioSummary;
  weather: { description: string; temp: number; location: string };
  advice: string;
  fxRate: number;
};

const FALLBACK_PORTFOLIO: PortfolioResponse = {
  portfolio: {
    totalValue: 0, totalCost: 0, totalPnl: 0, totalPnlPercent: 0,
    topMover: null, holdings: [], hasMockData: true, updatedAt: new Date().toISOString(),
  },
  weather: { description: "不明", temp: 20, location: "東京" },
  advice: "エージェントサーバーに接続できませんでした。",
  fxRate: 150,
};

async function loadData() {
  const [videosRes, articlesRes, portfolioRes, quotaRes, mountainsRes, aiNewsRes, healthRes] = await Promise.allSettled([
    fetchApi<{ videos: VideoAnalysis[] }>("/agent/youtube/videos?limit=20"),
    fetchApi<{ articles: NewsArticle[] }>("/agent/news/articles?limit=15"),
    fetchApi<PortfolioResponse>("/portfolio/summary"),
    fetchApi<{ usedToday: number; remaining: number; limit: number; usagePercent: number }>("/quota/status"),
    fetchApi<{ mountains: MountainWeather[] }>("/mountains/weather"),
    fetchApi<{ articles: AiArticle[] }>("/agent/ai-news/articles?limit=20"),
    fetchApi<{ data: HealthRecord[] }>("/health/data?days=7"),
  ]);

  return {
    videos: videosRes.status === "fulfilled" ? videosRes.value.videos : [],
    articles: articlesRes.status === "fulfilled" ? articlesRes.value.articles : [],
    portfolio: portfolioRes.status === "fulfilled" ? portfolioRes.value : FALLBACK_PORTFOLIO,
    quota: quotaRes.status === "fulfilled" ? quotaRes.value : {
      usedToday: 0, remaining: 10000, limit: 10000, usagePercent: 0,
    },
    mountains: mountainsRes.status === "fulfilled" ? mountainsRes.value.mountains : [],
    aiArticles: aiNewsRes.status === "fulfilled" ? aiNewsRes.value.articles : [],
    healthRecords: healthRes.status === "fulfilled" ? healthRes.value.data : [],
  };
}

export default async function HomePage() {
  const data = await loadData();

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="border-b border-zinc-800/80 px-6 py-3 flex items-center justify-between bg-zinc-950/80 backdrop-blur-sm sticky top-0 z-10 shadow-[0_1px_0_rgba(255,255,255,0.04)]">
        <div>
          <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-zinc-100 to-zinc-400 bg-clip-text text-transparent">
            マイダッシュボード
          </h1>
          <p className="text-[10px] text-zinc-600 tracking-widest uppercase">AI-Powered Personal Intelligence</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(52,211,153,0.8)] animate-pulse" />
          <span className="text-xs text-zinc-600 font-mono">
            {new Date().toLocaleDateString("ja-JP", {
              weekday: "short", year: "numeric", month: "short", day: "numeric",
            })}
          </span>
        </div>
      </header>

      <Suspense fallback={<div className="p-8 text-zinc-500">読み込み中...</div>}>
        <DashboardClient initialData={data} />
      </Suspense>
    </main>
  );
}
