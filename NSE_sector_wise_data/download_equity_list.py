import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("Attempting to download EQUITY_L.csv from NSE...")
print("=" * 60)

# Try multiple methods
methods = [
    {
        'name': 'Method 1: Direct NSE (with SSL)',
        'url': 'https://www1.nseindia.com/content/equities/EQUITY_L.csv',
        'verify': True
    },
    {
        'name': 'Method 2: Direct NSE (without SSL)',
        'url': 'https://www1.nseindia.com/content/equities/EQUITY_L.csv',
        'verify': False
    },
    {
        'name': 'Method 3: Archives NSE',
        'url': 'https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv',
        'verify': False
    },
    {
        'name': 'Method 4: Alternative endpoint',
        'url': 'https://www.nseindia.com/api/equity-stockIndices?csv=true&index=SECURITIES%20IN%20F%26O',
        'verify': False
    }
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

success = False

for method in methods:
    print(f"\n{method['name']}...")
    print(f"URL: {method['url']}")
    
    try:
        response = requests.get(
            method['url'], 
            headers=headers, 
            verify=method['verify'],
            timeout=30
        )
        
        if response.status_code == 200:
            # Check if we got CSV data
            content = response.content.decode('utf-8', errors='ignore')
            
            if 'SYMBOL' in content or 'Symbol' in content:
                with open("EQUITY_L.csv", "w", encoding='utf-8') as f:
                    f.write(content)
                
                # Count lines
                lines = content.strip().split('\n')
                print(f"✓ Success! Downloaded {len(lines)} lines")
                print(f"✓ File saved as: EQUITY_L.csv")
                success = True
                break
            else:
                print(f"✗ Got response but not CSV format")
        else:
            print(f"✗ HTTP {response.status_code}")
            
    except requests.exceptions.SSLError as e:
        print(f"✗ SSL Error: {str(e)[:100]}...")
    except requests.exceptions.Timeout:
        print(f"✗ Timeout")
    except Exception as e:
        print(f"✗ Error: {str(e)[:100]}...")

if not success:
    print("\n" + "=" * 60)
    print("All methods failed. Using fallback option...")
    print("=" * 60)
    
    # Create a minimal sample file with major stocks for testing
    sample_data = """SYMBOL,NAME OF COMPANY, SERIES, DATE OF LISTING, PAID UP VALUE, MARKET LOT, ISIN NUMBER, FACE VALUE
TCS,Tata Consultancy Services Limited,EQ,25-Aug-04,1,1,INE467B01029,1
INFY,Infosys Limited,EQ,08-Feb-95,5,1,INE009A01021,5
HDFCBANK,HDFC Bank Limited,EQ,08-Nov-95,1,1,INE040A01034,1
RELIANCE,Reliance Industries Limited,EQ,29-Nov-95,10,1,INE002A01018,10
ICICIBANK,ICICI Bank Limited,EQ,17-Sep-97,2,1,INE090A01021,2
SBIN,State Bank of India,EQ,01-Mar-95,1,1,INE062A01020,1
WIPRO,Wipro Limited,EQ,08-Nov-95,2,1,INE075A01022,2
BHARTIARTL,Bharti Airtel Limited,EQ,15-Feb-02,5,1,INE397D01024,5
AXISBANK,Axis Bank Limited,EQ,16-Nov-98,2,1,INE238A01034,2
KOTAKBANK,Kotak Mahindra Bank Limited,EQ,20-Dec-95,5,1,INE237A01028,5"""
    
    with open("EQUITY_L.csv", "w") as f:
        f.write(sample_data)
    
    print("\n✓ Created sample EQUITY_L.csv with 10 major stocks for testing")
    print("✓ You can replace this with the full file manually later")
    
    print("\nManual download option:")
    print("1. Visit: https://www.nseindia.com/market-data/securities-available-for-trading")
    print("2. Download 'Securities available for trading' CSV")
    print("3. Save as EQUITY_L.csv in this folder")

print("\n" + "=" * 60)
print("Next step: python sector_mapper.py")
print("=" * 60)
