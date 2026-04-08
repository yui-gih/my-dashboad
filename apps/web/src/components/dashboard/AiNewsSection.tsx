"use client";

import { useState } from "react";
import type { AiArticle } from "@/app/page";

interface Props {
  articles: AiArticle[];
}

const SOURCE_COLORS: Record<string, string> = {
  "ledge.ai": "bg-blue-500/15 text-blue-400 border-blue-500/40",
};

function formatDate(dateStr: string | null) {
  if (!dateStr) return "";
  try {
    return new Date(dateStr).toLocaleDateString("ja-JP", { month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

function ArticleCard({ article }: { article: AiArticle }) {
  const sourceColor = SOURCE_COLORS[article.source] ?? "bg-zinc-700/30 text-zinc-400 border-zinc-600/40";
  return (
    <a
      key={article.id}
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block rounded-lg border border-zinc-700/40 bg-gradient-to-b from-zinc-800/60 to-zinc-900 p-3 hover:border-zinc-600/60 hover:-translate-y-px transition-all duration-150 shadow-[0_2px_12px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(255,255,255,0.05)]"
    >
      <div className="flex items-start gap-2">
        <span className={`shrink-0 text-[10px] border px-1.5 py-0.5 rounded mt-0.5 whitespace-nowrap ${sourceColor}`}>
          {article.source}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-zinc-200 line-clamp-2 leading-snug">{article.title}</p>
          {article.summary && article.summary !== article.title && (
            <p className="text-xs text-zinc-500 mt-1 line-clamp-2 leading-relaxed">
              {article.summary.replace(/<[^>]*>/g, "")}
            </p>
          )}
        </div>
        <span className="shrink-0 text-[10px] text-zinc-600 font-mono mt-0.5" suppressHydrationWarning>
          {formatDate(article.publishedAt)}
        </span>
      </div>
    </a>
  );
}

export function AiNewsSection({ articles }: Props) {
  const [query, setQuery] = useState("");

  const filtered = query.trim()
    ? articles.filter((a) => {
        const q = query.trim().toLowerCase();
        return (
          a.title.toLowerCase().includes(q) ||
          (a.summary ?? "").toLowerCase().includes(q)
        );
      })
    : articles;

  return (
    <div className="space-y-4">
      {/* 検索欄 */}
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="キーワードで絞り込み（例: Claude、GPT、LLM）"
          className="w-full rounded-lg border border-zinc-700/50 bg-zinc-800/80 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 outline-none focus:border-zinc-500 focus:ring-1 focus:ring-zinc-500/30 shadow-[inset_0_1px_3px_rgba(0,0,0,0.3)] transition-colors"
        />
        {query && (
          <button
            onClick={() => setQuery("")}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 text-xs"
          >
            ✕
          </button>
        )}
      </div>

      {/* 件数表示 */}
      {query.trim() && (
        <p className="text-[10px] text-zinc-500 px-1">
          {filtered.length} 件ヒット
        </p>
      )}

      {/* 記事一覧 */}
      {filtered.length === 0 ? (
        <div className="text-center py-12 text-zinc-600 text-sm">
          {query.trim() ? "該当する記事が見つかりませんでした" : "AI ニュースを取得できませんでした"}
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      )}
    </div>
  );
}
