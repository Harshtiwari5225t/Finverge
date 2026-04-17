# FinVerge AI

FinVerge AI is a hackathon-ready portfolio, sentiment, and risk dashboard for Indian and global equities.

It combines:

- a premium animated React + TypeScript + Tailwind frontend
- a free-data FastAPI backend powered by `yfinance`, `feedparser`, and pandas
- a PDF risk-extraction endpoint for annual reports
- a Telegram bot for stock and risk alerts

## Demo Highlights

- One-time onboarding walkthrough for first-time users
- Demo-money portfolio wallet for judge presentations
- Indian stock support with tickers like `RELIANCE.NS`, `TCS.NS`, and `INFY.NS`
- AI sentiment gauge, deep risk analyzer, and portfolio-level storytelling
- Frontend and backend prepared to live in the same Vercel repo

## Tech Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, Lucide React
- Backend: FastAPI, pandas, yfinance, feedparser, PyPDF2
- AI tooling: LangChain Core, LangChain OpenAI
- Bot: python-telegram-bot, httpx

## Local Development

### 1. Start the backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

### 2. Start the frontend

```bash
npm install
npm run dev
```

Open:

- Frontend: `http://127.0.0.1:5173`
- Backend docs: `http://127.0.0.1:8000/docs`

## Deployment Notes

The repository includes:

- `vercel.json` for Vite + Python function deployment
- `api/index.py` as the Vercel Python runtime entrypoint
- environment-aware API prefixing so local development uses `/api/...` and Vercel does not double-prefix routes

## Main Project Files

- `frontend/FinGPTRiskDashboard.tsx`: judge-facing dashboard experience
- `api/main.py`: stock analysis and risk endpoints
- `api/report_risk.py`: PDF report risk extraction
- `bot/risk_alert_bot.py`: Telegram bot integration

## Example Tickers

- `RELIANCE.NS`
- `TCS.NS`
- `INFY.NS`
- `HDFCBANK.NS`
- `AAPL`
- `TSLA`
