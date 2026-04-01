"use client";

import type { NewsArticle } from "@repo/types";

interface Props {
  articles: NewsArticle[];
}

const URGENCY_CONFIG = {
  breaking: { label: "速報", color: "bg-red-500/15 text-red-400 border-red-500/40 shadow-[0_0_8px_rgba(239,68,68,0.2)]" },
  today:    { label: "本日", color: "bg-blue-500/15 text-blue-400 border-blue-500/40" },
  background: { label: "背景", color: "bg-zinc-700/30 text-zinc-500 border-zinc-600/30" },
};

const DIRECTION_ICON = {
  positive: { icon: "↑", color: "text-emerald-400" },
  negative: { icon: "↓", color: "text-red-400" },
  neutral:  { icon: "→", color: "text-zinc-400" },
};

export function NewsSection({ articles }: Props) {
  return (
    <div className="space-y-2">
      {articles.map((article) => {
        const urgency = URGENCY_CONFIG[article.urgency] ?? URGENCY_CONFIG.background;
        const impact = article.japanMarketImpact;
        const dir = DIRECTION_ICON[impact.direction] ?? DIRECTION_ICON.neutral;

        return (
          <a
            key={article.id}
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block rounded-lg border border-zinc-700/40 bg-gradient-to-b from-zinc-800/60 to-zinc-900 p-3 hover:border-zinc-600/60 hover:-translate-y-px transition-all duration-150 shadow-[0_2px_12px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(255,255,255,0.05)]"
          >
            <div className="flex items-start gap-2">
              <span className={`shrink-0 text-[10px] border px-1.5 py-0.5 rounded mt-0.5 ${urgency.color}`}>
                {urgency.label}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-[10px] text-zinc-600 mb-0.5">{article.source}</p>
                <p className="text-sm text-zinc-200 line-clamp-1 leading-snug">{article.title}</p>
                {article.summaryLines && (
                  <ul className="text-xs text-zinc-500 mt-1 space-y-0.5">
                    {article.summaryLines.map((line, i) => (
                      <li key={i}>• {line}</li>
                    ))}
                  </ul>
                )}
              </div>
              <div className="shrink-0 text-right">
                <p className={`text-sm font-mono font-semibold ${dir.color}`}>{dir.icon}</p>
                <p className="text-[10px] text-zinc-600">{Math.round(impact.score * 100)}%</p>
              </div>
            </div>
          </a>
        );
      })}
    </div>
  );
}
