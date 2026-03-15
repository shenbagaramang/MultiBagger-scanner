"""
screener.py
-----------
4-layer multibagger screening logic + Compounder Score engine.
"""

import pandas as pd
import numpy as np
from database import get_connection


def calculate_compounder_score(
    roce: float,
    roce_history: list,
    rev_cagr: float,
    pft_cagr: float,
    margin_expansion: bool,
    inst_accum: bool,
    promoter_holding: float,
    ocf_positive_3y: bool,
    ocf_gt_netprofit: bool,
) -> float:
    """
    Compounder Score 0–100:

    Component                   Max pts
    ─────────────────────────────────────
    ROCE stability (>20% 3y)      20
    Revenue CAGR strength         15
    Profit CAGR strength          15
    Margin expansion              15
    Institutional accumulation    10
    Promoter holding strength     10
    Cash flow quality             15
    ─────────────────────────────────────
    Total                        100
    """
    score = 0.0

    # 1. ROCE stability (20 pts)
    high_roce_years = sum(1 for r in roce_history if r > 20)
    score += min(20, high_roce_years * 4)   # 4 pts per year above 20%

    # 2. Revenue CAGR (15 pts)
    if rev_cagr >= 30:   score += 15
    elif rev_cagr >= 22: score += 11
    elif rev_cagr >= 15: score += 7
    elif rev_cagr >= 10: score += 3

    # 3. Profit CAGR (15 pts)
    if pft_cagr >= 35:   score += 15
    elif pft_cagr >= 25: score += 11
    elif pft_cagr >= 20: score += 7
    elif pft_cagr >= 12: score += 3

    # 4. Margin expansion (15 pts)
    if margin_expansion: score += 15

    # 5. Institutional accumulation (10 pts)
    if inst_accum: score += 10

    # 6. Promoter holding (10 pts)
    if promoter_holding >= 70:   score += 10
    elif promoter_holding >= 60: score += 7
    elif promoter_holding >= 50: score += 4
    elif promoter_holding >= 40: score += 1

    # 7. Cash flow quality (15 pts)
    if ocf_positive_3y and ocf_gt_netprofit: score += 15
    elif ocf_positive_3y:                    score += 8
    elif ocf_gt_netprofit:                   score += 5

    return min(100, round(score, 1))


def run_screener(
    min_score: float = 0,
    min_roce: float = 18,
    min_rev_cagr: float = 15,
    min_profit_cagr: float = 20,
    max_de: float = 0.5,
    min_promoter: float = 50,
) -> pd.DataFrame:
    """
    Run the 4-layer filter and return a ranked DataFrame.
    """
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM companies", conn)
    except Exception:
        conn.close()
        return pd.DataFrame()
    conn.close()

    if df.empty:
        return df

    # ── LAYER 1 — Size ────────────────────────────────────────────────────────
    df = df[
        (df["market_cap"].between(300, 5000)) &
        (df["revenue"].between(100, 2000))
    ]

    # ── LAYER 2 — Quality ─────────────────────────────────────────────────────
    df = df[
        (df["roce"] >= min_roce) &
        (df["roe"] >= 18) &
        (df["debt_equity"] <= max_de) &
        (df["ocf_positive_3y"] == 1) &
        (df["ocf_gt_netprofit"] == 1)
    ]

    # ── LAYER 3 — Growth ─────────────────────────────────────────────────────
    df = df[
        (df["revenue_cagr_3y"] >= min_rev_cagr) &
        (df["profit_cagr_3y"] >= min_profit_cagr)
    ]

    # ── LAYER 4 — Smart Money ─────────────────────────────────────────────────
    df = df[
        (df["promoter_holding"] >= min_promoter) &
        (df["promoter_pledge"] <= 5)
    ]

    # ── Compounder Score filter ───────────────────────────────────────────────
    df = df[df["compounder_score"] >= min_score]

    # ── Sort ──────────────────────────────────────────────────────────────────
    df = df.sort_values("compounder_score", ascending=False).reset_index(drop=True)

    return df
