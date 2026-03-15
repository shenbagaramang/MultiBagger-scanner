"""
config.py
---------
Configuration for Multibagger Scout.

Set LIVE_DATA = True and add your API key to fetch real NSE/BSE data.

Supported APIs (planned):
  - Screener.in  (https://www.screener.in/api/)
  - Tickertape   (https://www.tickertape.in)
  - Alpha Vantage (https://www.alphavantage.co)
  - NSE Python   (pip install nsetools)
"""

# ── Data source ───────────────────────────────────────────────────────────────
LIVE_DATA = False          # Set True to use real API
API_KEY   = ""             # Your API key here

# ── Screener thresholds (defaults; overridden by sidebar) ─────────────────────
DEFAULT_MIN_MARKET_CAP    = 300    # ₹ Crore
DEFAULT_MAX_MARKET_CAP    = 5000
DEFAULT_MIN_REVENUE       = 100
DEFAULT_MAX_REVENUE       = 2000
DEFAULT_MIN_ROCE          = 18
DEFAULT_MIN_ROE           = 18
DEFAULT_MAX_DE            = 0.5
DEFAULT_MIN_REV_CAGR      = 15
DEFAULT_MIN_PROFIT_CAGR   = 20
DEFAULT_MIN_PROMOTER      = 50
DEFAULT_MAX_PLEDGE        = 5
DEFAULT_MIN_SCORE         = 50

# ── Refresh schedule ──────────────────────────────────────────────────────────
REFRESH_INTERVAL_DAYS = 7
