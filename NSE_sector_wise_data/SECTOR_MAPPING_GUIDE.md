# NSE Real Sector Mapping - Production Guide

## The Problem
EQUITY_L.csv from NSE contains stock symbols but NOT sector information.

## Production Solution (3 Options)

### Option 1: NSE Sector-Wise Lists (RECOMMENDED)
NSE provides ready-made sector classification CSVs:

**Download from:**
```
https://www.nseindia.com/market-data/live-equity-market
```

Available sector files:
- IT sector stocks
- Banking sector stocks  
- Pharma sector stocks
- Auto sector stocks
- Metal sector stocks
- FMCG sector stocks
- etc.

**Implementation:**
```python
python download_nse_sector_csvs.py  # Downloads all sector files
python merge_sector_data.py         # Merges into single mapping
```

### Option 2: Use BSE Sector Classification
BSE provides better sector metadata:

```
https://www.bseindia.com/corporates/List_Scrips.aspx
```

Download "List of Securities" with sector column.

### Option 3: Dynamic API Fetching (Slowest)
```bash
python dynamic_sector_mapper.py
```

Makes live API calls to NSE for each stock (10-15 mins for 2000+ stocks).

## Quick Start for Testing

For now, use the scraped yfinance metadata during the OHLC pipeline:

```bash
python nse_cash_ohlc_pipeline.py --workers 2 --sleep 1.0
```

The scraper fetches yfinance sector data automatically during metadata collection.

Then update sectors from the scraped database:

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('nse_cash.db')
companies = pd.read_sql('SELECT symbol, sector FROM companies WHERE sector IS NOT NULL', conn)
companies.to_csv('stock_sector_mapping.csv', index=False)
```

## Bottom Line

**For production:** Use NSE's official sector-wise CSVs (Option 1)
**For now:** Run the scraper - it fetches sectors via yfinance automatically

The sector data will be in the `companies` table of `nse_cash.db` after scraping.
