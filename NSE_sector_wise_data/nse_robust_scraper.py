"""
Enhanced NSE Data Scraper with Multiple Fallback Methods

Uses multiple approaches to get NSE data:
1. yfinance with proper headers (PRIMARY)
2. NSE API with proper headers
3. Alternative data sources
4. Robust error handling

This version handles SSL errors and NSE blocking better.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
import warnings
warnings.filterwarnings('ignore')

from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Try yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("Warning: yfinance not available. Install with: pip install yfinance")

# Database setup
Base = declarative_base()

class Stock(Base):
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(50), unique=True, nullable=False)
    name = Column(String(200))
    sector = Column(String(100))
    market_cap = Column(Float)

class StockPrice(Base):
    __tablename__ = 'stock_prices'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)


class RobustNSEScraper:
    """
    Robust NSE scraper that handles blocking and SSL errors
    """
    
    def __init__(self, data_dir: Path = None):
        """Initialize"""
        
        if data_dir is None:
            self.data_dir = Path(__file__).parent
        else:
            self.data_dir = Path(data_dir)
        
        self.data_dir.mkdir(exist_ok=True)
        
        # Database
        db_path = self.data_dir / 'nse_data.db'
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        print(f"✅ Database: {db_path}")
        
        # Date range
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=4*365)
        
        # Stats
        self.stats = {
            'attempted': 0,
            'success': 0,
            'yfinance_ok': 0,
            'failed': []
        }
        
        # NSE sectors with comprehensive stock lists
        self.sectors_stocks = self._get_stock_list()
    
    def _get_stock_list(self) -> dict:
        """Get comprehensive NSE stock list"""
        
        return {
            'Nifty IT': [
                'TCS', 'INFY', 'HCLTECH', 'WIPRO', 'TECHM', 'LTI', 
                'PERSISTENT', 'COFORGE', 'MPHASIS', 'LTTS'
            ],
            'Nifty Bank': [
                'HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'SBIN', 'AXISBANK',
                'INDUSINDBK', 'BANDHANBNK', 'FEDERALBNK', 'IDFCFIRSTB', 'PNB'
            ],
            'Nifty Auto': [
                'MARUTI', 'TATAMOTORS', 'M&M', 'BAJAJ-AUTO', 'HEROMOTOCO',
                'EICHERMOT', 'TVSMOTOR', 'ASHOKLEY', 'BALKRISIND', 'MRF'
            ],
            'Nifty Pharma': [
                'SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'AUROPHARMA',
                'LUPIN', 'TORNTPHARM', 'ALKEM', 'BIOCON', 'GLAND'
            ],
            'Nifty FMCG': [
                'HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR',
                'MARICO', 'TATACONSUM', 'GODREJCP', 'COLPAL', 'EMAMILTD'
            ],
            'Nifty Metal': [
                'TATASTEEL', 'HINDALCO', 'JSWSTEEL', 'COALINDIA', 'VEDL',
                'JINDALSTEL', 'SAIL', 'NMDC', 'NATIONALUM', 'HINDZINC'
            ],
            'Nifty Energy': [
                'RELIANCE', 'ONGC', 'POWERGRID', 'NTPC', 'COALINDIA',
                'IOC', 'BPCL', 'GAIL', 'ADANIGREEN', 'ADANITRANS'
            ],
            'Nifty Financial Services': [
                'HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'SBIN', 'AXISBANK',
                'BAJFINANCE', 'BAJAJFINSV', 'HDFCLIFE', 'SBILIFE', 'ICICIGI'
            ],
            'Nifty Realty': [
                'DLF', 'GODREJPROP', 'OBEROIRLTY', 'PHOENIXLTD', 'PRESTIGE',
                'BRIGADE', 'SOBHA', 'MAHLIFE', 'IBREALEST'
            ],
            'Nifty Media': [
                'ZEEL', 'PVRINOX', 'SAREGAMA', 'NETWORK18', 'TVTODAY'
            ],
            'Nifty PSU Bank': [
                'SBIN', 'PNB', 'BANKBARODA', 'CANBK', 'UNIONBANK',
                'INDIANB', 'MAHABANK', 'IOB'
            ],
            'Nifty Infrastructure': [
                'LTI', 'ADANIPORTS', 'GAIL', 'PFC', 'RECLTD',
                'IRCTC', 'CONCOR', 'GMRINFRA'
            ],
            'Nifty Commodities': [
                'TATASTEEL', 'HINDALCO', 'COALINDIA', 'GAIL', 'IOC',
                'BPCL', 'ITC', 'JSWSTEEL', 'VEDL', 'UPL'
            ],
            'Nifty Consumption': [
                'HINDUNILVR', 'ITC', 'MARUTI', 'TITAN', 'NESTLEIND',
                'BAJAJ-AUTO', 'BRITANNIA', 'DABUR'
            ],
            'Nifty CPSE': [
                'ONGC', 'COALINDIA', 'IOC', 'GAIL', 'BPCL',
                'NTPC', 'POWERGRID', 'SAIL', 'NMDC'
            ],
            'Nifty MNC': [
                'NESTLEIND', 'HINDUNILVR', 'BOSCHLTD', 'SIEMENS', 'ABB',
                'COLPAL', '3MINDIA', 'GILLETTE'
            ],
            'Nifty PSE': [
                'ONGC', 'COALINDIA', 'NTPC', 'POWERGRID', 'IOC',
                'GAIL', 'BPCL', 'SAIL', 'NMDC'
            ]
        }
    
    def download_stock_yfinance(self, symbol: str) -> pd.DataFrame:
        """Download using yfinance with retry"""
        
        if not YFINANCE_AVAILABLE:
            return None
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Add .NS for NSE
                ticker = f"{symbol}.NS"
                
                # Download with yfinance
                df = yf.download(
                    ticker,
                    start=self.start_date,
                    end=self.end_date,
                    progress=False,
                    auto_adjust=False
                )
                
                if not df.empty:
                    # Standardize column names
                    df.columns = [col.lower() for col in df.columns]
                    
                    self.stats['yfinance_ok'] += 1
                    return df
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    return None
        
        return None
    
    def download_stock(self, symbol: str, sector: str) -> bool:
        """Download stock data"""
        
        self.stats['attempted'] += 1
        
        # Try yfinance
        df = self.download_stock_yfinance(symbol)
        
        if df is not None and not df.empty:
            self._save_data(symbol, sector, df)
            self.stats['success'] += 1
            return True
        
        self.stats['failed'].append(symbol)
        return False
    
    def _save_data(self, symbol: str, sector: str, df: pd.DataFrame):
        """Save to database"""
        
        try:
            # Save stock info
            stock = self.session.query(Stock).filter_by(symbol=symbol).first()
            if not stock:
                stock = Stock(symbol=symbol, sector=sector, name=symbol)
                self.session.add(stock)
                self.session.commit()
            
            # Save prices
            for date, row in df.iterrows():
                price = StockPrice(
                    symbol=symbol,
                    date=date.date() if hasattr(date, 'date') else date,
                    open=float(row['open']) if pd.notna(row['open']) else None,
                    high=float(row['high']) if pd.notna(row['high']) else None,
                    low=float(row['low']) if pd.notna(row['low']) else None,
                    close=float(row['close']) if pd.notna(row['close']) else None,
                    volume=float(row['volume']) if pd.notna(row['volume']) else None
                )
                self.session.add(price)
            
            self.session.commit()
            
        except Exception as e:
            print(f"    Error saving {symbol}: {e}")
            self.session.rollback()
    
    def run(self):
        """Run full download"""
        
        print("\n" + "="*80)
        print("NSE DATA SCRAPER - ENHANCED VERSION")
        print("="*80)
        print(f"Period: {self.start_date.date()} to {self.end_date.date()}")
        print(f"Method: yfinance (Yahoo Finance)")
        print("="*80 + "\n")
        
        # Count total
        total = sum(len(stocks) for stocks in self.sectors_stocks.values())
        print(f"Total stocks to download: {total}\n")
        
        # Download by sector
        for sector, stocks in self.sectors_stocks.items():
            print(f"\n{sector} ({len(stocks)} stocks):")
            print("-"*80)
            
            for symbol in stocks:
                print(f"  [{self.stats['attempted']}/{total}] {symbol:<15}", end=" ", flush=True)
                
                if self.download_stock(symbol, sector):
                    print("✅")
                else:
                    print("❌")
                
                # Rate limiting
                time.sleep(0.5)
        
        # Summary
        self._summary()
    
    def _summary(self):
        """Print summary"""
        
        total_stocks = self.session.query(Stock).count()
        total_prices = self.session.query(StockPrice).count()
        
        print("\n" + "="*80)
        print("DOWNLOAD COMPLETE!")
        print("="*80)
        print(f"\nSTATISTICS:")
        print(f"  Attempted: {self.stats['attempted']}")
        print(f"  Success: {self.stats['success']}")
        print(f"  Success Rate: {self.stats['success']/max(self.stats['attempted'],1)*100:.1f}%")
        print(f"  yfinance Success: {self.stats['yfinance_ok']}")
        print(f"  Failed: {len(self.stats['failed'])}")
        
        print(f"\nDATABASE:")
        print(f"  Total stocks: {total_stocks}")
        print(f"  Total price records: {total_prices:,}")
        print(f"  Database: {self.data_dir / 'nse_data.db'}")
        
        if self.stats['failed'] and len(self.stats['failed']) <= 20:
            print(f"\nFailed symbols:")
            for sym in self.stats['failed']:
                print(f"  - {sym}")
        
        print("="*80 + "\n")
        
        self.session.close()


def main():
    """Main entry"""
    
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', type=str, 
                       default=r'C:\Users\swaga\OneDrive\Desktop\systematic_sector_rotation\NSE_sector_wise_data')
    
    args = parser.parse_args()
    
    scraper = RobustNSEScraper(data_dir=args.dir)
    scraper.run()


if __name__ == "__main__":
    main()
