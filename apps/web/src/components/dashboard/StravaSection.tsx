"use client";

import type { StravaData, StravaActivity } from "@/app/page";

interface Props {
  data: StravaData;
}

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function ActivityCard({ activity }: { activity: StravaActivity }) {
  return (
    <div className="rounded-lg border border-zinc-700/40 bg-gradient-to-b from-zinc-800/60 to-zinc-900 p-3 shadow-[0_2px_12px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(255,255,255,0.05)]">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-lg shrink-0">{activity.icon}</span>
          <div className="min-w-0">
            <p className="text-sm text-zinc-200 font-medium truncate">{activity.name}</p>
            <p className="text-[10px] text-zinc-500">{activity.date} · {activity.sport}</p>
          </div>
        </div>
        {activity.kudos > 0 && (
          <span className="shrink-0 text-[10px] text-orange-400 font-mono">👍 {activity.kudos}</span>
        )}
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-1">
        {activity.distanceKm != null && (
          <Stat label="距離" value={`${activity.distanceKm} km`} color="text-emerald-400" />
        )}
        <Stat label="時間" value={formatDuration(activity.movingSec)} color="text-sky-400" />
        {activity.elevationM != null && activity.elevationM > 0 && (
          <Stat label="獲得標高" value={`${Math.round(activity.elevationM)} m`} color="text-violet-400" />
        )}
        {activity.avgHeartRate != null && (
          <Stat label="平均心拍" value={`${Math.round(activity.avgHeartRate)} bpm`} color="text-red-400" />
        )}
        {activity.avgSpeedKph != null && (
          <Stat label="平均速度" value={`${activity.avgSpeedKph} km/h`} color="text-zinc-400" />
        )}
        {activity.sufferScore != null && (
          <Stat label="苦しみスコア" value={String(activity.sufferScore)} color="text-orange-400" />
        )}
      </div>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div>
      <p className="text-[9px] text-zinc-600 uppercase tracking-wider">{label}</p>
      <p className={`text-xs font-mono font-semibold ${color}`}>{value}</p>
    </div>
  );
}

export function StravaSection({ data }: Props) {
  if (data.activities.length === 0) {
    return (
      <div className="text-center py-8 text-zinc-600 text-sm">
        <p>アクティビティがありません</p>
        <p className="text-xs mt-1">RailwayにSTRAVA_CLIENT_ID等の環境変数を設定してください</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {data.athlete && (
        <div className="flex items-center gap-2 mb-3">
          {data.athlete.profile && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={data.athlete.profile} alt="" className="w-7 h-7 rounded-full" />
          )}
          <p className="text-xs text-zinc-400">{data.athlete.name}</p>
        </div>
      )}
      {data.activities.map((activity) => (
        <ActivityCard key={activity.id} activity={activity} />
      ))}
    </div>
  );
}
