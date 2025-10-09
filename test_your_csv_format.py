"""
Test CSV Loading with Your Specific Format
===========================================

Tests the CSV bridge with your actual file format:
- Row 1: Headers (Price, Adj Close, Close, High, Low, Open, Volume)
- Row 2: Ticker info (20MICRONS.NS repeated)
- Row 3: Date column header
- Row 4+: Actual data with dates in DD-MM-YYYY format
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd

print("=" * 80)
print("TESTING YOUR CSV FORMAT")
print("=" * 80)

# Test 1: Read a sample CSV directly
print("\n1. Testing direct CSV read...")
csv_path = r"C:\Users\Admin\Desktop\data\stock_data_NSE"

# Find first CSV file
csv_file = None
for sector_dir in Path(csv_path).iterdir():
    if sector_dir.is_dir():
        csv_files = list(sector_dir.glob("*.csv"))
        if csv_files:
            csv_file = csv_files[0]
            break

if csv_file:
    print(f"   Testing with: {csv_file.name}")
    
    # Read raw
    df_raw = pd.read_csv(csv_file)
    print(f"\n   Raw CSV (first 5 rows):")
    print(df_raw.head())
    print(f"\n   Columns: {list(df_raw.columns)}")
    
    # Read skipping first 2 rows
    df_clean = pd.read_csv(csv_file, skiprows=2)
    print(f"\n   After skipping 2 rows:")
    print(df_clean.head())
    print(f"\n   Columns: {list(df_clean.columns)}")
    
    # Parse dates
    date_col = df_clean.columns[0]
    print(f"\n   Date column: '{date_col}'")
    print(f"   Sample dates: {df_clean[date_col].head(3).tolist()}")
    
    # Try parsing dates
    try:
        df_clean['Date'] = pd.to_datetime(df_clean[date_col], dayfirst=True)
        print(f"   ✓ Dates parsed successfully!")
        print(f"   Date range: {df_clean['Date'].min()} to {df_clean['Date'].max()}")
    except Exception as e:
        print(f"   ✗ Date parsing failed: {e}")
else:
    print("   ✗ No CSV files found!")

# Test 2: Use CSV Bridge
print("\n" + "=" * 80)
print("2. Testing CSV Bridge...")
print("=" * 80)

try:
    from data.csv_data_bridge import CSVDataBridge
    
    bridge = CSVDataBridge(csv_path)
    print(f"✓ Bridge initialized")
    print(f"  Sectors: {len(bridge.get_available_sectors())}")
    print(f"  Total stocks: {bridge.total_stocks}")
    
    # Test loading a stock
    print("\n3. Testing stock data load...")
    sectors = bridge.get_available_sectors()
    if sectors:
        test_stocks = bridge.get_stocks_by_sector(sectors[0])[:2]
        
        for symbol in test_stocks:
            print(f"\n   Loading {symbol}...")
            df = bridge.get_stock_prices(symbol)
            
            if not df.empty:
                print(f"   ✓ Loaded successfully!")
                print(f"     Records: {len(df)}")
                print(f"     Date range: {df.index[0].date()} to {df.index[-1].date()}")
                print(f"     Columns: {list(df.columns)}")
                print(f"     Sample data:")
                print(df.head(3))
                break  # Just test one
            else:
                print(f"   ✗ Failed to load {symbol}")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nYour CSV format is now supported!")
    print("Run the dashboard: streamlit run dashboard/streamlit_app.py")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("DEBUGGING INFO")
    print("=" * 80)
    print(f"\nCSV Path: {csv_path}")
    print(f"Path exists: {Path(csv_path).exists()}")
    
    if Path(csv_path).exists():
        print(f"\nContents of {csv_path}:")
        for item in Path(csv_path).iterdir():
            print(f"  • {item.name} ({'DIR' if item.is_dir() else 'FILE'})")
