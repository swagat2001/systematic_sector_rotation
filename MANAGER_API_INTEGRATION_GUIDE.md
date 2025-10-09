"""
MANAGER'S GUIDE: HOW TO INTEGRATE YOUR FUNDAMENTAL DATA API
============================================================

Dear Manager,

Currently, the system uses SYNTHETIC (random) fundamental data for:
- ROE (Return on Equity)
- ROCE (Return on Capital Employed)
- EPS CAGR (Earnings Per Share Growth Rate)
- PE Ratio, PB Ratio, Debt/Equity, Current Ratio, etc.

This guide explains how to plug in YOUR API to provide REAL fundamental data.

===============================================================================
STEP 1: UNDERSTAND THE ARCHITECTURE
===============================================================================

The system is now FULLY DYNAMIC and accepts data from any source through a
clean interface. No hardcoding needed!

Current Flow:
-------------
NSE Data Bridge → Fundamental Provider → Your API → Real Data

Files Involved:
--------------
1. data/fundamental_data_provider.py  ← Interface definition
2. data/nse_data_bridge.py           ← Uses the provider
3. config.py                         ← Configuration

===============================================================================
STEP 2: IMPLEMENT YOUR API PROVIDER
===============================================================================

Option A: Modify Existing Template (RECOMMENDED)
------------------------------------------------

File: data/fundamental_data_provider.py
Class: ManagerAPIFundamentalProvider

Find the class starting at line ~100 and fill in these methods:

def get_fundamental_data(self, symbol: str, as_of_date: datetime = None):
    '''
    YOUR CODE HERE:
    
    Example using requests library:
    
    import requests
    
    response = requests.get(
        f"{self.api_url}/fundamentals/{symbol}",
        headers={'Authorization': f'Bearer {self.api_key}'},
        params={'date': as_of_date.strftime('%Y-%m-%d') if as_of_date else None}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # Map your API response to our required format
        return {
            'roe': data['return_on_equity'],              # Required
            'roce': data['return_on_capital_employed'],   # Required
            'eps_cagr': data['eps_3year_cagr'],          # Required
            'pe_ratio': data['pe_ratio'],                # Required
            'pb_ratio': data['price_to_book'],           # Required
            'debt_to_equity': data['debt_equity_ratio'], # Required
            'current_ratio': data['current_ratio'],      # Required
            'market_cap': data['market_capitalization'], # Required
            
            # Optional but recommended:
            'revenue_growth': data.get('revenue_growth'),
            'profit_margin': data.get('net_profit_margin'),
            'dividend_yield': data.get('dividend_yield'),
        }
    else:
        raise Exception(f"API Error {response.status_code}: {response.text}")
    '''

def get_bulk_fundamental_data(self, symbols: List[str], as_of_date: datetime = None):
    '''
    If your API supports batch requests (recommended for performance):
    
    response = requests.post(
        f"{self.api_url}/fundamentals/bulk",
        headers={'Authorization': f'Bearer {self.api_key}'},
        json={'symbols': symbols, 'date': as_of_date.strftime('%Y-%m-%d')}
    )
    
    return {
        symbol: self._map_api_response_to_format(data)
        for symbol, data in response.json().items()
    }
    
    Otherwise, just loop through individual calls:
    
    return {
        symbol: self.get_fundamental_data(symbol, as_of_date)
        for symbol in symbols
    }
    '''

===============================================================================
STEP 3: CONFIGURE THE SYSTEM
===============================================================================

File: config.py

Find the FUNDAMENTAL_PROVIDER section and update:

FUNDAMENTAL_PROVIDER = {
    'type': 'manager_api',  # Change from 'default' to 'manager_api'
    
    # Add your API credentials:
    'api_key': 'YOUR_API_KEY_HERE',         # Your actual API key
    'api_url': 'https://your-api.com/v1',   # Your API base URL
    'timeout': 30,                           # Request timeout in seconds
    'retry_attempts': 3,                     # Number of retries on failure
}

===============================================================================
STEP 4: API RESPONSE FORMAT
===============================================================================

⚠️ IMPORTANT CLARIFICATION:

"Required" means these fields MUST BE RETURNED BY YOUR API automatically.
They are NOT manual input! Your API should fetch them from your database
and return them in the JSON response.

Your API should return data in this format (JSON):

Single Stock Request:
--------------------
GET /fundamentals/{symbol}?date=2024-01-15

Response:
{
    "symbol": "INFY",
    "date": "2024-01-15",
    "return_on_equity": 25.3,              # ROE in %
    "return_on_capital_employed": 28.1,    # ROCE in %
    "eps_3year_cagr": 15.2,               # EPS CAGR in %
    "pe_ratio": 22.5,
    "price_to_book": 4.2,
    "debt_equity_ratio": 0.15,
    "current_ratio": 2.8,
    "market_capitalization": 450000000000,  # Market cap in ₹
    
    # Optional fields:
    "revenue_growth": 18.5,
    "net_profit_margin": 22.1,
    "dividend_yield": 1.8,
    "earnings_per_share": 45.2,
    "book_value_per_share": 120.5
}

Bulk Request (if supported):
---------------------------
POST /fundamentals/bulk

Request Body:
{
    "symbols": ["INFY", "TCS", "WIPRO"],
    "date": "2024-01-15"
}

Response:
{
    "INFY": { ... },  # Same format as single stock
    "TCS": { ... },
    "WIPRO": { ... }
}

===============================================================================
STEP 5: AUTHENTICATION
===============================================================================

Common authentication methods we support:

1. Bearer Token (Most Common):
   Header: Authorization: Bearer YOUR_API_KEY

2. API Key Header:
   Header: X-API-Key: YOUR_API_KEY

3. Basic Auth:
   Header: Authorization: Basic base64(username:password)

Implement the authentication in your get_fundamental_data() method.

===============================================================================
STEP 6: ERROR HANDLING
===============================================================================

Your implementation should handle:

1. Network errors (timeout, connection failed)
2. API rate limits (HTTP 429)
3. Missing data (symbol not found)
4. Invalid dates
5. Authentication failures

Example with retry logic:

import requests
from time import sleep

def get_fundamental_data(self, symbol, as_of_date=None):
    for attempt in range(self.retry_attempts):
        try:
            response = requests.get(
                f"{self.api_url}/fundamentals/{symbol}",
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return self._parse_response(response.json())
            
            elif response.status_code == 429:  # Rate limit
                sleep(2 ** attempt)  # Exponential backoff
                continue
            
            elif response.status_code == 404:  # Not found
                logger.warning(f"No data for {symbol}")
                return {}  # Return empty dict (will use defaults)
            
            else:
                raise Exception(f"API Error {response.status_code}")
        
        except requests.Timeout:
            if attempt < self.retry_attempts - 1:
                sleep(1)
                continue
            else:
                logger.error(f"Timeout fetching {symbol}")
                return {}
        
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return {}
    
    return {}

===============================================================================
STEP 7: TESTING YOUR IMPLEMENTATION
===============================================================================

After implementing your API provider, test it:

1. Test with a single stock:
   
   python -c "
   from data.fundamental_data_provider import get_fundamental_provider
   provider = get_fundamental_provider(
       'manager_api',
       api_key='YOUR_KEY',
       api_url='YOUR_URL'
   )
   data = provider.get_fundamental_data('INFY')
   print(data)
   "

2. Test with bulk fetch:
   
   python -c "
   from data.fundamental_data_provider import get_fundamental_provider
   provider = get_fundamental_provider('manager_api', api_key='...', api_url='...')
   data = provider.get_bulk_fundamental_data(['INFY', 'TCS', 'WIPRO'])
   print(data)
   "

3. Run the full system:
   
   streamlit run dashboard/streamlit_app.py

===============================================================================
STEP 8: ALTERNATIVE: CSV FILE PROVIDER
===============================================================================

If you don't have an API yet, you can provide a CSV file:

File: fundamentals.csv
--------------------
symbol,date,roe,roce,eps_cagr,pe_ratio,pb_ratio,debt_to_equity,current_ratio,market_cap
INFY,2024-01-15,25.3,28.1,15.2,22.5,4.2,0.15,2.8,450000000000
TCS,2024-01-15,42.1,45.2,18.5,28.3,8.1,0.08,3.2,1200000000000
WIPRO,2024-01-15,18.2,20.5,10.3,18.5,3.1,0.25,2.1,280000000000

Config:
-------
FUNDAMENTAL_PROVIDER = {
    'type': 'csv',
    'csv_path': 'path/to/fundamentals.csv'
}

We'll implement a CSV provider if you need it - just let us know!

===============================================================================
STEP 9: ALTERNATIVE: DATABASE PROVIDER
===============================================================================

If you have fundamental data in a database:

Config:
-------
FUNDAMENTAL_PROVIDER = {
    'type': 'database',
    'db_connection': 'postgresql://user:pass@host:5432/dbname',
    'table_name': 'fundamentals',
    'symbol_column': 'ticker',
    'date_column': 'as_of_date',
}

We'll implement a database provider if you need it!

===============================================================================
STEP 10: CHECKLIST FOR MANAGER
===============================================================================

Before going live with real fundamental data:

[ ] Decide on data source (API, CSV, or Database)
[ ] Provide API credentials (if using API)
[ ] Implement get_fundamental_data() method
[ ] Implement get_bulk_fundamental_data() method
[ ] Add error handling and retries
[ ] Test with sample symbols
[ ] Update config.py with correct settings
[ ] Run test backtest to verify data is flowing
[ ] Verify ROE, ROCE, EPS CAGR values look correct
[ ] Compare results with synthetic data baseline
[ ] Monitor logs for any API errors

===============================================================================
EXPECTED FIELDS FROM YOUR API
===============================================================================

REQUIRED (Must provide):
------------------------
✓ roe                - Return on Equity (%)
✓ roce               - Return on Capital Employed (%)
✓ eps_cagr           - EPS 3-year CAGR (%)
✓ pe_ratio           - Price to Earnings ratio
✓ pb_ratio           - Price to Book ratio
✓ debt_to_equity     - Debt to Equity ratio
✓ current_ratio      - Current ratio
✓ market_cap         - Market capitalization (₹)

OPTIONAL (Nice to have):
-----------------------
○ revenue_growth     - Revenue growth rate (%)
○ profit_margin      - Net profit margin (%)
○ dividend_yield     - Dividend yield (%)
○ book_value         - Book value per share (₹)
○ eps                - Earnings per share (₹)
○ revenue            - Total revenue (₹)
○ net_profit         - Net profit (₹)
○ operating_margin   - Operating margin (%)
○ asset_turnover     - Asset turnover ratio
○ interest_coverage  - Interest coverage ratio

===============================================================================
BENEFITS OF REAL FUNDAMENTAL DATA
===============================================================================

Once your API is integrated:

✓ More accurate stock scoring
✓ Better stock selection (real ROE/ROCE instead of random)
✓ Improved fundamental analysis
✓ More reliable backtest results
✓ Production-ready system
✓ Can confidently trade live

===============================================================================
PERFORMANCE CONSIDERATIONS
===============================================================================

For 1,500+ stocks, we recommend:

1. Bulk API endpoint (fetch 100+ stocks at once)
2. Caching (cache data for 1 day to reduce API calls)
3. Async requests (if you have many symbols)
4. Database (store fetched data locally)

We can help implement any of these optimizations!

===============================================================================
SUPPORT & NEXT STEPS
===============================================================================

What we need from you:
----------------------
1. API documentation (endpoint URLs, auth method, response format)
2. API credentials (key, secret, etc.)
3. Sample API responses for 2-3 stocks
4. Rate limits (requests per minute/hour)
5. Data update frequency (daily, weekly?)

What we'll do:
-------------
1. Implement the provider for your specific API
2. Add caching if needed
3. Add error handling and retries
4. Test thoroughly with your data
5. Verify results match expectations
6. Document any API-specific quirks

===============================================================================
CONTACT
===============================================================================

Questions about API integration?
- Review: data/fundamental_data_provider.py (example implementation)
- Test: python data/fundamental_data_provider.py (runs demo)
- Check logs: logs/ directory for any errors

Once you provide your API details, we'll have it integrated within hours!

===============================================================================
CURRENT STATUS
===============================================================================

✓ System architecture is ready (fully dynamic)
✓ Interface is defined (FundamentalDataProvider)
✓ Default provider works (synthetic data)
✓ NSE Data Bridge is updated (uses provider)
⏳ Manager's API provider needs implementation (waiting for API details)

The system is READY to accept real fundamental data - we just need your API!

===============================================================================
"""
