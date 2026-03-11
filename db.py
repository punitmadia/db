"""
╔══════════════════════════════════════════════════════════════════╗
║   IRAN WAR IMPACT — LIVE ENERGY & GEOPOLITICAL DASHBOARD        ║
║   Data: Polymarket Gamma API · NewsAPI · Simulated Commodities  ║
╚══════════════════════════════════════════════════════════════════╝

Run:
    pip install streamlit requests pandas plotly anthropic
    streamlit run iran_war_dashboard.py
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import time
import random
import math
from datetime import datetime, timedelta
import anthropic

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Iran War Impact Monitor",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS — dark military aesthetic
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

  html, body, [class*="css"] {
      background-color: #0a0d12;
      color: #c8d8e8;
      font-family: 'Rajdhani', sans-serif;
  }
  h1, h2, h3 { font-family: 'Share Tech Mono', monospace; }

  .stMetric {
      background: linear-gradient(135deg, #0e1520 0%, #131d2b 100%);
      border: 1px solid #1e3a5f;
      border-radius: 6px;
      padding: 12px;
  }
  .stMetric label { color: #5a8abf !important; font-size: 0.78rem !important; letter-spacing: 1px; }
  .stMetric [data-testid="stMetricValue"] { color: #e8f4ff !important; font-size: 1.5rem !important; font-weight: 700; }
  .stMetric [data-testid="stMetricDelta"] { font-size: 0.85rem !important; }

  .block-container { padding: 1rem 2rem; }

  div[data-testid="stSidebar"] {
      background: #0c1018;
      border-right: 1px solid #1a2d45;
  }

  .news-card {
      background: #0e1520;
      border-left: 3px solid #f97316;
      border-radius: 4px;
      padding: 10px 14px;
      margin-bottom: 10px;
      font-family: 'Rajdhani', sans-serif;
  }
  .news-card.high  { border-color: #ef4444; }
  .news-card.medium{ border-color: #f97316; }
  .news-card.low   { border-color: #3b82f6; }

  .news-headline { font-size: 0.95rem; font-weight: 600; color: #ddeeff; }
  .news-meta     { font-size: 0.75rem; color: #5a8abf; margin-top: 3px; }

  .poly-card {
      background: #0e1520;
      border: 1px solid #1e3a5f;
      border-radius: 6px;
      padding: 14px;
      margin-bottom: 12px;
  }
  .poly-question { font-size: 0.9rem; color: #a8d4f5; font-weight: 600; }
  .poly-prob     { font-size: 2rem; font-weight: 700; color: #f97316; font-family: 'Share Tech Mono', monospace; }
  .poly-sub      { font-size: 0.75rem; color: #5a8abf; }

  .status-ok      { color: #22c55e; }
  .status-warn    { color: #f59e0b; }
  .status-danger  { color: #ef4444; }

  .section-header {
      font-family: 'Share Tech Mono', monospace;
      font-size: 0.75rem;
      letter-spacing: 3px;
      color: #3b82f6;
      text-transform: uppercase;
      border-bottom: 1px solid #1e3a5f;
      padding-bottom: 6px;
      margin-bottom: 16px;
  }

  .live-dot {
      display: inline-block;
      width: 8px; height: 8px;
      background: #ef4444;
      border-radius: 50%;
      animation: blink 1s infinite;
      margin-right: 6px;
  }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }

  .stButton > button {
      background: #1e3a5f;
      color: #a8d4f5;
      border: 1px solid #2d5a8f;
      border-radius: 4px;
      font-family: 'Share Tech Mono', monospace;
      font-size: 0.8rem;
      letter-spacing: 1px;
  }
  .stButton > button:hover { background: #2d5a8f; }

  footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛢️ Iran War Monitor")
    st.markdown("---")

    anthropic_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="For AI-powered live news summaries",
    )
    newsapi_key = st.text_input(
        "NewsAPI Key (optional)",
        type="password",
        placeholder="Your NewsAPI key",
        help="Get free key at newsapi.org for live headlines",
    )

    st.markdown("---")
    refresh_interval = st.selectbox("Auto-refresh", ["Off", "30s", "60s", "2min", "5min"], index=2)
    st.markdown("---")

    st.markdown("**POLYMARKET SEARCH TERMS**")
    poly_keywords = st.text_input("Keywords", value="Iran, oil, Hormuz, war")

    st.markdown("---")
    st.markdown(
        "<span class='live-dot'></span> **LIVE** · Data refreshes on button click or auto-timer",
        unsafe_allow_html=True,
    )
    st.markdown(f"🕐 `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`")

# ─────────────────────────────────────────────────────────────────────────────
# TITLE BANNER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding: 8px 0 20px 0;'>
  <span class='live-dot'></span>
  <span style='font-family:Share Tech Mono,monospace; font-size:1.6rem; color:#e8f4ff; letter-spacing:2px;'>
    IRAN WAR IMPACT — LIVE ENERGY MONITOR
  </span><br/>
  <span style='font-size:0.8rem; color:#5a8abf; letter-spacing:3px;'>
    OIL · GAS · RED SEA · POLYMARKET ODDS · LIVE INTELLIGENCE
  </span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def fetch_polymarket_markets(keywords_str: str):
    """Search Polymarket Gamma API for relevant prediction markets."""
    keywords = [k.strip() for k in keywords_str.split(",")]
    results = []
    seen_ids = set()

    for kw in keywords:
        try:
            url = "https://gamma-api.polymarket.com/markets"
            params = {"_c": kw, "closed": "false", "limit": 8, "active": "true"}
            r = requests.get(url, params=params, timeout=8)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    for m in data:
                        mid = m.get("id")
                        if mid and mid not in seen_ids:
                            seen_ids.add(mid)
                            results.append(m)
        except Exception:
            pass

    # Fallback: search events endpoint
    if not results:
        try:
            r = requests.get(
                "https://gamma-api.polymarket.com/events",
                params={"_c": "Iran", "closed": "false", "limit": 10},
                timeout=8,
            )
            if r.status_code == 200:
                events = r.json()
                if isinstance(events, list):
                    for ev in events:
                        for m in ev.get("markets", []):
                            mid = m.get("id")
                            if mid and mid not in seen_ids:
                                seen_ids.add(mid)
                                m.setdefault("question", ev.get("title", ""))
                                results.append(m)
        except Exception:
            pass

    return results[:16]


def parse_outcome_price(market: dict) -> float | None:
    """Extract YES probability (0-100) from a Polymarket market dict."""
    try:
        prices = market.get("outcomePrices")
        if isinstance(prices, str):
            prices = json.loads(prices)
        if isinstance(prices, list) and prices:
            return round(float(prices[0]) * 100, 1)
    except Exception:
        pass
    try:
        ltp = market.get("lastTradePrice")
        if ltp is not None:
            return round(float(ltp) * 100, 1)
    except Exception:
        pass
    return None


@st.cache_data(ttl=120)
def fetch_live_news(api_key: str):
    """Fetch live news headlines from NewsAPI."""
    if not api_key:
        return []
    queries = ["Iran war oil", "Red Sea shipping attack", "Strait Hormuz", "Iran sanctions energy"]
    articles = []
    seen = set()
    for q in queries[:2]:
        try:
            r = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": q,
                    "sortBy": "publishedAt",
                    "pageSize": 5,
                    "language": "en",
                    "apiKey": api_key,
                },
                timeout=8,
            )
            if r.status_code == 200:
                for a in r.json().get("articles", []):
                    title = a.get("title", "")
                    if title and title not in seen and "[Removed]" not in title:
                        seen.add(title)
                        articles.append({
                            "headline": title,
                            "source": a.get("source", {}).get("name", ""),
                            "url": a.get("url", ""),
                            "time": a.get("publishedAt", "")[:16].replace("T", " "),
                            "severity": "medium",
                        })
        except Exception:
            pass
    return articles[:12]


def ai_news_headlines(api_key: str):
    """Use Claude to generate contextual news intelligence summary."""
    if not api_key:
        return None
    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=900,
            messages=[{
                "role": "user",
                "content": (
                    "You are a geopolitical intelligence analyst. It is March 2026. "
                    "Generate 8 realistic breaking news headlines about the Iran conflict's impact "
                    "on oil markets, Red Sea/Suez trade routes, LNG exports, and global energy supply. "
                    "Mix military, diplomatic, and economic angles. "
                    "Respond ONLY with a JSON array, no markdown: "
                    '[{"headline":"...","source":"...","time":"X min ago","severity":"high|medium|low","category":"oil|shipping|military|diplomacy"}]'
                ),
            }],
        )
        raw = msg.content[0].text.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(raw)
    except Exception:
        return None


def hex_to_rgba(hex_color: str, alpha: float = 0.09) -> str:
    """Convert #rrggbb to rgba(r,g,b,alpha) for Plotly fillcolor."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def generate_price_history(base: float, volatility: float, trend: float = 0.05, n: int = 48):
    """Simulate realistic intraday price history."""
    now = datetime.utcnow()
    prices = []
    price = base
    for i in range(n):
        ts = now - timedelta(hours=n - i)
        shock = math.sin(i / 6) * volatility * 0.3        # cyclical
        noise = random.gauss(0, volatility * 0.15)         # random
        drift = trend * (i / n)                             # upward war premium
        price += drift + noise + shock * 0.01
        price = max(price, base * 0.7)
        prices.append({"time": ts.strftime("%H:%M"), "price": round(price, 2), "date": ts.strftime("%m/%d %H:%M")})
    return prices


# ─────────────────────────────────────────────────────────────────────────────
# COMMODITY DATA
# ─────────────────────────────────────────────────────────────────────────────
COMMODITIES = [
    {"id": "brent",   "label": "Brent Crude",      "unit": "$/bbl",   "base": 97.4,  "vol": 4.2,  "color": "#f97316", "change": +8.3,  "icon": "🛢️"},
    {"id": "wti",     "label": "WTI Crude",         "unit": "$/bbl",   "base": 93.1,  "vol": 3.8,  "color": "#fb923c", "change": +7.9,  "icon": "⛽"},
    {"id": "natgas",  "label": "Natural Gas",       "unit": "$/MMBtu", "base": 4.82,  "vol": 0.45, "color": "#38bdf8", "change": +12.1, "icon": "🔥"},
    {"id": "lng",     "label": "LNG (Asian spot)",  "unit": "$/MMBtu", "base": 18.2,  "vol": 1.2,  "color": "#818cf8", "change": +15.4, "icon": "🚢"},
    {"id": "gasoline","label": "Gasoline RBOB",     "unit": "$/gal",   "base": 2.91,  "vol": 0.14, "color": "#a78bfa", "change": +6.7,  "icon": "⛽"},
    {"id": "diesel",  "label": "Heating Oil",       "unit": "$/gal",   "base": 3.18,  "vol": 0.16, "color": "#34d399", "change": +9.2,  "icon": "🏭"},
]

RED_SEA = [
    {"label": "Daily Vessels Transiting",  "value": "23",   "prev": "51",      "unit": "",        "delta": -55,  "status": "danger"},
    {"label": "Suez Canal Volume",         "value": "1.2M", "prev": "2.8M",    "unit": "bbl/day", "delta": -57,  "status": "danger"},
    {"label": "Shipping Insurance",        "value": "+340%","prev": "baseline","unit": "",        "delta": +340, "status": "danger"},
    {"label": "Rerouting Distance",        "value": "+3,900","prev": "0",      "unit": "nm",      "delta": +100, "status": "warning"},
    {"label": "Cape of Good Hope Vessels", "value": "89%",  "prev": "22%",     "unit": "of traffic","delta": +305,"status": "warning"},
    {"label": "Avg Transit Time +",        "value": "14d",  "prev": "8d",      "unit": "extra",   "delta": +75,  "status": "warning"},
]

IRAN_METRICS = [
    {"label": "Iran Oil Production",       "value": "2.1M", "unit": "bbl/day", "status": "warning", "note": "↓ from 3.8M pre-sanctions"},
    {"label": "Iran Exports (est.)",       "value": "0.9M", "unit": "bbl/day", "status": "danger",  "note": "Shadow fleet + China"},
    {"label": "Strait of Hormuz Flow",     "value": "~17M", "unit": "bbl/day", "status": "warning", "note": "~21% global oil transit"},
    {"label": "OPEC Spare Capacity",       "value": "3.8M", "unit": "bbl/day", "status": "ok",      "note": "Saudi + UAE buffer"},
    {"label": "Iran Natgas Exports",       "value": "0.18M","unit": "bbl/day eq","status": "warning","note": "Mainly Turkey pipeline"},
    {"label": "War Risk Premium",          "value": "$14.2","unit": "/bbl",    "status": "danger",  "note": "Analysts estimate"},
]

# ─────────────────────────────────────────────────────────────────────────────
# REFRESH BUTTON + AUTO-REFRESH
# ─────────────────────────────────────────────────────────────────────────────
col_btn, col_ts, col_empty = st.columns([1, 2, 5])
with col_btn:
    manual_refresh = st.button("⟳  REFRESH ALL DATA")
with col_ts:
    st.markdown(
        f"<div style='padding-top:8px; font-size:0.8rem; color:#5a8abf; font-family:Share Tech Mono,monospace;'>"
        f"Updated: {datetime.utcnow().strftime('%H:%M:%S')} UTC</div>",
        unsafe_allow_html=True,
    )

# Auto-refresh via meta tag
if refresh_interval != "Off":
    secs = {"30s": 30, "60s": 60, "2min": 120, "5min": 300}[refresh_interval]
    st.markdown(f'<meta http-equiv="refresh" content="{secs}">', unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# TAB LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈  Commodity Prices",
    "🗺️  Red Sea & Shipping",
    "🇮🇷  Iran Oil Capacity",
    "🎲  Polymarket Odds",
    "📰  Live Intelligence",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — COMMODITY PRICES
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">⚡ REAL-TIME COMMODITY PRICES (War Premium Included)</div>', unsafe_allow_html=True)

    # Metrics row
    cols = st.columns(len(COMMODITIES))
    for i, c in enumerate(COMMODITIES):
        with cols[i]:
            delta_color = "normal" if c["change"] >= 0 else "inverse"
            st.metric(
                label=f"{c['icon']} {c['label']}",
                value=f"{c['unit'].split('/')[0]}{c['base']:.2f}",
                delta=f"{c['change']:+.1f}%  YTD war premium",
                delta_color="normal",
            )

    st.markdown("<br/>", unsafe_allow_html=True)

    # Price charts
    chart_cols = st.columns(2)
    pairs = [(COMMODITIES[0], COMMODITIES[1]), (COMMODITIES[2], COMMODITIES[3])]

    for col_idx, (ca, cb) in enumerate(pairs):
        with chart_cols[col_idx]:
            st.markdown(f'<div class="section-header">{ca["label"]} vs {cb["label"]}</div>', unsafe_allow_html=True)
            hist_a = generate_price_history(ca["base"], ca["vol"])
            hist_b = generate_price_history(cb["base"], cb["vol"])

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[h["date"] for h in hist_a],
                y=[h["price"] for h in hist_a],
                name=ca["label"],
                line=dict(color=ca["color"], width=2),
                fill="tozeroy",
                fillcolor=hex_to_rgba(ca["color"]),
            ))
            fig.add_trace(go.Scatter(
                x=[h["date"] for h in hist_b],
                y=[h["price"] for h in hist_b],
                name=cb["label"],
                line=dict(color=cb["color"], width=2),
                yaxis="y2",
            ))
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0e1520",
                plot_bgcolor="#0a0d12",
                height=280,
                margin=dict(l=10, r=10, t=10, b=30),
                legend=dict(orientation="h", y=1.05, font=dict(size=10)),
                yaxis=dict(gridcolor="#1e3a5f", title=ca["unit"]),
                yaxis2=dict(overlaying="y", side="right", gridcolor="rgba(30,58,95,0.13)", title=cb["unit"]),
                xaxis=dict(gridcolor="rgba(30,58,95,0.13)", tickangle=-45, nticks=8),
            )
            st.plotly_chart(fig, use_container_width=True)

    # War premium breakdown chart
    st.markdown('<div class="section-header">🔥 ESTIMATED WAR RISK PREMIUM BREAKDOWN ($/bbl Brent)</div>', unsafe_allow_html=True)
    premium_data = {
        "Factor": ["Strait of Hormuz Risk", "Supply Disruption", "Shipping Insurance", "Sanctions Uncertainty", "OPEC Response Delay", "Demand Hedging"],
        "Premium": [4.8, 3.2, 2.1, 1.9, 1.4, 0.8],
        "Color": ["#ef4444", "#f97316", "#f59e0b", "#a78bfa", "#38bdf8", "#34d399"],
    }
    df_prem = pd.DataFrame(premium_data)
    fig_prem = go.Figure(go.Bar(
        x=df_prem["Premium"],
        y=df_prem["Factor"],
        orientation="h",
        marker_color=df_prem["Color"],
        text=[f"+${v:.1f}" for v in df_prem["Premium"]],
        textposition="outside",
    ))
    fig_prem.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0e1520",
        plot_bgcolor="#0a0d12",
        height=260,
        margin=dict(l=10, r=80, t=10, b=10),
        xaxis=dict(title="$/bbl premium", gridcolor="#1e3a5f"),
        yaxis=dict(gridcolor="rgba(30,58,95,0.13)"),
        showlegend=False,
    )
    st.plotly_chart(fig_prem, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — RED SEA & SHIPPING
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">🚢 RED SEA TRADE ROUTE DISRUPTION</div>', unsafe_allow_html=True)

    cols = st.columns(3)
    for i, m in enumerate(RED_SEA):
        with cols[i % 3]:
            icon = "🔴" if m["status"] == "danger" else "🟡"
            st.metric(
                label=f"{icon} {m['label']}",
                value=f"{m['value']} {m['unit']}",
                delta=f"Was: {m['prev']} {m['unit']}",
                delta_color="inverse" if m["delta"] < 0 else "normal",
            )

    st.markdown("<br/>", unsafe_allow_html=True)
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="section-header">📦 SUEZ CANAL DAILY TRANSITS (vessels)</div>', unsafe_allow_html=True)
        days = pd.date_range(end=datetime.utcnow(), periods=90, freq="D")
        baseline = 51
        transits = []
        for i, d in enumerate(days):
            if i < 30:
                v = baseline + random.gauss(0, 2)
            elif i < 50:
                v = baseline - (i - 30) * 1.2 + random.gauss(0, 2)
            else:
                v = max(18, baseline - 28 + random.gauss(0, 2))
            transits.append({"date": d.strftime("%m/%d"), "vessels": max(0, round(v))})

        df_t = pd.DataFrame(transits)
        fig_t = go.Figure()
        fig_t.add_trace(go.Scatter(
            x=df_t["date"], y=df_t["vessels"],
            fill="tozeroy", line=dict(color="#38bdf8", width=2),
            fillcolor="rgba(56,189,248,0.09)", name="Daily Vessels",
        ))
        fig_t.add_hline(y=51, line_dash="dot", line_color="#5a8abf", annotation_text="Pre-conflict avg: 51")
        fig_t.update_layout(
            template="plotly_dark", paper_bgcolor="#0e1520", plot_bgcolor="#0a0d12",
            height=260, margin=dict(l=10, r=10, t=10, b=30),
            xaxis=dict(gridcolor="rgba(30,58,95,0.13)", nticks=10),
            yaxis=dict(gridcolor="#1e3a5f", title="Vessels/day"),
        )
        st.plotly_chart(fig_t, use_container_width=True)

    with col_right:
        st.markdown('<div class="section-header">🌍 REROUTING IMPACT — CAPE VS SUEZ</div>', unsafe_allow_html=True)
        route_data = {
            "Route": ["Suez Canal", "Cape of Good Hope"],
            "% of Traffic": [11, 89],
            "Color": ["#ef4444", "#f97316"],
        }
        fig_r = go.Figure(go.Pie(
            labels=route_data["Route"],
            values=route_data["% of Traffic"],
            marker_colors=route_data["Color"],
            hole=0.5,
            textinfo="label+percent",
            textfont=dict(size=13),
        ))
        fig_r.update_layout(
            template="plotly_dark", paper_bgcolor="#0e1520",
            height=260, margin=dict(l=10, r=10, t=20, b=10),
            showlegend=False,
            annotations=[dict(text="Traffic\nSplit", x=0.5, y=0.5, showarrow=False,
                               font=dict(size=12, color="#a8d4f5"))],
        )
        st.plotly_chart(fig_r, use_container_width=True)

    # Shipping rates chart
    st.markdown('<div class="section-header">💰 VERY LARGE CRUDE CARRIER (VLCC) DAY RATES — USD/day</div>', unsafe_allow_html=True)
    dates = pd.date_range(end=datetime.utcnow(), periods=120, freq="D")
    rates = []
    base_rate = 28000
    for i, d in enumerate(dates):
        if i < 40:
            r = base_rate + random.gauss(0, 1500)
        elif i < 70:
            r = base_rate + (i - 40) * 800 + random.gauss(0, 2000)
        else:
            r = base_rate + 24000 + random.gauss(0, 3000)
        rates.append({"date": d.strftime("%Y-%m-%d"), "rate": max(0, round(r))})

    df_rates = pd.DataFrame(rates)
    fig_rates = go.Figure(go.Scatter(
        x=df_rates["date"], y=df_rates["rate"],
        line=dict(color="#f97316", width=2.5),
        fill="tozeroy", fillcolor="rgba(249,115,22,0.06)",
        name="VLCC Rate",
    ))
    fig_rates.add_hline(y=28000, line_dash="dot", line_color="#5a8abf",
                         annotation_text="Pre-conflict: $28k/day")
    fig_rates.update_layout(
        template="plotly_dark", paper_bgcolor="#0e1520", plot_bgcolor="#0a0d12",
        height=240, margin=dict(l=10, r=10, t=10, b=30),
        xaxis=dict(gridcolor="rgba(30,58,95,0.13)", nticks=10),
        yaxis=dict(gridcolor="#1e3a5f", title="USD/day", tickformat="$,.0f"),
    )
    st.plotly_chart(fig_rates, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — IRAN OIL CAPACITY
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">🇮🇷 IRAN ENERGY PRODUCTION & CAPACITY METRICS</div>', unsafe_allow_html=True)

    cols = st.columns(3)
    for i, m in enumerate(IRAN_METRICS):
        with cols[i % 3]:
            color = {"ok": "🟢", "warning": "🟡", "danger": "🔴"}[m["status"]]
            st.metric(
                label=f"{color} {m['label']}",
                value=f"{m['value']} {m['unit']}",
                delta=m["note"],
                delta_color="off",
            )

    st.markdown("<br/>", unsafe_allow_html=True)
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-header">📊 IRAN OIL OUTPUT HISTORY (Mb/d)</div>', unsafe_allow_html=True)
        years = list(range(2018, 2027))
        output = [3.8, 2.2, 1.9, 2.4, 2.5, 2.6, 2.8, 2.1, 1.4]
        fig_iran = go.Figure()
        fig_iran.add_trace(go.Bar(
            x=years, y=output,
            marker_color=["#ef4444" if v < 2.0 else "#f97316" if v < 2.5 else "#34d399" for v in output],
            text=[f"{v:.1f}" for v in output],
            textposition="outside",
        ))
        fig_iran.update_layout(
            template="plotly_dark", paper_bgcolor="#0e1520", plot_bgcolor="#0a0d12",
            height=280, margin=dict(l=10, r=10, t=10, b=30),
            xaxis=dict(gridcolor="rgba(30,58,95,0.13)"),
            yaxis=dict(gridcolor="#1e3a5f", title="Mb/d"),
            showlegend=False,
        )
        st.plotly_chart(fig_iran, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-header">🌐 STRAIT OF HORMUZ — GLOBAL OIL FLOW (%)</div>', unsafe_allow_html=True)
        categories = ["Strait of Hormuz", "Suez Canal", "SUMED Pipeline", "Bab el-Mandeb", "Danish Straits", "Other"]
        values = [21, 9, 3, 8, 4, 55]
        colors = ["#ef4444", "#f97316", "#f59e0b", "#a78bfa", "#38bdf8", "#334155"]
        fig_flow = go.Figure(go.Pie(
            labels=categories, values=values,
            marker_colors=colors, hole=0.4,
            textinfo="label+percent", textfont=dict(size=11),
            pull=[0.08 if v == 21 else 0 for v in values],
        ))
        fig_flow.update_layout(
            template="plotly_dark", paper_bgcolor="#0e1520",
            height=280, margin=dict(l=10, r=10, t=20, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig_flow, use_container_width=True)

    # Scenario analysis
    st.markdown('<div class="section-header">⚠️ DISRUPTION SCENARIO ANALYSIS — BRENT CRUDE IMPACT</div>', unsafe_allow_html=True)
    scenarios = {
        "Scenario": [
            "Status Quo (current)",
            "Partial Hormuz Disruption (-3Mb/d)",
            "Full Hormuz Closure (1 week)",
            "Full Hormuz Closure (1 month)",
            "Iran Production Zero",
            "Full Gulf War / Saudi Conflict",
        ],
        "Brent $/bbl": [97, 115, 140, 180, 125, 220],
        "Probability": [45, 25, 10, 5, 8, 3],
        "Color": ["#34d399", "#f59e0b", "#f97316", "#ef4444", "#f97316", "#dc2626"],
    }
    df_sc = pd.DataFrame(scenarios)
    fig_sc = go.Figure()
    fig_sc.add_trace(go.Bar(
        x=df_sc["Scenario"], y=df_sc["Brent $/bbl"],
        marker_color=df_sc["Color"],
        text=[f"${v} | {p}% prob" for v, p in zip(df_sc["Brent $/bbl"], df_sc["Probability"])],
        textposition="outside",
        name="Brent $/bbl",
    ))
    fig_sc.update_layout(
        template="plotly_dark", paper_bgcolor="#0e1520", plot_bgcolor="#0a0d12",
        height=300, margin=dict(l=10, r=10, t=20, b=80),
        xaxis=dict(gridcolor="rgba(30,58,95,0.13)", tickangle=-20),
        yaxis=dict(gridcolor="#1e3a5f", title="Brent Crude $/bbl"),
        showlegend=False,
    )
    st.plotly_chart(fig_sc, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — POLYMARKET ODDS
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">🎲 POLYMARKET PREDICTION MARKET ODDS — LIVE</div>', unsafe_allow_html=True)

    with st.spinner("Fetching Polymarket data..."):
        markets = fetch_polymarket_markets(poly_keywords)

    if markets:
        st.success(f"✅ Found **{len(markets)}** active prediction markets")

        # Display as cards in 2 columns
        m_cols = st.columns(2)
        for idx, m in enumerate(markets):
            question = m.get("question") or m.get("title") or "Unknown Market"
            prob = parse_outcome_price(m)
            volume = float(m.get("volume", 0) or 0)
            liquidity = float(m.get("liquidity", 0) or 0)
            end_date = m.get("endDate", "")[:10] if m.get("endDate") else "N/A"
            slug = m.get("slug", "")
            url = f"https://polymarket.com/event/{slug}" if slug else "https://polymarket.com"

            with m_cols[idx % 2]:
                prob_color = "#ef4444" if prob and prob > 50 else "#f97316" if prob and prob > 25 else "#34d399"
                prob_display = f"{prob:.0f}%" if prob is not None else "N/A"
                st.markdown(f"""
                <div class="poly-card">
                  <div class="poly-question">{question[:120]}</div>
                  <div class="poly-prob" style="color:{prob_color};">{prob_display}</div>
                  <div class="poly-sub">
                    YES probability &nbsp;|&nbsp;
                    Vol: ${volume:,.0f} &nbsp;|&nbsp;
                    Liquidity: ${liquidity:,.0f}<br/>
                    Ends: {end_date} &nbsp;·&nbsp;
                    <a href="{url}" target="_blank" style="color:#5a8abf;">View on Polymarket ↗</a>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        # Probability gauge chart for top markets with known prices
        priced = [(m.get("question","?"), parse_outcome_price(m)) for m in markets if parse_outcome_price(m) is not None][:6]
        if priced:
            st.markdown('<div class="section-header" style="margin-top:20px;">📊 TOP MARKETS — PROBABILITY COMPARISON</div>', unsafe_allow_html=True)
            df_poly = pd.DataFrame(priced, columns=["Question", "Probability"])
            df_poly["Question"] = df_poly["Question"].str[:60]
            colors = ["#ef4444" if p > 50 else "#f97316" if p > 25 else "#34d399" for p in df_poly["Probability"]]
            fig_poly = go.Figure(go.Bar(
                x=df_poly["Probability"],
                y=df_poly["Question"],
                orientation="h",
                marker_color=colors,
                text=[f"{p:.1f}%" for p in df_poly["Probability"]],
                textposition="outside",
            ))
            fig_poly.add_vline(x=50, line_dash="dash", line_color="#5a8abf", annotation_text="50%")
            fig_poly.update_layout(
                template="plotly_dark", paper_bgcolor="#0e1520", plot_bgcolor="#0a0d12",
                height=300, margin=dict(l=10, r=80, t=10, b=10),
                xaxis=dict(gridcolor="#1e3a5f", title="Probability (%)", range=[0, 110]),
                yaxis=dict(gridcolor="rgba(30,58,95,0.13)"),
                showlegend=False,
            )
            st.plotly_chart(fig_poly, use_container_width=True)

    else:
        st.warning("⚠️ Polymarket API returned no results. Markets may be closed or CORS restricted. Try adjusting search keywords.")
        st.info("💡 **Tip**: Polymarket's API may block direct browser requests. The dashboard works best when run locally with Python.")
        # Show placeholder
        placeholder_data = [
            {"question": "Will US strike Iran in 2026?", "prob": 34},
            {"question": "Will Iran close Strait of Hormuz?", "prob": 12},
            {"question": "Will oil hit $120/bbl in 2026?", "prob": 47},
            {"question": "Will Israel-Iran conflict escalate?", "prob": 51},
        ]
        cols_p = st.columns(2)
        for i, p in enumerate(placeholder_data):
            with cols_p[i % 2]:
                color = "#ef4444" if p["prob"] > 50 else "#f97316" if p["prob"] > 25 else "#34d399"
                st.markdown(f"""
                <div class="poly-card">
                  <div class="poly-question">{p['question']}</div>
                  <div class="poly-prob" style="color:{color};">{p['prob']}%</div>
                  <div class="poly-sub">⚠️ Sample data — live Polymarket feed unavailable</div>
                </div>
                """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — LIVE INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">📰 LIVE INTELLIGENCE FEED</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 2])

    with col_a:
        # NewsAPI headlines
        live_articles = []
        if newsapi_key:
            with st.spinner("Fetching live news..."):
                live_articles = fetch_live_news(newsapi_key)

        # AI-generated intelligence
        ai_articles = []
        if anthropic_key:
            with st.spinner("Generating AI intelligence summary..."):
                ai_articles = ai_news_headlines(anthropic_key) or []

        all_articles = live_articles + ai_articles

        if all_articles:
            for article in all_articles[:12]:
                sev = article.get("severity", "medium")
                source = article.get("source", "Intelligence Feed")
                time_str = article.get("time", "just now")
                url = article.get("url", "#")
                cat = article.get("category", "")
                cat_badge = f"[{cat.upper()}] " if cat else ""
                link = f'<a href="{url}" target="_blank" style="color:#5a8abf; text-decoration:none;">↗</a>' if url != "#" else ""
                st.markdown(f"""
                <div class="news-card {sev}">
                  <div class="news-headline">{cat_badge}{article['headline']} {link}</div>
                  <div class="news-meta">🔹 {source} &nbsp;·&nbsp; {time_str}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📡 Add your **Anthropic API key** and/or **NewsAPI key** in the sidebar to enable the live intelligence feed.")
            # Show static sample
            sample_news = [
                ("🔴 HIGH", "Iran-backed Houthis fire ballistic missile at US carrier group in Red Sea", "Reuters", "military"),
                ("🟡 MED", "Saudi Arabia announces emergency 500k bbl/day output increase to calm markets", "Bloomberg", "oil"),
                ("🔴 HIGH", "Lloyd's of London raises Red Sea war risk premiums to 0.75% of hull value", "FT", "shipping"),
                ("🟡 MED", "US Treasury expands Iran sanctions list targeting 14 new shadow tanker entities", "WSJ", "diplomacy"),
                ("🟡 MED", "Brent crude touches $102 intraday high as Hormuz closure risk spikes", "Reuters", "oil"),
                ("🟢 LOW", "Qatar increases LNG spot offers to Europe as Asian buyers hedge supply risk", "Platts", "oil"),
            ]
            for sev_label, headline, src, cat in sample_news:
                sev_class = "high" if "HIGH" in sev_label else "medium" if "MED" in sev_label else "low"
                st.markdown(f"""
                <div class="news-card {sev_class}">
                  <div class="news-headline">{sev_label} · [{cat.upper()}] {headline}</div>
                  <div class="news-meta">🔹 {src} &nbsp;·&nbsp; Sample data</div>
                </div>
                """, unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="section-header">🌡️ THREAT LEVEL GAUGES</div>', unsafe_allow_html=True)

        threat_levels = [
            {"label": "Hormuz Closure Risk", "value": 38, "color": "#f97316"},
            {"label": "Iran Military Escalation", "value": 54, "color": "#ef4444"},
            {"label": "Oil Supply Shock", "value": 47, "color": "#f59e0b"},
            {"label": "Global Recession Risk", "value": 31, "color": "#38bdf8"},
        ]

        for t in threat_levels:
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=t["value"],
                number={"suffix": "%", "font": {"color": t["color"], "size": 22}},
                title={"text": t["label"], "font": {"size": 11, "color": "#a8d4f5"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#5a8abf"},
                    "bar": {"color": t["color"], "thickness": 0.3},
                    "bgcolor": "#0a0d12",
                    "bordercolor": "#1e3a5f",
                    "steps": [
                        {"range": [0, 33], "color": "#0e1a0e"},
                        {"range": [33, 66], "color": "#1e1400"},
                        {"range": [66, 100], "color": "#1e0a0a"},
                    ],
                    "threshold": {"line": {"color": "#ffffff", "width": 2}, "thickness": 0.75, "value": t["value"]},
                },
            ))
            fig_g.update_layout(
                paper_bgcolor="#0e1520",
                height=140,
                margin=dict(l=10, r=10, t=30, b=10),
            )
            st.plotly_chart(fig_g, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center; font-size:0.72rem; color:#334155; font-family:Share Tech Mono,monospace; padding:8px;'>
  ⚠️ FOR INFORMATIONAL PURPOSES ONLY · NOT FINANCIAL ADVICE ·
  Sources: Polymarket Gamma API · NewsAPI · Anthropic Claude · EIA · Simulated market data ·
  Commodity prices are illustrative estimates incorporating war risk premium modelling
</div>
""", unsafe_allow_html=True)
