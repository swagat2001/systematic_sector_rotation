"""
Quick diagnostic script to test NSE connection
"""
import requests
from datetime import datetime, timedelta

def test_nse_connection():
    # Test URL from yesterday
    yesterday = datetime.now() - timedelta(days=1)
    y = yesterday.year
    m = f'{yesterday:%b}'.upper()
    d = f'{yesterday.day:02d}'
    url = f'https://nsearchives.nseindia.com/content/historical/EQUITIES/{y}/{m}/cm{d}{m}{y}bhav.csv.zip'
    
    print(f"Testing URL: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Test 1: With SSL verification
    print("\n1. Testing WITH SSL verification...")
    try:
        response = requests.get(url, headers=headers, timeout=30, verify=True)
        print(f"   ✓ Success! Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✓ Downloaded {len(response.content)} bytes")
    except requests.exceptions.SSLError as e:
        print(f"   ✗ SSL Error: {str(e)[:200]}")
    except Exception as e:
        print(f"   ✗ Error: {str(e)[:200]}")
    
    # Test 2: Without SSL verification
    print("\n2. Testing WITHOUT SSL verification...")
    try:
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        print(f"   ✓ Success! Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✓ Downloaded {len(response.content)} bytes")
    except Exception as e:
        print(f"   ✗ Error: {str(e)[:200]}")
    
    # Test 3: Check urllib3 version
    print("\n3. Package versions:")
    try:
        import urllib3
        print(f"   urllib3: {urllib3.__version__}")
    except:
        pass
    
    try:
        print(f"   requests: {requests.__version__}")
    except:
        pass
    
    # Test 4: Try a known working date
    print("\n4. Testing with a known working date (2024-01-02)...")
    test_url = "https://nsearchives.nseindia.com/content/historical/EQUITIES/2024/JAN/cm02JAN2024bhav.csv.zip"
    try:
        response = requests.get(test_url, headers=headers, timeout=30, verify=True)
        print(f"   ✓ Success! Status: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {str(e)[:200]}")

if __name__ == '__main__':
    test_nse_connection()
