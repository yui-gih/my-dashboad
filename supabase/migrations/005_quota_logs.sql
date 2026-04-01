-- YouTube API クォータ消費ログ
CREATE TABLE quota_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  date date NOT NULL DEFAULT CURRENT_DATE,
  units integer NOT NULL,
  operation text NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- 日付別クォータ合計を高速取得するインデックス
CREATE INDEX ON quota_logs (date);

-- 今日の消費量を返すビュー
CREATE OR REPLACE VIEW quota_usage_today AS
  SELECT
    COALESCE(SUM(units), 0) AS units_used,
    10000 - COALESCE(SUM(units), 0) AS units_remaining
  FROM quota_logs
  WHERE date = CURRENT_DATE;

-- エージェント実行ログ
CREATE TABLE agent_run_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_name text NOT NULL,
  status text CHECK (status IN ('running', 'success', 'error')),
  steps jsonb DEFAULT '[]',
  error_message text,
  started_at timestamptz DEFAULT now(),
  finished_at timestamptz
);
