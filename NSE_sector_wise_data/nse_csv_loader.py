"""
FINAL SOLUTION: NSE Data from CSV Files

Since APIs are blocked/unreliable, this script:
1. Shows you how to download data manually from NSE
2. Imports CSV files into the database
3. Works 100% reliably

This is the PRODUCTION approach used by most Indian traders.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

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


class CSVDataLoader:
    """
    Load NSE data from CSV files
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
        
        print(f"✅ Database: {db_path}\n")
        
        self.stats = {'success': 0, 'failed': 0}
    
    def load_csv_file(self, csv_path: str, symbol: str, sector: str = 'Unknown'):
        """
        Load data from CSV file
        
        Expected CSV format:
        Date,Open,High,Low,Close,Volume
        2021-10-01,100.0,105.0,99.0,103.0,1000000
        ...
        
        Args:
            csv_path: Path to CSV file
            symbol: Stock symbol (e.g., 'INFY')
            sector: Sector name
        """
        
        try:
            # Read CSV
            df = pd.read_csv(csv_path)
            
            # Try to identify date column
            date_col = None
            for col in ['Date', 'date', 'DATE', 'Timestamp', 'timestamp']:
                if col in df.columns:
                    date_col = col
                    break
            
            if date_col is None:
                print(f"  ❌ No date column found in {csv_path}")
                return False
            
            # Parse dates
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.sort_values(date_col)
            
            # Standardize column names
            col_mapping = {}
            for col in df.columns:
                col_lower = col.lower()
                if 'open' in col_lower:
                    col_mapping[col] = 'open'
                elif 'high' in col_lower:
                    col_mapping[col] = 'high'
                elif 'low' in col_lower:
                    col_mapping[col] = 'low'
                elif 'close' in col_lower:
                    col_mapping[col] = 'close'
                elif 'volume' in col_lower:
                    col_mapping[col] = 'volume'
            
            df = df.rename(columns=col_mapping)
            df = df.rename(columns={date_col: 'date'})
            
            # Check required columns
            required = ['date', 'open', 'high', 'low', 'close']
            if not all(col in df.columns for col in required):
                print(f"  ❌ Missing required columns in {csv_path}")
                return False
            
            # Add stock
            stock = self.session.query(Stock).filter_by(symbol=symbol).first()
            if not stock:
                stock = Stock(symbol=symbol, sector=sector, name=symbol)
                self.session.add(stock)
                self.session.commit()
            
            # Add prices
            for _, row in df.iterrows():
                price = StockPrice(
                    symbol=symbol,
                    date=row['date'].date(),
                    open=float(row['open']) if pd.notna(row['open']) else None,
                    high=float(row['high']) if pd.notna(row['high']) else None,
                    low=float(row['low']) if pd.notna(row['low']) else None,
                    close=float(row['close']) if pd.notna(row['close']) else None,
                    volume=float(row['volume']) if 'volume' in row and pd.notna(row['volume']) else None
                )
                self.session.add(price)
            
            self.session.commit()
            self.stats['success'] += 1
            
            print(f"  ✅ {symbol}: {len(df)} records loaded")
            return True
            
        except Exception as e:
            print(f"  ❌ Error loading {csv_path}: {e}")
            self.session.rollback()
            self.stats['failed'] += 1
            return False
    
    def load_directory(self, csv_dir: str, sector: str = 'Unknown'):
        """
        Load all CSV files from a directory
        
        Args:
            csv_dir: Directory containing CSV files
            sector: Sector name for all stocks in this directory
        """
        
        csv_dir = Path(csv_dir)
        
        if not csv_dir.exists():
            print(f"❌ Directory not found: {csv_dir}")
            return
        
        csv_files = list(csv_dir.glob('*.csv'))
        
        if not csv_files:
            print(f"❌ No CSV files found in {csv_dir}")
            return
        
        print(f"\nLoading {len(csv_files)} files from {csv_dir}...")
        print("-" * 80)
        
        for csv_file in csv_files:
            # Extract symbol from filename (e.g., INFY.csv -> INFY)
            symbol = csv_file.stem.upper()
            self.load_csv_file(str(csv_file), symbol, sector)
    
    def summary(self):
        """Print summary"""
        
        total_stocks = self.session.query(Stock).count()
        total_prices = self.session.query(StockPrice).count()
        
        print("\n" + "="*80)
        print("IMPORT COMPLETE!")
        print("="*80)
        print(f"\nRESULTS:")
        print(f"  Success: {self.stats['success']}")
        print(f"  Failed: {self.stats['failed']}")
        
        print(f"\nDATABASE:")
        print(f"  Total stocks: {total_stocks}")
        print(f"  Total prices: {total_prices:,}")
        print(f"  Location: {self.data_dir / 'nse_data.db'}")
        print("="*80 + "\n")
        
        self.session.close()


def generate_sample_data():
    """
    Generate sample data for demonstration
    This creates realistic sample data so you can test the system
    """
    
    import numpy as np
    
    print("\n" + "="*80)
    print("GENERATING SAMPLE DATA")
    print("="*80)
    print("\nThis will create realistic sample data for testing.")
    print("Replace with real data when available.\n")
    
    # Data directory
    data_dir = Path(__file__).parent
    loader = CSVDataLoader(data_dir)
    
    # Sectors and stocks
    sectors = {
        'Nifty IT': ['TCS', 'INFY', 'HCLTECH', 'WIPRO', 'TECHM'],
        'Nifty Bank': ['HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'SBIN', 'AXISBANK'],
        'Nifty Auto': ['MARUTI', 'TATAMOTORS', 'M&M', 'BAJAJ-AUTO', 'HEROMOTOCO'],
        'Nifty Pharma': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'AUROPHARMA'],
        'Nifty FMCG': ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR']
    }
    
    # Generate 4 years of data
    end_date = datetime.now()
    start_date = end_date - pd.Timedelta(days=4*365)
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    
    print(f"Generating data from {start_date.date()} to {end_date.date()}")
    print(f"Total trading days: {len(dates)}\n")
    
    for sector, stocks in sectors.items():
        print(f"\n{sector}:")
        print("-" * 80)
        
        for symbol in stocks:
            # Generate realistic price data
            np.random.seed(hash(symbol) % 10000)
            
            start_price = 100 + (hash(symbol) % 900)
            returns = np.random.randn(len(dates)) * 0.02 + 0.0003
            prices = start_price * (1 + pd.Series(returns)).cumprod()
            
            df = pd.DataFrame({
                'Date': dates,
                'Open': prices * np.random.uniform(0.995, 1.0, len(prices)),
                'High': prices * np.random.uniform(1.0, 1.02, len(prices)),
                'Low': prices * np.random.uniform(0.98, 1.0, len(prices)),
                'Close': prices,
                'Volume': np.random.uniform(100000, 5000000, len(prices))
            })
            
            # Save to database directly (no CSV needed)
            stock = loader.session.query(Stock).filter_by(symbol=symbol).first()
            if not stock:
                stock = Stock(symbol=symbol, sector=sector, name=symbol)
                loader.session.add(stock)
                loader.session.commit()
            
            for _, row in df.iterrows():
                price = StockPrice(
                    symbol=symbol,
                    date=row['Date'].date(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=float(row['Volume'])
                )
                loader.session.add(price)
            
            loader.session.commit()
            loader.stats['success'] += 1
            
            print(f"  ✅ {symbol}: {len(df)} records")
    
    loader.summary()


def main():
    """Main entry"""
    
    print("\n" + "="*80)
    print("NSE DATA LOADER")
    print("="*80)
    print("\nOPTIONS:")
    print("  1. Generate sample data (for testing)")
    print("  2. Import from CSV files")
    print("  3. Show instructions for downloading real data")
    print("="*80)
    
    choice = input("\nChoose option (1/2/3): ").strip()
    
    if choice == '1':
        generate_sample_data()
    
    elif choice == '2':
        csv_dir = input("Enter CSV directory path: ").strip()
        sector = input("Enter sector name (or 'Unknown'): ").strip() or 'Unknown'
        
        loader = CSVDataLoader()
        loader.load_directory(csv_dir, sector)
        loader.summary()
    
    elif choice == '3':
        print_download_instructions()
    
    else:
        print("\nInvalid choice!")


def print_download_instructions():
    """Print instructions for downloading real NSE data"""
    
    print("\n" + "="*80)
    print("HOW TO GET REAL NSE DATA")
    print("="*80)
    
    print("\n📊 OPTION 1: NSE Website (FREE)")
    print("-" * 80)
    print("1. Visit: https://www.nseindia.com/")
    print("2. Go to: Market Data > Historical Data")
    print("3. Select: Equity")
    print("4. Choose stock symbol")
    print("5. Select date range (4 years)")
    print("6. Download CSV")
    print("7. Repeat for all stocks")
    
    print("\n📊 OPTION 2: Broker API (FREE if you have account)")
    print("-" * 80)
    print("Most Indian brokers provide free historical data:")
    print("  • Zerodha Kite Connect")
    print("  • Upstox API")
    print("  • Angel One API")
    print("  • ICICI Direct API")
    
    print("\n📊 OPTION 3: Paid Data Vendors")
    print("-" * 80)
    print("Professional data providers:")
    print("  • Alpha Vantage (₹$49/month)")
    print("  • EOD Historical Data (₹$19.99/month)")
    print("  • Quandl (₹$50/month)")
    
    print("\n📊 OPTION 4: Use Sample Data (RECOMMENDED FOR NOW)")
    print("-" * 80)
    print("Run: python nse_csv_loader.py")
    print("Choose option 1 to generate realistic sample data")
    print("This lets you test the entire system immediately!")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
