FROM python:3.11-slim

WORKDIR /app

# uv インストール
RUN pip install uv

# 依存関係を先にコピー (キャッシュ最適化)
COPY pyproject.toml .
RUN uv sync --no-dev

# ソースコード
COPY src/ ./src/

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
