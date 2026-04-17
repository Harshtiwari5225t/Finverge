from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, List, Literal

import feedparser
import pandas as pd
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from api.report_risk import router as report_risk_router
    from api.runtime import API_BASE_PREFIX
except ImportError:  # pragma: no cover - local script fallback
    from report_risk import router as report_risk_router
    from runtime import API_BASE_PREFIX


class RiskAnalysis(BaseModel):
    risk_level: Literal["Low", "Medium", "High"]
    volatility_score: float = Field(..., ge=1, le=10)
    key_risk_factors: List[str]


class StockResponse(BaseModel):
    ticker: str
    price: float
    overall_sentiment: float = Field(..., ge=0, le=100)
    risk_metrics: RiskAnalysis
    news: List[Dict[str, Any]]


class RiskOnlyResponse(BaseModel):
    ticker: str
    volatility_score: float = Field(..., ge=1, le=10)
    risk_level: Literal["Low", "Medium", "High"]
    key_risk_factors: List[str]


app = FastAPI(
    title="FinGPT Portfolio & Sentiment API",
    version="1.0.0",
    description="Free stock analysis, sentiment scoring, volatility risk, and PDF report risk extraction.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report_risk_router)


TICKER_PATTERN = re.compile(r"^[A-Z0-9.\-]{1,20}$")
POSITIVE_KEYWORDS = {
    "beat",
    "beats",
    "bullish",
    "buyback",
    "expansion",
    "growth",
    "guidance raised",
    "outperform",
    "profit",
    "surge",
    "upgrade",
}
NEGATIVE_KEYWORDS = {
    "bearish",
    "cut",
    "cuts",
    "default",
    "decline",
    "downgrade",
    "fall",
    "falls",
    "investigation",
    "lawsuit",
    "miss",
    "misses",
    "recall",
    "risk",
    "warning",
}


def normalize_ticker(ticker: str) -> str:
    cleaned = ticker.strip().upper()
    if not cleaned or not TICKER_PATTERN.fullmatch(cleaned):
        raise HTTPException(
            status_code=400,
            detail="Ticker must be 1-20 characters using letters, numbers, dots, or dashes.",
        )
    return cleaned


def classify_headline_sentiment(headline: str) -> tuple[str, float]:
    text = headline.lower()
    positive_hits = sum(keyword in text for keyword in POSITIVE_KEYWORDS)
    negative_hits = sum(keyword in text for keyword in NEGATIVE_KEYWORDS)
    raw_score = positive_hits - negative_hits

    if raw_score > 0:
        return "Positive", min(raw_score / 3, 1.0)
    if raw_score < 0:
        return "Negative", max(raw_score / 3, -1.0)
    return "Neutral", 0.0


def aggregate_sentiment(news: List[Dict[str, Any]]) -> float:
    if not news:
        return 50.0

    label_to_score = {"Positive": 1.0, "Neutral": 0.0, "Negative": -1.0}
    average = sum(label_to_score.get(item["sentiment"], 0.0) for item in news) / len(news)
    return round(max(0.0, min(100.0, (average + 1.0) * 50.0)), 2)


def normalize_volatility_score(daily_volatility: float) -> float:
    # Typical daily volatilities cluster below 4%; scaling by 250 spreads the values well into a 1-10 score.
    normalized = daily_volatility * 250
    return round(max(1.0, min(10.0, normalized)), 2)


def evaluate_risk(sentiment_score: float, volatility_score: float) -> RiskAnalysis:
    risk_factors: List[str] = []

    if volatility_score > 7:
        risk_factors.append("High recent price fluctuation")
    elif volatility_score > 4.5:
        risk_factors.append("Moderate short-term volatility")

    if sentiment_score < 30:
        risk_factors.append("Negative news volume increasing")
    elif sentiment_score < 45:
        risk_factors.append("Market sentiment remains cautious")

    if volatility_score > 6 and sentiment_score < 40:
        risk_factors.append("Bearish headlines are amplifying market swings")

    if not risk_factors:
        risk_factors.append("Price action and headlines remain relatively stable")

    if volatility_score > 7 or sentiment_score < 30:
        risk_level: Literal["Low", "Medium", "High"] = "High"
    elif volatility_score > 4 or sentiment_score < 45:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return RiskAnalysis(
        risk_level=risk_level,
        volatility_score=round(volatility_score, 2),
        key_risk_factors=risk_factors,
    )


def _fetch_stock_data_sync(ticker: str) -> float:
    stock = yf.Ticker(ticker)

    try:
        fast_info = getattr(stock, "fast_info", {}) or {}
        last_price = fast_info.get("lastPrice") or fast_info.get("regularMarketPrice")
        if last_price:
            return round(float(last_price), 2)
    except Exception:
        pass

    history = stock.history(period="5d", interval="1d", auto_adjust=False)
    if history.empty or "Close" not in history:
        raise ValueError(f"Unable to find market data for ticker '{ticker}'.")

    closes = history["Close"].dropna()
    if closes.empty:
        raise ValueError(f"Unable to find a closing price for ticker '{ticker}'.")

    return round(float(closes.iloc[-1]), 2)


async def fetch_stock_data(ticker: str) -> float:
    return await asyncio.to_thread(_fetch_stock_data_sync, ticker)


def _fetch_news_sync(ticker: str) -> List[Dict[str, Any]]:
    feed_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    parsed_feed = feedparser.parse(feed_url)

    news_items: List[Dict[str, Any]] = []
    for index, entry in enumerate(parsed_feed.entries[:8]):
        headline = (entry.get("title") or "").strip()
        if not headline:
            continue

        sentiment_label, _ = classify_headline_sentiment(headline)
        news_items.append(
            {
                "id": f"{ticker}-{index}",
                "headline": headline,
                "sentiment": sentiment_label,
            }
        )

    return news_items


async def fetch_news(ticker: str) -> List[Dict[str, Any]]:
    return await asyncio.to_thread(_fetch_news_sync, ticker)


def _calculate_volatility_sync(ticker: str) -> float:
    closes_frame = yf.download(
        tickers=ticker,
        period="2mo",
        interval="1d",
        progress=False,
        auto_adjust=False,
        threads=False,
    )

    if closes_frame.empty or "Close" not in closes_frame:
        raise ValueError(f"Unable to download price history for ticker '{ticker}'.")

    close_prices = closes_frame["Close"].dropna()
    if isinstance(close_prices, pd.DataFrame):
        close_prices = close_prices.iloc[:, 0]

    close_prices = close_prices.tail(30)
    daily_returns = close_prices.pct_change().dropna()
    if daily_returns.empty:
        raise ValueError(f"Insufficient price history to calculate volatility for '{ticker}'.")

    daily_volatility = float(daily_returns.std())
    return normalize_volatility_score(daily_volatility)


async def calculate_volatility(ticker: str) -> float:
    return await asyncio.to_thread(_calculate_volatility_sync, ticker)


@app.get("/", include_in_schema=False)
async def root() -> Dict[str, str]:
    return {"message": "FinGPT hackathon API is running."}


@app.get("/health", include_in_schema=False)
async def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}


@app.get(f"{API_BASE_PREFIX}/v1/analyze/{{ticker}}", response_model=StockResponse)
async def analyze_ticker(ticker: str) -> StockResponse:
    normalized_ticker = normalize_ticker(ticker)

    try:
        price, news, volatility_score = await asyncio.gather(
            fetch_stock_data(normalized_ticker),
            fetch_news(normalized_ticker),
            calculate_volatility(normalized_ticker),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to analyze ticker '{normalized_ticker}'.") from exc

    overall_sentiment = aggregate_sentiment(news)
    risk_metrics = evaluate_risk(overall_sentiment, volatility_score)

    return StockResponse(
        ticker=normalized_ticker,
        price=price,
        overall_sentiment=overall_sentiment,
        risk_metrics=risk_metrics,
        news=news,
    )


@app.get(f"{API_BASE_PREFIX}/v1/risk/{{ticker}}", response_model=RiskOnlyResponse)
async def analyze_risk_only(ticker: str) -> RiskOnlyResponse:
    normalized_ticker = normalize_ticker(ticker)

    try:
        volatility_score = await calculate_volatility(normalized_ticker)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to calculate risk for ticker '{normalized_ticker}'.") from exc

    risk_metrics = evaluate_risk(sentiment_score=50.0, volatility_score=volatility_score)
    filtered_factors = [
        factor
        for factor in risk_metrics.key_risk_factors
        if "sentiment" not in factor.lower() and "headlines" not in factor.lower()
    ]

    if not filtered_factors:
        filtered_factors = ["Price volatility is the dominant current risk signal"]

    return RiskOnlyResponse(
        ticker=normalized_ticker,
        volatility_score=volatility_score,
        risk_level=risk_metrics.risk_level,
        key_risk_factors=filtered_factors,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
