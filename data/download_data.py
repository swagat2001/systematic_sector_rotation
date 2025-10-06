"""
Simple Data Downloader for NSE Stocks

Downloads data directly using yfinance with .NS suffix
Works around NSE API issues by using Yahoo Finance India
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from data.data_storage import DataStorage
from config import NSESectors
from utils.logger import setup_logger

logger = setup_logger(__name__)


def download_nifty50_stocks():
    """Download NIFTY 50 stocks data"""
    
    # NIFTY 50 constituents (sample - you can add more)
    nifty50_stocks = [
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR',
        'ICICIBANK', 'KOTAKBANK', 'SBIN', 'BHARTIARTL', 'BAJFINANCE',
        'ITC', 'ASIANPAINT', 'AXISBANK', 'LT', 'DMART',
        'SUNPHARMA', 'TITAN', 'ULTRACEMCO', 'NESTLEIND', 'MARUTI',
        'WIPRO', 'HCLTECH', 'TECHM', 'POWERGRID', 'NTPC',
        'BAJAJFINSV', 'ONGC', 'TATASTEEL', 'TATAMOTORS', 'ADANIPORTS'
    ]
    
    storage = DataStorage()
    
    # Add sectors first
    storage.bulk_load_sectors(NSESectors.SECTOR_TICKERS)
    
    print(f"\n{'='*60}")
    print(f"Downloading NIFTY 50 Stocks Data")
    print(f"{'='*60}\n")
    
    successful = 0
    failed = 0
    
    # Date range (last 4 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=4*365)
    
    for i, symbol in enumerate(nifty50_stocks, 1):
        try:
            ticker = f"{symbol}.NS"  # Add .NS for NSE
            print(f"[{i}/{len(nifty50_stocks)}] Downloading {symbol}...", end=" ")
            
            # Download data
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)
            
            if df.empty:
                print(f"❌ No data")
                failed += 1
                continue
            
            # Get basic info
            info = stock.info
            market_cap = info.get('marketCap', 0)
            
            # Add stock to database
            stock_obj = storage.get_stock_by_symbol(symbol)
            if not stock_obj:
                storage.add_stock(symbol, sector_name='Nifty 50', market_cap=market_cap)
            
            # Save prices
            storage.save_stock_prices(symbol, df)
            
            print(f"✅ {len(df)} records")
            successful += 1
            
        except Exception as e:
            print(f"❌ Error: {e}")
            failed += 1
    
    storage.close()
    
    print(f"\n{'='*60}")
    print(f"Download Complete!")
    print(f"{'='*60}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"\nDatabase location: {storage.db_path}")


def download_sector_indices():
    """Download sector index data"""
    
    # Sector index tickers (corrected)
    sector_tickers = {
        'Nifty IT': '^CNXIT',
        'Nifty Bank': '^NSEBANK', 
        'Nifty Auto': '^CNXAUTO',
        'Nifty Pharma': '^CNXPHARMA',
        'Nifty FMCG': '^CNXFMCG',
        'Nifty Metal': '^CNXMETAL',
        'Nifty Energy': '^CNXENERGY',
        'Nifty Realty': '^CNXREALTY'
    }
    
    storage = DataStorage()
    storage.bulk_load_sectors(NSESectors.SECTOR_TICKERS)
    
    print(f"\n{'='*60}")
    print(f"Downloading Sector Indices")
    print(f"{'='*60}\n")
    
    successful = 0
    failed = 0
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=4*365)
    
    for sector_name, ticker in sector_tickers.items():
        try:
            print(f"Downloading {sector_name}...", end=" ")
            
            # Download
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if df.empty:
                print(f"❌ No data")
                failed += 1
                continue
            
            # Save
            storage.save_sector_prices(sector_name, df)
            
            print(f"✅ {len(df)} records")
            successful += 1
            
        except Exception as e:
            print(f"❌ Error: {e}")
            failed += 1
    
    storage.close()
    
    print(f"\n{'='*60}")
    print(f"Sector Download Complete!")
    print(f"{'='*60}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")


def check_database():
    """Check what's in the database"""
    
    storage = DataStorage()
    summary = storage.get_data_summary()
    
    print(f"\n{'='*60}")
    print(f"DATABASE CONTENTS")
    print(f"{'='*60}")
    print(f"Location: {storage.db_path}")
    print(f"\nSectors: {summary.get('sectors', 0)}")
    print(f"Stocks: {summary.get('stocks', 0)}")
    print(f"Stock Price Records: {summary.get('stock_price_records', 0):,}")
    print(f"Sector Price Records: {summary.get('sector_price_records', 0):,}")
    print(f"Fundamental Records: {summary.get('fundamental_records', 0)}")
    print(f"Latest Price Date: {summary.get('latest_price_date', 'N/A')}")
    print(f"{'='*60}\n")
    
    storage.close()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download market data')
    parser.add_argument('--stocks', action='store_true', help='Download NIFTY 50 stocks')
    parser.add_argument('--sectors', action='store_true', help='Download sector indices')
    parser.add_argument('--all', action='store_true', help='Download everything')
    parser.add_argument('--check', action='store_true', help='Check database contents')
    
    args = parser.parse_args()
    
    if args.check:
        check_database()
    elif args.all:
        download_sector_indices()
        download_nifty50_stocks()
        check_database()
    elif args.stocks:
        download_nifty50_stocks()
        check_database()
    elif args.sectors:
        download_sector_indices()
        check_database()
    else:
        print("Usage:")
        print("  python data/download_data.py --stocks    # Download NIFTY 50 stocks")
        print("  python data/download_data.py --sectors   # Download sector indices")
        print("  python data/download_data.py --all       # Download everything")
        print("  python data/download_data.py --check     # Check database")


if __name__ == "__main__":
    main()
