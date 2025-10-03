# 🚀 Quick Start Guide

**Get up and running in 5 minutes!**

---

## ✅ Prerequisites

- Python 3.11+
- pip installed
- Git (optional)

---

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/yourusername/systematic_sector_rotation.git
cd systematic_sector_rotation

# Install dependencies
pip install -r requirements.txt
```

---

## 🎯 Option 1: Use Existing Data (FASTEST)

**If you already have `NSE_sector_wise_data/nse_cash.db`:**

```bash
# Just run the dashboard
streamlit run dashboard/streamlit_app.py
```

Then:
1. Navigate to **"Real Data Backtest"** tab
2. Click **"Run Backtest"**
3. See results!

**Time:** 1 minute ⚡

---

## 📊 Option 2: Scrape Fresh Data

**If you need fresh NSE data:**

### Step 1: Download Stock List (10 seconds)
```bash
cd NSE_sector_wise_data
python download_equity_list.py
```

### Step 2: Run Scraper (50-70 minutes)
```bash
python nse_cash_ohlc_pipeline.py --workers 2 --sleep 1.0
```

**What this does:**
- Downloads 4 years of NSE Bhavcopy files
- Fetches sector data from yfinance (dynamic!)
- Creates database with 1,744 stocks
- 971,772 price records

☕ **Take a coffee break!**

### Step 3: Verify Data (5 seconds)
```bash
python check_nse_database.py
```

### Step 4: Test Bridge (5 seconds)
```bash
cd ../data
python nse_data_bridge.py
```

### Step 5: Run Dashboard
```bash
cd ..
streamlit run dashboard/streamlit_app.py
```

**Total Time:** ~60 minutes (mostly automated)

---

## 🎨 Dashboard Features

### Tab 1: Overview
- System architecture diagram
- Current portfolio holdings
- Quick statistics

### Tab 2: Real Data Backtest ⭐
- **Select date range:** Oct 2021 - Jul 2024
- **Set initial capital:** ₹10,00,000
- **Click "Run Backtest"**
- See complete results with charts

### Tab 3: Sector Analysis
- Heatmap of sector returns
- Correlation matrix
- Sector momentum scores

### Tab 4: Performance
- Equity curve with drawdowns
- Monthly returns heatmap
- Risk/return metrics

### Tab 5: Trade History
- Complete trade log
- Filters and search
- Download CSV

---

## 🔧 Common Commands

```bash
# Run dashboard
streamlit run dashboard/streamlit_app.py

# Check database
cd NSE_sector_wise_data
python check_nse_database.py

# Test NSE connection
python test_nse_connection.py

# Run CLI backtest
cd ..
python main.py

# Cleanup old files
python cleanup_obsolete_files.py
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `README.md` | Complete documentation |
| `FILE_MAP.md` | Every file explained |
| `ARCHITECTURE.md` | System design |
| `config.py` | Configuration settings |
| `nse_cash.db` | Your data (180 MB) |

---

## ⚙️ Configuration

Edit `config.py` to customize:

```python
STRATEGY_CONFIG = {
    'top_n_sectors': 3,         # Change to 2 or 4
    'stocks_per_sector': 5,     # Change to 3-7
    'rebalance_frequency': 'monthly',  # Or 'weekly'
}

RISK_CONFIG = {
    'max_position_size': 0.10,  # Max 10% per stock
    'stop_loss': 0.15,          # 15% stop loss
}
```

---

## 🎯 Example Backtest

```bash
streamlit run dashboard/streamlit_app.py
```

**In Dashboard:**
1. Go to "Real Data Backtest"
2. Start Date: **2021-10-05**
3. End Date: **2024-07-05**
4. Initial Capital: **₹10,00,000**
5. Click **"Run Backtest"**

**Results you'll see:**
- Total Return: X%
- Sharpe Ratio: X.XX
- Max Drawdown: -X%
- Win Rate: X%
- Complete equity curve
- All trades executed

---

## 📚 Documentation

**Must Read:**
1. **[README.md](README.md)** - Start here
2. **[FILE_MAP.md](FILE_MAP.md)** - File reference
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** - How it works

**Data Pipeline:**
- [NSE_sector_wise_data/README.md](NSE_sector_wise_data/README.md)

**Live Trading (Future):**
- [ZERODHA_KITE_GUIDE.md](ZERODHA_KITE_GUIDE.md)

---

## 🐛 Troubleshooting

### Scraper fails with SSL error
```bash
cd NSE_sector_wise_data
python test_nse_connection.py
```

If NSE blocks you, wait 5 minutes and retry with:
```bash
python nse_cash_ohlc_pipeline.py --workers 1 --sleep 2.0
```

### Dashboard won't start
```bash
# Check if streamlit is installed
pip install streamlit

# Check if database exists
cd NSE_sector_wise_data
python check_nse_database.py
```

### No sector data
- This is normal for ~0.3% of stocks
- System handles it automatically
- Unmapped stocks go to "Nifty 50"

### Backtest takes too long
- Normal for 2.8 years of data
- First run: 2-3 minutes
- Subsequent runs: faster (cached)

---

## 💡 Tips

**Speed up scraping:**
- Use `--workers 3` (but be careful of NSE rate limits)
- Best: `--workers 2 --sleep 1.0`

**Better backtest:**
- Longer date range = more reliable results
- Test multiple parameter combinations
- Compare against benchmark (Nifty 50)

**Production use:**
- Review all trades before going live
- Start with paper trading
- Monitor daily performance
- Keep logs for analysis

---

## 🎓 Learning Resources

**Strategy Theory:**
- Momentum Investing: Jegadeesh & Titman (1993)
- Sector Rotation: Faber (2007)
- Multi-factor Models: Fama-French

**Code Learning:**
- Start with `strategy/sector_rotation.py`
- Then `strategy/stock_selection.py`
- Finally `backtesting/backtest_engine.py`

---

## 🤝 Getting Help

1. Check `FILE_MAP.md` for file explanations
2. Review `ARCHITECTURE.md` for system design
3. Search issues on GitHub
4. Open new issue with error logs

---

## ✨ What Makes This Special

✅ **100% Dynamic** - Zero hardcoded data  
✅ **Production Ready** - Real NSE data, tested  
✅ **Fully Documented** - Every file explained  
✅ **Modular Design** - Easy to extend  
✅ **Open Source** - MIT License  

---

## 🚀 Next Steps

After running your first backtest:

1. **Analyze results** - What worked? What didn't?
2. **Tune parameters** - Edit `config.py`
3. **Try different periods** - Bear vs Bull markets
4. **Compare strategies** - Add your own ideas
5. **Paper trade** - Test with virtual money
6. **Go live** - Use Zerodha Kite API

---

**Ready? Let's go!**

```bash
streamlit run dashboard/streamlit_app.py
```

---

*Last Updated: October 2025*  
*Version: 1.0.0*  
*Status: Production Ready ✅*
