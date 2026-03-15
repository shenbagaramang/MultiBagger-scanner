from datetime import datetime
from database import get_connection

def get_watchlist():
    conn = get_connection()
    try:
        import pandas as pd
        df = pd.read_sql("SELECT * FROM watchlist ORDER BY added_on DESC", conn)
        conn.close()
        return df.to_dict("records")
    except:
        conn.close()
        return []

def add_to_watchlist(company_name, market_cap, compounder_score):
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO watchlist (company_name, market_cap, compounder_score, added_on)
        VALUES (?,?,?,?)
    """, (company_name, market_cap, compounder_score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def remove_from_watchlist(company_name):
    conn = get_connection()
    conn.execute("DELETE FROM watchlist WHERE company_name=?", (company_name,))
    conn.commit()
    conn.close()
