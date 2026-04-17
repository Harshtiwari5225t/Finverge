from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, Iterable, List

import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


load_dotenv()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")
MARKDOWN_V2_SPECIALS = r"_*[]()~`>#+-=|{}.!"


def escape_markdown_v2(text: str) -> str:
    escaped = text.replace("\\", "\\\\")
    return re.sub(f"([{re.escape(MARKDOWN_V2_SPECIALS)}])", r"\\\1", escaped)


def build_risk_label(level: str) -> str:
    mapping = {
        "Low": "🟢 Low Risk",
        "Medium": "🟡 Medium Risk",
        "High": "🚨 HIGH RISK",
    }
    return mapping.get(level, "⚪ Unknown Risk")


def format_bullets(items: Iterable[str]) -> List[str]:
    values = list(items)
    if not values:
        return ["• No major risk factors returned"]
    return [f"• {escape_markdown_v2(item)}" for item in values]


async def reply_markdown(update: Update, text: str) -> None:
    if update.message:
        await update.message.reply_text(text=text, parse_mode=ParseMode.MARKDOWN_V2)


async def fetch_api_json(path: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(base_url=FASTAPI_BASE_URL, timeout=20.0) as client:
        response = await client.get(path)
        response.raise_for_status()
        return response.json()


def get_ticker_argument(context: ContextTypes.DEFAULT_TYPE) -> str | None:
    if not context.args:
        return None
    ticker = context.args[0].strip().upper()
    return ticker or None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = "\n".join(
        [
            "*FinGPT Risk Bot*",
            "Use `/analyze AAPL` for the full snapshot or `/risk TSLA` for a quick volatility check\\.",
        ]
    )
    await reply_markdown(update, message)


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ticker = get_ticker_argument(context)
    if not ticker:
        await reply_markdown(update, "Usage: `/analyze AAPL`")
        return

    try:
        payload = await fetch_api_json(f"/api/v1/analyze/{ticker}")
    except httpx.HTTPStatusError as exc:
        detail = exc.response.json().get("detail", "Ticker lookup failed.")
        await reply_markdown(update, escape_markdown_v2(f"Could not analyze {ticker}: {detail}"))
        return
    except httpx.HTTPError:
        await reply_markdown(update, "I couldn\\'t reach the local FastAPI service at `http://localhost:8000`\\.")
        return

    risk_metrics = payload.get("risk_metrics", {})
    news_items = payload.get("news", [])[:3]

    lines = [
        "*FinGPT Portfolio & Sentiment Dashboard*",
        f"*Ticker:* {escape_markdown_v2(str(payload.get('ticker', ticker)))}",
        f"*Price:* `${payload.get('price', 0):.2f}`",
        f"*Sentiment:* `{payload.get('overall_sentiment', 0):.1f}/100`",
        "",
        "⚠️ *RISK ANALYSIS* ⚠️",
        f"*Risk Level:* {escape_markdown_v2(build_risk_label(str(risk_metrics.get('risk_level', 'Unknown'))))}",
        f"*Volatility Score:* `{risk_metrics.get('volatility_score', 0):.1f}/10`",
        "*Risk Factors:*",
        *format_bullets(risk_metrics.get("key_risk_factors", [])),
    ]

    if news_items:
        lines.extend(["", "*Latest Headlines:*"])
        for item in news_items:
            headline = str(item.get("headline", "Untitled headline"))
            sentiment = str(item.get("sentiment", "Neutral"))
            lines.append(f"• {escape_markdown_v2(headline)} \\({escape_markdown_v2(sentiment)}\\)")

    await reply_markdown(update, "\n".join(lines))


async def risk_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ticker = get_ticker_argument(context)
    if not ticker:
        await reply_markdown(update, "Usage: `/risk NVDA`")
        return

    try:
        payload = await fetch_api_json(f"/api/v1/risk/{ticker}")
    except httpx.HTTPStatusError as exc:
        detail = exc.response.json().get("detail", "Risk lookup failed.")
        await reply_markdown(update, escape_markdown_v2(f"Could not fetch risk for {ticker}: {detail}"))
        return
    except httpx.HTTPError:
        await reply_markdown(update, "I couldn\\'t reach the local FastAPI service at `http://localhost:8000`\\.")
        return

    lines = [
        f"*Quick Risk Check for* {escape_markdown_v2(str(payload.get('ticker', ticker)))}",
        "⚠️ *RISK ANALYSIS* ⚠️",
        f"*Risk Level:* {escape_markdown_v2(build_risk_label(str(payload.get('risk_level', 'Unknown'))))}",
        f"*Volatility Score:* `{payload.get('volatility_score', 0):.1f}/10`",
        "*Risk Factors:*",
        *format_bullets(payload.get("key_risk_factors", [])),
    ]

    await reply_markdown(update, "\n".join(lines))


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN in environment.")

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("risk", risk_command))
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
