"""
Check NSE Cash Database - Verify Scraper Results

Shows complete summary of scraped data:
- Total stocks and OHLC records
- Dynamic sector distribution from yfinance
- Date coverage
- Sample data
"""

import sqlite3
import pandas as pd
import os

def check_database():
    """Check and display database contents"""
    
    db_path = 'nse_cash.db'
    
    if not os.path.exists(db_path):
        print("❌ Database not found: nse_cash.db")
        print("Make sure you're in the NSE_sector_wise_data directory")
        print("Run: cd NSE_sector_wise_data")
        return
    
    print("=" * 70)
    print("NSE CASH DATABASE SUMMARY")
    print("=" * 70)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Total companies
    cursor.execute("SELECT COUNT(*) FROM companies")
    total_companies = cursor.fetchone()[0]
    print(f"\n📊 Total Companies: {total_companies}")
    
    # Companies with sectors
    cursor.execute("SELECT COUNT(*) FROM companies WHERE sector IS NOT NULL")
    with_sectors = cursor.fetchone()[0]
    print(f"✓ With Sector Data: {with_sectors} ({with_sectors/total_companies*100:.1f}%)")
    
    # Companies without sectors
    without_sectors = total_companies - with_sectors
    print(f"✗ Without Sector Data: {without_sectors} ({without_sectors/total_companies*100:.1f}%)")
    
    # Total OHLC records
    cursor.execute("SELECT COUNT(*) FROM ohlc")
    total_ohlc = cursor.fetchone()[0]
    print(f"\n📈 Total OHLC Records: {total_ohlc:,}")
    
    # Unique stocks with price data
    cursor.execute("SELECT COUNT(DISTINCT symbol) FROM ohlc")
    stocks_with_data = cursor.fetchone()[0]
    print(f"✓ Stocks with Price Data: {stocks_with_data}")
    
    # Date range
    cursor.execute("SELECT MIN(date), MAX(date) FROM ohlc")
    min_date, max_date = cursor.fetchone()
    print(f"📅 Date Range: {min_date} to {max_date}")
    
    # Calculate days
    from datetime import datetime
    if min_date and max_date:
        days = (datetime.strptime(max_date, '%Y-%m-%d') - 
                datetime.strptime(min_date, '%Y-%m-%d')).days
        print(f"   Total Days: {days} days (~{days/365:.1f} years)")
    
    # Sector distribution
    print("\n" + "=" * 70)
    print("SECTOR DISTRIBUTION (Dynamic from yfinance)")
    print("=" * 70)
    
    sectors_df = pd.read_sql("""
        SELECT sector, COUNT(*) as count 
        FROM companies 
        WHERE sector IS NOT NULL
        GROUP BY sector 
        ORDER BY count DESC
    """, conn)
    
    if len(sectors_df) > 0:
        print(f"\n{'SECTOR':<40s} {'COUNT':>8s} {'%':>8s}")
        print("-" * 70)
        for _, row in sectors_df.iterrows():
            percentage = (row['count'] / with_sectors) * 100
            print(f"{row['sector']:<40s} {row['count']:>8d} {percentage:>7.1f}%")
        print("-" * 70)
        print(f"{'TOTAL':<40s} {with_sectors:>8d} {'100.0':>7s}%")
    else:
        print("⚠️  No sector data found!")
    
    # Industry distribution (top 10)
    print("\n" + "=" * 70)
    print("TOP 10 INDUSTRIES (Dynamic from yfinance)")
    print("=" * 70)
    
    industries_df = pd.read_sql("""
        SELECT industry, COUNT(*) as count 
        FROM companies 
        WHERE industry IS NOT NULL
        GROUP BY industry 
        ORDER BY count DESC
        LIMIT 10
    """, conn)
    
    if len(industries_df) > 0:
        print(f"\n{'INDUSTRY':<50s} {'COUNT':>8s}")
        print("-" * 70)
        for _, row in industries_df.iterrows():
            print(f"{row['industry']:<50s} {row['count']:>8d}")
    
    # Sample stocks with complete data
    print("\n" + "=" * 70)
    print("SAMPLE STOCKS WITH COMPLETE DATA")
    print("=" * 70)
    
    sample = pd.read_sql("""
        SELECT symbol, fullname, sector, industry 
        FROM companies 
        WHERE sector IS NOT NULL AND industry IS NOT NULL
        LIMIT 15
    """, conn)
    
    if len(sample) > 0:
        print("\n" + sample.to_string(index=False, max_colwidth=40))
    
    # Stocks without sector data (show some examples)
    print("\n" + "=" * 70)
    print("STOCKS WITHOUT SECTOR DATA (Sample)")
    print("=" * 70)
    
    no_sector = pd.read_sql("""
        SELECT symbol, fullname 
        FROM companies 
        WHERE sector IS NULL
        LIMIT 10
    """, conn)
    
    if len(no_sector) > 0:
        print("\n" + no_sector.to_string(index=False, max_colwidth=50))
        print(f"\n... and {without_sectors - 10} more stocks without sectors")
        print("\nNote: Some stocks may not have yfinance data available")
    
    # Data quality check
    print("\n" + "=" * 70)
    print("DATA QUALITY CHECK")
    print("=" * 70)
    
    # Average records per stock
    avg_records = total_ohlc / stocks_with_data if stocks_with_data > 0 else 0
    print(f"\n✓ Average OHLC records per stock: {avg_records:.0f}")
    
    # Expected records (4 years ≈ 1000 trading days)
    expected_records = 1000
    coverage = (avg_records / expected_records) * 100
    print(f"✓ Data coverage: {coverage:.1f}% of expected")
    
    if coverage > 80:
        print("✓ Excellent data coverage!")
    elif coverage > 50:
        print("⚠️  Good data coverage, but some gaps exist")
    else:
        print("⚠️  Low data coverage - check scraper logs")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("✓ DATABASE CHECK COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review sector distribution above")
    print("2. Run: python ../data/nse_data_bridge.py (to integrate with trading system)")
    print("3. Or start dashboard: streamlit run ../dashboard/streamlit_app.py")

if __name__ == "__main__":
    check_database()
