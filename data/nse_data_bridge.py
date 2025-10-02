"""
NSE Data Bridge for Backtesting

Loads real NSE data from NSE_sector_wise_data database
and prepares it for the backtesting system.

This connects your scraped data to the main strategy.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import numpy as np

from utils.logger import setup_logger

logger = setup_logger(__name__)


class NSEDataBridge:
    """
    Bridge between NSE database and backtesting system
    """
    
    def __init__(self, nse_db_path: str = None):
        """
        Initialize bridge
        
        Args:
            nse_db_path: Path to NSE database. If None, uses default location.
        """
        
        if nse_db_path is None:
            # Default location
            project_root = Path(__file__).parent.parent
            nse_db_path = project_root / 'NSE_sector_wise_data' / 'nse_data.db'
        
        self.nse_db_path = Path(nse_db_path)
        
        if not self.nse_db_path.exists():
            raise FileNotFoundError(
                f"NSE database not found at {self.nse_db_path}\n"
                f"Please run: python NSE_sector_wise_data/nse_csv_loader.py"
            )
        
        logger.info(f"NSE Database: {self.nse_db_path}")
        
        # Connect to database
        self.conn = sqlite3.connect(self.nse_db_path)
        
        # Check what's available
        self._check_database()
    
    def _check_database(self):
        """Check database contents"""
        
        stocks_count = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM stocks", 
            self.conn
        )['count'][0]
        
        prices_count = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM stock_prices", 
            self.conn
        )['count'][0]
        
        logger.info(f"Database contains {stocks_count} stocks with {prices_count:,} price records")
        
        if stocks_count == 0:
            raise ValueError(
                "Database is empty! Please load data first:\n"
                "python NSE_sector_wise_data/nse_csv_loader.py"
            )
    
    def get_available_sectors(self) -> list:
        """Get list of sectors in database"""
        
        query = """
        SELECT DISTINCT sector 
        FROM stocks 
        WHERE sector IS NOT NULL 
        ORDER BY sector
        """
        
        sectors = pd.read_sql_query(query, self.conn)
        return sectors['sector'].tolist()
    
    def get_stocks_by_sector(self, sector: str) -> list:
        """Get stocks in a sector"""
        
        query = f"""
        SELECT symbol FROM stocks 
        WHERE sector = '{sector}'
        ORDER BY symbol
        """
        
        stocks = pd.read_sql_query(query, self.conn)
        return stocks['symbol'].tolist()
    
    def get_stock_prices(self, symbol: str, 
                        start_date: datetime = None,
                        end_date: datetime = None) -> pd.DataFrame:
        """
        Get price data for a stock
        
        Args:
            symbol: Stock symbol
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            DataFrame with OHLCV data
        """
        
        query = f"""
        SELECT date, open, high, low, close, volume
        FROM stock_prices
        WHERE symbol = '{symbol}'
        """
        
        if start_date:
            query += f" AND date >= '{start_date.date()}'"
        
        if end_date:
            query += f" AND date <= '{end_date.date()}'"
        
        query += " ORDER BY date"
        
        df = pd.read_sql_query(query, self.conn)
        
        if df.empty:
            logger.warning(f"No data found for {symbol}")
            return pd.DataFrame()
        
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Rename columns to match expected format
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        return df
    
    def get_sector_stocks_prices(self, sector: str,
                                 start_date: datetime = None,
                                 end_date: datetime = None) -> Dict[str, pd.DataFrame]:
        """
        Get all stock prices in a sector
        
        Args:
            sector: Sector name
            start_date: Start date
            end_date: End date
            
        Returns:
            Dict mapping symbol to DataFrame
        """
        
        stocks = self.get_stocks_by_sector(sector)
        
        prices_dict = {}
        
        for symbol in stocks:
            df = self.get_stock_prices(symbol, start_date, end_date)
            if not df.empty:
                prices_dict[symbol] = df
        
        logger.info(f"Loaded {len(prices_dict)} stocks from {sector}")
        
        return prices_dict
    
    def get_all_stocks_prices(self, start_date: datetime = None,
                             end_date: datetime = None) -> Dict[str, pd.DataFrame]:
        """
        Get all stock prices
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dict mapping symbol to DataFrame
        """
        
        query = "SELECT DISTINCT symbol FROM stocks ORDER BY symbol"
        symbols = pd.read_sql_query(query, self.conn)['symbol'].tolist()
        
        prices_dict = {}
        
        for symbol in symbols:
            df = self.get_stock_prices(symbol, start_date, end_date)
            if not df.empty:
                prices_dict[symbol] = df
        
        logger.info(f"Loaded {len(prices_dict)} stocks total")
        
        return prices_dict
    
    def prepare_backtest_data(self, start_date: datetime, 
                             end_date: datetime) -> Tuple[Dict, Dict, Dict]:
        """
        Prepare complete data for backtesting
        
        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            
        Returns:
            Tuple of (sector_prices, stocks_data, stocks_prices)
        """
        
        logger.info(f"Preparing backtest data: {start_date.date()} to {end_date.date()}")
        
        # 1. Get sector prices (create synthetic sector indices from stocks)
        sector_prices = {}
        sectors = self.get_available_sectors()
        
        for sector in sectors:
            stocks_in_sector = self.get_sector_stocks_prices(sector, start_date, end_date)
            
            if stocks_in_sector:
                # Create sector index as average of stocks
                all_closes = pd.DataFrame({
                    symbol: df['Close'] 
                    for symbol, df in stocks_in_sector.items()
                })
                
                sector_close = all_closes.mean(axis=1)
                
                sector_prices[sector] = pd.DataFrame({
                    'Close': sector_close,
                    'Open': sector_close * 0.998,
                    'High': sector_close * 1.005,
                    'Low': sector_close * 0.995,
                    'Volume': 1000000
                })
        
        logger.info(f"Created {len(sector_prices)} sector indices")
        
        # 2. Get all stock prices
        stocks_prices = self.get_all_stocks_prices(start_date, end_date)
        
        # 3. Create stocks fundamental data
        stocks_data = {}
        
        for symbol in stocks_prices.keys():
            # Get basic info from database
            query = f"""
            SELECT symbol, sector, market_cap 
            FROM stocks 
            WHERE symbol = '{symbol}'
            """
            
            stock_info = pd.read_sql_query(query, self.conn)
            
            if not stock_info.empty:
                stocks_data[symbol] = {
                    'sector': stock_info['sector'].iloc[0],
                    'market_cap': stock_info['market_cap'].iloc[0] if pd.notna(stock_info['market_cap'].iloc[0]) else 1e10,
                    # Generate synthetic fundamentals
                    'pe_ratio': np.random.uniform(15, 30),
                    'pb_ratio': np.random.uniform(2, 8),
                    'roe': np.random.uniform(0.12, 0.25),
                    'debt_to_equity': np.random.uniform(0.3, 1.2),
                    'current_ratio': np.random.uniform(1.2, 2.5)
                }
        
        logger.info(f"Prepared data for {len(stocks_data)} stocks")
        
        return sector_prices, stocks_data, stocks_prices
    
    def get_date_range(self) -> Tuple[datetime, datetime]:
        """Get available date range in database"""
        
        query = """
        SELECT MIN(date) as min_date, MAX(date) as max_date
        FROM stock_prices
        """
        
        result = pd.read_sql_query(query, self.conn)
        
        min_date = pd.to_datetime(result['min_date'].iloc[0])
        max_date = pd.to_datetime(result['max_date'].iloc[0])
        
        return min_date, max_date
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


def demo_bridge():
    """Demonstrate bridge usage"""
    
    print("\n" + "="*80)
    print("NSE DATA BRIDGE DEMO")
    print("="*80)
    
    try:
        # Initialize bridge
        bridge = NSEDataBridge()
        
        # Show available data
        print("\n📊 AVAILABLE DATA:")
        print("-" * 80)
        
        sectors = bridge.get_available_sectors()
        print(f"\nSectors: {len(sectors)}")
        for sector in sectors:
            stocks = bridge.get_stocks_by_sector(sector)
            print(f"  • {sector}: {len(stocks)} stocks")
        
        # Show date range
        min_date, max_date = bridge.get_date_range()
        print(f"\nDate Range:")
        print(f"  From: {min_date.date()}")
        print(f"  To:   {max_date.date()}")
        print(f"  Days: {(max_date - min_date).days}")
        
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
        
        print("\n" + "="*80)
        print("✅ Bridge is working! Ready for backtesting.")
        print("="*80 + "\n")
        
        bridge.close()
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}\n")
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")


if __name__ == "__main__":
    demo_bridge()
