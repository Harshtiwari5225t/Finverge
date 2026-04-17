"""
FinGPT Trader — Premium Trading Dashboard
Run with:  streamlit run dashboard.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

from utils.dashboard_data import DashboardDataProvider

# ─────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinGPT Trader",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────
# THEME / CSS
# ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Import Inter font ───────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Root variables ──────────────────────────────────────────── */
:root {
    --bg-primary: #0a0e17;
    --bg-secondary: #111827;
    --bg-card: rgba(17, 24, 39, 0.7);
    --border-color: rgba(0, 212, 255, 0.12);
    --accent: #00d4ff;
    --accent-dim: rgba(0, 212, 255, 0.15);
    --green: #22c55e;
    --green-dim: rgba(34, 197, 94, 0.15);
    --red: #ef4444;
    --red-dim: rgba(239, 68, 68, 0.15);
    --yellow: #eab308;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
}

/* ── Global ──────────────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--text-primary);
}
.stApp {
    background: var(--bg-primary) !important;
}
[data-testid="stHeader"] {
    background: transparent !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #0a0e17 100%) !important;
    border-right: 1px solid var(--border-color) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}

/* ── Glass Card ──────────────────────────────────────────────── */
.glass-card {
    background: var(--bg-card);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.glass-card:hover {
    border-color: rgba(0, 212, 255, 0.3);
    box-shadow: 0 0 30px rgba(0, 212, 255, 0.06);
}

/* ── Metric Cards ────────────────────────────────────────────── */
.metric-card {
    background: var(--bg-card);
    backdrop-filter: blur(12px);
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: 20px 22px;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}
.metric-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--text-muted);
    margin-bottom: 6px;
}
.metric-value {
    font-size: 28px;
    font-weight: 800;
    color: var(--text-primary);
    line-height: 1.1;
}
.metric-value.accent { color: var(--accent); }
.metric-value.green  { color: var(--green); }
.metric-value.red    { color: var(--red); }
.metric-delta {
    font-size: 12px;
    font-weight: 600;
    margin-top: 4px;
}
.metric-delta.up   { color: var(--green); }
.metric-delta.down { color: var(--red); }

/* ── Section Headers ─────────────────────────────────────────── */
.section-header {
    font-size: 15px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--accent);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-header .dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 8px var(--accent);
    animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* ── Badge ───────────────────────────────────────────────────── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.badge-green  { background: var(--green-dim); color: var(--green); }
.badge-red    { background: var(--red-dim); color: var(--red); }
.badge-blue   { background: var(--accent-dim); color: var(--accent); }
.badge-yellow { background: rgba(234, 179, 8, 0.15); color: var(--yellow); }

/* ── Strength Bar ────────────────────────────────────────────── */
.strength-bar-bg {
    width: 100%;
    height: 6px;
    background: rgba(255,255,255,0.06);
    border-radius: 3px;
    overflow: hidden;
}
.strength-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.5s ease;
}

/* ── Status Indicator ────────────────────────────────────────── */
.status-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 6px;
    animation: pulse-dot 2s infinite;
}
.status-dot.online  { background: var(--green); box-shadow: 0 0 8px var(--green); }
.status-dot.demo    { background: var(--yellow); box-shadow: 0 0 8px var(--yellow); }

/* ── Plotly overrides ────────────────────────────────────────── */
.js-plotly-plot .plotly .main-svg { background: transparent !important; }

/* ── Hide Streamlit branding ─────────────────────────────────── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* ── Scrollbar ───────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--text-muted); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# DATA PROVIDER
# ─────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_data_provider():
    return DashboardDataProvider()

dp = get_data_provider()

# ─────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────

def _color(val: float) -> str:
    return "green" if val >= 0 else "red"

def _sign(val: float) -> str:
    return "+" if val >= 0 else ""

def _badge(text: str, variant: str = "blue") -> str:
    return f'<span class="badge badge-{variant}">{text}</span>'

def _metric_card(label: str, value: str, delta: str = "", css_class: str = "accent") -> str:
    delta_html = ""
    if delta:
        d_class = "up" if "+" in delta else "down"
        delta_html = f'<span class="metric-delta {d_class}" style="display:block;">{delta}</span>'
    return f'<div class="metric-card"><span class="metric-label" style="display:block;">{label}</span><span class="metric-value {css_class}" style="display:block;">{value}</span>{delta_html}</div>'

def _section(title: str, icon: str = "") -> str:
    return f'<div class="section-header"><span class="dot"></span>{icon} {title}</div>'

def _strength_bar(value: float, color: str = "#00d4ff") -> str:
    pct = int(value * 100)
    return f'''<div class="strength-bar-bg">
        <div class="strength-bar-fill" style="width:{pct}%; background:{color};"></div>
    </div>'''

def make_sparkline(data: list, color: str = "#00d4ff", height: int = 45) -> go.Figure:
    is_up = data[-1] >= data[0]
    c = "#22c55e" if is_up else "#ef4444"
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=data, mode='lines', line=dict(color=c, width=2),
        fill='tozeroy', fillcolor=f'rgba({34 if is_up else 239},{197 if is_up else 68},{94 if is_up else 68},0.08)',
        hoverinfo='skip',
    ))
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
    )
    return fig

# ─────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:20px 0 10px;">
        <div style="font-size:32px; font-weight:900; background:linear-gradient(135deg,#00d4ff,#7c3aed);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            FinGPT Trader
        </div>
        <div style="font-size:12px; color:#64748b; letter-spacing:2px; margin-top:2px;">
            AI-POWERED TRADING SYSTEM
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Status
    health = dp.get_system_health()
    status_class = "demo" if dp.is_demo else "online"
    status_text = health.get('status', 'Demo Mode')
    st.markdown(f'''
    <div style="display:flex; align-items:center; gap:8px; margin-bottom:18px;">
        <span class="status-dot {status_class}"></span>
        <span style="font-size:13px; font-weight:600;">{status_text}</span>
    </div>
    ''', unsafe_allow_html=True)

    # Quick stats
    perf = dp.get_performance()
    st.markdown(f'''
    <div class="glass-card" style="padding:16px;">
        <div style="font-size:11px; color:#64748b; text-transform:uppercase; letter-spacing:1px;">Total Return</div>
        <div style="font-size:24px; font-weight:800; color:#22c55e;">{_sign(perf["total_return"]*100)}{perf["total_return"]*100:.2f}%</div>
        <div style="font-size:11px; color:#64748b; margin-top:8px;">Trades: {perf["total_trades"]}  •  Win Rate: {perf["win_rate"]*100:.1f}%</div>
    </div>
    ''', unsafe_allow_html=True)

    # Config
    st.markdown(f'''
    <div class="glass-card" style="padding:16px;">
        <div style="font-size:11px; color:#64748b; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px;">Configuration</div>
        <div style="font-size:12px; color:#94a3b8; line-height:1.8;">
            Exchange: {_badge("Binance Testnet", "blue")}<br>
            Model: {_badge("Falcon-7B", "blue")}<br>
            Strategy: {_badge("Sentiment + Technical", "blue")}<br>
            Risk Limit: {_badge("10% Max Drawdown", "yellow")}
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Refresh
    auto_refresh = st.toggle("Auto Refresh (60s)", value=False)
    if st.button("🔄 Refresh Now", width='stretch'):
        st.cache_resource.clear()
        st.rerun()

    st.markdown(f'<div style="text-align:center; font-size:10px; color:#475569; margin-top:20px;">Last update: {datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────────────────────────────

# ── Top Metrics Row ──────────────────────────────────────────────────
portfolio = dp.get_portfolio()
perf = dp.get_performance()

cols = st.columns(5)
metrics_data = [
    ("Portfolio Value", f"${portfolio['total_value']:,.2f}", f"{_sign(perf['total_return']*100)}{perf['total_return']*100:.2f}%", "accent"),
    ("Cash Balance", f"${portfolio['cash']:,.2f}", "", "accent"),
    ("Sharpe Ratio", f"{perf['sharpe_ratio']:.2f}", "", "green" if perf['sharpe_ratio'] > 1 else "red"),
    ("Win Rate", f"{perf['win_rate']*100:.1f}%", "", "green" if perf['win_rate'] > 0.5 else "red"),
    ("Max Drawdown", f"{perf['max_drawdown']*100:.1f}%", "", "green" if perf['max_drawdown'] < 0.1 else "red"),
]
for col, (label, value, delta, css) in zip(cols, metrics_data):
    with col:
        st.markdown(_metric_card(label, value, delta, css), unsafe_allow_html=True)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ── Market Overview + Signals ────────────────────────────────────────
left_col, right_col = st.columns([3, 2])

with left_col:
    st.markdown(_section("Market Overview", "📊"), unsafe_allow_html=True)
    market = dp.get_market_data()

    for asset in market:
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([1.5, 1.5, 1, 1.2, 2])
            with c1:
                st.markdown(f"""
                <div style="font-weight:700; font-size:16px; color:#f1f5f9;">{asset['symbol']}</div>
                <div style="font-size:11px; color:#64748b;">{asset['pair']}</div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div style="font-size:18px; font-weight:700; color:#f1f5f9;">${asset["price"]:,.2f}</div>', unsafe_allow_html=True)
            with c3:
                chg_color = _color(asset['change_24h'])
                st.markdown(f'<div style="font-size:14px; font-weight:600; color:var(--{chg_color});">{_sign(asset["change_24h"])}{asset["change_24h"]:.2f}%</div>', unsafe_allow_html=True)
            with c4:
                sent = asset['sentiment']
                v = 'green' if sent == 'Bullish' else 'red' if sent == 'Bearish' else 'yellow'
                st.markdown(_badge(sent, v), unsafe_allow_html=True)
            with c5:
                fig = make_sparkline(asset['sparkline'])
                st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

with right_col:
    st.markdown(_section("Trading Signals", "⚡"), unsafe_allow_html=True)
    signals = dp.get_signals()

    for sig in signals:
        dir_color = "green" if sig['direction'] == 'BUY' else "red"
        dir_icon = "▲" if sig['direction'] == 'BUY' else "▼"
        age = datetime.now() - sig['timestamp']
        age_str = f"{int(age.total_seconds()//60)}m ago" if age.total_seconds() < 3600 else f"{int(age.total_seconds()//3600)}h ago"

        st.markdown(f'''
        <div class="glass-card" style="padding:16px; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div>
                    <span style="font-size:16px; font-weight:700;">{sig['symbol']}</span>
                    <span style="color:var(--{dir_color}); font-weight:700; margin-left:8px;">{dir_icon} {sig['direction']}</span>
                </div>
                <span style="font-size:11px; color:#64748b;">{age_str}</span>
            </div>
            <div style="display:flex; gap:16px; margin-bottom:8px;">
                <div style="flex:1;">
                    <div style="font-size:10px; color:#64748b; text-transform:uppercase; letter-spacing:0.5px;">Strength</div>
                    <div style="font-size:14px; font-weight:600;">{sig['strength']:.0%}</div>
                    {_strength_bar(sig['strength'], '#00d4ff')}
                </div>
                <div style="flex:1;">
                    <div style="font-size:10px; color:#64748b; text-transform:uppercase; letter-spacing:0.5px;">Confidence</div>
                    <div style="font-size:14px; font-weight:600;">{sig['confidence']:.0%}</div>
                    {_strength_bar(sig['confidence'], '#22c55e' if sig['confidence'] > 0.7 else '#eab308')}
                </div>
            </div>
            <div style="font-size:11px; color:#64748b;">
                @ ${sig['price']:,.2f}  •  {_badge(sig['source'], 'blue')}
            </div>
        </div>
        ''', unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Portfolio + Performance ──────────────────────────────────────────
port_col, perf_col = st.columns([3, 2])

with port_col:
    st.markdown(_section("Portfolio Positions", "💼"), unsafe_allow_html=True)

    positions = portfolio['positions']
    if positions:
        # Build a table
        table_html = '''<div class="glass-card" style="padding:16px; overflow-x:auto;">
        <table style="width:100%; border-collapse:collapse; font-size:13px;">
        <tr style="border-bottom:1px solid rgba(148,163,184,0.1);">
            <th style="text-align:left; padding:8px 12px; color:#64748b; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Asset</th>
            <th style="text-align:right; padding:8px 12px; color:#64748b; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Quantity</th>
            <th style="text-align:right; padding:8px 12px; color:#64748b; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Entry</th>
            <th style="text-align:right; padding:8px 12px; color:#64748b; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Current</th>
            <th style="text-align:right; padding:8px 12px; color:#64748b; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Value</th>
            <th style="text-align:right; padding:8px 12px; color:#64748b; font-size:11px; text-transform:uppercase; letter-spacing:1px;">P&L</th>
        </tr>'''

        for pos in positions:
            pnl_color = "var(--green)" if pos['pnl'] >= 0 else "var(--red)"
            table_html += f'''<tr style="border-bottom:1px solid rgba(148,163,184,0.05);">
                <td style="padding:10px 12px; font-weight:600; color:#f1f5f9;">{pos['symbol']}</td>
                <td style="padding:10px 12px; text-align:right; color:#94a3b8;">{pos['quantity']:.4f}</td>
                <td style="padding:10px 12px; text-align:right; color:#94a3b8;">${pos['entry_price']:,.2f}</td>
                <td style="padding:10px 12px; text-align:right; color:#f1f5f9; font-weight:600;">${pos['current_price']:,.2f}</td>
                <td style="padding:10px 12px; text-align:right; color:#f1f5f9;">${pos['value']:,.2f}</td>
                <td style="padding:10px 12px; text-align:right; color:{pnl_color}; font-weight:600;">
                    {_sign(pos['pnl'])}${abs(pos['pnl']):,.2f} <span style="font-size:11px;">({_sign(pos['pnl_pct'])}{abs(pos['pnl_pct']):.2f}%)</span>
                </td>
            </tr>'''

        total_pnl = sum(p['pnl'] for p in positions)
        tp_color = "var(--green)" if total_pnl >= 0 else "var(--red)"
        table_html += f'''<tr style="border-top:2px solid rgba(0,212,255,0.2);">
            <td style="padding:10px 12px; font-weight:700; color:var(--accent);">TOTAL</td>
            <td colspan="3"></td>
            <td style="padding:10px 12px; text-align:right; font-weight:700; color:var(--accent);">${portfolio['total_value']:,.2f}</td>
            <td style="padding:10px 12px; text-align:right; font-weight:700; color:{tp_color};">{_sign(total_pnl)}${abs(total_pnl):,.2f}</td>
        </tr>'''
        table_html += '</table></div>'
        st.markdown(table_html, unsafe_allow_html=True)

    # Allocation donut
    alloc = portfolio.get('allocation', {})
    if alloc:
        colors = ['#00d4ff', '#7c3aed', '#22c55e', '#eab308', '#ef4444', '#ec4899', '#64748b']
        fig_donut = go.Figure(data=[go.Pie(
            labels=list(alloc.keys()),
            values=list(alloc.values()),
            hole=0.65,
            marker=dict(colors=colors[:len(alloc)]),
            textinfo='label+percent',
            textfont=dict(size=12, color='#f1f5f9'),
            hovertemplate='%{label}: $%{value:,.2f}<extra></extra>',
        )])
        fig_donut.update_layout(
            height=260, margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(font=dict(color='#94a3b8', size=11), orientation='h', y=-0.1),
            showlegend=True,
            annotations=[dict(text=f'${portfolio["total_value"]:,.0f}', x=0.5, y=0.5,
                             font=dict(size=18, color='#f1f5f9', family='Inter'), showarrow=False)],
        )
        st.plotly_chart(fig_donut, width='stretch', config={'displayModeBar': False})

with perf_col:
    st.markdown(_section("Performance", "📈"), unsafe_allow_html=True)

    # Key metrics in a 2x2 grid
    p1, p2 = st.columns(2)
    with p1:
        st.markdown(_metric_card("Sharpe Ratio", f"{perf['sharpe_ratio']:.2f}", "",
                                 "green" if perf['sharpe_ratio'] > 1 else "red"), unsafe_allow_html=True)
        st.markdown(_metric_card("Profit Factor", f"{perf['profit_factor']:.2f}", "",
                                 "green" if perf['profit_factor'] > 1 else "red"), unsafe_allow_html=True)
    with p2:
        st.markdown(_metric_card("Win Rate", f"{perf['win_rate']*100:.1f}%", "",
                                 "green" if perf['win_rate'] > 0.5 else "red"), unsafe_allow_html=True)
        st.markdown(_metric_card("Avg Trade", f"${perf['avg_trade']:.2f}", "",
                                 "green" if perf['avg_trade'] > 0 else "red"), unsafe_allow_html=True)

    # Equity curve
    if 'equity_curve' in perf and len(perf['equity_curve']) > 2:
        curve = perf['equity_curve']
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(
            y=curve, mode='lines',
            line=dict(color='#00d4ff', width=2.5),
            fill='tozeroy', fillcolor='rgba(0,212,255,0.06)',
            hovertemplate='$%{y:,.2f}<extra></extra>',
        ))
        fig_eq.update_layout(
            height=200, margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
        )
        st.plotly_chart(fig_eq, width='stretch', config={'displayModeBar': False})

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Trade Log + System Health ────────────────────────────────────────
log_col, health_col = st.columns([3, 2])

with log_col:
    st.markdown(_section("Trade Log", "📋"), unsafe_allow_html=True)

    trades = dp.get_trade_log()
    if trades:
        log_html = '''<div class="glass-card" style="padding:16px; overflow-x:auto; max-height:340px; overflow-y:auto;">
        <table style="width:100%; border-collapse:collapse; font-size:12px;">
        <tr style="border-bottom:1px solid rgba(148,163,184,0.1); position:sticky; top:0; background:rgba(17,24,39,0.95);">
            <th style="text-align:left; padding:6px 10px; color:#64748b; font-size:10px; text-transform:uppercase;">Time</th>
            <th style="text-align:left; padding:6px 10px; color:#64748b; font-size:10px; text-transform:uppercase;">Asset</th>
            <th style="text-align:left; padding:6px 10px; color:#64748b; font-size:10px; text-transform:uppercase;">Side</th>
            <th style="text-align:right; padding:6px 10px; color:#64748b; font-size:10px; text-transform:uppercase;">Price</th>
            <th style="text-align:right; padding:6px 10px; color:#64748b; font-size:10px; text-transform:uppercase;">Qty</th>
            <th style="text-align:right; padding:6px 10px; color:#64748b; font-size:10px; text-transform:uppercase;">Value</th>
            <th style="text-align:center; padding:6px 10px; color:#64748b; font-size:10px; text-transform:uppercase;">Status</th>
            <th style="text-align:right; padding:6px 10px; color:#64748b; font-size:10px; text-transform:uppercase;">P&L</th>
        </tr>'''

        for t in trades:
            side_color = "var(--green)" if t['side'] == 'BUY' else "var(--red)"
            side_icon = "▲" if t['side'] == 'BUY' else "▼"
            status_variant = "green" if t['status'] == 'FILLED' else "yellow"
            pnl_str = ""
            if t.get('pnl') is not None:
                pnl_color = "var(--green)" if t['pnl'] >= 0 else "var(--red)"
                pnl_str = f'<span style="color:{pnl_color}; font-weight:600;">{_sign(t["pnl"])}${abs(t["pnl"]):.2f}</span>'

            log_html += f'''<tr style="border-bottom:1px solid rgba(148,163,184,0.04);">
                <td style="padding:8px 10px; color:#94a3b8;">{t['timestamp'].strftime('%H:%M')}</td>
                <td style="padding:8px 10px; font-weight:600; color:#f1f5f9;">{t['symbol']}</td>
                <td style="padding:8px 10px; color:{side_color}; font-weight:600;">{side_icon} {t['side']}</td>
                <td style="padding:8px 10px; text-align:right; color:#94a3b8;">${t['price']:,.2f}</td>
                <td style="padding:8px 10px; text-align:right; color:#94a3b8;">{t['quantity']:.4f}</td>
                <td style="padding:8px 10px; text-align:right; color:#f1f5f9;">${t['value']:,.2f}</td>
                <td style="padding:8px 10px; text-align:center;">{_badge(t['status'], status_variant)}</td>
                <td style="padding:8px 10px; text-align:right;">{pnl_str}</td>
            </tr>'''

        log_html += '</table></div>'
        st.markdown(log_html, unsafe_allow_html=True)

with health_col:
    st.markdown(_section("System Health", "🖥️"), unsafe_allow_html=True)

    health = dp.get_system_health()

    st.markdown(f'''
    <div class="glass-card" style="padding:20px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:20px;">
            <div>
                <div style="font-size:11px; color:#64748b; text-transform:uppercase; letter-spacing:1px;">Status</div>
                <div style="font-size:15px; font-weight:700; color:var(--green); margin-top:4px;">
                    <span class="status-dot {'online' if not dp.is_demo else 'demo'}"></span>
                    {health['status']}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:11px; color:#64748b; text-transform:uppercase; letter-spacing:1px;">Uptime</div>
                <div style="font-size:15px; font-weight:600; color:#f1f5f9; margin-top:4px;">{health['uptime']}</div>
            </div>
        </div>

        <div style="margin-bottom:16px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                <span style="font-size:12px; color:#94a3b8;">CPU Usage</span>
                <span style="font-size:12px; font-weight:600; color:#f1f5f9;">{health['cpu_percent']:.1f}%</span>
            </div>
            {_strength_bar(health['cpu_percent']/100, '#22c55e' if health['cpu_percent'] < 70 else '#eab308' if health['cpu_percent'] < 90 else '#ef4444')}
        </div>

        <div style="margin-bottom:16px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                <span style="font-size:12px; color:#94a3b8;">Memory Usage</span>
                <span style="font-size:12px; font-weight:600; color:#f1f5f9;">{health['memory_used_gb']:.1f} / {health['memory_total_gb']:.1f} GB</span>
            </div>
            {_strength_bar(health['memory_percent']/100, '#00d4ff' if health['memory_percent'] < 70 else '#eab308' if health['memory_percent'] < 90 else '#ef4444')}
        </div>

        <div style="display:flex; justify-content:space-between; padding-top:12px; border-top:1px solid rgba(148,163,184,0.1);">
            <div>
                <div style="font-size:10px; color:#64748b; text-transform:uppercase;">Cycle</div>
                <div style="font-size:14px; font-weight:600; color:var(--accent);">#{health.get('cycle', 0)}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:10px; color:#64748b; text-transform:uppercase;">Memory %</div>
                <div style="font-size:14px; font-weight:600; color:#f1f5f9;">{health['memory_percent']:.1f}%</div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

# ── Auto Refresh ─────────────────────────────────────────────────────
if auto_refresh:
    import time
    time.sleep(60)
    st.rerun()
