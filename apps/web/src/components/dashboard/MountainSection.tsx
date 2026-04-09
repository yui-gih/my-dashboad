"use client";

import { useState } from "react";
import type { MountainWeather } from "@/app/page";

interface Props {
  mountains: MountainWeather[];
}

function WindBadge({ speed }: { speed: number }) {
  const config =
    speed >= 15 ? { label: "危険", color: "text-red-400 border-red-500/40 bg-red-500/10" } :
    speed >= 10 ? { label: "警戒", color: "text-orange-400 border-orange-500/40 bg-orange-500/10" } :
    speed >= 5  ? { label: "注意", color: "text-yellow-400 border-yellow-500/40 bg-yellow-500/10" } :
                  { label: "良好", color: "text-emerald-400 border-emerald-500/40 bg-emerald-500/10" };
  return (
    <span className={`text-[10px] border px-1.5 py-0.5 rounded ${config.color}`}>
      {config.label}
    </span>
  );
}

function WeatherEmoji({ description }: { description: string }) {
  const d = description;
  if (d.includes("雷") || d.includes("storm"))  return "⛈️";
  if (d.includes("雪") || d.includes("snow"))    return "❄️";
  if (d.includes("雨") || d.includes("rain"))    return "🌧️";
  if (d.includes("霧") || d.includes("fog") || d.includes("mist")) return "🌫️";
  if (d.includes("曇") || d.includes("cloud"))   return "☁️";
  if (d.includes("晴") || d.includes("clear"))   return "☀️";
  return "🌤️";
}

function MountainCard({ m }: { m: MountainWeather }) {
  return (
    <div className="rounded-xl border border-zinc-700/50 bg-gradient-to-b from-zinc-800/80 to-zinc-900 p-4 shadow-[0_4px_20px_rgba(0,0,0,0.4),inset_0_1px_0_rgba(255,255,255,0.06)]">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-sm font-semibold text-zinc-100">{m.name}</p>
          <p className="text-[10px] text-zinc-500 mt-0.5">{m.prefecture}</p>
        </div>
        {m.elevation && (
          <span className="text-[10px] text-zinc-500 border border-zinc-700 px-1.5 py-0.5 rounded font-mono">
            {m.elevation.toLocaleString()}m
          </span>
        )}
      </div>
      <div className="flex items-center gap-3 mb-3">
        <span className="text-3xl">{WeatherEmoji({ description: m.description })}</span>
        <div>
          <p className="text-2xl font-bold text-zinc-100 leading-none">{m.temp}℃</p>
          <p className="text-[11px] text-zinc-500 mt-0.5">{m.description}</p>
        </div>
      </div>
      <div className="flex items-center justify-between border-t border-zinc-700/40 pt-2.5">
        <div className="flex items-center gap-3 text-xs text-zinc-400">
          <span>💨 {m.windSpeed} m/s</span>
          <span>💧 {m.humidity}%</span>
        </div>
        <WindBadge speed={m.windSpeed} />
      </div>
    </div>
  );
}

export function MountainSection({ mountains }: Props) {
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<MountainWeather | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setSearchResult(null);
    setSearchError(null);
    try {
      const res = await fetch(`/api/mountains/search?q=${encodeURIComponent(query.trim())}`);
      const data = await res.json();
      if (data.error) {
        setSearchError(data.error);
      } else {
        setSearchResult(data.mountain);
      }
    } catch {
      setSearchError("通信エラーが発生しました");
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* 検索欄 */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="flex-1 relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="山名・地名で検索（例: 乗鞍岳、穂高岳）"
            className="w-full rounded-lg border border-zinc-700/50 bg-zinc-800/80 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 outline-none focus:border-zinc-500 focus:ring-1 focus:ring-zinc-500/30 shadow-[inset_0_1px_3px_rgba(0,0,0,0.3)] transition-colors"
          />
        </div>
        <button
          type="submit"
          disabled={searching || !query.trim()}
          className="px-4 py-2 rounded-lg border border-zinc-700/50 bg-zinc-800 hover:bg-zinc-700 hover:border-zinc-600 disabled:opacity-40 text-sm text-zinc-200 transition-all shadow-[0_1px_4px_rgba(0,0,0,0.3)]"
        >
          {searching ? "検索中..." : "検索"}
        </button>
      </form>

      {/* 検索結果 */}
      {searchError && (
        <p className="text-xs text-red-400 px-1">{searchError}</p>
      )}
      {searchResult && (
        <div>
          <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-2">検索結果</p>
          <MountainCard m={searchResult} />
        </div>
      )}

      {/* プリセット山岳 */}
      {mountains.length > 0 && (
        <div>
          <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-2">主要山岳</p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {mountains.map((m) => (
              <MountainCard key={m.name} m={m} />
            ))}
          </div>
        </div>
      )}

      {mountains.length === 0 && !searchResult && (
        <div className="text-center py-12 text-zinc-600 text-sm">
          山情報を取得できませんでした
        </div>
      )}
    </div>
  );
}
