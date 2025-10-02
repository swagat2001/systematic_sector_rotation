"""
Quick Database Checker

Check status of NSE database and display summary
"""

import sqlite3
from pathlib import Path
import pandas as pd

def check_database():
    """Check and display database contents"""
    
    db_path = Path(__file__).parent / 'nse_data.db'
    
    if not db_path.exists():
        print("\n❌ Database not found!")
        print(f"Expected location: {db_path}")
        print("\nRun the scraper first:")
        print("  python nse_data_scraper.py\n")
        return
    
    conn = sqlite3.connect(db_path)
    
    print("\n" + "="*60)
    print("NSE DATABASE STATUS")
    print("="*60)
    
    # Total stocks
    stocks_count = conn.execute("SELECT COUNT(*) FROM stocks").fetchone()[0]
    print(f"\nTotal Stocks: {stocks_count}")
    
    # Total price records
    prices_count = conn.execute("SELECT COUNT(*) FROM stock_prices").fetchone()[0]
    print(f"Total Price Records: {prices_count:,}")
    
    # By sector
    print("\nStocks by Sector:")
    print("-"*60)
    sector_query = """
    SELECT sector, COUNT(*) as count
    FROM stocks
    GROUP BY sector
    ORDER BY count DESC
    """
    sectors = pd.read_sql_query(sector_query, conn)
    for _, row in sectors.iterrows():
        print(f"  {row['sector']:<35} {row['count']:>5} stocks")
    
    # Date range
    date_query = """
    SELECT MIN(date) as first_date, MAX(date) as last_date
    FROM stock_prices
    """
    dates = pd.read_sql_query(date_query, conn)
    if not dates.empty and dates['first_date'].notna().any():
        print(f"\nDate Range:")
        print(f"  From: {dates['first_date'].iloc[0]}")
        print(f"  To:   {dates['last_date'].iloc[0]}")
    
    # Top stocks by records
    print("\nTop 10 Stocks by Price Records:")
    print("-"*60)
    top_query = """
    SELECT symbol, COUNT(*) as records
    FROM stock_prices
    GROUP BY symbol
    ORDER BY records DESC
    LIMIT 10
    """
    top_stocks = pd.read_sql_query(top_query, conn)
    for _, row in top_stocks.iterrows():
        print(f"  {row['symbol']:<15} {row['records']:>6} records")
    
    print("\n" + "="*60)
    print(f"Database: {db_path}")
    print("="*60 + "\n")
    
    conn.close()


if __name__ == "__main__":
    check_database()
