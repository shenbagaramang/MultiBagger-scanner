# 🚀 Multibagger Scout — NSE/BSE Small-Cap Research App

A professional 4-layer multibagger discovery framework for Indian small-cap stocks.

## Features
- **4-Layer Framework**: Size → Quality → Growth → Smart Money
- **Compounder Score** (0–100) ranks companies by multibagger potential
- **Early Signal Detection**: Accelerating revenue, margin expansion, institutional buying
- **Interactive Charts**: Revenue, profit, ROCE, margins, capex, promoter trends
- **Watchlist**: Save companies for monitoring
- **Alert System**: Highlights top candidates

## Quick Start

### 1. Install dependencies
```bash
cd multibagger_app
pip install -r requirements.txt
```

### 2. Launch the app
```bash
streamlit run app.py
```

### 3. Load data
- Click **🔄 Data Refresh** in the sidebar
- Click **🚀 Refresh Data Now**
- Wait ~10 seconds for 150+ companies to load

### 4. Screen stocks
- Adjust filters in the sidebar
- Go to **📊 Dashboard** to see shortlisted companies
- Click any company name → **📈 Open Detail Page** for deep-dive charts

## Data Source
By default, the app uses a **realistic synthetic dataset** modelled on actual NSE/BSE small-cap financial distributions.

To use live data:
1. Open `config.py`
2. Set `LIVE_DATA = True`
3. Add your API key from Screener.in or similar

## 4-Layer Framework

| Layer | Filter |
|-------|--------|
| **Size** | Market Cap ₹300–5000 Cr, Revenue ₹100–2000 Cr |
| **Quality** | ROCE>18%, ROE>18%, D/E<0.5, Positive OCF |
| **Growth** | Rev CAGR>15%, PAT CAGR>20%, Margin expansion, Capex↑ |
| **Smart Money** | Promoter>50%, Pledge<5%, Inst accumulation 3Q+ |

## Compounder Score Breakdown

| Component | Max Score |
|-----------|-----------|
| ROCE stability (>20% multi-year) | 20 |
| Revenue CAGR strength | 15 |
| Profit CAGR strength | 15 |
| Margin expansion | 15 |
| Cash flow quality | 15 |
| Promoter holding strength | 10 |
| Institutional accumulation | 10 |
| **Total** | **100** |

Companies with **Score ≥ 75** are highlighted as **Strong Multibagger Candidates**.

## Tech Stack
- Python 3.10+
- Streamlit (UI)
- Pandas (analysis)
- Plotly (charts)
- SQLite (local database)
- NumPy (calculations)
# MultiBagger-scanner
