CREATE TABLE portfolio_holdings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  ticker text NOT NULL,
  quantity decimal NOT NULL,
  average_cost decimal NOT NULL,
  currency text DEFAULT 'JPY',
  -- 仮データから実データへの移行フラグ
  is_mock boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  UNIQUE (user_id, ticker)
);

-- デフォルト仮データ (開発用)
INSERT INTO portfolio_holdings (user_id, ticker, quantity, average_cost, currency, is_mock) VALUES
  ('00000000-0000-0000-0000-000000000001', '7203.T', 100, 2500.0, 'JPY', true),
  ('00000000-0000-0000-0000-000000000001', '9984.T', 50, 6800.0, 'JPY', true),
  ('00000000-0000-0000-0000-000000000001', 'AAPL',   10, 180.0,  'USD', true);
