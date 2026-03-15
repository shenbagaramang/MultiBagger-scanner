import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "multibagger.db")

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT UNIQUE,
        exchange TEXT,
        sector TEXT,
        market_cap REAL,
        revenue REAL,
        net_profit REAL,
        roce REAL,
        roe REAL,
        debt_equity REAL,
        operating_margin REAL,
        revenue_cagr_3y REAL,
        profit_cagr_3y REAL,
        promoter_holding REAL,
        promoter_pledge REAL,
        inst_holding_change REAL,
        ocf_positive_3y INTEGER,
        ocf_gt_netprofit INTEGER,
        accel_revenue INTEGER,
        profit_gt_rev INTEGER,
        capex_expansion INTEGER,
        inst_accumulation INTEGER,
        margin_expansion INTEGER,
        high_roce_reinvest INTEGER,
        compounder_score REAL,
        last_updated TEXT
    );

    CREATE TABLE IF NOT EXISTS financials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT,
        year INTEGER,
        revenue REAL,
        net_profit REAL,
        operating_margin REAL,
        roce REAL,
        roe REAL,
        capex REAL,
        fixed_assets REAL,
        depreciation REAL,
        ocf REAL,
        UNIQUE(company_name, year)
    );

    CREATE TABLE IF NOT EXISTS institutional (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT,
        quarter TEXT,
        promoter_pct REAL,
        fii_pct REAL,
        dii_pct REAL,
        mf_pct REAL,
        total_inst_pct REAL,
        UNIQUE(company_name, quarter)
    );

    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT UNIQUE,
        market_cap REAL,
        compounder_score REAL,
        added_on TEXT
    );

    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)

    conn.commit()
    conn.close()
