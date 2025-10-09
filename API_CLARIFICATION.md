# CLARIFICATION: What "Required" Means

## Summary

**"Required" fields are AUTOMATICALLY FETCHED from your API - NO manual input!**

---

## How It Works

### Step 1: You Provide API Details

Tell us:
- API URL: `https://your-api.com/fundamentals`
- API Key: `your-api-key-here`
- Field names: What your API calls each metric

### Step 2: We Write Code to Call Your API

```python
def get_fundamental_data(self, symbol):
    # We write this code
    response = requests.get(
        f"{self.api_url}/fundamentals/{symbol}",
        headers={'Authorization': f'Bearer {self.api_key}'}
    )
    
    data = response.json()  # Your API's response
    
    # Map your field names → our system
    return {
        'roe': data['YOUR_ROE_FIELD_NAME'],
        'roce': data['YOUR_ROCE_FIELD_NAME'],
        'eps_cagr': data['YOUR_EPS_CAGR_FIELD_NAME'],
        # etc.
    }
```

### Step 3: System Uses It Automatically

```python
# During backtest, for each stock:
fundamentals = provider.get_fundamental_data('INFY')
# Returns: {'roe': 25.3, 'roce': 28.1, ...}

# Strategy uses these values
score = calculate_score(fundamentals)
```

**All automatic! No manual input needed anywhere!**

---

## Real Example

### Your API Response

When we call `GET https://your-api.com/fundamentals/INFY`:

```json
{
  "ticker": "INFY",
  "date": "2024-01-15",
  "financials": {
    "return_on_equity": 25.3,
    "return_on_capital_employed": 28.1,
    "earnings_per_share_3y_cagr": 15.2,
    "price_earnings_ratio": 22.5,
    "price_book_ratio": 4.2,
    "debt_equity": 0.15,
    "current": 2.8,
    "market_cap_inr": 450000000000
  }
}
```

### We Map It

```python
def get_fundamental_data(self, symbol):
    response = requests.get(f"{self.api_url}/fundamentals/{symbol}")
    data = response.json()
    
    # Extract from nested structure
    fin = data['financials']
    
    return {
        'roe': fin['return_on_equity'],
        'roce': fin['return_on_capital_employed'],
        'eps_cagr': fin['earnings_per_share_3y_cagr'],
        'pe_ratio': fin['price_earnings_ratio'],
        'pb_ratio': fin['price_book_ratio'],
        'debt_to_equity': fin['debt_equity'],
        'current_ratio': fin['current'],
        'market_cap': fin['market_cap_inr'],
    }
```

### Result

System gets: `{'roe': 25.3, 'roce': 28.1, 'eps_cagr': 15.2, ...}`

**No manual input! All from your API!**

---

## What If API Doesn't Have a Field?

### Option 1: Use Default Value

```python
return {
    'roe': data.get('return_on_equity', 15.0),  # If missing, use 15.0
    'roce': data.get('roce', 18.0),              # If missing, use 18.0
}
```

### Option 2: Skip the Stock

```python
if 'return_on_equity' not in data:
    logger.warning(f"No ROE for {symbol}, skipping")
    return None  # Stock won't be selected
```

### Option 3: Calculate It

```python
# If your API has net_income and equity, calculate ROE
if 'roe' not in data:
    roe = (data['net_income'] / data['shareholders_equity']) * 100
    return {'roe': roe, ...}
```

---

## Required vs Optional

### Required (8 fields)
These are **essential** for the strategy:
- ✅ ROE - Used in fundamental scoring
- ✅ ROCE - Used in fundamental scoring  
- ✅ EPS CAGR - Used in fundamental scoring
- ✅ PE Ratio - Used in valuation
- ✅ PB Ratio - Used in valuation
- ✅ Debt/Equity - Used in financial health
- ✅ Current Ratio - Used in liquidity
- ✅ Market Cap - Used in filtering

**If your API has these 8, the system works perfectly!**

### Optional (Nice to Have)
These **enhance** the strategy if available:
- ○ Revenue Growth
- ○ Profit Margin
- ○ Dividend Yield
- ○ Book Value
- ○ Operating Margin

**If your API has extras, we can use them for better scoring!**

---

## Checklist for Manager

- [ ] I have an API that returns fundamental data
- [ ] API requires authentication (I have the key)
- [ ] API returns at least the 8 required fields
- [ ] I know what my API calls each field (field names)
- [ ] I can provide a sample API response for 2-3 stocks

**Once you confirm these, we'll integrate in 1-2 hours!**

---

## Common Questions

**Q: Do I need to enter ROE, ROCE manually for each stock?**
A: No! Your API provides them automatically.

**Q: Where do the values come from?**
A: Your API calls your database/service and returns them.

**Q: What if I don't have an API?**
A: You can provide a CSV file, or we can query your database directly.

**Q: How often is data fetched?**
A: Once per backtest run (bulk fetch for efficiency). Can add caching if needed.

**Q: What if API is slow?**
A: We'll implement caching and bulk requests to optimize.

**Q: What if some stocks don't have data?**
A: System skips them or uses default values - no crashes.

---

## Bottom Line

**Everything is AUTOMATIC:**
1. We call your API
2. API returns data
3. We map field names
4. Strategy uses values
5. Stocks are scored
6. Best stocks selected

**Zero manual input. Fully automated. Just provide API details!**

---

**Need help? See MANAGER_API_INTEGRATION_GUIDE.md for step-by-step instructions.**
