"use client";

interface Props {
  usedToday: number;
  remaining: number;
  limit: number;
  usagePercent: number;
}

export function QuotaIndicator({ usedToday, remaining, limit, usagePercent }: Props) {
  const barGradient =
    usagePercent >= 80 ? "from-red-600 to-red-400" :
    usagePercent >= 60 ? "from-orange-500 to-amber-400" :
    "from-emerald-600 to-emerald-400";
  const glowColor =
    usagePercent >= 80 ? "shadow-[0_0_8px_rgba(239,68,68,0.5)]" :
    usagePercent >= 60 ? "shadow-[0_0_8px_rgba(251,146,60,0.5)]" :
    "shadow-[0_0_8px_rgba(52,211,153,0.4)]";

  return (
    <div className="rounded-xl border border-zinc-700/50 bg-gradient-to-b from-zinc-800/80 to-zinc-900 p-4 shadow-[0_4px_20px_rgba(0,0,0,0.4),inset_0_1px_0_rgba(255,255,255,0.06)]">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] text-zinc-500 uppercase tracking-wider">YouTube API Quota</span>
        <span className="text-xs font-mono text-zinc-300">
          {usedToday.toLocaleString()} <span className="text-zinc-600">/ {limit.toLocaleString()}</span>
        </span>
      </div>
      <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden shadow-inner">
        <div
          className={`h-full rounded-full bg-gradient-to-r transition-all ${barGradient} ${glowColor}`}
          style={{ width: `${Math.min(usagePercent, 100)}%` }}
        />
      </div>
      <p className="text-[10px] text-zinc-600 mt-1.5">残り {remaining.toLocaleString()} units</p>
    </div>
  );
}
