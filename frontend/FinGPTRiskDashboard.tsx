import React, { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BriefcaseBusiness,
  Clock3,
  Gauge,
  IndianRupee,
  Landmark,
  Loader2,
  Plus,
  Search,
  ShieldAlert,
  Sparkles,
  Trash2,
  TrendingDown,
  TrendingUp,
  Wallet,
  X,
} from "lucide-react";

interface NewsItem {
  id: string;
  headline: string;
  sentiment: "Positive" | "Negative" | "Neutral";
}

interface RiskMetrics {
  riskLevel: "Low" | "Medium" | "High";
  volatilityScore: number;
  riskFactors: string[];
}

interface DashboardData {
  ticker: string;
  currentPrice: number;
  averageSentiment: number;
  risk: RiskMetrics;
  news: NewsItem[];
}

interface PortfolioHolding {
  id: string;
  ticker: string;
  label: string;
  quantity: number;
  buyPrice: number;
  lastKnownPrice: number;
  riskLevel: RiskMetrics["riskLevel"];
  averageSentiment: number;
  currency: "INR" | "USD";
}

interface DashboardFetchResult {
  snapshot: DashboardData;
  dailyChange: number;
}

const AUTO_REFRESH_SECONDS = 45;
const INITIAL_DEMO_CASH_INR = 1_000_000;
const USD_TO_INR = 83;
const OVERVIEW_STORAGE_KEY = "finverge-ai-overview-seen";
const PORTFOLIO_STORAGE_KEY = "finverge-ai-demo-portfolio";

const FEATURED_TICKERS = [
  { ticker: "RELIANCE.NS", label: "Reliance" },
  { ticker: "TCS.NS", label: "TCS" },
  { ticker: "INFY.NS", label: "Infosys" },
  { ticker: "HDFCBANK.NS", label: "HDFC Bank" },
  { ticker: "SBIN.NS", label: "SBI" },
  { ticker: "AAPL", label: "Apple" },
];

const DEMO_PORTFOLIO: PortfolioHolding[] = [
  {
    id: "demo-reliance",
    ticker: "RELIANCE.NS",
    label: "Reliance",
    quantity: 18,
    buyPrice: 2890,
    lastKnownPrice: 2940,
    riskLevel: "Medium",
    averageSentiment: 61,
    currency: "INR",
  },
  {
    id: "demo-tcs",
    ticker: "TCS.NS",
    label: "TCS",
    quantity: 12,
    buyPrice: 3985,
    lastKnownPrice: 4055,
    riskLevel: "Low",
    averageSentiment: 66,
    currency: "INR",
  },
  {
    id: "demo-infy",
    ticker: "INFY.NS",
    label: "Infosys",
    quantity: 24,
    buyPrice: 1495,
    lastKnownPrice: 1528,
    riskLevel: "Low",
    averageSentiment: 58,
    currency: "INR",
  },
];

const inrFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

const clamp = (value: number, min: number, max: number) =>
  Math.min(Math.max(value, min), max);

function getCurrencyForTicker(ticker: string): "INR" | "USD" {
  return ticker.endsWith(".NS") || ticker.endsWith(".BO") ? "INR" : "USD";
}

function findTickerLabel(ticker: string): string {
  return FEATURED_TICKERS.find((item) => item.ticker === ticker)?.label ?? ticker;
}

function formatCurrency(
  value: number,
  currency: "INR" | "USD",
  maximumFractionDigits = 2
): string {
  if (currency === "INR") {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits,
    }).format(value);
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits,
  }).format(value);
}

function toInr(value: number, currency: "INR" | "USD"): number {
  return currency === "INR" ? value : value * USD_TO_INR;
}

function estimateDailyChange(snapshot: DashboardData): number {
  const sentimentBias = (snapshot.averageSentiment - 50) / 12;
  const volatilityDrag = (snapshot.risk.volatilityScore - 5) * 0.38;
  return Number((sentimentBias - volatilityDrag).toFixed(2));
}

function sentimentTone(score: number) {
  if (score >= 70) {
    return {
      label: "Bullish",
      accent: "text-emerald-300",
      chip: "bg-emerald-500/15 text-emerald-200 ring-1 ring-emerald-400/30",
      meter: "from-emerald-400 to-lime-300",
    };
  }

  if (score <= 40) {
    return {
      label: "Fragile",
      accent: "text-red-300",
      chip: "bg-red-500/15 text-red-200 ring-1 ring-red-400/30",
      meter: "from-red-400 to-amber-300",
    };
  }

  return {
    label: "Balanced",
    accent: "text-sky-300",
    chip: "bg-sky-500/15 text-sky-200 ring-1 ring-sky-400/30",
    meter: "from-sky-400 to-cyan-300",
  };
}

function riskStyles(level: RiskMetrics["riskLevel"]) {
  if (level === "High") {
    return {
      badge: "bg-red-500/15 text-red-200 ring-1 ring-red-400/35",
      border: "border-red-500/50",
      glow: "shadow-[0_0_60px_rgba(239,68,68,0.18)]",
      progress: "bg-red-400",
      dot: "bg-red-400",
    };
  }

  if (level === "Medium") {
    return {
      badge: "bg-amber-500/15 text-amber-100 ring-1 ring-amber-400/35",
      border: "border-amber-500/50",
      glow: "shadow-[0_0_55px_rgba(245,158,11,0.16)]",
      progress: "bg-amber-400",
      dot: "bg-amber-400",
    };
  }

  return {
    badge: "bg-emerald-500/15 text-emerald-100 ring-1 ring-emerald-400/30",
    border: "border-emerald-500/50",
    glow: "shadow-[0_0_48px_rgba(16,185,129,0.16)]",
    progress: "bg-emerald-400",
    dot: "bg-emerald-400",
  };
}

function buildDecisionSummary(snapshot: DashboardData, dailyChange: number): string {
  if (snapshot.risk.riskLevel === "High") {
    return "Risk is elevated right now. Present this as a watchlist candidate, not an immediate conviction buy.";
  }

  if (snapshot.averageSentiment >= 60 && dailyChange >= 0) {
    return "Momentum and sentiment are aligned. This is a clean stock to showcase as a positive AI-assisted idea.";
  }

  return "Signals are mixed. Use this view to explain why FinVerge AI balances hype with disciplined risk control.";
}

function normalizeDashboardPayload(payload: unknown, ticker: string): DashboardFetchResult {
  const normalizedPayload = payload as {
    ticker?: string;
    price?: number;
    overall_sentiment?: number;
    news?: NewsItem[];
    risk_metrics?: {
      risk_level?: RiskMetrics["riskLevel"];
      volatility_score?: number;
      key_risk_factors?: string[];
    };
  };

  const snapshot: DashboardData = {
    ticker: normalizedPayload.ticker ?? ticker,
    currentPrice: normalizedPayload.price ?? 0,
    averageSentiment: normalizedPayload.overall_sentiment ?? 50,
    risk: {
      riskLevel: normalizedPayload.risk_metrics?.risk_level ?? "Medium",
      volatilityScore: normalizedPayload.risk_metrics?.volatility_score ?? 5,
      riskFactors: normalizedPayload.risk_metrics?.key_risk_factors ?? [],
    },
    news: normalizedPayload.news ?? [],
  };

  return {
    snapshot,
    dailyChange: estimateDailyChange(snapshot),
  };
}

async function fetchDashboardSnapshot(
  ticker: string,
  signal?: AbortSignal
): Promise<DashboardFetchResult> {
  const response = await fetch(`/api/v1/analyze/${encodeURIComponent(ticker)}`, {
    signal,
  });
  const payload = (await response.json()) as { detail?: string };

  if (!response.ok) {
    throw new Error(payload.detail ?? `Ticker ${ticker} could not be analyzed.`);
  }

  return normalizeDashboardPayload(payload, ticker);
}

function SentimentGauge({ value }: { value: number }) {
  const score = clamp(value, 0, 100);
  const circumference = 251.2;
  const progress = circumference * (1 - score / 100);
  const tone = sentimentTone(score);

  return (
    <div className="relative flex items-center justify-center">
      <div className="absolute inset-x-8 bottom-6 top-10 rounded-full bg-gradient-to-r from-sky-500/10 via-transparent to-emerald-500/10 blur-2xl" />
      <svg viewBox="0 0 200 120" className="relative h-52 w-full">
        <defs>
          <linearGradient id="sentimentArc" x1="0%" x2="100%" y1="0%" y2="0%">
            <stop offset="0%" stopColor="#f87171" />
            <stop offset="52%" stopColor="#fbbf24" />
            <stop offset="100%" stopColor="#34d399" />
          </linearGradient>
        </defs>
        <path
          d="M20 100 A80 80 0 0 1 180 100"
          fill="none"
          stroke="rgba(148, 163, 184, 0.18)"
          strokeWidth="16"
          strokeLinecap="round"
        />
        <path
          d="M20 100 A80 80 0 0 1 180 100"
          fill="none"
          stroke="url(#sentimentArc)"
          strokeDasharray={circumference}
          strokeDashoffset={progress}
          strokeWidth="16"
          strokeLinecap="round"
          className="transition-all duration-700"
        />
      </svg>

      <div className="absolute bottom-7 flex flex-col items-center">
        <span className="text-5xl font-semibold tracking-tight text-white">
          {Math.round(score)}
        </span>
        <span
          className={`mt-2 rounded-full px-3 py-1 text-xs font-medium uppercase tracking-[0.28em] ${tone.chip}`}
        >
          {tone.label}
        </span>
      </div>
    </div>
  );
}

function LoadingCard() {
  return (
    <div className="dashboard-card animate-fade-up p-6">
      <div className="animate-pulse space-y-4">
        <div className="h-4 w-32 rounded-full bg-slate-700/80" />
        <div className="h-12 w-40 rounded-2xl bg-slate-700/60" />
        <div className="h-28 rounded-3xl bg-slate-800/80" />
      </div>
    </div>
  );
}

function OverviewModal({
  onClose,
  onLoadDemo,
}: {
  onClose: () => void;
  onLoadDemo: () => void;
}) {
  const featureCards = [
    {
      title: "Live Risk Story",
      body: "Judges instantly see price, sentiment, and risk in a single AI-guided flow.",
      icon: ShieldAlert,
    },
    {
      title: "Demo Money Ready",
      body: "A virtual capital wallet makes the product feel deployable even before brokerage integration.",
      icon: Wallet,
    },
    {
      title: "Indian Market Friendly",
      body: "Use NSE tickers like RELIANCE.NS, TCS.NS, or HDFCBANK.NS with the same experience.",
      icon: Landmark,
    },
    {
      title: "Portfolio You Control",
      body: "Add your own holdings, update quantities, and show why AI plus risk control is useful.",
      icon: BriefcaseBusiness,
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/78 px-4 py-8 backdrop-blur-xl">
      <div className="animate-fade-up relative w-full max-w-5xl overflow-hidden rounded-[32px] border border-white/10 bg-slate-900/95 shadow-[0_24px_120px_rgba(2,6,23,0.75)]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.12),_transparent_32%),radial-gradient(circle_at_bottom_right,_rgba(251,146,60,0.14),_transparent_28%)]" />
        <div className="relative p-6 sm:p-8">
          <div className="flex items-start justify-between gap-6">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1 text-xs font-medium uppercase tracking-[0.3em] text-cyan-200">
                <Sparkles className="h-3.5 w-3.5" />
                Welcome To FinVerge AI
              </div>
              <h2 className="mt-4 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                One quick walkthrough, then you are judge-demo ready.
              </h2>
              <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300 sm:text-base">
                This dashboard is designed to tell a simple story: what to buy,
                what to avoid, and how much virtual capital to deploy with Indian
                market support built in.
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full border border-white/10 bg-white/5 p-2 text-slate-300 transition hover:bg-white/10 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {featureCards.map(({ title, body, icon: Icon }, index) => (
              <div
                key={title}
                className="dashboard-card animate-fade-up p-5"
                style={{ animationDelay: `${index * 120}ms` }}
              >
                <div className="inline-flex rounded-2xl border border-white/10 bg-slate-950/70 p-3 text-cyan-300">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-white">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-300">{body}</p>
              </div>
            ))}
          </div>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={() => {
                onLoadDemo();
                onClose();
              }}
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
            >
              Load Demo Setup
              <ArrowRight className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={onClose}
              className="inline-flex items-center justify-center rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-medium text-white transition hover:bg-white/10"
            >
              Explore Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FinGPTRiskDashboard() {
  const [tickerInput, setTickerInput] = useState("RELIANCE.NS");
  const [activeTicker, setActiveTicker] = useState("RELIANCE.NS");
  const [requestNonce, setRequestNonce] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<DashboardData | null>(null);
  const [dailyChange, setDailyChange] = useState(0);
  const [refreshCountdown, setRefreshCountdown] = useState(AUTO_REFRESH_SECONDS);
  const [liveTimestamp, setLiveTimestamp] = useState(new Date());

  const [holdings, setHoldings] = useState<PortfolioHolding[]>(DEMO_PORTFOLIO);
  const [portfolioReady, setPortfolioReady] = useState(false);
  const [portfolioTickerInput, setPortfolioTickerInput] = useState("RELIANCE.NS");
  const [portfolioQuantityInput, setPortfolioQuantityInput] = useState("10");
  const [portfolioBuyPriceInput, setPortfolioBuyPriceInput] = useState("");
  const [portfolioError, setPortfolioError] = useState<string | null>(null);
  const [isAddingHolding, setIsAddingHolding] = useState(false);
  const [isOverviewOpen, setIsOverviewOpen] = useState(false);

  useEffect(() => {
    document.title = "FinVerge AI Risk Dashboard";
  }, []);

  useEffect(() => {
    const rawPortfolio = window.localStorage.getItem(PORTFOLIO_STORAGE_KEY);
    if (rawPortfolio) {
      try {
        const parsed = JSON.parse(rawPortfolio) as PortfolioHolding[];
        if (parsed.length > 0) {
          setHoldings(parsed);
        }
      } catch {
        setHoldings(DEMO_PORTFOLIO);
      }
    }

    setIsOverviewOpen(window.localStorage.getItem(OVERVIEW_STORAGE_KEY) !== "true");
    setPortfolioReady(true);
  }, []);

  useEffect(() => {
    if (!portfolioReady) {
      return;
    }

    window.localStorage.setItem(PORTFOLIO_STORAGE_KEY, JSON.stringify(holdings));
  }, [holdings, portfolioReady]);

  useEffect(() => {
    const controller = new AbortController();

    const loadDashboard = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const result = await fetchDashboardSnapshot(activeTicker, controller.signal);
        setData(result.snapshot);
        setDailyChange(result.dailyChange);
      } catch (fetchError) {
        if (controller.signal.aborted) {
          return;
        }

        const message =
          fetchError instanceof Error
            ? fetchError.message
            : "The analyzer is unavailable right now.";
        setError(message);
        setData(null);
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    };

    void loadDashboard();

    return () => controller.abort();
  }, [activeTicker, requestNonce]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setLiveTimestamp(new Date());
      setRefreshCountdown((current) => {
        if (current <= 1) {
          setRequestNonce((value) => value + 1);
          return AUTO_REFRESH_SECONDS;
        }

        return current - 1;
      });
    }, 1000);

    return () => window.clearInterval(intervalId);
  }, []);

  useEffect(() => {
    if (!data) {
      return;
    }

    setHoldings((current) =>
      current.map((holding) =>
        holding.ticker === data.ticker
          ? {
              ...holding,
              lastKnownPrice: data.currentPrice,
              riskLevel: data.risk.riskLevel,
              averageSentiment: data.averageSentiment,
            }
          : holding
      )
    );
  }, [data]);

  const analyzeTicker = (ticker: string) => {
    const normalizedTicker = ticker.trim().toUpperCase();
    if (!normalizedTicker) {
      return;
    }

    setTickerInput(normalizedTicker);
    setActiveTicker(normalizedTicker);
    setRefreshCountdown(AUTO_REFRESH_SECONDS);
    setRequestNonce((value) => value + 1);
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!tickerInput.trim()) {
      setError("Enter a stock ticker like RELIANCE.NS, TCS.NS, or AAPL.");
      return;
    }

    analyzeTicker(tickerInput);
  };

  const closeOverview = () => {
    window.localStorage.setItem(OVERVIEW_STORAGE_KEY, "true");
    setIsOverviewOpen(false);
  };

  const loadDemoPortfolio = () => {
    setHoldings(DEMO_PORTFOLIO);
    setPortfolioTickerInput("RELIANCE.NS");
    setPortfolioQuantityInput("10");
    setPortfolioBuyPriceInput("2890");
    setPortfolioError(null);
  };

  const useCurrentAnalysis = () => {
    if (!data) {
      return;
    }

    setPortfolioTickerInput(data.ticker);
    setPortfolioBuyPriceInput(data.currentPrice.toFixed(2));
    setPortfolioError(null);
  };

  const investedCapitalInr = holdings.reduce(
    (total, holding) =>
      total + toInr(holding.buyPrice * holding.quantity, holding.currency),
    0
  );
  const liveValueInr = holdings.reduce(
    (total, holding) =>
      total + toInr(holding.lastKnownPrice * holding.quantity, holding.currency),
    0
  );
  const availableDemoCashInr = clamp(
    INITIAL_DEMO_CASH_INR - investedCapitalInr,
    0,
    INITIAL_DEMO_CASH_INR
  );
  const totalPortfolioValueInr = availableDemoCashInr + liveValueInr;
  const pnlInr = liveValueInr - investedCapitalInr;
  const pnlPct = investedCapitalInr > 0 ? (pnlInr / investedCapitalInr) * 100 : 0;

  const handleAddHolding = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const normalizedTicker = portfolioTickerInput.trim().toUpperCase();
    const quantity = Number(portfolioQuantityInput);
    const buyPrice = Number(portfolioBuyPriceInput);

    if (!normalizedTicker) {
      setPortfolioError("Add a valid ticker. Example: RELIANCE.NS or TCS.NS.");
      return;
    }

    if (!Number.isFinite(quantity) || quantity <= 0) {
      setPortfolioError("Quantity should be greater than 0.");
      return;
    }

    if (!Number.isFinite(buyPrice) || buyPrice <= 0) {
      setPortfolioError("Buy price should be greater than 0.");
      return;
    }

    setIsAddingHolding(true);
    setPortfolioError(null);

    try {
      const snapshot =
        data?.ticker === normalizedTicker
          ? { snapshot: data, dailyChange }
          : await fetchDashboardSnapshot(normalizedTicker);

      const currency = getCurrencyForTicker(normalizedTicker);
      const requiredCapital = toInr(quantity * buyPrice, currency);

      if (requiredCapital > availableDemoCashInr) {
        throw new Error(
          `Not enough demo cash. Available: ${inrFormatter.format(availableDemoCashInr)}`
        );
      }

      setHoldings((current) => {
        const existing = current.find((holding) => holding.ticker === normalizedTicker);
        if (!existing) {
          return [
            {
              id: `${normalizedTicker}-${Date.now()}`,
              ticker: normalizedTicker,
              label: findTickerLabel(normalizedTicker),
              quantity,
              buyPrice,
              lastKnownPrice: snapshot.snapshot.currentPrice,
              riskLevel: snapshot.snapshot.risk.riskLevel,
              averageSentiment: snapshot.snapshot.averageSentiment,
              currency,
            },
            ...current,
          ];
        }

        const mergedQuantity = existing.quantity + quantity;
        const mergedBuyPrice =
          (existing.buyPrice * existing.quantity + buyPrice * quantity) /
          mergedQuantity;

        return current.map((holding) =>
          holding.ticker === normalizedTicker
            ? {
                ...holding,
                quantity: mergedQuantity,
                buyPrice: mergedBuyPrice,
                lastKnownPrice: snapshot.snapshot.currentPrice,
                riskLevel: snapshot.snapshot.risk.riskLevel,
                averageSentiment: snapshot.snapshot.averageSentiment,
              }
            : holding
        );
      });

      setPortfolioTickerInput(normalizedTicker);
      setPortfolioQuantityInput("10");
      setPortfolioBuyPriceInput(snapshot.snapshot.currentPrice.toFixed(2));
    } catch (addError) {
      setPortfolioError(
        addError instanceof Error
          ? addError.message
          : "Could not add this holding right now."
      );
    } finally {
      setIsAddingHolding(false);
    }
  };

  const removeHolding = (holdingId: string) => {
    setHoldings((current) => current.filter((holding) => holding.id !== holdingId));
  };

  const activeCurrency = getCurrencyForTicker(activeTicker);
  const sentiment = sentimentTone(data?.averageSentiment ?? 50);
  const activeRiskStyles = riskStyles(data?.risk.riskLevel ?? "Medium");
  const isPositiveDay = dailyChange >= 0;

  const marketTape = [...FEATURED_TICKERS, ...FEATURED_TICKERS];

  return (
    <section className="relative min-h-screen overflow-hidden bg-slate-950 px-4 py-8 text-slate-100 sm:px-6 lg:px-8">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-[-10%] top-0 h-72 w-72 rounded-full bg-cyan-500/12 blur-3xl animate-float-slow" />
        <div
          className="absolute bottom-0 right-[-8%] h-72 w-72 rounded-full bg-orange-500/12 blur-3xl animate-float-slow"
          style={{ animationDelay: "800ms" }}
        />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(15,23,42,0.82),rgba(15,23,42,0.82)),linear-gradient(90deg,rgba(148,163,184,0.04)_1px,transparent_1px),linear-gradient(rgba(148,163,184,0.04)_1px,transparent_1px)] bg-[size:auto,36px_36px,36px_36px]" />
      </div>

      {isOverviewOpen ? (
        <OverviewModal onClose={closeOverview} onLoadDemo={loadDemoPortfolio} />
      ) : null}

      <div className="relative mx-auto max-w-7xl space-y-6">
        <div className="grid gap-6 xl:grid-cols-[1.22fr_0.78fr]">
          <div className="dashboard-card noise-scan animate-fade-up overflow-hidden p-6 sm:p-8">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.14),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(251,146,60,0.16),_transparent_28%)]" />
            <div className="relative">
              <div className="flex flex-wrap items-center gap-3">
                <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1 text-xs font-medium uppercase tracking-[0.3em] text-cyan-200">
                  <Sparkles className="h-3.5 w-3.5" />
                  FinVerge AI
                </div>
                <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-4 py-1 text-xs font-medium uppercase tracking-[0.28em] text-emerald-200">
                  <span className="inline-flex h-2.5 w-2.5 rounded-full bg-emerald-300 animate-pulse" />
                  Live Demo Mode
                </div>
                <button
                  type="button"
                  onClick={() => setIsOverviewOpen(true)}
                  className="rounded-full border border-white/10 bg-white/5 px-4 py-1 text-xs font-medium uppercase tracking-[0.28em] text-slate-200 transition hover:bg-white/10"
                >
                  Replay Overview
                </button>
              </div>

              <h1 className="mt-5 max-w-4xl text-4xl font-semibold tracking-tight text-white sm:text-5xl">
                Explain stocks, sentiment, and risk in a way judges immediately understand.
              </h1>
              <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
                FinVerge AI turns raw market signals into a story: what is moving,
                why sentiment matters, how risky it is, and how much demo capital
                you would allocate in an Indian-market-friendly portfolio.
              </p>

              <form
                onSubmit={handleSubmit}
                className="mt-6 flex flex-col gap-3 md:flex-row"
              >
                <label className="relative flex-1">
                  <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                  <input
                    value={tickerInput}
                    onChange={(event) => setTickerInput(event.target.value)}
                    placeholder="Analyze Indian or global stocks, e.g. RELIANCE.NS"
                    className="h-14 w-full rounded-2xl border border-white/10 bg-slate-950/80 pl-11 pr-4 text-sm text-white outline-none transition focus:border-cyan-400/40 focus:ring-2 focus:ring-cyan-400/15"
                  />
                </label>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="inline-flex h-14 items-center justify-center gap-2 rounded-2xl bg-cyan-400 px-6 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Activity className="h-4 w-4" />
                  )}
                  Run Live Analysis
                </button>
              </form>

              <div className="mt-5 flex flex-wrap gap-2">
                {FEATURED_TICKERS.map((item) => (
                  <button
                    key={item.ticker}
                    type="button"
                    onClick={() => analyzeTicker(item.ticker)}
                    className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium tracking-[0.22em] text-slate-200 transition hover:border-cyan-400/30 hover:bg-cyan-400/10 hover:text-white"
                  >
                    {item.label}
                  </button>
                ))}
              </div>

              <div className="mt-6 overflow-hidden rounded-2xl border border-white/10 bg-slate-950/55">
                <div className="marquee-track flex min-w-max gap-3 px-4 py-3">
                  {marketTape.map((item, index) => (
                    <div
                      key={`${item.ticker}-${index}`}
                      className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium tracking-[0.22em] text-slate-200"
                    >
                      <span className="inline-flex h-2 w-2 rounded-full bg-cyan-300" />
                      {item.label}
                      <span className="text-slate-500">{item.ticker}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-3">
                <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-4">
                  <div className="flex items-center gap-3">
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-cyan-300">
                      <Clock3 className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.28em] text-slate-400">
                        Next Refresh
                      </p>
                      <p className="mt-1 text-2xl font-semibold text-white">
                        {refreshCountdown}s
                      </p>
                    </div>
                  </div>
                </div>

                <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-4">
                  <div className="flex items-center gap-3">
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-emerald-300">
                      <Activity className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.28em] text-slate-400">
                        Live Sync
                      </p>
                      <p className="mt-1 text-lg font-semibold text-white">
                        {liveTimestamp.toLocaleTimeString("en-IN")}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-xs uppercase tracking-[0.28em] text-slate-400">
                        Story Angle
                      </p>
                      <p className="mt-2 text-sm leading-6 text-slate-200">
                        AI tells you if upside is worth the risk.
                      </p>
                    </div>
                    <div className="signal-bars flex h-10 items-end gap-1.5">
                      <span className="signal-bar h-4 w-2 rounded-full bg-cyan-300" />
                      <span
                        className="signal-bar h-8 w-2 rounded-full bg-emerald-300"
                        style={{ animationDelay: "160ms" }}
                      />
                      <span
                        className="signal-bar h-6 w-2 rounded-full bg-amber-300"
                        style={{ animationDelay: "320ms" }}
                      />
                      <span
                        className="signal-bar h-10 w-2 rounded-full bg-cyan-200"
                        style={{ animationDelay: "480ms" }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <aside className="dashboard-card animate-fade-up p-6" style={{ animationDelay: "100ms" }}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="inline-flex items-center gap-2 rounded-full border border-orange-400/20 bg-orange-400/10 px-4 py-1 text-xs font-medium uppercase tracking-[0.28em] text-orange-200">
                  <Wallet className="h-3.5 w-3.5" />
                  Demo Capital
                </div>
                <h2 className="mt-4 text-3xl font-semibold text-white">
                  {inrFormatter.format(totalPortfolioValueInr)}
                </h2>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  Virtual money for the hackathon demo, with Indian market holdings
                  and live AI-assisted stock insights.
                </p>
              </div>
              <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-4 text-orange-200">
                <IndianRupee className="h-7 w-7" />
              </div>
            </div>

            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-4">
                <p className="text-xs uppercase tracking-[0.28em] text-slate-400">
                  Available Cash
                </p>
                <p className="mt-2 text-2xl font-semibold text-white">
                  {inrFormatter.format(availableDemoCashInr)}
                </p>
              </div>
              <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-4">
                <p className="text-xs uppercase tracking-[0.28em] text-slate-400">
                  Unrealised P&L
                </p>
                <p
                  className={`mt-2 text-2xl font-semibold ${
                    pnlInr >= 0 ? "text-emerald-300" : "text-red-300"
                  }`}
                >
                  {pnlInr >= 0 ? "+" : ""}
                  {inrFormatter.format(pnlInr)}
                </p>
                <p className="mt-1 text-sm text-slate-400">{pnlPct.toFixed(2)}%</p>
              </div>
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-4">
                <p className="text-xs uppercase tracking-[0.28em] text-slate-400">
                  Holdings
                </p>
                <p className="mt-2 text-2xl font-semibold text-white">{holdings.length}</p>
              </div>
              <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-4">
                <p className="text-xs uppercase tracking-[0.28em] text-slate-400">
                  Demo Budget
                </p>
                <p className="mt-2 text-2xl font-semibold text-white">
                  {inrFormatter.format(INITIAL_DEMO_CASH_INR)}
                </p>
              </div>
            </div>

            <div className="mt-6 space-y-3">
              <button
                type="button"
                onClick={loadDemoPortfolio}
                className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
              >
                Load Judge Demo Portfolio
                <ArrowRight className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={useCurrentAnalysis}
                className="inline-flex w-full items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-medium text-white transition hover:bg-white/10"
              >
                Use Current Stock In Portfolio Form
              </button>
            </div>
          </aside>
        </div>

        {error ? (
          <div className="animate-fade-up rounded-3xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-100 shadow-[0_0_30px_rgba(239,68,68,0.12)]">
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 h-5 w-5 flex-none text-red-300" />
              <div>
                <p className="font-medium text-red-200">Ticker issue or analyzer error</p>
                <p className="mt-1 text-red-100/80">{error}</p>
              </div>
            </div>
          </div>
        ) : null}

        <div className="grid gap-5 xl:grid-cols-[1fr_1fr_1.15fr]">
          {isLoading ? (
            <>
              <LoadingCard />
              <LoadingCard />
              <LoadingCard />
            </>
          ) : (
            <>
              <article className="dashboard-card animate-fade-up p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-[0.28em] text-slate-400">
                      Market Overview
                    </p>
                    <h2 className="mt-2 text-2xl font-semibold text-white">
                      {data?.ticker ?? "----"}
                    </h2>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-3 text-cyan-300">
                    <Activity className="h-5 w-5" />
                  </div>
                </div>

                <div className="mt-8 space-y-6">
                  <div>
                    <p className="text-sm text-slate-400">Current price</p>
                    <p className="mt-2 text-4xl font-semibold tracking-tight text-white">
                      {formatCurrency(data?.currentPrice ?? 0, activeCurrency)}
                    </p>
                  </div>

                  <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-4">
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <div
                          className={`rounded-full p-2 ${
                            isPositiveDay
                              ? "bg-emerald-500/15 text-emerald-300"
                              : "bg-red-500/15 text-red-300"
                          }`}
                        >
                          {isPositiveDay ? (
                            <TrendingUp className="h-4 w-4" />
                          ) : (
                            <TrendingDown className="h-4 w-4" />
                          )}
                        </div>
                        <div>
                          <p className="text-sm text-slate-400">Daily move</p>
                          <p
                            className={`text-xl font-semibold ${
                              isPositiveDay ? "text-emerald-300" : "text-red-300"
                            }`}
                          >
                            {isPositiveDay ? "+" : ""}
                            {dailyChange.toFixed(2)}%
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs uppercase tracking-[0.28em] text-slate-500">
                          Best for
                        </p>
                        <p className="mt-2 text-sm text-slate-200">
                          {activeCurrency === "INR" ? "Indian market demo" : "Global reference stock"}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-slate-950 via-slate-900 to-cyan-950/30 p-4">
                    <p className="text-sm text-slate-400">What to say now</p>
                    <p className="mt-3 text-sm leading-7 text-slate-200">
                      {data ? buildDecisionSummary(data, dailyChange) : "Waiting for live analysis."}
                    </p>
                  </div>
                </div>
              </article>

              <article className="dashboard-card animate-fade-up p-6" style={{ animationDelay: "90ms" }}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-[0.28em] text-slate-400">
                      AI Sentiment Engine
                    </p>
                    <h2 className="mt-2 text-2xl font-semibold text-white">
                      Market Mood Gauge
                    </h2>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-3 text-cyan-300">
                    <Gauge className="h-5 w-5" />
                  </div>
                </div>

                <div className="mt-6 rounded-[28px] border border-white/10 bg-slate-950/60 p-4">
                  <SentimentGauge value={data?.averageSentiment ?? 50} />
                </div>

                <div className="mt-5 rounded-3xl border border-white/10 bg-slate-950/60 p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm text-slate-400">Average sentiment</p>
                      <p className={`mt-1 text-2xl font-semibold ${sentiment.accent}`}>
                        {(data?.averageSentiment ?? 50).toFixed(0)}/100
                      </p>
                    </div>
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-medium uppercase tracking-[0.28em] ${sentiment.chip}`}
                    >
                      {sentiment.label}
                    </span>
                  </div>

                  <div className="mt-4">
                    <div className="mb-2 flex items-center justify-between text-sm text-slate-400">
                      <span>Confidence pulse</span>
                      <span>{Math.round((data?.averageSentiment ?? 50) * 0.82)} pts</span>
                    </div>
                    <div className="h-3 overflow-hidden rounded-full bg-slate-800">
                      <div
                        className={`h-full rounded-full bg-gradient-to-r ${sentiment.meter}`}
                        style={{
                          width: `${clamp((data?.averageSentiment ?? 50) * 0.82, 0, 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                </div>
              </article>

              <article
                className={`dashboard-card animate-fade-up p-6 ${activeRiskStyles.border} ${activeRiskStyles.glow}`}
                style={{ animationDelay: "180ms" }}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-[0.28em] text-slate-400">
                      Deep Risk Analyzer
                    </p>
                    <h2 className="mt-2 text-2xl font-semibold text-white">
                      Risk Pulse
                    </h2>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-3 text-red-300">
                    <ShieldAlert className="h-5 w-5" />
                  </div>
                </div>

                <div className="mt-8 grid gap-4 md:grid-cols-[1.05fr_0.95fr]">
                  <div className="rounded-[28px] border border-white/10 bg-slate-950/65 p-5">
                    <p className="text-sm text-slate-400">Risk level</p>
                    <div className="mt-4 flex items-center gap-3">
                      <span
                        className={`inline-flex rounded-full px-4 py-2 text-sm font-semibold uppercase tracking-[0.28em] ${activeRiskStyles.badge}`}
                      >
                        {data?.risk.riskLevel ?? "Medium"}
                      </span>
                    </div>

                    <div className="mt-6">
                      <div className="mb-2 flex items-center justify-between text-sm text-slate-400">
                        <span>Volatility score</span>
                        <span>{(data?.risk.volatilityScore ?? 0).toFixed(1)}/10</span>
                      </div>
                      <div className="h-3 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className={`h-full rounded-full ${activeRiskStyles.progress}`}
                          style={{
                            width: `${clamp(
                              ((data?.risk.volatilityScore ?? 0) / 10) * 100,
                              0,
                              100
                            )}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="rounded-[28px] border border-white/10 bg-gradient-to-br from-slate-950 via-slate-900 to-red-950/20 p-5">
                    <p className="text-sm text-slate-400">Potential red flags</p>
                    <ul className="mt-4 space-y-3">
                      {(data?.risk.riskFactors.length
                        ? data.risk.riskFactors
                        : ["Waiting for the analyzer to return risk factors."]
                      ).map((factor) => (
                        <li key={factor} className="flex items-start gap-3 text-sm text-slate-200">
                          <span
                            className={`mt-1.5 h-2.5 w-2.5 rounded-full ${activeRiskStyles.dot}`}
                          />
                          <span>{factor}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </article>
            </>
          )}
        </div>

        <div className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
          <section className="dashboard-card animate-fade-up p-6" style={{ animationDelay: "120ms" }}>
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.28em] text-slate-400">
                  AI Briefing
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-white">
                  Human-friendly explanation
                </h2>
              </div>
              <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-3 text-cyan-300">
                <Sparkles className="h-5 w-5" />
              </div>
            </div>

            <div className="mt-6 rounded-3xl border border-white/10 bg-slate-950/60 p-5">
              <p className="text-sm leading-7 text-slate-200">
                {data
                  ? buildDecisionSummary(data, dailyChange)
                  : "Analyze a stock to generate the AI briefing."}
              </p>
            </div>

            <div className="mt-5 space-y-3">
              {(data?.news.slice(0, 3) ?? []).map((item, index) => (
                <div
                  key={item.id}
                  className="rounded-3xl border border-white/10 bg-white/5 p-4 animate-fade-up"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-sm leading-6 text-slate-200">{item.headline}</p>
                    <span
                      className={`whitespace-nowrap rounded-full px-3 py-1 text-[11px] font-medium uppercase tracking-[0.24em] ${
                        item.sentiment === "Positive"
                          ? "bg-emerald-500/15 text-emerald-200"
                          : item.sentiment === "Negative"
                            ? "bg-red-500/15 text-red-200"
                            : "bg-slate-700/70 text-slate-300"
                      }`}
                    >
                      {item.sentiment}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="dashboard-card animate-fade-up p-6" style={{ animationDelay: "180ms" }}>
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.28em] text-slate-400">
                  Personal Demo Portfolio
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-white">
                  Add your own holdings
                </h2>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
                  Show the judge a real use case: add Indian stocks, compare risk,
                  and explain how AI sentiment changes your portfolio story.
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-right">
                <p className="text-xs uppercase tracking-[0.28em] text-slate-500">
                  Demo wallet
                </p>
                <p className="mt-1 text-lg font-semibold text-white">
                  {inrFormatter.format(availableDemoCashInr)}
                </p>
              </div>
            </div>

            <div className="mt-6 grid gap-5 xl:grid-cols-[0.8fr_1.2fr]">
              <form
                onSubmit={handleAddHolding}
                className="rounded-[28px] border border-white/10 bg-slate-950/60 p-5"
              >
                <div className="space-y-4">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-200">
                      Ticker
                    </label>
                    <input
                      value={portfolioTickerInput}
                      onChange={(event) => setPortfolioTickerInput(event.target.value)}
                      placeholder="RELIANCE.NS"
                      className="h-12 w-full rounded-2xl border border-white/10 bg-slate-950/80 px-4 text-sm text-white outline-none transition focus:border-cyan-400/40 focus:ring-2 focus:ring-cyan-400/15"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="mb-2 block text-sm font-medium text-slate-200">
                        Quantity
                      </label>
                      <input
                        value={portfolioQuantityInput}
                        onChange={(event) => setPortfolioQuantityInput(event.target.value)}
                        inputMode="decimal"
                        placeholder="10"
                        className="h-12 w-full rounded-2xl border border-white/10 bg-slate-950/80 px-4 text-sm text-white outline-none transition focus:border-cyan-400/40 focus:ring-2 focus:ring-cyan-400/15"
                      />
                    </div>
                    <div>
                      <label className="mb-2 block text-sm font-medium text-slate-200">
                        Buy Price
                      </label>
                      <input
                        value={portfolioBuyPriceInput}
                        onChange={(event) => setPortfolioBuyPriceInput(event.target.value)}
                        inputMode="decimal"
                        placeholder="2890"
                        className="h-12 w-full rounded-2xl border border-white/10 bg-slate-950/80 px-4 text-sm text-white outline-none transition focus:border-cyan-400/40 focus:ring-2 focus:ring-cyan-400/15"
                      />
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {FEATURED_TICKERS.slice(0, 5).map((item) => (
                      <button
                        key={item.ticker}
                        type="button"
                        onClick={() => setPortfolioTickerInput(item.ticker)}
                        className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] font-medium uppercase tracking-[0.24em] text-slate-200 transition hover:bg-white/10"
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>

                  {portfolioError ? (
                    <div className="rounded-2xl border border-red-500/25 bg-red-500/10 p-3 text-sm text-red-100">
                      {portfolioError}
                    </div>
                  ) : null}

                  <button
                    type="submit"
                    disabled={isAddingHolding}
                    className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
                  >
                    {isAddingHolding ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Plus className="h-4 w-4" />
                    )}
                    Add To Demo Portfolio
                  </button>
                </div>
              </form>

              <div className="rounded-[28px] border border-white/10 bg-slate-950/60 p-5">
                <div className="space-y-3">
                  {holdings.map((holding) => {
                    const liveHoldingValue = holding.lastKnownPrice * holding.quantity;
                    const costBasis = holding.buyPrice * holding.quantity;
                    const pnlValue = liveHoldingValue - costBasis;
                    const pnlPercent = costBasis > 0 ? (pnlValue / costBasis) * 100 : 0;
                    const holdingRiskStyles = riskStyles(holding.riskLevel);

                    return (
                      <div
                        key={holding.id}
                        className="rounded-3xl border border-white/10 bg-white/5 p-4"
                      >
                        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                          <div>
                            <div className="flex flex-wrap items-center gap-2">
                              <p className="text-lg font-semibold text-white">{holding.label}</p>
                              <span className="text-sm text-slate-400">{holding.ticker}</span>
                              <span
                                className={`rounded-full px-3 py-1 text-[11px] font-medium uppercase tracking-[0.24em] ${holdingRiskStyles.badge}`}
                              >
                                {holding.riskLevel} Risk
                              </span>
                            </div>
                            <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-300">
                              <span>Qty: {holding.quantity}</span>
                              <span>
                                Avg: {formatCurrency(holding.buyPrice, holding.currency)}
                              </span>
                              <span>
                                Live: {formatCurrency(holding.lastKnownPrice, holding.currency)}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center gap-4">
                            <div className="text-right">
                              <p className="text-sm text-slate-400">
                                {formatCurrency(liveHoldingValue, holding.currency)}
                              </p>
                              <p
                                className={`mt-1 text-sm font-semibold ${
                                  pnlValue >= 0 ? "text-emerald-300" : "text-red-300"
                                }`}
                              >
                                {pnlValue >= 0 ? "+" : ""}
                                {formatCurrency(pnlValue, holding.currency)} ({pnlPercent.toFixed(2)}%)
                              </p>
                            </div>
                            <button
                              type="button"
                              onClick={() => removeHolding(holding.id)}
                              className="rounded-full border border-white/10 bg-white/5 p-2 text-slate-300 transition hover:bg-white/10 hover:text-white"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}

                  {holdings.length === 0 ? (
                    <div className="rounded-3xl border border-dashed border-white/10 bg-white/5 p-8 text-center text-sm text-slate-400">
                      Your demo portfolio is empty. Add Indian stocks like RELIANCE.NS
                      to show a personalized story.
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </section>
  );
}
