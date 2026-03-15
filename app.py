import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sqlite3
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from database import init_db, get_connection
from data_fetcher import refresh_data, get_last_refresh_time
from screener import run_screener, calculate_compounder_score
from watchlist import get_watchlist, add_to_watchlist, remove_from_watchlist

st.set_page_config(
    page_title="Multibagger Scout — NSE/BSE",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main { background: #0f1117; }

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, #1e2130 0%, #252836 100%);
    border: 1px solid #2d3147;
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
}
.metric-card .label { color: #8b92a5; font-size: 12px; font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase; }
.metric-card .value { color: #e2e8f0; font-size: 24px; font-weight: 700; margin-top: 4px; }

/* Score badge */
.score-high   { background:#064e3b; color:#34d399; border:1px solid #065f46; border-radius:8px; padding:3px 10px; font-weight:700; font-size:14px; }
.score-medium { background:#1e3a5f; color:#60a5fa; border:1px solid #1e40af; border-radius:8px; padding:3px 10px; font-weight:700; font-size:14px; }
.score-low    { background:#2d1a1a; color:#f87171; border:1px solid #7f1d1d; border-radius:8px; padding:3px 10px; font-weight:700; font-size:14px; }

/* Signal tags */
.signal-tag { display:inline-block; background:#14532d22; color:#86efac; border:1px solid #166534; border-radius:6px; padding:2px 8px; font-size:11px; font-weight:600; margin:2px; }

/* Alert banner */
.alert-banner { background:linear-gradient(90deg,#1a1a2e,#16213e); border-left:4px solid #f59e0b; border-radius:8px; padding:12px 16px; margin:8px 0; }

/* Watchlist button */
.stButton > button { border-radius: 8px !important; font-weight: 600 !important; }

/* Table header */
.table-header { background:#1e2130; color:#8b92a5; font-size:11px; font-weight:600; letter-spacing:0.5px; text-transform:uppercase; padding:8px; }

/* Sidebar */
section[data-testid="stSidebar"] { background:#141620 !important; border-right:1px solid #2d3147; }

/* Divider */
hr { border-color: #2d3147 !important; }

.stDataFrame { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Init DB ───────────────────────────────────────────────────────────────────
init_db()

# ── Session state ─────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "selected_company" not in st.session_state:
    st.session_state.selected_company = None
if "watchlist_tab" not in st.session_state:
    st.session_state.watchlist_tab = False

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚀 Multibagger Scout")
    st.markdown("<p style='color:#8b92a5;font-size:13px;margin-top:-8px;'>NSE & BSE Small-Cap Screener</p>", unsafe_allow_html=True)
    st.markdown("---")

    nav = st.radio("Navigation", ["📊 Dashboard", "🔍 Screener", "⭐ Watchlist", "🔄 Data Refresh"],
                   label_visibility="collapsed")

    st.markdown("---")
    st.markdown("### ⚙️ Screener Filters")

    min_score = st.slider("Min Compounder Score", 0, 100, 50, 5)
    min_roce  = st.slider("Min ROCE (%)", 0, 50, 18, 1)
    min_rev_cagr = st.slider("Min Revenue CAGR (%)", 0, 50, 15, 1)
    min_profit_cagr = st.slider("Min Profit CAGR (%)", 0, 60, 20, 1)
    max_de = st.slider("Max Debt/Equity", 0.0, 2.0, 0.5, 0.1)
    min_promoter = st.slider("Min Promoter Holding (%)", 0, 80, 50, 1)

    st.markdown("---")
    last_refresh = get_last_refresh_time()
    if last_refresh:
        st.markdown(f"<p style='color:#8b92a5;font-size:12px;'>📅 Last refresh:<br>{last_refresh}</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#f87171;font-size:12px;'>⚠️ No data loaded yet.<br>Go to Data Refresh tab.</p>", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_screened_data(min_score, min_roce, min_rev_cagr, min_profit_cagr, max_de, min_promoter):
    return run_screener(min_score=min_score, min_roce=min_roce,
                        min_rev_cagr=min_rev_cagr, min_profit_cagr=min_profit_cagr,
                        max_de=max_de, min_promoter=min_promoter)

def score_badge(score):
    if score >= 75:
        cls = "score-high"
    elif score >= 50:
        cls = "score-medium"
    else:
        cls = "score-low"
    return f'<span class="{cls}">{score}</span>'

def signal_tags(row):
    tags = []
    if row.get("accel_revenue"):    tags.append("📈 Accel Revenue")
    if row.get("profit_gt_rev"):    tags.append("💹 Profit>Rev")
    if row.get("capex_expansion"):  tags.append("🏗️ Capex↑")
    if row.get("inst_accumulation"):tags.append("🏦 Inst Buying")
    if row.get("margin_expansion"): tags.append("📊 Margin↑")
    if row.get("high_roce_reinvest"):tags.append("♻️ ROCE+Reinvest")
    return " ".join([f'<span class="signal-tag">{t}</span>' for t in tags])

# ═══════════════════════════════════════════════════════════════════════════════
# PAGES
# ═══════════════════════════════════════════════════════════════════════════════

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
if nav == "📊 Dashboard":

    df = load_screened_data(min_score, min_roce, min_rev_cagr, min_profit_cagr, max_de, min_promoter)

    st.markdown("## 📊 Multibagger Dashboard")
    st.markdown("<p style='color:#8b92a5;'>Real-time scan of NSE/BSE small-caps through the 4-layer framework.</p>", unsafe_allow_html=True)

    if df.empty:
        st.warning("No data found. Please go to **Data Refresh** to load stock data first.")
        st.stop()

    # KPI row
    total       = len(df)
    strong_mb   = len(df[df["compounder_score"] >= 75])
    avg_roce    = df["roce"].mean() if "roce" in df.columns else 0
    avg_score   = df["compounder_score"].mean() if "compounder_score" in df.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    for col, label, value in [
        (c1, "Companies Shortlisted", total),
        (c2, "Strong Multibaggers (≥75)", strong_mb),
        (c3, "Avg ROCE (%)", f"{avg_roce:.1f}"),
        (c4, "Avg Compounder Score", f"{avg_score:.1f}"),
    ]:
        col.markdown(f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Alert banners
    alerts = df[df["compounder_score"] >= 75].head(3)
    if not alerts.empty:
        st.markdown("### 🚨 Top Alerts — Strong Multibagger Candidates")
        for _, row in alerts.iterrows():
            sigs = []
            if row.get("accel_revenue"):    sigs.append("Accelerating Revenue")
            if row.get("margin_expansion"): sigs.append("Margin Expansion")
            if row.get("inst_accumulation"):sigs.append("Institutional Buying")
            sig_str = " • ".join(sigs) if sigs else "Strong Fundamentals"
            st.markdown(f"""
            <div class="alert-banner">
                <b style='color:#f59e0b;'>⚡ {row['company_name']}</b>
                <span style='color:#8b92a5;font-size:13px;'> — Score: {row['compounder_score']} | {sig_str}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main table
    st.markdown("### 📋 Screened Companies")
    sort_col = st.selectbox("Sort by", ["compounder_score", "roce", "revenue_cagr_3y", "profit_cagr_3y", "market_cap"], index=0)
    df_sorted = df.sort_values(sort_col, ascending=False).reset_index(drop=True)

    # Render interactive table
    display_cols = {
        "company_name":        "Company",
        "exchange":            "Exchange",
        "market_cap":          "Mkt Cap (Cr)",
        "revenue_cagr_3y":     "Rev CAGR 3Y%",
        "profit_cagr_3y":      "PAT CAGR 3Y%",
        "roce":                "ROCE%",
        "roe":                 "ROE%",
        "debt_equity":         "D/E",
        "operating_margin":    "Op Margin%",
        "promoter_holding":    "Promoter%",
        "inst_holding_change": "Inst Δ%",
        "compounder_score":    "Score",
    }
    df_display = df_sorted[[c for c in display_cols if c in df_sorted.columns]].rename(columns=display_cols)

    # Round numerics
    for col in df_display.select_dtypes("float").columns:
        df_display[col] = df_display[col].round(1)

    # Highlight score column
    def highlight_score(val):
        if val >= 75: return "background-color:#064e3b;color:#34d399;font-weight:700"
        elif val >= 50: return "background-color:#1e3a5f;color:#60a5fa;font-weight:700"
        return "background-color:#2d1a1a;color:#f87171;font-weight:700"

    styled = df_display.style.applymap(highlight_score, subset=["Score"])
    st.dataframe(styled, use_container_width=True, height=520)

    # Click to detail
    st.markdown("---")
    st.markdown("### 🔎 View Company Detail")
    company_names = df_sorted["company_name"].tolist()
    selected = st.selectbox("Select a company", company_names)
    if st.button("📈 Open Detail Page", type="primary"):
        st.session_state.selected_company = selected
        st.session_state.page = "detail"
        st.rerun()

# ── SCREENER ──────────────────────────────────────────────────────────────────
elif nav == "🔍 Screener":
    st.markdown("## 🔍 4-Layer Multibagger Screener")

    df = load_screened_data(min_score, min_roce, min_rev_cagr, min_profit_cagr, max_de, min_promoter)

    if df.empty:
        st.warning("No data. Please refresh data first.")
        st.stop()

    tab1, tab2, tab3, tab4 = st.tabs(["Layer 1 — Size", "Layer 2 — Quality", "Layer 3 — Growth", "Layer 4 — Smart Money"])

    def layer_table(df, cols):
        avail = [c for c in cols if c in df.columns]
        return df[avail].sort_values("compounder_score", ascending=False).reset_index(drop=True)

    with tab1:
        st.markdown("#### Size Filter: Market Cap ₹300Cr–₹5000Cr | Revenue ₹100Cr–₹2000Cr")
        cols = ["company_name","exchange","market_cap","revenue","compounder_score"]
        st.dataframe(layer_table(df, cols), use_container_width=True)

    with tab2:
        st.markdown("#### Quality: ROCE>18% | ROE>18% | D/E<0.5 | Positive OCF | OCF≥Net Profit")
        cols = ["company_name","roce","roe","debt_equity","ocf_positive_3y","ocf_gt_netprofit","compounder_score"]
        st.dataframe(layer_table(df, cols), use_container_width=True)

    with tab3:
        st.markdown("#### Growth: Rev CAGR>15% | PAT CAGR>20% | Margin Expansion | Capex↑")
        cols = ["company_name","revenue_cagr_3y","profit_cagr_3y","margin_expansion","capex_expansion","accel_revenue","compounder_score"]
        st.dataframe(layer_table(df, cols), use_container_width=True)

    with tab4:
        st.markdown("#### Smart Money: Promoter>50% | Pledge<5% | Institutional Accumulation 3Q+")
        cols = ["company_name","promoter_holding","promoter_pledge","inst_holding_change","inst_accumulation","compounder_score"]
        st.dataframe(layer_table(df, cols), use_container_width=True)

    st.markdown("---")
    st.markdown("### 🏆 Early Signal Detection")
    signal_df = df[df["compounder_score"] >= min_score].copy()
    if not signal_df.empty:
        for _, row in signal_df.iterrows():
            tags = signal_tags(row)
            if tags:
                st.markdown(f"**{row['company_name']}** — {tags}", unsafe_allow_html=True)
    else:
        st.info("No companies match the current filters.")

# ── WATCHLIST ─────────────────────────────────────────────────────────────────
elif nav == "⭐ Watchlist":
    st.markdown("## ⭐ My Watchlist")

    wl = get_watchlist()
    if not wl:
        st.info("Your watchlist is empty. Add companies from the Dashboard or Detail pages.")
    else:
        wl_df = pd.DataFrame(wl)
        st.dataframe(wl_df, use_container_width=True)

        remove_name = st.selectbox("Remove from watchlist", [r["company_name"] for r in wl])
        if st.button("🗑️ Remove", type="secondary"):
            remove_from_watchlist(remove_name)
            st.success(f"Removed {remove_name} from watchlist.")
            st.rerun()

# ── DATA REFRESH ──────────────────────────────────────────────────────────────
elif nav == "🔄 Data Refresh":
    st.markdown("## 🔄 Data Refresh")
    st.markdown("""
    This will fetch financial data for NSE/BSE small-cap companies and populate the local SQLite database.

    **Data source:** Realistic synthetic financial dataset (modelled on real small-cap distributions).
    To use live data, configure your API key in `config.py`.
    """)

    last = get_last_refresh_time()
    if last:
        st.success(f"✅ Last refreshed: {last}")
    else:
        st.warning("⚠️ No data loaded yet.")

    col1, col2 = st.columns(2)
    with col1:
        num_stocks = st.slider("Number of companies to generate", 50, 500, 150, 50)
    with col2:
        seed = st.number_input("Random seed (for reproducibility)", value=42, step=1)

    if st.button("🚀 Refresh Data Now", type="primary"):
        with st.spinner("Fetching and processing financial data..."):
            count = refresh_data(num_stocks=num_stocks, seed=int(seed))
        st.cache_data.clear()
        st.success(f"✅ Successfully loaded {count} companies into the database!")
        st.balloons()

# ── DETAIL PAGE ───────────────────────────────────────────────────────────────
if st.session_state.page == "detail" and st.session_state.selected_company:
    company = st.session_state.selected_company
    conn = get_connection()

    st.markdown("---")
    st.markdown(f"## 📈 {company}")

    row = pd.read_sql(f"SELECT * FROM companies WHERE company_name=?", conn, params=(company,))
    hist = pd.read_sql(f"SELECT * FROM financials WHERE company_name=? ORDER BY year", conn, params=(company,))
    inst = pd.read_sql(f"SELECT * FROM institutional WHERE company_name=? ORDER BY quarter", conn, params=(company,))

    if row.empty:
        st.error("Company data not found.")
    else:
        r = row.iloc[0]
        score = int(r.get("compounder_score", 0))

        # Header metrics
        cols = st.columns(6)
        metrics = [
            ("Market Cap", f"₹{r.get('market_cap',0):.0f} Cr"),
            ("ROCE", f"{r.get('roce',0):.1f}%"),
            ("ROE", f"{r.get('roe',0):.1f}%"),
            ("D/E", f"{r.get('debt_equity',0):.2f}"),
            ("Promoter%", f"{r.get('promoter_holding',0):.1f}%"),
            ("Score", score),
        ]
        for col, (label, val) in zip(cols, metrics):
            col.markdown(f"""
            <div class="metric-card">
                <div class="label">{label}</div>
                <div class="value">{val}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Watchlist button
        wl_names = [w["company_name"] for w in get_watchlist()]
        if company in wl_names:
            if st.button("⭐ Remove from Watchlist"):
                remove_from_watchlist(company)
                st.rerun()
        else:
            if st.button("⭐ Add to Watchlist", type="primary"):
                add_to_watchlist(company, int(r.get("market_cap",0)), score)
                st.success("Added to watchlist!")

        if not hist.empty:
            # Chart theme
            chart_theme = dict(
                paper_bgcolor="#0f1117", plot_bgcolor="#141620",
                font=dict(color="#8b92a5", family="Inter"),
                xaxis=dict(gridcolor="#1e2130", linecolor="#2d3147"),
                yaxis=dict(gridcolor="#1e2130", linecolor="#2d3147"),
            )

            # Revenue & Profit
            st.markdown("### 📊 Revenue & Profit Trends")
            fig = make_subplots(rows=1, cols=2, subplot_titles=["Revenue (₹ Cr)", "Net Profit (₹ Cr)"])
            fig.add_trace(go.Bar(x=hist["year"], y=hist["revenue"], name="Revenue",
                                 marker_color="#3b82f6"), row=1, col=1)
            fig.add_trace(go.Bar(x=hist["year"], y=hist["net_profit"], name="Net Profit",
                                 marker_color="#10b981"), row=1, col=2)
            fig.update_layout(**chart_theme, showlegend=False, height=320,
                              margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig, use_container_width=True)

            # ROCE & Margin
            st.markdown("### 📈 ROCE & Operating Margin Trend")
            fig2 = make_subplots(rows=1, cols=2, subplot_titles=["ROCE (%)", "Operating Margin (%)"])
            fig2.add_trace(go.Scatter(x=hist["year"], y=hist["roce"], mode="lines+markers",
                                      line=dict(color="#f59e0b", width=2), name="ROCE"), row=1, col=1)
            fig2.add_trace(go.Scatter(x=hist["year"], y=hist["operating_margin"], mode="lines+markers",
                                      line=dict(color="#a78bfa", width=2), name="Op Margin"), row=1, col=2)
            fig2.update_layout(**chart_theme, showlegend=False, height=320,
                               margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig2, use_container_width=True)

            # Capex & Fixed Assets
            if "capex" in hist.columns and "fixed_assets" in hist.columns:
                st.markdown("### 🏗️ Capex & Fixed Assets")
                fig3 = make_subplots(rows=1, cols=2, subplot_titles=["Capex (₹ Cr)", "Fixed Assets (₹ Cr)"])
                fig3.add_trace(go.Bar(x=hist["year"], y=hist["capex"], name="Capex",
                                      marker_color="#f97316"), row=1, col=1)
                fig3.add_trace(go.Bar(x=hist["year"], y=hist["fixed_assets"], name="Fixed Assets",
                                      marker_color="#06b6d4"), row=1, col=2)
                fig3.update_layout(**chart_theme, showlegend=False, height=320,
                                   margin=dict(l=20,r=20,t=40,b=20))
                st.plotly_chart(fig3, use_container_width=True)

        if not inst.empty:
            st.markdown("### 🏦 Institutional & Promoter Holding Trend")
            fig4 = go.Figure()
            if "promoter_pct" in inst.columns:
                fig4.add_trace(go.Scatter(x=inst["quarter"], y=inst["promoter_pct"],
                                          mode="lines+markers", name="Promoter %",
                                          line=dict(color="#f59e0b", width=2)))
            if "total_inst_pct" in inst.columns:
                fig4.add_trace(go.Scatter(x=inst["quarter"], y=inst["total_inst_pct"],
                                          mode="lines+markers", name="Institutional %",
                                          line=dict(color="#3b82f6", width=2)))
            fig4.update_layout(**chart_theme, height=320, margin=dict(l=20,r=20,t=20,b=20),
                               legend=dict(bgcolor="#1e2130"))
            st.plotly_chart(fig4, use_container_width=True)

    if st.button("← Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.session_state.selected_company = None
        st.rerun()

    conn.close()
