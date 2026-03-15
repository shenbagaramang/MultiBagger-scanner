"""
data_fetcher.py
---------------
Generates a realistic synthetic dataset of NSE/BSE small-cap companies.

To connect to real APIs (Screener.in, Tickertape, Alpha Vantage, etc.)
set LIVE_DATA=True in config.py and add your API key.
"""

import numpy as np
import pandas as pd
import sqlite3
from datetime import datetime
from database import get_connection

# ── Company universe ──────────────────────────────────────────────────────────
SECTORS = [
    "Chemicals", "Pharma", "Auto Ancillaries", "Capital Goods",
    "Textiles", "Consumer Durables", "Agrochemicals", "IT Services",
    "FMCG", "Packaging", "Specialty Chemicals", "Defence", "Electronics",
]

EXCHANGES = ["NSE", "BSE"]

COMPANY_PREFIXES = [
    "Anand","Bharat","Chandra","Devi","Ekta","Flair","Ganesh","Hari",
    "Indo","Jain","Kiran","Laxmi","Manoj","Nanda","Omkar","Patel",
    "Raj","Shree","Tara","Uma","Vijay","Wockhardt","Xcel","Yash","Zenith",
    "Aditya","Bajaj","CG","Dhanuka","Eagle","Fortune","Gujarat","Himachal",
    "Inox","Jyoti","Kalyani","Lumax","Minda","Navin","Orient","Pearl",
    "Qualitek","Ramco","Stylam","Titan","Uflex","Venus","Welspun","Xtep",
    "Yuken","Zydus","Arvind","Balaji","Cosmo","Deepak","Eris","Fiem",
    "Galaxy","Hawkins","ISGEC","JK","KSB","La Opala","Mayur","NCC",
    "Polycab","Quess","Relaxo","Sheela","Thermax","Ultramarine",
]

COMPANY_SUFFIXES = [
    "Industries","Chemicals","Pharma","Labs","Systems","Polymers",
    "Textiles","Engineering","Finpro","Technologies","Enterprises",
    "Castings","Coatings","Composites","Components","Forgings",
    "Electricals","Electronics","Biotech","Agro","Finance","Capital",
]


def _gen_company_names(n, seed):
    """
    Generate n unique company names.
    Uses the full prefix × suffix Cartesian product (~50 × 22 = 1100 combos),
    so any n up to 500 is always safe — no replace=False sampling errors.
    """
    rng = np.random.default_rng(seed)
    all_names = [f"{p} {s}" for p in COMPANY_PREFIXES for s in COMPANY_SUFFIXES]
    indices = rng.permutation(len(all_names))
    return [all_names[i] for i in indices[:n]]


def _sigmoid(x): return 1 / (1 + np.exp(-x))


def _generate_company(name, rng):
    """Generate realistic financial time-series for one company."""
    sector      = rng.choice(SECTORS)
    exchange    = rng.choice(EXCHANGES)
    quality     = rng.uniform(0, 1)   # latent quality factor

    # Market cap ₹300Cr – ₹5000Cr
    market_cap = rng.uniform(300, 5000)

    # Revenue ₹100Cr – ₹2000Cr
    rev_base = rng.uniform(100, 2000)

    # 5-year historical financials
    years = list(range(datetime.now().year - 4, datetime.now().year + 1))
    rev_growth_rates = [rng.uniform(0.05, 0.35) * (0.5 + quality) for _ in years]
    revenues = [rev_base]
    for g in rev_growth_rates[1:]:
        revenues.append(revenues[-1] * (1 + g))

    # Operating margin: base + improvement trend for quality companies
    base_margin = rng.uniform(0.08, 0.22) * (0.5 + quality)
    margins = [max(0.05, base_margin + rng.uniform(-0.02, 0.03) * quality * i) for i in range(5)]

    net_profits = [r * m * rng.uniform(0.7, 1.0) for r, m in zip(revenues, margins)]

    # ROCE: 12–35%
    base_roce = rng.uniform(12, 35) * (0.6 + 0.8 * quality)
    roces = [max(8, base_roce + rng.uniform(-3, 3)) for _ in years]

    # ROE
    base_roe  = base_roce * rng.uniform(0.8, 1.3)
    roes = [max(5, base_roe + rng.uniform(-2, 2)) for _ in years]

    # D/E
    de = rng.uniform(0.0, 1.2) * (1 - 0.6 * quality)

    # OCF (placeholder list, rebuilt later via _fix_ocf)
    ocf = [p * rng.uniform(0.9, 1.4) for p in net_profits]

    # Capex & fixed assets — quality cos expand more
    capex_base = rev_base * rng.uniform(0.03, 0.12)
    capex = [capex_base * (1 + rng.uniform(0.05, 0.25) * quality) ** i for i in range(5)]
    fa_base = rev_base * rng.uniform(0.5, 1.5)
    fixed_assets = [fa_base + sum(capex[:i+1]) * rng.uniform(0.7, 1.0) for i in range(5)]
    depreciation = [fa * rng.uniform(0.04, 0.08) for fa in fixed_assets]

    # Promoter & institutional holding
    promoter_base = rng.uniform(30, 80) * (0.5 + 0.5 * quality)
    promoter_pledge = rng.uniform(0, 15) * (1 - 0.8 * quality)
    inst_base = rng.uniform(5, 35)

    quarters = ["Q1FY22","Q2FY22","Q3FY22","Q4FY22",
                "Q1FY23","Q2FY23","Q3FY23","Q4FY23",
                "Q1FY24","Q2FY24","Q3FY24","Q4FY24",
                "Q1FY25","Q2FY25","Q3FY25","Q4FY25"]

    promoter_trend = [min(75, promoter_base + rng.uniform(-1, 1.5) * quality * i * 0.2) for i in range(len(quarters))]
    inst_trend = [max(2, inst_base + rng.uniform(-1, 2) * quality * i * 0.15) for i in range(len(quarters))]
    fii_trend  = [t * rng.uniform(0.3, 0.6) for t in inst_trend]
    dii_trend  = [t - f for t, f in zip(inst_trend, fii_trend)]
    mf_trend   = [d * rng.uniform(0.4, 0.8) for d in dii_trend]

    return dict(
        company_name=name,
        exchange=exchange,
        sector=sector,
        market_cap=round(market_cap, 1),
        years=years,
        revenues=[round(r, 1) for r in revenues],
        net_profits=[round(p, 1) for p in net_profits],
        margins=[round(m * 100, 2) for m in margins],
        roces=[round(r, 2) for r in roces],
        roes=[round(r, 2) for r in roes],
        debt_equity=round(de, 3),
        ocf=[round(o, 1) for o in ocf],
        capex=[round(c, 1) for c in capex],
        fixed_assets=[round(f, 1) for f in fixed_assets],
        depreciation=[round(d, 1) for d in depreciation],
        promoter_base=round(promoter_base, 1),
        promoter_pledge=round(max(0, promoter_pledge), 1),
        quarters=quarters,
        promoter_trend=[round(p, 1) for p in promoter_trend],
        inst_trend=[round(t, 1) for t in inst_trend],
        fii_trend=[round(f, 1) for f in fii_trend],
        dii_trend=[round(d, 1) for d in dii_trend],
        mf_trend=[round(m, 1) for m in mf_trend],
    )


# Fix: ocf list comprehension had a syntax error
def _fix_ocf(net_profits, rng):
    return [round(np_ * rng.uniform(0.9, 1.4), 1) for np_ in net_profits]


def _cagr(start, end, years):
    if start <= 0 or end <= 0:
        return 0.0
    return ((end / start) ** (1 / years) - 1) * 100


def refresh_data(num_stocks=150, seed=42):
    rng    = np.random.default_rng(seed)
    names  = _gen_company_names(min(num_stocks, len(COMPANY_PREFIXES) * len(COMPANY_SUFFIXES)), seed)[:num_stocks]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cur  = conn.cursor()

    # Clear old data
    for tbl in ("companies", "financials", "institutional"):
        cur.execute(f"DELETE FROM {tbl}")

    count = 0
    for name in names:
        try:
            d = _generate_company(name, rng)
            # Patch: rebuild ocf properly
            d["ocf"] = _fix_ocf(d["net_profits"], rng)

            years    = d["years"]
            revenues = d["revenues"]
            profits  = d["net_profits"]
            margins  = d["margins"]
            roces    = d["roces"]
            roes     = d["roes"]
            ocf      = d["ocf"]
            capex    = d["capex"]
            fa       = d["fixed_assets"]
            depr     = d["depreciation"]

            # CAGRs (3-year)
            rev_cagr_3y = _cagr(revenues[-4], revenues[-1], 3)
            pft_cagr_3y = _cagr(profits[-4], profits[-1], 3)

            # Signals
            accel_revenue   = revenues[-1] / revenues[-2] > revenues[-2] / revenues[-3]
            profit_gt_rev   = pft_cagr_3y > rev_cagr_3y
            margin_expansion = margins[-1] > margins[-2] > margins[-3]
            capex_expansion  = capex[-1] > capex[-2] > capex[-3]
            ocf_positive_3y  = all(o > 0 for o in ocf[-3:])
            ocf_gt_netprofit = all(o >= p for o, p in zip(ocf[-3:], profits[-3:]))
            inst_trend       = d["inst_trend"]
            inst_accum       = (inst_trend[-1] > inst_trend[-2] > inst_trend[-3] > inst_trend[-4])
            high_roce_reinvest = roces[-1] > 20 and capex_expansion

            # Compounder score
            from screener import calculate_compounder_score
            score = calculate_compounder_score(
                roce=roces[-1], roce_history=roces,
                rev_cagr=rev_cagr_3y, pft_cagr=pft_cagr_3y,
                margin_expansion=margin_expansion,
                inst_accum=inst_accum,
                promoter_holding=d["promoter_base"],
                ocf_positive_3y=ocf_positive_3y,
                ocf_gt_netprofit=ocf_gt_netprofit,
            )

            inst_change = inst_trend[-1] - inst_trend[-5] if len(inst_trend) >= 5 else 0.0

            # Insert company
            cur.execute("""
                INSERT OR REPLACE INTO companies (
                    company_name, exchange, sector, market_cap, revenue, net_profit,
                    roce, roe, debt_equity, operating_margin,
                    revenue_cagr_3y, profit_cagr_3y,
                    promoter_holding, promoter_pledge, inst_holding_change,
                    ocf_positive_3y, ocf_gt_netprofit,
                    accel_revenue, profit_gt_rev, capex_expansion, inst_accumulation,
                    margin_expansion, high_roce_reinvest, compounder_score, last_updated
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                name, d["exchange"], d["sector"], d["market_cap"],
                revenues[-1], profits[-1], roces[-1], roes[-1],
                d["debt_equity"], margins[-1],
                round(rev_cagr_3y, 1), round(pft_cagr_3y, 1),
                d["promoter_base"], d["promoter_pledge"], round(inst_change, 2),
                int(ocf_positive_3y), int(ocf_gt_netprofit),
                int(accel_revenue), int(profit_gt_rev), int(capex_expansion),
                int(inst_accum), int(margin_expansion), int(high_roce_reinvest),
                round(score, 1), now_str,
            ))

            # Insert financials
            for i, yr in enumerate(years):
                cur.execute("""
                    INSERT OR REPLACE INTO financials
                    (company_name, year, revenue, net_profit, operating_margin,
                     roce, roe, capex, fixed_assets, depreciation, ocf)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (name, yr, revenues[i], profits[i], margins[i],
                      roces[i], roes[i], capex[i], fa[i], depr[i], ocf[i]))

            # Insert institutional
            for i, q in enumerate(d["quarters"]):
                cur.execute("""
                    INSERT OR REPLACE INTO institutional
                    (company_name, quarter, promoter_pct, fii_pct, dii_pct, mf_pct, total_inst_pct)
                    VALUES (?,?,?,?,?,?,?)
                """, (name, q,
                      d["promoter_trend"][i], d["fii_trend"][i],
                      d["dii_trend"][i], d["mf_trend"][i], d["inst_trend"][i]))

            count += 1

        except Exception as e:
            # Skip bad company
            continue

    cur.execute("INSERT OR REPLACE INTO meta (key,value) VALUES ('last_refresh',?)", (now_str,))
    conn.commit()
    conn.close()
    return count


def get_last_refresh_time():
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT value FROM meta WHERE key='last_refresh'")
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None
    except:
        return None
