# API Integration - Visual Flow Diagram

## How Fundamental Data Flows (NO Manual Input!)

```
┌─────────────────────────────────────────────────────────────────┐
│                         MANAGER'S SYSTEM                         │
│                                                                  │
│  ┌────────────────┐                                             │
│  │   Database     │  Contains fundamental data:                 │
│  │                │  - ROE, ROCE, EPS CAGR                      │
│  │   PostgreSQL   │  - PE Ratio, PB Ratio                       │
│  │   MySQL        │  - Debt/Equity, Current Ratio               │
│  │   MongoDB      │  - Market Cap                               │
│  │   etc.         │  - For all 1,500+ stocks                    │
│  └───────┬────────┘                                             │
│          │                                                       │
│          ↓                                                       │
│  ┌────────────────┐                                             │
│  │  Manager's API │  HTTP Endpoint:                             │
│  │                │  GET /fundamentals/{symbol}                 │
│  │  Flask/FastAPI │                                             │
│  │  Django/Node   │  Returns JSON with all metrics              │
│  └───────┬────────┘                                             │
└──────────┼─────────────────────────────────────────────────────┘
           │
           │ HTTPS Request
           │ GET /fundamentals/INFY
           │ Headers: Authorization: Bearer API_KEY
           │
           ↓
┌─────────────────────────────────────────────────────────────────┐
│                      OUR TRADING SYSTEM                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  FundamentalDataProvider (Our Code)                        │ │
│  │                                                             │ │
│  │  def get_fundamental_data(symbol):                         │ │
│  │      # 1. Call Manager's API                               │ │
│  │      response = requests.get(                              │ │
│  │          f"{api_url}/fundamentals/{symbol}",              │ │
│  │          headers={'Authorization': f'Bearer {api_key}'}    │ │
│  │      )                                                      │ │
│  │                                                             │ │
│  │      # 2. Get JSON response                                │ │
│  │      data = response.json()                                │ │
│  │                                                             │ │
│  │      # 3. Map fields                                       │ │
│  │      return {                                              │ │
│  │          'roe': data['return_on_equity'],     ← AUTOMATIC │ │
│  │          'roce': data['roce'],                ← AUTOMATIC │ │
│  │          'eps_cagr': data['eps_3y_cagr'],    ← AUTOMATIC │ │
│  │          ...                                               │ │
│  │      }                                                      │ │
│  └──────────────────────┬──────────────────────────────────────┘ │
│                         │                                         │
│                         ↓                                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Stock Selection Strategy                                   │ │
│  │                                                             │ │
│  │  For each stock:                                           │ │
│  │    fundamentals = provider.get_fundamental_data(symbol)    │ │
│  │    score = calculate_score(fundamentals)                   │ │
│  │    ...                                                      │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Key Points

### ✅ Automatic (No Manual Input)
- Manager's API returns data
- Our code calls API
- Values flow automatically

### ❌ NOT Manual Input
- No one types ROE values
- No CSV files to update monthly
- No spreadsheets to maintain

### 🔄 Update Frequency
- API is called during backtest
- Frequency: Once per backtest run
- Can add caching if API has rate limits

---

## Example: Complete Flow for One Stock (INFY)

```
Step 1: Strategy Needs Data
├─> "I need fundamentals for INFY"
│
Step 2: Call Provider
├─> provider.get_fundamental_data('INFY')
│
Step 3: Provider Calls Manager's API
├─> GET https://api.manager.com/fundamentals/INFY
├─> Headers: Authorization: Bearer xyz123
│
Step 4: Manager's API Queries Database
├─> SELECT roe, roce, eps_cagr, ... FROM fundamentals WHERE symbol='INFY'
│
Step 5: Database Returns Data
├─> {roe: 25.3, roce: 28.1, eps_cagr: 15.2, ...}
│
Step 6: API Returns JSON
├─> HTTP 200 OK
├─> Content-Type: application/json
├─> {
│     "symbol": "INFY",
│     "return_on_equity": 25.3,
│     "return_on_capital_employed": 28.1,
│     "eps_3year_cagr": 15.2,
│     ...
│   }
│
Step 7: Our Code Maps Fields
├─> Extract values from JSON
├─> Convert field names to our format
├─> return {'roe': 25.3, 'roce': 28.1, 'eps_cagr': 15.2, ...}
│
Step 8: Strategy Uses Values
├─> Calculate fundamental score: 0.78
├─> Calculate composite score: 0.82
├─> Rank against other stocks
├─> Select for portfolio if in top 15
│
✓ Complete! All automatic!
```

---

## What Manager Needs to Do

### One-Time Setup (30 minutes)

1. **Provide API Endpoint**
   ```
   URL: https://your-api.company.com/v1
   ```

2. **Provide API Key**
   ```
   Key: abc-123-xyz-789
   Method: Bearer token in Authorization header
   ```

3. **Share Field Names**
   ```
   ROE is called: "return_on_equity"
   ROCE is called: "return_on_capital_employed"
   EPS CAGR is called: "eps_3year_cagr"
   ...
   ```

4. **Provide Sample Response**
   ```json
   Share actual API response for 2-3 stocks
   So we can see exact structure
   ```

### That's It!

We write the integration code (1-2 hours).
System calls API automatically forever.

---

## Cost/Performance

### API Calls
- **When:** During backtest only (not live)
- **Frequency:** Once per backtest run
- **Count:** 1,500-2,000 stocks (bulk or individual)
- **Total:** ~1,500 API calls per backtest

### Optimization Options
1. **Bulk API:** Fetch 100 stocks at once (15 calls instead of 1,500)
2. **Caching:** Cache results for 1 day (reduce repeated backtests)
3. **Database:** Store locally, sync daily (no API calls during backtest)

---

## Different API Types Supported

### REST API (Most Common)
```
GET https://api.manager.com/fundamentals/INFY
Headers: Authorization: Bearer TOKEN
Response: JSON
```

### GraphQL
```
POST https://api.manager.com/graphql
Body: {query: "{ fundamental(symbol: 'INFY') { roe roce } }"}
Response: JSON
```

### SOAP
```
XML request/response
We can handle this too
```

### Database Direct
```
No API? We can query your database directly
PostgreSQL, MySQL, MongoDB, etc.
```

### CSV/Excel Files
```
If you prefer file-based approach
We can read from shared folder
```

**We support ANY method - just tell us what you have!**

---

## Security

### API Key Storage
- Stored in `config.py` (local file)
- NOT committed to git
- Can use environment variables
- Can use encrypted vault

### Data Privacy
- API calls only from your server (if on-premise)
- No data stored permanently (unless you want caching)
- SSL/TLS encryption (HTTPS)

### Access Control
- API key can be read-only
- Can whitelist our IP address
- Can set rate limits

---

## Summary

```
┌─────────────────────────────────────────┐
│  Manager's API (Your System)            │
│  ↓                                       │
│  Returns: ROE, ROCE, EPS CAGR, etc.    │
│  ↓                                       │
│  Our Code (We Write)                    │
│  ↓                                       │
│  Maps: API response → Our format       │
│  ↓                                       │
│  Strategy (Automatic)                   │
│  ↓                                       │
│  Uses: Values to score stocks          │
└─────────────────────────────────────────┘

NO MANUAL INPUT ANYWHERE!
```

---

**Questions? See:**
- `MANAGER_API_INTEGRATION_GUIDE.md` - Full integration guide
- `API_CLARIFICATION.md` - This file
- `README.md` - Project overview
