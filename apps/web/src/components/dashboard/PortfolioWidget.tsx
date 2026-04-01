"use client";

import type { PortfolioSummary } from "@repo/types";

interface Props {
  summary: PortfolioSummary;
  weather: { description: string; temp: number; location: string };
  fxRate: number;
  advice: string;
}

function WeatherIcon({ description }: { description: string }) {
  const d = description;
  if (d.includes("雷") || d.includes("storm") || d.includes("thunder")) {
    return <span className="text-3xl inline-block animate-pulse" title={description}>⛈️</span>;
  }
  if (d.includes("雪") || d.includes("snow")) {
    return <span className="text-3xl inline-block" style={{ animation: "spin 6s linear infinite" }} title={description}>❄️</span>;
  }
  if (d.includes("雨") || d.includes("rain") || d.includes("drizzle") || d.includes("shower")) {
    return <span className="text-3xl inline-block animate-bounce" title={description}>🌧️</span>;
  }
  if (d.includes("霧") || d.includes("fog") || d.includes("mist") || d.includes("haze")) {
    return <span className="text-3xl inline-block animate-pulse" title={description}>🌫️</span>;
  }
  if (d.includes("曇") || d.includes("cloud") || d.includes("overcast")) {
    return <span className="text-3xl inline-block" style={{ animation: "drift 4s ease-in-out infinite" }} title={description}>☁️</span>;
  }
  if (d.includes("晴") || d.includes("clear") || d.includes("sunny")) {
    return <span className="text-3xl inline-block" style={{ animation: "spin 8s linear infinite" }} title={description}>☀️</span>;
  }
  return <span className="text-3xl" title={description}>🌡️</span>;
}

export function PortfolioWidget({ summary, weather, fxRate, advice }: Props) {
  const isPositive = summary.totalPnl >= 0;
  const pnlColor = isPositive ? "text-emerald-400" : "text-red-400";
  const pnlGlow = isPositive
    ? "[filter:drop-shadow(0_0_8px_rgba(52,211,153,0.5))]"
    : "[filter:drop-shadow(0_0_8px_rgba(248,113,113,0.5))]";

  return (
    <div className="rounded-xl border border-zinc-700/50 bg-gradient-to-b from-zinc-800/80 to-zinc-900 p-4 space-y-3 shadow-[0_4px_24px_rgba(0,0,0,0.5),inset_0_1px_0_rgba(255,255,255,0.07)]">
      <style>{`
        @keyframes drift {
          0%, 100% { transform: translateX(0); }
          50% { transform: translateX(6px); }
        }
      `}</style>
      <div className="flex items-start gap-3">
        {/* 保有資産 */}
        <div className="flex-1">
          <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-0.5">保有資産</p>
          <p className="text-2xl font-bold text-zinc-100 tracking-tight">
            ¥{summary.totalValue.toLocaleString()}
          </p>
          <p className={`text-sm font-mono mt-0.5 ${pnlColor} ${pnlGlow}`}>
            {isPositive ? "+" : ""}¥{summary.totalPnl.toLocaleString()}
            <span className="text-xs ml-1 opacity-80">
              （{isPositive ? "+" : ""}{summary.totalPnlPercent}%）
            </span>
          </p>
        </div>

        <div className="w-px bg-gradient-to-b from-transparent via-zinc-700 to-transparent self-stretch" />

        {/* USD/JPY */}
        <div className="text-center min-w-[80px]">
          <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-0.5">USD/JPY</p>
          <p className="text-xl font-mono font-semibold text-zinc-200">{fxRate.toFixed(1)}</p>
          <p className="text-[10px] text-zinc-600">円</p>
        </div>

        <div className="w-px bg-gradient-to-b from-transparent via-zinc-700 to-transparent self-stretch" />

        {/* 天気 */}
        <div className="text-center min-w-[80px]">
          <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-0.5">{weather.location}</p>
          <WeatherIcon description={weather.description} />
          <p className="text-sm font-medium text-zinc-300">{weather.temp}℃</p>
          <p className="text-[10px] text-zinc-500 mt-0.5">{weather.description}</p>
        </div>
      </div>

      {summary.hasMockData && (
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-orange-400 border border-orange-400/30 bg-orange-400/5 px-1.5 py-0.5 rounded">
            仮データ
          </span>
          <span className="text-[10px] text-zinc-600">実データ連携後に更新されます</span>
        </div>
      )}

      <div className="border-t border-zinc-700/50 pt-3">
        <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1.5">AI ブリーフィング</p>
        <p className="text-xs text-zinc-300 leading-relaxed">{advice}</p>
      </div>
    </div>
  );
}
