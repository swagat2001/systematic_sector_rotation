# HOW TO LOAD YOUR 1800+ STOCKS DATA

## PROBLEM SUMMARY

The automated data pipeline is facing two issues:
1. **yfinance ticker failures** - Yahoo Finance API is not returning data for NSE sectoral indices
2. **NSE website timeouts** - niftyindices.com is timing out when fetching constituent lists

## SOLUTION: Load Your Pre-Downloaded Data

Since you already have 1800+ stocks with 4 years of OHLC data downloaded, we'll load it directly into the database.

---

## STEP 1: Organize Your Data

Choose one of these formats:

### Option A: Folder Structure (Recommended)

```
data/your_data/
  ├── sectors/              # Sector index data
  │   ├── NIFTY_AUTO.csv
  │   ├── NIFTY_BANK.csv
  │   ├── NIFTY_IT.csv
  │   └── ... (17 sector files)
  │
  └── stocks/               # Individual stock data
      ├── INFY.csv
      ├── TCS.csv
      ├── WIPRO.csv
      └── ... (1800+ files)
```

**CSV Format:** Each file should have these columns:
```
Date,Open,High,Low,Close,Volume
2020-01-01,1000.00,1020.00,995.00,1015.00,5000000
2020-01-02,1015.00,1025.00,1010.00,1020.00,4800000
...
```

### Option B: Single File

Create one CSV/Excel file with all data:
```
Symbol,Date,Open,High,Low,Close,Volume,Sector
INFY,2020-01-01,1000,1020,995,1015,5000000,Nifty IT
INFY,2020-01-02,1015,1025,1010,1020,4800000,Nifty IT
TCS,2020-01-01,2000,2050,1980,2030,3000000,Nifty IT
...
```

---

## STEP 2: Load Data into Database

### Method 1: Using the Custom Loader

```bash
# Show instructions
python data/load_your_data.py --instructions

# Load from folder structure
python data/load_your_data.py --folder data/your_data

# Load from single file
python data/load_your_data.py --file data/your_data/all_data.csv
```

### Method 2: Manual Loading (Python Script)

Create a script `load_my_data.py`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from data.data_storage import DataStorage
from config import NSESectors

# Initialize database
storage = DataStorage()

# Load sectors
storage.bulk_load_sectors(NSESectors.SECTOR_TICKERS)

# Load your stock data
data_folder = Path("data/your_data/stocks")

for csv_file in data_folder.glob("*.csv"):
    symbol = csv_file.stem  # e.g., "INFY.csv" -> "INFY"
    
    # Read CSV
    df = pd.read_csv(csv_file, parse_dates=['Date'], index_col='Date')
    
    # Add stock to database
    stock = storage.get_stock_by_symbol(symbol)
    if not stock:
        storage.add_stock(symbol, sector_name="Nifty IT")  # Adjust sector as needed
    
    # Save prices
    storage.save_stock_prices(symbol, df)
    
    print(f"Loaded {symbol}: {len(df)} records")

storage.close()
print("Done!")
```

---

## STEP 3: Verify Data Loaded

```python
from data.data_storage import DataStorage

storage = DataStorage()

# Check database status
summary = storage.get_data_summary()

print(f"Sectors: {summary['sectors']}")
print(f"Stocks: {summary['stocks']}")
print(f"Price records: {summary['stock_price_records']:,}")
print(f"Latest date: {summary.get('latest_price_date')}")

storage.close()
```

Expected output:
```
Sectors: 17
Stocks: 1800+
Price records: 1,800,000+ (1800 stocks × 4 years × 252 days)
Latest date: 2024-XX-XX
```

---

## STEP 4: After Data is Loaded

Once your data is in the database, you can proceed with Phase 4:

```bash
# Test that everything works
python tests/test_phase1.py
python tests/test_phase2.py
python tests/test_phase3.py

# All tests should pass, then proceed to Phase 4
```

---

## TROUBLESHOOTING

### Issue: "ModuleNotFoundError: No module named 'config'"
**Solution:** Always run scripts from the project root directory:
```bash
cd C:\Users\swaga\OneDrive\Desktop\systematic_sector_rotation
python data/load_your_data.py --folder data/your_data
```

### Issue: "Table already exists" or duplicate data
**Solution:** Delete the database and start fresh:
```bash
# Delete database
rm database/strategy.db

# Run loader again
python data/load_your_data.py --folder data/your_data
```

### Issue: Data format doesn't match
**Solution:** Adjust column names in your CSVs to match:
- `Date` (index column)
- `Open, High, Low, Close, Volume`

Or modify the loader script to match your format.

---

## NEXT STEPS

After successfully loading data:

1. **Verify data quality:**
   ```bash
   python tests/test_phase1.py
   ```

2. **Test scoring models:**
   ```bash
   python tests/test_phase2.py
   ```

3. **Test strategy:**
   ```bash
   python tests/test_phase3.py
   ```

4. **Proceed to Phase 4:** Execution & Paper Trading

---

## NEED HELP?

If you encounter issues, please share:
1. The format/structure of your downloaded data
2. Error messages from the loader
3. Sample of your CSV files (first few rows)

We can then customize the loader to match your exact format.
