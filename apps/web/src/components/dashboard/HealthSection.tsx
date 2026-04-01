"use client";

import type { HealthRecord } from "@/app/page";

interface Props {
  records: HealthRecord[];
}

const AGENT_URL = process.env.NEXT_PUBLIC_AGENT_URL ?? "http://localhost:8000";

function Ring({
  value,
  max,
  color,
  size = 64,
}: {
  value: number;
  max: number;
  color: string;
  size?: number;
}) {
  const r = (size - 8) / 2;
  const circ = 2 * Math.PI * r;
  const pct = Math.min(value / max, 1);
  const dash = pct * circ;
  return (
    <svg width={size} height={size} className="-rotate-90">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={6} />
      <circle
        cx={size / 2} cy={size / 2} r={r}
        fill="none"
        stroke={color}
        strokeWidth={6}
        strokeDasharray={`${dash} ${circ}`}
        strokeLinecap="round"
        style={{ filter: `drop-shadow(0 0 4px ${color})` }}
      />
    </svg>
  );
}

interface MetricCardProps {
  icon: string;
  label: string;
  value: number | null;
  unit: string;
  max: number;
  color: string;
  ringColor: string;
}

function MetricCard({ icon, label, value, unit, max, color, ringColor }: MetricCardProps) {
  return (
    <div className="rounded-xl border border-zinc-700/50 bg-gradient-to-b from-zinc-800/80 to-zinc-900 p-4 shadow-[0_4px_20px_rgba(0,0,0,0.4),inset_0_1px_0_rgba(255,255,255,0.06)] flex items-center gap-4">
      <div className="relative shrink-0">
        <Ring value={value ?? 0} max={max} color={ringColor} size={60} />
        <span className="absolute inset-0 flex items-center justify-center text-lg">{icon}</span>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[10px] text-zinc-500 uppercase tracking-wider">{label}</p>
        {value != null ? (
          <p className={`text-xl font-bold leading-tight ${color}`}>
            {typeof value === "number" && !Number.isInteger(value)
              ? value.toFixed(1)
              : value.toLocaleString()}
            <span className="text-xs font-normal text-zinc-500 ml-1">{unit}</span>
          </p>
        ) : (
          <p className="text-sm text-zinc-600">–</p>
        )}
      </div>
    </div>
  );
}

function SetupGuide() {
  const endpoint = `${AGENT_URL}/api/health/data`;
  return (
    <div className="rounded-xl border border-zinc-700/50 bg-gradient-to-b from-zinc-800/60 to-zinc-900 p-5 shadow-[0_4px_20px_rgba(0,0,0,0.4),inset_0_1px_0_rgba(255,255,255,0.05)] space-y-4">
      <div className="flex items-center gap-2">
        <span className="text-lg">📱</span>
        <p className="text-sm font-semibold text-zinc-200">iPhone ショートカットで連携する</p>
      </div>
      <p className="text-xs text-zinc-500 leading-relaxed">
        「ショートカット」アプリから毎日自動でヘルスデータを送信するように設定できます。
      </p>

      <ol className="space-y-3 text-xs text-zinc-400">
        <li className="flex gap-2">
          <span className="shrink-0 w-5 h-5 rounded-full bg-zinc-700 text-zinc-300 flex items-center justify-center text-[10px] font-bold">1</span>
          <span>ショートカットアプリ → 新規ショートカット作成</span>
        </li>
        <li className="flex gap-2">
          <span className="shrink-0 w-5 h-5 rounded-full bg-zinc-700 text-zinc-300 flex items-center justify-center text-[10px] font-bold">2</span>
          <div>
            <span>以下のアクションを追加:</span>
            <ul className="mt-1.5 space-y-1 pl-2 text-zinc-500">
              <li>「ヘルスケアサンプルを取得」→ 歩数 (今日)</li>
              <li>「ヘルスケアサンプルを取得」→ 睡眠解析 (昨夜)</li>
              <li>「ヘルスケアサンプルを取得」→ 心拍数 (今日・平均)</li>
              <li>「ヘルスケアサンプルを取得」→ アクティブエネルギー (今日)</li>
            </ul>
          </div>
        </li>
        <li className="flex gap-2">
          <span className="shrink-0 w-5 h-5 rounded-full bg-zinc-700 text-zinc-300 flex items-center justify-center text-[10px] font-bold">3</span>
          <div className="space-y-1">
            <span>「URLの内容を取得」アクションを追加:</span>
            <div className="mt-1.5 rounded-lg border border-zinc-700 bg-zinc-950 p-2.5 font-mono text-[10px] text-zinc-400 break-all select-all">
              POST {endpoint}
            </div>
            <p className="text-zinc-600">メソッド: POST / 本文の種類: JSON</p>
          </div>
        </li>
        <li className="flex gap-2">
          <span className="shrink-0 w-5 h-5 rounded-full bg-zinc-700 text-zinc-300 flex items-center justify-center text-[10px] font-bold">4</span>
          <div className="space-y-1">
            <span>JSON 本文の例:</span>
            <div className="mt-1.5 rounded-lg border border-zinc-700 bg-zinc-950 p-2.5 font-mono text-[10px] text-zinc-400 whitespace-pre-wrap">
{`{
  "date": "<今日の日付>",
  "steps": <歩数>,
  "sleepHours": <睡眠時間>,
  "heartRateAvg": <平均心拍数>,
  "activeCalories": <消費カロリー>,
  "exerciseMinutes": <運動分数>,
  "standHours": <スタンド時間>
}`}
            </div>
          </div>
        </li>
        <li className="flex gap-2">
          <span className="shrink-0 w-5 h-5 rounded-full bg-zinc-700 text-zinc-300 flex items-center justify-center text-[10px] font-bold">5</span>
          <span>オートメーション → 毎朝指定時刻に自動実行するよう設定</span>
        </li>
      </ol>
    </div>
  );
}

function WeekChart({ records }: { records: HealthRecord[] }) {
  if (records.length < 2) return null;
  const maxSteps = Math.max(...records.map((r) => r.steps ?? 0), 10000);
  const sorted = [...records].sort((a, b) => a.date.localeCompare(b.date));
  return (
    <div className="rounded-xl border border-zinc-700/50 bg-gradient-to-b from-zinc-800/80 to-zinc-900 p-4 shadow-[0_4px_20px_rgba(0,0,0,0.4),inset_0_1px_0_rgba(255,255,255,0.06)]">
      <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-3">歩数 (7日間)</p>
      <div className="flex items-end gap-1.5 h-16">
        {sorted.map((r) => {
          const pct = (r.steps ?? 0) / maxSteps;
          const isToday = r.date === new Date().toISOString().slice(0, 10);
          return (
            <div key={r.date} className="flex-1 flex flex-col items-center gap-1">
              <div className="w-full relative flex items-end" style={{ height: "48px" }}>
                <div
                  className={`w-full rounded-sm transition-all ${isToday ? "bg-emerald-500/70" : "bg-zinc-600/60"}`}
                  style={{ height: `${Math.max(pct * 48, 2)}px`, boxShadow: isToday ? "0 0 6px rgba(52,211,153,0.4)" : undefined }}
                />
              </div>
              <span className="text-[8px] text-zinc-600 font-mono">
                {r.date.slice(5).replace("-", "/")}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function HealthSection({ records }: Props) {
  const today = records[0] ?? null;
  const hasData = records.length > 0;

  return (
    <div className="space-y-4">
      {hasData && today && (
        <>
          <p className="text-[10px] text-zinc-500 uppercase tracking-wider px-1">
            今日のデータ — {today.date}
          </p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <MetricCard
              icon="🚶"
              label="歩数"
              value={today.steps}
              unit="歩"
              max={10000}
              color="text-emerald-400"
              ringColor="#34d399"
            />
            <MetricCard
              icon="😴"
              label="睡眠"
              value={today.sleepHours}
              unit="h"
              max={8}
              color="text-indigo-400"
              ringColor="#818cf8"
            />
            <MetricCard
              icon="❤️"
              label="心拍数"
              value={today.heartRateAvg}
              unit="bpm"
              max={100}
              color="text-red-400"
              ringColor="#f87171"
            />
            <MetricCard
              icon="🔥"
              label="消費カロリー"
              value={today.activeCalories}
              unit="kcal"
              max={600}
              color="text-orange-400"
              ringColor="#fb923c"
            />
            <MetricCard
              icon="🏃"
              label="運動時間"
              value={today.exerciseMinutes}
              unit="分"
              max={30}
              color="text-sky-400"
              ringColor="#38bdf8"
            />
            <MetricCard
              icon="🧍"
              label="スタンド"
              value={today.standHours}
              unit="h"
              max={12}
              color="text-violet-400"
              ringColor="#a78bfa"
            />
          </div>

          {today.weight != null && (
            <div className="rounded-xl border border-zinc-700/50 bg-gradient-to-b from-zinc-800/80 to-zinc-900 p-4 shadow-[0_4px_20px_rgba(0,0,0,0.4),inset_0_1px_0_rgba(255,255,255,0.06)] flex items-center gap-3">
              <span className="text-2xl">⚖️</span>
              <div>
                <p className="text-[10px] text-zinc-500 uppercase tracking-wider">体重</p>
                <p className="text-xl font-bold text-zinc-200">
                  {today.weight.toFixed(1)}<span className="text-xs font-normal text-zinc-500 ml-1">kg</span>
                </p>
              </div>
            </div>
          )}

          <WeekChart records={records} />
        </>
      )}

      <SetupGuide />
    </div>
  );
}
