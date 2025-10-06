"""
Zerodha Kite Connect Integration for NSE Data

Provides real-time and historical market data using Zerodha Kite API.
Requires Kite Connect subscription (₹2000/month).

Setup:
1. Create Kite Connect app: https://kite.trade/
2. Get API key and secret
3. Set environment variables:
   - KITE_API_KEY
   - KITE_API_SECRET
   - KITE_ACCESS_TOKEN (generated via login flow)

Features:
- Real-time OHLCV data
- Historical data (up to years)
- Tick-by-tick data
- Market depth
- Order placement (optional)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

from data.data_storage import DataStorage
from config import NSESectors
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Load environment variables
load_dotenv()

try:
    from kiteconnect import KiteConnect
    KITE_AVAILABLE = True
except ImportError:
    KITE_AVAILABLE = False
    logger.warning("kiteconnect library not installed. Install with: pip install kiteconnect")


class ZerodhaDataDownloader:
    """
    Download NSE data using Zerodha Kite Connect API
    """
    
    def __init__(self, api_key: str = None, access_token: str = None):
        """
        Initialize Kite Connect
        
        Args:
            api_key: Kite API key (or set KITE_API_KEY env variable)
            access_token: Access token (or set KITE_ACCESS_TOKEN env variable)
        """
        if not KITE_AVAILABLE:
            raise ImportError("kiteconnect not installed. Run: pip install kiteconnect")
        
        self.api_key = api_key or os.getenv('KITE_API_KEY')
        self.access_token = access_token or os.getenv('KITE_ACCESS_TOKEN')
        
        if not self.api_key:
            raise ValueError("API key required. Set KITE_API_KEY environment variable or pass api_key")
        
        # Initialize Kite Connect
        self.kite = KiteConnect(api_key=self.api_key)
        
        if self.access_token:
            self.kite.set_access_token(self.access_token)
            logger.info("Kite Connect initialized with access token")
        else:
            logger.warning("No access token. You'll need to complete login flow.")
        
        self.storage = DataStorage()
        
        self.stats = {
            'sectors': 0,
            'stocks': 0,
            'price_records': 0,
            'failed': []
        }
    
    def generate_login_url(self) -> str:
        """
        Generate login URL for obtaining access token
        
        Returns:
            Login URL
        """
        login_url = self.kite.login_url()
        print("\n" + "="*80)
        print("KITE CONNECT LOGIN")
        print("="*80)
        print(f"\n1. Open this URL in browser:\n{login_url}\n")
        print("2. Login with your Zerodha credentials")
        print("3. Copy the 'request_token' from redirected URL")
        print("4. Use set_access_token() method with request_token")
        print("\n" + "="*80 + "\n")
        
        return login_url
    
    def set_access_token_from_request(self, request_token: str, api_secret: str = None):
        """
        Generate and set access token from request token
        
        Args:
            request_token: Token from login redirect
            api_secret: API secret (or set KITE_API_SECRET env variable)
        """
        api_secret = api_secret or os.getenv('KITE_API_SECRET')
        
        if not api_secret:
            raise ValueError("API secret required")
        
        # Generate session
        data = self.kite.generate_session(request_token, api_secret=api_secret)
        self.access_token = data["access_token"]
        self.kite.set_access_token(self.access_token)
        
        logger.info("Access token generated successfully")
        print(f"\nAccess Token: {self.access_token}")
        print("Save this token as KITE_ACCESS_TOKEN environment variable")
        
        return self.access_token
    
    def get_nse_instruments(self) -> pd.DataFrame:
        """
        Get all NSE instruments
        
        Returns:
            DataFrame with all instruments
        """
        instruments = self.kite.instruments("NSE")
        df = pd.DataFrame(instruments)
        
        logger.info(f"Found {len(df)} NSE instruments")
        
        return df
    
    def get_nifty_stocks(self) -> Dict[str, List[Dict]]:
        """
        Get NIFTY stocks organized by sector
        
        Returns:
            Dict mapping sector to list of instrument dicts
        """
        # Get all instruments
        instruments = self.get_nse_instruments()
        
        # Filter equity stocks only
        equity_stocks = instruments[instruments['segment'] == 'NSE']
        
        # Pre-defined sector mappings
        sector_stocks = {
            'Nifty IT': ['TCS', 'INFY', 'HCLTECH', 'WIPRO', 'TECHM', 'LTIM', 'PERSISTENT', 'COFORGE'],
            'Nifty Bank': ['HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'SBIN', 'AXISBANK', 'INDUSINDBK'],
            'Nifty Auto': ['MARUTI', 'TATAMOTORS', 'M&M', 'BAJAJ-AUTO', 'HEROMOTOCO', 'EICHERMOT'],
            'Nifty Pharma': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'AUROPHARMA', 'LUPIN'],
            'Nifty FMCG': ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR', 'MARICO'],
            'Nifty Metal': ['TATASTEEL', 'HINDALCO', 'JSWSTEEL', 'COALINDIA', 'VEDL', 'JINDALSTEL'],
            'Nifty Energy': ['RELIANCE', 'ONGC', 'POWERGRID', 'NTPC', 'IOC', 'BPCL'],
            'Nifty Financial Services': ['HDFCBANK', 'ICICIBANK', 'BAJFINANCE', 'BAJAJFINSV', 'HDFCLIFE'],
            'Nifty Realty': ['DLF', 'GODREJPROP', 'OBEROIRLTY', 'PHOENIXLTD', 'PRESTIGE'],
            'Nifty Media': ['ZEEL', 'PVRINOX', 'SAREGAMA', 'NETWORK18'],
            'Nifty PSU Bank': ['SBIN', 'PNB', 'BANKBARODA', 'CANBK', 'UNIONBANK'],
            'Nifty Infrastructure': ['ADANIPORTS', 'GAIL', 'PFC', 'RECLTD', 'IRCTC'],
            'Nifty Commodities': ['TATASTEEL', 'HINDALCO', 'COALINDIA', 'ITC', 'UPL'],
            'Nifty Consumption': ['HINDUNILVR', 'ITC', 'MARUTI', 'TITAN', 'NESTLEIND'],
            'Nifty CPSE': ['ONGC', 'COALINDIA', 'IOC', 'GAIL', 'NTPC'],
            'Nifty MNC': ['NESTLEIND', 'HINDUNILVR', 'BOSCHLTD', 'SIEMENS', 'ABB'],
            'Nifty PSE': ['ONGC', 'COALINDIA', 'NTPC', 'POWERGRID', 'IOC']
        }
        
        # Map stocks to instrument tokens
        sector_instruments = {}
        
        for sector, symbols in sector_stocks.items():
            sector_instruments[sector] = []
            
            for symbol in symbols:
                # Find instrument
                instrument = equity_stocks[equity_stocks['tradingsymbol'] == symbol]
                
                if not instrument.empty:
                    sector_instruments[sector].append({
                        'symbol': symbol,
                        'instrument_token': instrument.iloc[0]['instrument_token'],
                        'exchange_token': instrument.iloc[0]['exchange_token'],
                        'name': instrument.iloc[0]['name']
                    })
        
        logger.info(f"Mapped {len(sector_instruments)} sectors")
        
        return sector_instruments
    
    def download_historical_data(self, instrument_token: int, symbol: str,
                                 from_date: datetime, to_date: datetime,
                                 interval: str = 'day') -> pd.DataFrame:
        """
        Download historical OHLCV data
        
        Args:
            instrument_token: Instrument token from Kite
            symbol: Stock symbol
            from_date: Start date
            to_date: End date
            interval: Candle interval (minute, day, etc.)
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Fetch historical data
            data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
            
            if not data:
                logger.warning(f"No data for {symbol}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Rename columns to match our format
            df = df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })
            
            logger.info(f"Downloaded {len(df)} records for {symbol}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error downloading {symbol}: {e}")
            return pd.DataFrame()
    
    def download_all_stocks(self, years: int = 4):
        """
        Download all stocks with historical data
        
        Args:
            years: Years of historical data
        """
        print("\n" + "="*80)
        print("DOWNLOADING NSE DATA VIA ZERODHA KITE")
        print("="*80)
        
        # Date range
        to_date = datetime.now()
        from_date = to_date - timedelta(days=years * 365)
        
        print(f"Period: {from_date.date()} to {to_date.date()}")
        print("="*80 + "\n")
        
        # Initialize database
        self.storage.bulk_load_sectors(NSESectors.SECTOR_TICKERS)
        
        # Get stock mappings
        print("Step 1: Getting instrument mappings...")
        sector_instruments = self.get_nifty_stocks()
        
        # Count total stocks
        total_stocks = sum(len(stocks) for stocks in sector_instruments.values())
        print(f"Found {total_stocks} stocks across {len(sector_instruments)} sectors\n")
        
        # Download each stock
        print("Step 2: Downloading stock data...")
        print("-"*80)
        
        downloaded = 0
        
        for sector, instruments in sector_instruments.items():
            print(f"\n{sector}:")
            
            for inst in instruments:
                symbol = inst['symbol']
                token = inst['instrument_token']
                
                print(f"  [{downloaded+1}/{total_stocks}] {symbol:<15}", end=" ")
                
                # Download data
                df = self.download_historical_data(token, symbol, from_date, to_date)
                
                if not df.empty:
                    # Add to database
                    stock_obj = self.storage.get_stock_by_symbol(symbol)
                    if not stock_obj:
                        self.storage.add_stock(symbol, sector_name=sector)
                    
                    self.storage.save_stock_prices(symbol, df)
                    
                    self.stats['stocks'] += 1
                    self.stats['price_records'] += len(df)
                    
                    print(f"✅ {len(df)} records")
                else:
                    print("❌")
                    self.stats['failed'].append(symbol)
                
                downloaded += 1
                
                # Rate limiting (Kite has limits)
                time.sleep(0.5)
                
                if downloaded % 10 == 0:
                    print(f"\n  Progress: {downloaded}/{total_stocks} ({downloaded/total_stocks*100:.1f}%)")
                    time.sleep(2)
        
        # Summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate download summary"""
        summary = self.storage.get_data_summary()
        
        print("\n" + "="*80)
        print("DOWNLOAD COMPLETE!")
        print("="*80)
        print(f"\nSTATISTICS:")
        print(f"  Stocks downloaded: {self.stats['stocks']}")
        print(f"  Price records: {self.stats['price_records']:,}")
        print(f"  Failed: {len(self.stats['failed'])}")
        
        print(f"\nDATABASE:")
        print(f"  Total stocks: {summary['stocks']}")
        print(f"  Stock prices: {summary['stock_price_records']:,}")
        print(f"  Fundamentals: {summary['fundamental_records']}")
        print(f"  Latest date: {summary['latest_price_date']}")
        print(f"\nLocation: {self.storage.db_path}")
        print("="*80 + "\n")
        
        self.storage.close()


def setup_kite_connect():
    """Interactive setup for Kite Connect"""
    print("\n" + "="*80)
    print("ZERODHA KITE CONNECT SETUP")
    print("="*80)
    print("\nYou need:")
    print("1. Kite Connect subscription (₹2000/month)")
    print("2. API Key and Secret from https://kite.trade/")
    print("3. Zerodha trading account")
    print("\n" + "="*80)
    
    # Get credentials
    api_key = input("\nEnter your API Key: ").strip()
    
    if not api_key:
        print("Setup cancelled")
        return
    
    # Create .env file
    env_path = Path(__file__).parent.parent / '.env'
    
    with open(env_path, 'a') as f:
        f.write(f"\n# Zerodha Kite Connect\n")
        f.write(f"KITE_API_KEY={api_key}\n")
    
    print(f"\n✅ API Key saved to {env_path}")
    
    # Initialize and get login URL
    downloader = ZerodhaDataDownloader(api_key=api_key)
    login_url = downloader.generate_login_url()
    
    print("\nAfter logging in, run:")
    print("  python data/zerodha_kite.py --request-token YOUR_TOKEN")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Zerodha Kite data downloader')
    parser.add_argument('--setup', action='store_true', help='Setup Kite Connect')
    parser.add_argument('--request-token', type=str, help='Request token from login')
    parser.add_argument('--download', action='store_true', help='Download all data')
    parser.add_argument('--years', type=int, default=4, help='Years of data')
    parser.add_argument('--check', action='store_true', help='Check database')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_kite_connect()
    
    elif args.request_token:
        api_key = os.getenv('KITE_API_KEY')
        api_secret = input("Enter API Secret: ").strip()
        
        if not api_key or not api_secret:
            print("API credentials missing")
            return
        
        downloader = ZerodhaDataDownloader(api_key=api_key)
        access_token = downloader.set_access_token_from_request(args.request_token, api_secret)
        
        # Save to .env
        env_path = Path(__file__).parent.parent / '.env'
        with open(env_path, 'a') as f:
            f.write(f"KITE_ACCESS_TOKEN={access_token}\n")
        
        print(f"\n✅ Access token saved to {env_path}")
        print("\nNow run: python data/zerodha_kite.py --download")
    
    elif args.download:
        if not KITE_AVAILABLE:
            print("kiteconnect not installed. Run: pip install kiteconnect")
            return
        
        downloader = ZerodhaDataDownloader()
        downloader.download_all_stocks(years=args.years)
    
    elif args.check:
        storage = DataStorage()
        summary = storage.get_data_summary()
        print(f"\nDatabase: {storage.db_path}")
        print(f"Stocks: {summary['stocks']}")
        print(f"Prices: {summary['stock_price_records']:,}")
        print(f"Latest: {summary['latest_price_date']}\n")
        storage.close()
    
    else:
        print("\nZerodha Kite Connect Data Downloader")
        print("\nUsage:")
        print("  python data/zerodha_kite.py --setup          # Initial setup")
        print("  python data/zerodha_kite.py --download       # Download data")
        print("  python data/zerodha_kite.py --check          # Check database")
        print("\nNote: Requires Kite Connect subscription (₹2000/month)")
        print("Sign up: https://kite.trade/\n")


if __name__ == "__main__":
    main()
