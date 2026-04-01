CREATE TABLE youtube_videos (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id text UNIQUE NOT NULL,
  channel_id text NOT NULL,
  channel_title text NOT NULL,
  title text NOT NULL,
  published_at timestamptz NOT NULL,
  thumbnail_url text,

  -- 字幕取得の品質追跡
  transcript_source text CHECK (transcript_source IN (
    'manual_ja', 'auto_ja', 'manual_en', 'auto_en', 'description', 'title_only'
  )),

  -- AI解析結果
  priority_score float CHECK (priority_score >= 0 AND priority_score <= 1),
  summary jsonb,

  -- セマンティック検索用ベクトル
  content_embedding vector(1536),

  -- 品質・コスト管理メタデータ
  analysis_version text DEFAULT 'v1',
  llm_tokens_used integer DEFAULT 0,
  analyzed_at timestamptz,

  created_at timestamptz DEFAULT now()
);

-- 優先度スコア降順インデックス (ダッシュボード表示用)
CREATE INDEX ON youtube_videos (priority_score DESC);

-- チャンネル別最新動画取得インデックス
CREATE INDEX ON youtube_videos (channel_id, published_at DESC);

-- セマンティック類似検索インデックス
CREATE INDEX ON youtube_videos USING ivfflat (content_embedding vector_cosine_ops)
  WITH (lists = 100);

-- ユーザーの興味ベクトル (視聴履歴から自動生成)
CREATE TABLE user_interest_profiles (
  user_id uuid PRIMARY KEY,
  interest_vector vector(1536),
  -- 何本の動画を元に計算したか
  based_on_video_count integer DEFAULT 0,
  updated_at timestamptz DEFAULT now()
);

-- チャンネル設定 (ユーザーごとの重み付け)
CREATE TABLE user_channel_weights (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  channel_id text NOT NULL,
  channel_title text NOT NULL,
  -- 優先度ウェイト (0-1)
  weight float DEFAULT 0.5,
  -- アップロードプレイリストID (APIコール削減)
  uploads_playlist_id text,
  -- 最後にチェックした動画のpublished_at (ポーリング最適化)
  last_checked_at timestamptz,
  created_at timestamptz DEFAULT now(),
  UNIQUE (user_id, channel_id)
);
