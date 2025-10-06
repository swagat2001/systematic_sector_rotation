"""
Check NSE database for actual tradeable data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from datetime import datetime, timedelta
from data.nse_data_bridge import NSEDataBridge

print("\n" + "="*80)
print("NSE DATABASE DIAGNOSTIC CHECK")
print("="*80 + "\n")

try:
    bridge = NSEDataBridge()
    
    # 1. Check date range
    min_date, max_date = bridge.get_date_range()
    print(f"1. DATE RANGE:")
    print(f"   From: {min_date.date()}")
    print(f"   To: {max_date.date()}")
    print(f"   Days: {(max_date - min_date).days}")
    
    # 2. Check sectors
    sectors = bridge.get_available_sectors()
    print(f"\n2. SECTORS: {len(sectors)}")
    for sector in sectors[:5]:
        stocks = bridge.get_stocks_by_sector(sector)
        print(f"   {sector}: {len(stocks)} stocks")
    
    # 3. Sample actual data for a stock
    print(f"\n3. SAMPLE STOCK DATA:")
    test_sector = sectors[0]
    test_stocks = bridge.get_stocks_by_sector(test_sector)[:3]
    
    for symbol in test_stocks:
        df = bridge.get_stock_prices(symbol)
        if not df.empty:
            print(f"\n   {symbol}:")
            print(f"     Records: {len(df)}")
            print(f"     Date range: {df.index[0].date()} to {df.index[-1].date()}")
            print(f"     Last close: ₹{df['Close'].iloc[-1]:.2f}")
            print(f"     Has volume: {df['Volume'].iloc[-1] > 0}")
            break
    
    # 4. Test prepare_backtest_data
    print(f"\n4. TESTING BACKTEST DATA PREPARATION:")
    start_date = max_date - timedelta(days=365)
    end_date = max_date
    
    print(f"   Loading data from {start_date.date()} to {end_date.date()}...")
    
    sector_prices, stocks_data, stocks_prices = bridge.prepare_backtest_data(
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"   ✓ Sector indices created: {len(sector_prices)}")
    print(f"   ✓ Stocks with data: {len(stocks_data)}")
    print(f"   ✓ Stock prices loaded: {len(stocks_prices)}")
    
    # Check sector indices have data
    if sector_prices:
        sample_sector = list(sector_prices.keys())[0]
        sample_df = sector_prices[sample_sector]
        print(f"\n   Sample sector index ({sample_sector}):")
        print(f"     Records: {len(sample_df)}")
        print(f"     Columns: {sample_df.columns.tolist()}")
        print(f"     Date range: {sample_df.index[0]} to {sample_df.index[-1]}")
        print(f"     Last value: {sample_df['Close'].iloc[-1]:.2f}")
    
    # Check a stock has data
    if stocks_prices:
        sample_stock = list(stocks_prices.keys())[0]
        sample_df = stocks_prices[sample_stock]
        print(f"\n   Sample stock ({sample_stock}):")
        print(f"     Records: {len(sample_df)}")
        print(f"     Last close: ₹{sample_df['Close'].iloc[-1]:.2f}")
    
    print("\n" + "="*80)
    print("DIAGNOSIS:")
    print("="*80)
    
    if len(sector_prices) == 0:
        print("❌ NO SECTOR INDICES CREATED - Database has no usable data")
    elif len(stocks_data) == 0:
        print("❌ NO STOCKS WITH DATA - Stock data missing fundamentals")
    elif len(stocks_prices) == 0:
        print("❌ NO STOCK PRICES - Price data not loading")
    else:
        print("✅ Database has data - Issue is in backtest logic")
        print(f"   - {len(sector_prices)} sector indices available")
        print(f"   - {len(stocks_data)} stocks with data")
        print(f"   - {len(stocks_prices)} stocks with prices")
        print("\n   → Problem likely in:")
        print("     1. Sector rotation filters (momentum/trend too strict)")
        print("     2. Stock selection filters (scoring thresholds too high)")
        print("     3. Date range calculation (not enough history)")
    
    bridge.close()
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80 + "\n")
