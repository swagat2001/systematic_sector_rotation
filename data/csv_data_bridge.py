"""
CSV Data Bridge - Load OHLC data from CSV files
================================================

Reads stock data from CSV files organized by sector directories.

Directory Structure:
C:/Users/Admin/Desktop/data/stock_data_NSE/
├── IT/
│   ├── INFY.csv
│   ├── TCS.csv
│   └── ...
├── Banking/
│   ├── HDFCBANK.csv
│   └── ...
└── ...

Each CSV file contains OHLC data for one stock.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime
from typing import Dict, Tuple, List, Optional
import numpy as np

from config import Config
from utils.logger import setup_logger
from data.fundamental_data_provider import get_fundamental_provider

logger = setup_logger(__name__)


class CSVDataBridge:
    """
    Bridge between CSV files and backtesting system.
    
    Replaces SQLite database with CSV file reading.
    """
    
    def __init__(self, csv_data_path: str = None):
        """
        Initialize CSV data bridge
        
        Args:
            csv_data_path: Path to stock_data_NSE folder
        """
        
        if csv_data_path is None:
            # Default location
            csv_data_path = r"C:\Users\Admin\Desktop\data\stock_data_NSE"
        
        self.data_path = Path(csv_data_path)
        
        if not self.data_path.exists():
            raise FileNotFoundError(
                f"CSV data directory not found: {csv_data_path}\n"
                f"Please ensure stock_data_NSE folder exists."
            )
        
        # Initialize fundamental data provider
        provider_config = Config.FUNDAMENTAL_PROVIDER
        self.fundamental_provider = get_fundamental_provider(**provider_config)
        
        # Scan directory structure
        self._scan_directory_structure()
        
        logger.info(f"✓ CSV Data Bridge initialized")
        logger.info(f"✓ Data path: {self.data_path}")
        logger.info(f"✓ Found {len(self.sectors)} sectors")
        logger.info(f"✓ Found {self.total_stocks} stocks")
        logger.info(f"✓ Fundamental provider: {provider_config['type']}")
    
    def _scan_directory_structure(self):
        """Scan directory to find sectors and stocks"""
        
        self.sectors = {}  # {sector_name: [list of stock symbols]}
        self.stock_to_sector = {}  # {symbol: sector_name}
        self.total_stocks = 0
        
        # Get all sector directories
        for sector_dir in self.data_path.iterdir():
            if sector_dir.is_dir():
                sector_name = sector_dir.name
                stock_files = list(sector_dir.glob("*.csv"))
                
                if stock_files:
                    symbols = [f.stem for f in stock_files]  # filename without .csv
                    self.sectors[sector_name] = symbols
                    self.total_stocks += len(symbols)
                    
                    # Map symbol to sector
                    for symbol in symbols:
                        self.stock_to_sector[symbol] = sector_name
                    
                    logger.info(f"  • {sector_name}: {len(symbols)} stocks")
        
        if not self.sectors:
            raise ValueError(f"No sector directories found in {self.data_path}")
    
    def get_available_sectors(self) -> List[str]:
        """Get list of all available sectors"""
        return list(self.sectors.keys())
    
    def get_stocks_by_sector(self, sector: str) -> List[str]:
        """Get list of stocks in a sector"""
        return self.sectors.get(sector, [])
    
    def get_stock_prices(self, symbol: str, 
                        start_date: datetime = None,
                        end_date: datetime = None) -> pd.DataFrame:
        """
        Get OHLC price data for a stock
        
        Args:
            symbol: Stock symbol (e.g., 'INFY', 'TCS')
            start_date: Start date (optional)
            end_date: End date (optional)
        
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
            Index: Date (datetime)
        """
        
        # Find which sector this stock belongs to
        sector = self.stock_to_sector.get(symbol)
        
        if not sector:
            logger.warning(f"Stock {symbol} not found in any sector")
            return pd.DataFrame()
        
        # Build file path
        csv_file = self.data_path / sector / f"{symbol}.csv"
        
        if not csv_file.exists():
            logger.warning(f"CSV file not found: {csv_file}")
            return pd.DataFrame()
        
        try:
            # Read CSV file
            # Your format has:
            # Row 0: Price, Adj Close, Close, High, Low, Open, Volume (actual headers)
            # Row 1: Ticker repeated (20MICRONS.NS, 20MICRONS.NS, ...)
            # Row 2: Date, NaN, NaN, ... (fake date header)
            # Row 3+: Actual data with real dates
            
            # First, read to get the headers from row 0
            headers_df = pd.read_csv(csv_file, nrows=1)
            original_headers = headers_df.columns.tolist()
            
            # Now read the actual data, skipping first 3 rows:
            # Skip: Row 0 (headers - we already have them)
            #       Row 1 (ticker row)
            #       Row 2 ("Date" row)
            # Start: Row 3 (actual data)
            df = pd.read_csv(csv_file, skiprows=3, names=original_headers)
            
            # Clean up column names
            df.columns = df.columns.str.strip()
            
            # Map to standard names
            column_mapping = {
                'Price': 'Date',  # First column is actually dates
                'Adj Close': 'AdjClose',  # Keep for reference but not used
                'Close': 'Close',
                'High': 'High',
                'Low': 'Low',
                'Open': 'Open',
                'Volume': 'Volume'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Parse date and set as index
            # Handle multiple date formats automatically
            try:
                # Try with infer_datetime_format for automatic detection
                df['Date'] = pd.to_datetime(df['Date'], infer_datetime_format=True)
            except:
                try:
                    # Try with dayfirst=True for DD-MM-YYYY format
                    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
                except:
                    try:
                        # Try explicit YYYY-MM-DD format
                        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
                    except:
                        try:
                            # Try explicit DD-MM-YYYY format
                            df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')
                        except Exception as e:
                            logger.error(f"Could not parse dates in {csv_file}: {e}")
                            return pd.DataFrame()
            
            df = df.set_index('Date')
            df = df.sort_index()
            
            # Filter by date range if provided
            if start_date:
                df = df[df.index >= start_date]
            
            if end_date:
                df = df[df.index <= end_date]
            
            # Ensure we have the required columns
            required = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing = [col for col in required if col not in df.columns]
            
            if missing:
                logger.warning(f"{symbol}: Missing columns {missing}")
                return pd.DataFrame()
            
            return df[required]
        
        except Exception as e:
            logger.error(f"Error reading {csv_file}: {e}")
            return pd.DataFrame()
    
    def prepare_backtest_data(self, 
                             start_date: datetime,
                             end_date: datetime) -> Tuple[Dict, Dict, Dict]:
        """
        Prepare all data needed for backtesting
        
        Args:
            start_date: Backtest start date
            end_date: Backtest end date
        
        Returns:
            sector_prices: Dict of sector OHLC DataFrames
            stocks_data: Dict of fundamental data for each stock
            stocks_prices: Dict of stock OHLC DataFrames
        """
        
        logger.info(f"Preparing backtest data: {start_date.date()} to {end_date.date()}")
        
        # 1. Get stock prices for all stocks
        stocks_prices = {}
        
        logger.info("Loading stock prices from CSV files...")
        
        for symbol in self.stock_to_sector.keys():
            df = self.get_stock_prices(symbol, start_date, end_date)
            if not df.empty:
                stocks_prices[symbol] = df
        
        logger.info(f"✓ Loaded {len(stocks_prices)} stocks with price data")
        
        # 2. Create sector prices (indices from stocks)
        sector_prices = {}
        
        logger.info("Creating sector indices...")
        
        for sector in self.sectors.keys():
            stocks_in_sector = []
            
            # Get all stocks in this sector that have price data
            for symbol in self.sectors[sector]:
                if symbol in stocks_prices:
                    stocks_in_sector.append(stocks_prices[symbol]['Close'])
            
            if stocks_in_sector:
                # Create sector index as equal-weighted average
                sector_df = pd.concat(stocks_in_sector, axis=1)
                sector_close = sector_df.mean(axis=1)
                
                sector_prices[sector] = pd.DataFrame({
                    'Close': sector_close,
                    'Open': sector_close * 0.998,   # Approximate
                    'High': sector_close * 1.005,   # Approximate
                    'Low': sector_close * 0.995,    # Approximate
                    'Volume': 1000000  # Dummy volume
                })
        
        logger.info(f"✓ Created {len(sector_prices)} sector indices")
        
        # 3. Get fundamental data from provider
        symbols_with_prices = list(stocks_prices.keys())
        logger.info(f"Fetching fundamental data for {len(symbols_with_prices)} stocks...")
        
        fundamentals_bulk = self.fundamental_provider.get_bulk_fundamental_data(symbols_with_prices)
        
        # 4. Create stocks_data dict
        stocks_data = {}
        
        for symbol in stocks_prices.keys():
            sector = self.stock_to_sector[symbol]
            fundamental_data = fundamentals_bulk.get(symbol, {})
            
            stocks_data[symbol] = {
                'sector': sector,
                
                # Real fundamental data from provider
                'roe': fundamental_data.get('roe', 15.0),
                'roce': fundamental_data.get('roce', 18.0),
                'eps_cagr': fundamental_data.get('eps_cagr', 10.0),
                'pe_ratio': fundamental_data.get('pe_ratio', 20.0),
                'pb_ratio': fundamental_data.get('pb_ratio', 3.0),
                'debt_to_equity': fundamental_data.get('debt_to_equity', 0.5),
                'current_ratio': fundamental_data.get('current_ratio', 1.5),
                'market_cap': fundamental_data.get('market_cap', 1e10),
                
                # Optional additional fundamentals
                'revenue_growth': fundamental_data.get('revenue_growth'),
                'profit_margin': fundamental_data.get('profit_margin'),
                'dividend_yield': fundamental_data.get('dividend_yield'),
                'book_value': fundamental_data.get('book_value'),
                'eps': fundamental_data.get('eps'),
                'revenue': fundamental_data.get('revenue'),
                'net_profit': fundamental_data.get('net_profit'),
            }
        
        logger.info(f"✓ Prepared data for {len(stocks_data)} stocks")
        
        return sector_prices, stocks_data, stocks_prices
    
    def get_date_range(self) -> Tuple[datetime, datetime]:
        """Get available date range by sampling some stocks"""
        
        min_date = None
        max_date = None
        
        # Sample 10 stocks to find date range
        sample_symbols = list(self.stock_to_sector.keys())[:10]
        
        for symbol in sample_symbols:
            df = self.get_stock_prices(symbol)
            
            if not df.empty:
                if min_date is None or df.index.min() < min_date:
                    min_date = df.index.min()
                
                if max_date is None or df.index.max() > max_date:
                    max_date = df.index.max()
        
        if min_date is None or max_date is None:
            # Default to last 3 years
            max_date = datetime.now()
            min_date = max_date - pd.Timedelta(days=3*365)
        
        return min_date, max_date
    
    def close(self):
        """Close method for compatibility with NSEDataBridge (CSV doesn't need closing)"""
        pass  # CSV files don't need closing like database connections


def demo_csv_bridge():
    """Demonstrate CSV bridge usage"""
    
    print("\n" + "="*80)
    print("CSV DATA BRIDGE DEMO")
    print("="*80)
    
    try:
        # Initialize bridge
        bridge = CSVDataBridge()
        
        # Show available data
        print("\n📊 AVAILABLE DATA:")
        print("-" * 80)
        
        sectors = bridge.get_available_sectors()
        print(f"\nSectors: {len(sectors)}")
        for sector in sectors:
            stocks = bridge.get_stocks_by_sector(sector)
            print(f"  • {sector:30s}: {len(stocks):4d} stocks")
        
        # Show date range
        min_date, max_date = bridge.get_date_range()
        print(f"\nDate Range:")
        print(f"  From: {min_date.date()}")
        print(f"  To:   {max_date.date()}")
        print(f"  Days: {(max_date - min_date).days} (~{(max_date - min_date).days/365:.1f} years)")
        
        # Sample stock data
        print("\n📈 SAMPLE STOCK DATA:")
        print("-" * 80)
        
        if sectors:
            sample_stocks = bridge.get_stocks_by_sector(sectors[0])[:3]
            
            for symbol in sample_stocks:
                df = bridge.get_stock_prices(symbol)
                if not df.empty:
                    print(f"\n{symbol}:")
                    print(f"  Records: {len(df)}")
                    print(f"  First date: {df.index[0].date()}")
                    print(f"  Last date: {df.index[-1].date()}")
                    print(f"  Price range: ₹{df['Close'].min():.2f} - ₹{df['Close'].max():.2f}")
                    print(f"\n  Sample data (last 5 days):")
                    print(df.tail())
        
        print("\n" + "="*80)
        print("✅ CSV Bridge is working! Ready for backtesting.")
        print("="*80)
        print("\nNext: Update config.py to use CSV bridge instead of SQLite")
        print("="*80 + "\n")
        
    except FileNotFoundError as e:
        print(f"\n{e}\n")
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_csv_bridge()
