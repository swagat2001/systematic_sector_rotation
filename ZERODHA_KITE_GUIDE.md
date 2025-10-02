# 🔌 ZERODHA KITE CONNECT INTEGRATION GUIDE

## Overview

Zerodha Kite Connect provides real-time NSE market data via official API.

**Cost:** ₹2,000/month  
**Data:** Real-time OHLCV, fundamentals, tick data  
**Coverage:** All NSE stocks (1800+)

---

## 🚀 QUICK START

### Step 1: Get Kite Connect Subscription

1. Visit: https://kite.trade/
2. Sign up using your Zerodha account
3. Subscribe to Kite Connect (₹2000/month)
4. Create a new app in Kite Connect dashboard
5. Get your **API Key** and **API Secret**

### Step 2: Install Dependencies

```bash
pip install kiteconnect python-dotenv
```

### Step 3: Setup Authentication

```bash
# Run interactive setup
python data/zerodha_kite.py --setup
```

This will:
- Ask for your API Key
- Generate login URL
- Save credentials to .env file

### Step 4: Complete Login Flow

1. Open the login URL in your browser
2. Login with Zerodha credentials
3. Copy the `request_token` from redirected URL
4. Run:

```bash
python data/zerodha_kite.py --request-token YOUR_REQUEST_TOKEN
```

Enter your API Secret when prompted.

### Step 5: Download Data

```bash
# Download 4 years of data for all stocks
python data/zerodha_kite.py --download

# Or specify years
python data/zerodha_kite.py --download --years 5
```

This will download:
- ✅ All NIFTY sectoral indices
- ✅ 150+ major stocks across 17 sectors
- ✅ Complete OHLCV data
- ✅ Saves to database automatically

---

## 📋 WHAT YOU'LL GET

### Data Coverage

| Category | Count | Data |
|----------|-------|------|
| Sectors | 17 | 4 years OHLCV |
| Stocks | 150+ | 4 years OHLCV |
| Price Records | 150,000+ | Daily candles |
| Real-time | Yes | Via websocket |

### Stock Coverage by Sector

- **Nifty IT**: 8 stocks (TCS, INFY, HCLTECH, etc.)
- **Nifty Bank**: 6 stocks (HDFCBANK, ICICIBANK, etc.)
- **Nifty Auto**: 6 stocks (MARUTI, TATAMOTORS, etc.)
- **Nifty Pharma**: 6 stocks (SUNPHARMA, DRREDDY, etc.)
- **Nifty FMCG**: 6 stocks (HINDUNILVR, ITC, etc.)
- **And 12 more sectors...**

---

## 🔐 AUTHENTICATION

### Environment Variables

Create a `.env` file in project root:

```
# Zerodha Kite Connect
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
KITE_ACCESS_TOKEN=your_access_token_here
```

**Security:** Never commit .env file to Git!

### Access Token

- **Valid for:** 24 hours
- **Renewal:** Login flow generates new token
- **Storage:** Saved in .env automatically

---

## 📊 USAGE EXAMPLES

### Check Database

```bash
python data/zerodha_kite.py --check
```

Output:
```
Database: /path/to/strategy.db
Stocks: 150
Prices: 150,000
Latest: 2025-10-02
```

### Download Specific Period

```python
from data.zerodha_kite import ZerodhaDataDownloader

downloader = ZerodhaDataDownloader()
downloader.download_all_stocks(years=3)
```

### Get Real-time Data

```python
# In your strategy
from data.zerodha_kite import ZerodhaDataDownloader

downloader = ZerodhaDataDownloader()

# Get latest price
instruments = downloader.get_nse_instruments()

# Download today's data
df = downloader.download_historical_data(
    instrument_token=258121,
    symbol='INFY',
    from_date=datetime.now() - timedelta(days=1),
    to_date=datetime.now(),
    interval='day'
)
```

---

## 💰 COSTS

### Kite Connect Pricing

| Plan | Cost | Features |
|------|------|----------|
| Monthly | ₹2,000 | Full API access |
| Yearly | Not available | - |

### What's Included

- ✅ Historical data (years)
- ✅ Real-time tick data
- ✅ Market depth
- ✅ Order placement
- ✅ Portfolio tracking
- ✅ Unlimited API calls

### What's NOT Included

- ❌ News data
- ❌ Corporate actions
- ❌ Fundamental ratios (limited)

---

## 🔄 ALTERNATIVE: FREE OPTIONS

If you don't want to pay ₹2000/month:

### Option 1: Use Synthetic Data (Current)

```bash
# Generate realistic synthetic data (FREE)
python data/load_production_data.py
```

**Pros:**
- ✅ Works immediately
- ✅ Realistic correlations
- ✅ Good for learning/testing

**Cons:**
- ❌ Not real market data
- ❌ Can't trade with it

### Option 2: Manual CSV Import

Download data manually from NSE:
1. Visit: https://www.nseindia.com/
2. Download historical data
3. Organize as CSV files
4. Import:

```bash
python data/load_your_data.py --folder data/your_data
```

### Option 3: Use yfinance (FREE but unreliable)

Already implemented in `scrape_nse_data.py` but:
- Often fails for NSE
- Rate limited
- Missing data issues

---

## 📈 AFTER DATA IS LOADED

Once you have real data:

### Run Backtest

```bash
streamlit run dashboard/streamlit_app.py
```

Then:
1. Go to "Backtest" page
2. Click "Run Backtest"
3. View real performance on real data!

### Run Strategy Live

```python
from strategy.portfolio_manager import PortfolioManager

manager = PortfolioManager()

# Rebalance with real data
result = manager.rebalance_portfolio(
    sector_prices,  # From Kite
    stocks_data,    # From Kite
    stocks_prices,  # From Kite
    benchmark_data
)
```

---

## ⚠️ IMPORTANT NOTES

### Rate Limits

Kite Connect has rate limits:
- **3 requests/second** per API endpoint
- Script includes automatic rate limiting
- Avoid parallel downloads

### Market Hours

- **Pre-open:** 9:00 AM - 9:15 AM IST
- **Trading:** 9:15 AM - 3:30 PM IST
- **After-market:** 3:40 PM - 4:00 PM IST

### Data Availability

- Historical data: Available immediately
- Real-time data: Only during market hours
- Weekend/holidays: No new data

---

## 🛠️ TROUBLESHOOTING

### "kiteconnect not installed"

```bash
pip install kiteconnect
```

### "Invalid API key"

- Check API key in Kite Console
- Ensure no extra spaces
- Regenerate if needed

### "Token expired"

Access tokens expire in 24 hours:

```bash
# Get new token
python data/zerodha_kite.py --setup
```

### "Rate limit exceeded"

- Wait 1-2 minutes
- Script will auto-resume
- Don't run multiple instances

### "No data returned"

- Check market hours
- Verify symbol exists
- Check NSE trading calendar

---

## 📞 SUPPORT

### Zerodha Support

- **Kite Connect Forum:** https://kite.trade/forum
- **Documentation:** https://kite.trade/docs/
- **Email:** kiteconnect@zerodha.com
- **Phone:** 080-4721-7777

### This Project

- Open GitHub issue
- Check documentation
- Review examples

---

## 🎯 RECOMMENDATION

**For Learning/Testing:**
→ Use synthetic data (FREE)

**For Production Trading:**
→ Use Kite Connect (₹2000/month)

**For Research:**
→ Manual CSV import (FREE but manual)

---

**Ready to download real data?**

```bash
python data/zerodha_kite.py --setup
```

