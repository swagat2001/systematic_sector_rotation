?** → `python NSE_sector_wise_data/check_nse_database.py`
- **Test NSE connection?** → `python NSE_sector_wise_data/test_nse_connection.py`
- **Understand data flow?** → Read this file!

---

## 🎯 Essential Files (Must Keep)

**Data Pipeline (4 files):**
1. `NSE_sector_wise_data/nse_cash_ohlc_pipeline.py` - Main scraper
2. `NSE_sector_wise_data/download_equity_list.py` - Download stock list
3. `NSE_sector_wise_data/check_nse_database.py` - Verify data
4. `data/nse_data_bridge.py` - Connect DB to strategy

**Strategy (4 files):**
1. `strategy/sector_rotation.py` - Rank sectors
2. `strategy/stock_selection.py` - Pick stocks
3. `strategy/portfolio_manager.py` - Manage positions
4. `config.py` - Configuration

**Backtesting (2 files):**
1. `backtesting/backtest_engine.py` - Run simulation
2. `backtesting/performance_analyzer.py` - Calculate metrics

**Models (4 files):**
1. `models/technical_scorer.py` - Technical analysis
2. `models/fundamental_scorer.py` - Fundamental analysis
3. `models/statistical_scorer.py` - Statistical analysis
4. `models/composite_scorer.py` - Combined scoring

**Dashboard (3 files):**
1. `dashboard/streamlit_app.py` - Main UI
2. `dashboard/real_data_backtest.py` - Backtest logic
3. `dashboard/chart_generator.py` - Charts

**Utilities (2 files):**
1. `utils/logger.py` - Logging
2. `utils/helpers.py` - Common functions

**Total: 24 essential files**

---

## 🔄 Execution Order

### First Time Setup:
```bash
# 1. Download stock list
cd NSE_sector_wise_data
python download_equity_list.py

# 2. Run scraper (50-70 mins)
python nse_cash_ohlc_pipeline.py --workers 2 --sleep 1.0

# 3. Verify data
python check_nse_database.py

# 4. Test data bridge
cd ../data
python nse_data_bridge.py

# 5. Run dashboard
cd ..
streamlit run dashboard/streamlit_app.py
```

### Regular Use:
```bash
# Just run dashboard
streamlit run dashboard/streamlit_app.py
```

---

## 🗑️ Safe to Delete

Run this cleanup script:

```python
# cleanup_obsolete_files.py
import os
from pathlib import Path

obsolete_files = [
    # Root level
    'PHASE1_README.md',
    'PHASE2_README.md', 
    'PHASE3_README.md',
    'PHASE4_README.md',
    'PHASE5_README.md',
    'PHASE6_README.md',
    'PROGRESS_REPORT.md',
    'PROJECT_COMPLETE.md',
    'PROJECT_STATUS_FINAL.md',
    'STATUS_UPDATE.md',
    'CLEANUP_PLAN.md',
    'cleanup.py',
    'directory.md',
    'DATA_LOADING_GUIDE.md',
    'REAL_DATA_QUICKSTART.md',
    'test_setup.py',
    
    # NSE_sector_wise_data
    'NSE_sector_wise_data/check_database.py',
    'NSE_sector_wise_data/nse_csv_loader.py',
    'NSE_sector_wise_data/nse_data_scraper.py',
    'NSE_sector_wise_data/nse_robust_scraper.py',
    'NSE_sector_wise_data/dynamic_sector_mapper.py',
    'NSE_sector_wise_data/sector_mapper.py',
    'NSE_sector_wise_data/SCRAPER_INTEGRATION_GUIDE.md',
    'NSE_sector_wise_data/SECTOR_MAPPING_GUIDE.md',
    'NSE_sector_wise_data/requirements.txt',  # Use root requirements.txt
]

deleted = []
not_found = []

for file_path in obsolete_files:
    full_path = Path(file_path)
    if full_path.exists():
        full_path.unlink()
        deleted.append(file_path)
        print(f"✓ Deleted: {file_path}")
    else:
        not_found.append(file_path)
        print(f"⊗ Not found: {file_path}")

print(f"\n{'='*60}")
print(f"Cleanup Complete!")
print(f"{'='*60}")
print(f"Deleted: {len(deleted)} files")
print(f"Not found: {len(not_found)} files")
```

---

## 📋 Dependency Matrix

| Component | Depends On | Used By |
|-----------|-----------|---------|
| `config.py` | None | Everything |
| `nse_cash_ohlc_pipeline.py` | yfinance, requests, pandas | None (run once) |
| `nse_cash.db` | Scraper | `nse_data_bridge.py` |
| `nse_data_bridge.py` | `nse_cash.db` | Backtest, Dashboard |
| `sector_rotation.py` | Data bridge | `stock_selection.py` |
| `stock_selection.py` | Sector rotation, Models | `portfolio_manager.py` |
| `portfolio_manager.py` | Stock selection | `backtest_engine.py` |
| `backtest_engine.py` | All strategy components | Dashboard |
| `performance_analyzer.py` | Backtest results | Dashboard |
| `streamlit_app.py` | All components | User |

---

## 🔐 Important Files (DO NOT DELETE)

| File | Why Critical |
|------|--------------|
| `nse_cash.db` | **Contains all scraped data** (971K records) |
| `EQUITY_L.csv` | NSE stock master list |
| `config.py` | System configuration |
| `requirements.txt` | Package dependencies |
| `.gitignore` | Git configuration |
| `LICENSE` | Legal protection |

---

## 📝 File Sizes (Approximate)

```
nse_cash.db                     ~180 MB    (LARGE - all data)
EQUITY_L.csv                    ~250 KB
stock_sector_mapping.csv        ~150 KB
logs/                           ~1-10 MB   (grows over time)

Total project: ~200 MB
```

---

## 🎓 Learning Path

**Understanding the system:**

1. **Start here:** `README.md`
2. **Architecture:** `ARCHITECTURE.md`
3. **Data flow:** This file (FILE_MAP.md)
4. **Run scraper:** `NSE_sector_wise_data/nse_cash_ohlc_pipeline.py`
5. **Understand bridge:** `data/nse_data_bridge.py`
6. **Strategy logic:** `strategy/sector_rotation.py`
7. **Run backtest:** `dashboard/streamlit_app.py`

**Modifying the system:**

1. **Change strategy params:** Edit `config.py`
2. **Add new indicator:** Edit `models/technical_scorer.py`
3. **Modify scoring:** Edit `models/composite_scorer.py`
4. **Change rebalancing:** Edit `strategy/portfolio_manager.py`

---

## 🐛 Debugging Guide

| Problem | Check File | Solution |
|---------|-----------|----------|
| No data | `nse_cash.db` | Run scraper |
| Scraper fails | `test_nse_connection.py` | Check NSE connectivity |
| Wrong sectors | `nse_data_bridge.py` | Review sector mapping |
| Poor performance | `config.py` | Tune parameters |
| Backtest error | `backtest_engine.py` | Check logs/ |

---

## 📞 Support

**File-specific questions:**
- Scraper issues → Check `NSE_sector_wise_data/README.md`
- Strategy questions → See strategy/ files
- Dashboard problems → Check dashboard/ files

**General questions:**
- Read `README.md`
- Check `ARCHITECTURE.md`
- Review this file (FILE_MAP.md)

---

**Last Updated:** October 2025  
**Total Active Files:** 24 core + documentation  
**Lines of Code:** ~8,000+  
**100% Dynamic, Zero Hardcoding** ✨
