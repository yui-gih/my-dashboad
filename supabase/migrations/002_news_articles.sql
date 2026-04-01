CREATE TABLE news_articles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  url text UNIQUE NOT NULL,
  source text NOT NULL,
  published_at timestamptz,
  -- セマンティック重複排除用ベクトル (text-embedding-3-small: 1536次元)
  embedding vector(1536),
  -- LLM生成の構造化要約
  summary jsonb,
  -- 日本市場への影響度 (0-1)
  impact_score float,
  -- 速報性分類
  urgency text CHECK (urgency IN ('breaking', 'today', 'background')),
  created_at timestamptz DEFAULT now()
);

-- IVFFlat インデックス: コサイン類似度検索を高速化
CREATE INDEX ON news_articles USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- 重複排除のためのRPC関数
CREATE OR REPLACE FUNCTION match_news_articles(
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id uuid,
  title text,
  url text,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    id, title, url,
    1 - (embedding <=> query_embedding) AS similarity
  FROM news_articles
  WHERE 1 - (embedding <=> query_embedding) > match_threshold
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;
