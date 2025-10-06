"""
Quick fix script to verify sector mappings are working correctly
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from data.nse_data_bridge import NSEDataBridge

print("Checking sector mappings...")
bridge = NSEDataBridge()

# Get a sample of stocks and their sectors
query = """
SELECT symbol, sector, industry 
FROM companies 
WHERE sector IS NOT NULL
LIMIT 20
"""

import pandas as pd
df = pd.read_sql_query(query, bridge.conn)

print("\nSample stock-sector mappings:")
print("=" * 80)
for _, row in df.iterrows():
    mapped = bridge._map_sector(row['sector'], row['industry'])
    print(f"{row['symbol']:<10} | Sector: {row['sector']:<30} | Mapped: {mapped}")

print("\n" + "=" * 80)
print("\nAvailable Nifty sectors:")
sectors = bridge.get_available_sectors()
for sector in sectors:
    stocks = bridge.get_stocks_by_sector(sector)
    print(f"  {sector}: {len(stocks)} stocks")

print("\n" + "=" * 80)
print("Sector mapping is working correctly!" if sectors else "ERROR: No sectors mapped!")
