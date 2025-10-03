# NSE Historical Data Integration Guide

## Overview

This guide shows you how to integrate your **existing NSE data scraper** with the systematic trading system. Your scraper fetches 4 years of historical OHLC data for 1800+ NSE stocks.

## Files You Have

From your uploaded documents:

1. **EQUITY_L.csv** - Complete NSE equity list (download fresh or use provided)
2. **download_equity_list.py** - Downloads latest EQUITY_L.csv from NSE  
3. **nse_cash_ohlc_pipeline.py** - Main scraper with concurrent Bhavcopy downloads
4. **test_nse_connection.py** - Diagnostic tool for connection testing

## Quick Start (3 Steps)

### Step 1: Place Your Scraper Files

Copy your 4 scraper files to: `NSE_sector_wise_data/`

```bash
NSE_sector_wise_data/
├── EQUITY_L.csv                    # NSE equity list
├── download_equity_list.py         # List downloader
├── nse_cash_ohlc_pipeline.py       # Main scraper
└── test_nse_connection.py          # Connection tester
```

### Step 2: Install Dependencies

```bash
pip install pandas requests yfinance sqlalchemy tqdm urllib3
```

### Step 3: Run the Scraper

```bash
# Test connection first (optional)
python NSE_sector_wise_data/test_nse_connection.py

# Run the scraper (30-45 minutes)
python NSE_sector_wise_data/nse_cash_ohlc_pipeline.py --workers 2 --sleep 1.0
```

## What The Scraper Does

1. **Reads EQUITY_L.csv** - Gets list of ~1800 stocks
2. **Fetches Metadata** - Gets sector/industry from yfinance  
3. **Downloads Bhavcopy** - Concurrent download of ~1000 daily files (4 years)
4. **Stores in SQLite** - Creates `nse_cash.db` with:
   - `companies` table (metadata)
   - `ohlc` table (price data)

## Database Schema (nse_cash.db)

### companies table
```sql
symbol          TEXT PRIMARY KEY
fullname        TEXT
isin            TEXT
series          TEXT
sector          TEXT
industry        TEXT
last_metadata_sync  DATETIME
```

### ohlc table
```sql
id              INTEGER PRIMARY KEY
symbol          TEXT (indexed)
date            DATE (indexed)
open            FLOAT
high            FLOAT
low             FLOAT
close           FLOAT
adj_close       FLOAT
volume          BIGINT
```

## Integration with Trading System

### Option 1: Use Existing nse_csv_loader.py

Our system already has `NSE_sector_wise_data/nse_csv_loader.py` which:
- Loads from your `nse_cash.db`
- Maps to our 17 sector categories
- Imports into `nse_data.db` (our format)

**Usage:**
```bash
python NSE_sector_wise_data/nse_csv_loader.py
# Choose option 3: Import from scraped database
```

### Option 2: Direct Bridge (recommended)

Update `data/nse_data_bridge.py` to read directly from `nse_cash.db`:

```python
def load_from_scraped_db():
    """Load data from nse_cash.db"""
    import sqlite3
    
    # Connect to scraped database
    conn = sqlite3.connect('NSE_sector_wise_data/nse_cash.db')
    
    # Read companies with sector mapping
    companies_df = pd.read_sql("SELECT * FROM companies", conn)
    
    # Sector mapping to our 17 categories
    SECTOR_MAP = {
        'Information Technology': 'Nifty IT',
        'Banks': 'Nifty Bank',
        'Pharmaceuticals': 'Nifty Pharma',
        # ... add all mappings
    }
    
    companies_df['sector'] = companies_df['sector'].map(SECTOR_MAP)
    
    # Read OHLC data
    ohlc_df = pd.read_sql("SELECT * FROM ohlc", conn)
    
    return companies_df, ohlc_df
```

## Sector Mapping (NSE → Our System)

| NSE Sector | Our Sector Category |
|------------|---------------------|
| Information Technology | Nifty IT |
| Banks | Nifty Bank |
| Pharmaceuticals | Nifty Pharma |
| Consumer Goods / FMCG | Nifty FMCG |
| Automobiles | Nifty Auto |
| Metals / Steel | Nifty Metal |
| Oil & Gas / Power | Nifty Energy |
| Real Estate | Nifty Realty |
| Media / Entertainment | Nifty Media |
| Financial Services / NBFC | Nifty Financial Services |
| Construction | Nifty Infrastructure |

## Scraper Configuration

### Command Line Arguments

```bash
python nse_cash_ohlc_pipeline.py \
  --database-url sqlite:///nse_cash.db \
  --workers 2 \
  --sleep 1.0
```

**Parameters:**
- `--workers`: Concurrent downloads (default: 2, max recommended: 4)
- `--sleep`: Seconds between downloads (default: 1.0, min: 0.5)
- `--database-url`: Output database (SQLite or PostgreSQL)

### SSL/Connection Issues

If you face SSL errors:

1. **Test connection first:**
   ```bash
   python NSE_sector_wise_data/test_nse_connection.py
   ```

2. **The scraper auto-handles:**
   - SSL certificate verification
   - Retry logic (3 attempts)
   - Exponential backoff
   - Fallback to non-SSL if needed

3. **Manual fix (if needed):**
   ```python
   # In nse_cash_ohlc_pipeline.py
   # Line ~80: session.verify = False  # Disable SSL
   ```

## Data Coverage

**After scraping completes:**
- **~1,800 stocks** across all NSE sectors
- **~25,000 OHLC records** (1800 stocks × ~1000 trading days × 4 years)
- **Date range:** Last 4 years from today
- **All EQ series** stocks only

## Running Backtest with Real Data

Once scraper completes:

```bash
# Start dashboard
streamlit run dashboard/streamlit_app.py

# In UI:
1. Go to "Real Data Backtest"
2. Select date range (up to 4 years)
3. Set initial capital
4. Click "Run Backtest"
```

The system will:
1. Load data from `nse_cash.db` or `nse_data.db`
2. Run strategy with real prices
3. Display complete results with all metrics

## Troubleshooting

### Issue: SSL Certificate Error
**Solution:** Run `test_nse_connection.py` and check output

### Issue: 404 Errors for Some Dates
**Solution:** Normal - NSE didn't publish on holidays/weekends

### Issue: Slow Download Speed
**Solution:** Increase `--workers` to 3-4 (max), but may hit rate limits

### Issue: Database Locked
**Solution:** SQLite doesn't handle high concurrency well - reduce workers to 1-2

### Issue: yfinance Metadata Failures
**Solution:** Some stocks may not have yfinance data - scraper continues anyway

## Production Recommendations

1. **Run scraper overnight** (30-45 minutes)
2. **Update weekly** to get latest prices
3. **Keep workers at 2** for stability
4. **Monitor logs** for failed Bhavcopy downloads
5. **Backup nse_cash.db** before re-running

## Next Steps

After scraping completes:

1. ✅ Run backtest with real 4-year data
2. ✅ Analyze strategy performance across sectors
3. ✅ Generate production-ready reports
4. ✅ Deploy strategy with confidence

## Files Modified in Our System

When integrating your scraper:

- `data/nse_data_bridge.py` - Add function to read from `nse_cash.db`
- `NSE_sector_wise_data/nse_csv_loader.py` - Add import option
- `config.py` - Update database paths if needed

---

**Your scraper is production-ready and will give us real historical data for 1800+ stocks!** 🎯
