"""
ポートフォリオ + 気象エージェント。
株価・為替・天気を統合してコンテキストアウェアなAIアドバイスを生成する。
"""
import json
import logging
from datetime import datetime, timezone
from typing import TypedDict

import httpx
from anthropic import AsyncAnthropic
from langgraph.graph import StateGraph, END

from src.config import settings
from src.db import get_supabase

logger = logging.getLogger(__name__)
client = AsyncAnthropic(api_key=settings.anthropic_api_key)

# デフォルトユーザーID (開発用)
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


class PortfolioState(TypedDict):
    holdings: list[dict]
    prices: dict[str, float]     # ticker → 現在価格
    weather: dict
    fx_rate: float               # USD/JPY
    portfolio_summary: dict
    advice: str


def fetch_holdings(state: PortfolioState) -> dict:
    db = get_supabase()
    result = db.table("portfolio_holdings").select("*").eq(
        "user_id", DEFAULT_USER_ID
    ).execute()
    return {"holdings": result.data}


async def fetch_market_data(state: PortfolioState) -> dict:
    """Yahoo Finance の非公式 API で株価・為替を取得"""
    tickers = [h["ticker"] for h in state["holdings"]]
    prices = {}
    fx_rate = 150.0  # デフォルト値

    async with httpx.AsyncClient() as http:
        # 為替レート (USD/JPY)
        try:
            resp = await http.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/USDJPY=X",
                params={"interval": "1m", "range": "1d"},
                timeout=10,
            )
            data = resp.json()
            fx_rate = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        except Exception as e:
            logger.warning(f"FX rate fetch failed: {e}")

        # 株価 (バッチ取得)
        for ticker in tickers:
            try:
                resp = await http.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                    params={"interval": "1d", "range": "1d"},
                    timeout=10,
                )
                data = resp.json()
                price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
                prices[ticker] = price
            except Exception as e:
                logger.warning(f"Price fetch failed for {ticker}: {e}")

    return {"prices": prices, "fx_rate": fx_rate}


async def fetch_weather(state: PortfolioState) -> dict:
    """OpenWeatherMap API で現在地の気象データを取得"""
    weather = {"description": "不明", "temp": 20, "location": "東京"}
    if not settings.openweather_api_key:
        return {"weather": weather}
    try:
        async with httpx.AsyncClient() as http:
            resp = await http.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": "Tokyo,jp",
                    "appid": settings.openweather_api_key,
                    "units": "metric",
                    "lang": "ja",
                },
                timeout=10,
            )
            data = resp.json()
            weather = {
                "description": data["weather"][0]["description"],
                "temp": round(data["main"]["temp"]),
                "location": data["name"],
            }
    except Exception as e:
        logger.warning(f"Weather fetch failed: {e}")
    return {"weather": weather}


def calculate_portfolio_summary(state: PortfolioState) -> dict:
    """保有資産の時価総額と損益を計算"""
    total_value = 0.0
    total_cost = 0.0
    movers = []
    fx = state["fx_rate"]

    for h in state["holdings"]:
        ticker = h["ticker"]
        qty = float(h["quantity"])
        avg_cost = float(h["average_cost"])
        price = state["prices"].get(ticker)
        if price is None:
            price = avg_cost  # フォールバック: 取得コストで代替

        # JPY 換算
        multiplier = fx if h["currency"] == "USD" else 1.0
        value_jpy = price * qty * multiplier
        cost_jpy = avg_cost * qty * multiplier
        pnl_pct = (price - avg_cost) / avg_cost * 100 if avg_cost > 0 else 0.0

        total_value += value_jpy
        total_cost += cost_jpy
        movers.append({"ticker": ticker, "change": pnl_pct})

    movers.sort(key=lambda x: abs(x["change"]), reverse=True)
    total_pnl = total_value - total_cost
    total_pnl_pct = total_pnl / total_cost * 100 if total_cost > 0 else 0.0

    holdings_detail = []
    fx = state["fx_rate"]
    for h in state["holdings"]:
        ticker = h["ticker"]
        qty = float(h["quantity"])
        avg_cost = float(h["average_cost"])
        price = state["prices"].get(ticker, avg_cost)
        multiplier = fx if h["currency"] == "USD" else 1.0
        holdings_detail.append({
            "ticker": ticker,
            "quantity": qty,
            "averageCost": avg_cost,
            "currentPrice": price,
            "currency": h["currency"],
            "valueJpy": round(price * qty * multiplier),
            "pnlPercent": round((price - avg_cost) / avg_cost * 100, 2) if avg_cost > 0 else 0.0,
        })

    summary = {
        "totalValue": round(total_value),
        "totalCost": round(total_cost),
        "totalPnl": round(total_pnl),
        "totalPnlPercent": round(total_pnl_pct, 2),
        "topMover": movers[0] if movers else None,
        "holdings": holdings_detail,
        "hasMockData": any(h.get("is_mock") for h in state["holdings"]),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    return {"portfolio_summary": summary}


async def generate_advice(state: PortfolioState) -> dict:
    """天気・為替・資産の3要素を統合したAIアドバイスを生成"""
    summary = state["portfolio_summary"]
    weather = state["weather"]
    prompt = f"""
現在の状況:
- 天気: {weather['description']}（気温{weather['temp']}℃、{weather['location']}）
- USD/JPY: {state['fx_rate']:.1f}円
- 保有資産の時価総額: {summary['totalValue']:,}円（損益: {summary['totalPnlPercent']:+.2f}%）
- 最大変動銘柄: {summary['topMover']['ticker'] if summary['topMover'] else 'なし'}

ユーザーへの朝のブリーフィングを150文字以内で生成してください。
天気・為替・資産の3要素を必ず関連づけること。具体的なアクションを提案すること。
"""
    try:
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return {"advice": response.content[0].text.strip()}
    except Exception as e:
        logger.warning(f"AI advice generation failed: {e}")
        pnl = summary.get('totalPnlPercent', 0)
        fx = state['fx_rate']
        temp = weather.get('temp', '?')
        return {"advice": f"本日の東京は{temp}℃。USD/JPY {fx:.1f}円。資産損益 {pnl:+.2f}%。AIアドバイスは一時利用不可です。"}


def build_portfolio_agent():
    workflow = StateGraph(PortfolioState)
    workflow.add_node("fetch_holdings", fetch_holdings)
    workflow.add_node("fetch_market_data", fetch_market_data)
    workflow.add_node("fetch_weather", fetch_weather)
    workflow.add_node("calculate_summary", calculate_portfolio_summary)
    workflow.add_node("generate_advice", generate_advice)

    workflow.set_entry_point("fetch_holdings")
    workflow.add_edge("fetch_holdings", "fetch_market_data")
    workflow.add_edge("fetch_market_data", "fetch_weather")
    workflow.add_edge("fetch_weather", "calculate_summary")
    workflow.add_edge("calculate_summary", "generate_advice")
    workflow.add_edge("generate_advice", END)

    return workflow.compile()


portfolio_agent = build_portfolio_agent()


async def run_portfolio_agent() -> dict:
    initial: PortfolioState = {
        "holdings": [],
        "prices": {},
        "weather": {},
        "fx_rate": 150.0,
        "portfolio_summary": {},
        "advice": "",
    }
    result = await portfolio_agent.ainvoke(initial)
    return {
        "portfolio": result["portfolio_summary"],
        "weather": result["weather"],
        "advice": result["advice"],
        "fxRate": result["fx_rate"],
    }
