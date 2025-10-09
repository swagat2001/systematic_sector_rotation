"""
Test CSV Data Bridge
====================

Quick test to verify CSV data loading works correctly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from data.csv_data_bridge import CSVDataBridge

print("=" * 80)
print("TESTING CSV DATA BRIDGE")
print("=" * 80)

try:
    # Initialize
    print("\n1. Initializing CSV bridge...")
    bridge = CSVDataBridge(r"C:\Users\Admin\Desktop\data\stock_data_NSE")
    print("✓ Bridge initialized")
    
    # Get sectors
    print("\n2. Getting available sectors...")
    sectors = bridge.get_available_sectors()
    print(f"✓ Found {len(sectors)} sectors:")
    for sector in sectors[:5]:  # Show first 5
        stocks = bridge.get_stocks_by_sector(sector)
        print(f"  • {sector}: {len(stocks)} stocks")
    
    if len(sectors) > 5:
        print(f"  ... and {len(sectors)-5} more sectors")
    
    # Get date range
    print("\n3. Getting date range...")
    min_date, max_date = bridge.get_date_range()
    print(f"✓ Date range: {min_date.date()} to {max_date.date()}")
    print(f"  ({(max_date - min_date).days} days, ~{(max_date - min_date).days/365:.1f} years)")
    
    # Test loading a stock
    print("\n4. Testing stock data load...")
    if sectors:
        test_stocks = bridge.get_stocks_by_sector(sectors[0])[:3]
        
        for symbol in test_stocks:
            df = bridge.get_stock_prices(symbol)
            if not df.empty:
                print(f"\n  {symbol}:")
                print(f"    Records: {len(df)}")
                print(f"    Date range: {df.index[0].date()} to {df.index[-1].date()}")
                print(f"    Price range: ₹{df['Close'].min():.2f} - ₹{df['Close'].max():.2f}")
                print(f"    Columns: {list(df.columns)}")
                break  # Just test one stock
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nCSV data bridge is working correctly.")
    print("You can now run the dashboard with CSV data source.")
    print("\nNext step: streamlit run dashboard/streamlit_app.py")
    print("=" * 80)

except FileNotFoundError as e:
    print(f"\n❌ ERROR: {e}")
    print("\nPlease check:")
    print("1. Path is correct: C:\\Users\\Admin\\Desktop\\data\\stock_data_NSE")
    print("2. Folder contains sector subdirectories")
    print("3. Each sector folder contains CSV files")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    
    print("\nPlease ensure your CSV files have these columns:")
    print("  - Date (or date)")
    print("  - Open (or open)")
    print("  - High (or high)")
    print("  - Low (or low)")
    print("  - Close (or close)")
    print("  - Volume (or volume)")
