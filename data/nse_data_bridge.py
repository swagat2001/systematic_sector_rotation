"""
NSE Data Bridge for Backtesting

Loads real NSE data from nse_cash.db (scraped database)
and prepares it for the backtesting system.

Maps yfinance sectors to Nifty categories dynamically.
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


# Map yfinance sectors to Nifty categories
SECTOR_MAPPING = {
    'Technology': 'Nifty IT',
    'Information Technology Services': 'Nifty IT',
    'Software - Application': 'Nifty IT',
    'Software - Infrastructure': 'Nifty IT',
    
    'Financial Services': 'Nifty Financial Services',
    'Banks': 'Nifty Bank',
    'Capital Markets': 'Nifty Financial Services',
    'Asset Management': 'Nifty Financial Services',
    'Credit Services': 'Nifty Financial Services',
    'Insurance': 'Nifty Financial Services',
    
    'Healthcare': 'Nifty Pharma',
    'Drug Manufacturers - Specialty & Generic': 'Nifty Pharma',
    'Drug Manufacturers - General': 'Nifty Pharma',
    'Medical Care Facilities': 'Nifty Healthcare',
    'Medical Instruments & Supplies': 'Nifty Healthcare',
    
    'Consumer Cyclical': 'Nifty Consumption',
    'Consumer Defensive': 'Nifty FMCG',
    'Packaged Foods': 'Nifty FMCG',
    'Beverages - Non-Alcoholic': 'Nifty FMCG',
    'Household & Personal Products': 'Nifty FMCG',
    
    'Industrials': 'Nifty Infrastructure',
    'Engineering & Construction': 'Nifty Infrastructure',
    'Specialty Industrial Machinery': 'Nifty Infrastructure',
    'Electrical Equipment & Parts': 'Nifty Infrastructure',
    'Auto Parts': 'Nifty Auto',
    'Auto Manufacturers': 'Nifty Auto',
    
    'Basic Materials': 'Nifty Commodities',
    'Steel': 'Nifty Metal',
    'Aluminum': 'Nifty Metal',
    'Copper': 'Nifty Metal',
    'Other Industrial Metals & Mining': 'Nifty Metal',
    'Specialty Chemicals': 'Nifty Commodities',
    
    'Energy': 'Nifty Energy',
    'Oil & Gas Equipment & Services': 'Nifty Energy',
    'Oil & Gas Integrated': 'Nifty Energy',
    'Utilities': 'Nifty Energy',
    
    'Real Estate': 'Nifty Realty',
    'Real Estate Services': 'Nifty Realty',
    'Real Estate - Development': 'Nifty Realty',
    
    'Communication Services': 'Nifty Media',
    'Telecom Services': 'Nifty Media',
    'Entertainment': 'Nifty Media',
    'Broadcasting': 'Nifty Media',
    
    'Textile Manufacturing': 'Nifty Consumption',
}


class NSEDataBridge:
    """
    Bridge between NSE scraped database (nse_cash.db) and backtesting system
    """
    
    def __init__(self, nse_db_path: str = None):
        """
        Initialize bridge
        
        Args:
            nse_db_path: Path to NSE database. If None, uses default (nse_cash.db)
        """
        
        if nse_db_path is None:
            # Default location - nse_cash.db from scraper
            project_root = Path(__file__).parent.parent
            nse_db_path = project_root / 'NSE_sector_wise_data' / 'nse_cash.db'
        
        self.nse_db_path = Path(nse_db_path)
        
        if not self.nse_db_path.exists():
            raise FileNotFoundError(
                f"❌ Scraped database not found at {self.nse_db_path}\n"
                f"Please run the scraper first:\n"
                f"python NSE_sector_wise_data/nse_cash_ohlc_pipeline.py --workers 2 --sleep 1.0"
            )
        
        logger.info(f"✓ NSE Database: {self.nse_db_path}")
        
        # Connect to database
        self.conn = sqlite3.connect(str(self.nse_db_path))
        
        # Check what's available
        self._check_database()
    
    def _check_database(self):
        """Check database contents"""
        
        stocks_count = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM companies", 
            self.conn
        )['count'][0]
        
        prices_count = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM ohlc", 
            self.conn
        )['count'][0]
        
        logger.info(f"✓ Database contains {stocks_count} stocks with {prices_count:,} price records")
        
        if stocks_count == 0:
            raise ValueError("Database is empty! Please run the scraper first.")
    
    def _map_sector(self, yfinance_sector: str, yfinance_industry: str) -> str:
        """Map yfinance sector/industry to Nifty category"""
        
        # Try industry first (more specific)
        if yfinance_industry and yfinance_industry in SECTOR_MAPPING:
            return SECTOR_MAPPING[yfinance_industry]
        
        # Then try sector
        if yfinance_sector and yfinance_sector in SECTOR_MAPPING:
            return SECTOR_MAPPING[yfinance_sector]
        
        # Default to Nifty 50 if unmapped
        return 'Nifty 50'
    
    def get_available_sectors(self) -> list:
        """Get list of Nifty sectors available"""
        
        query = """
        SELECT DISTINCT sector, industry 
        FROM companies 
        WHERE sector IS NOT NULL
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        # Map to Nifty categories
        nifty_sectors = set()
        for _, row in df.iterrows():
            nifty_sector = self._map_sector(row['sector'], row['industry'])
            nifty_sectors.add(nifty_sector)
        
        return sorted(list(nifty_sectors))
    
    def get_stocks_by_sector(self, nifty_sector: str) -> list:
        """Get stocks in a Nifty sector"""
        
        query = """
        SELECT symbol, sector, industry 
        FROM companies 
        WHERE sector IS NOT NULL
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        # Filter by mapped Nifty sector
        symbols = []
        for _, row in df.iterrows():
            mapped_sector = self._map_sector(row['sector'], row['industry'])
            if mapped_sector == nifty_sector:
                symbols.append(row['symbol'])
        
        return sorted(symbols)
    
    def get_stock_prices(self, symbol: str, 
                        start_date: datetime = None,
                        end_date: datetime = None) -> pd.DataFrame:
        """
        Get price data for a stock from ohlc table
        """
        
        query = f"""
        SELECT date, open, high, low, close, volume
        FROM ohlc
        WHERE symbol = '{symbol}'
        """
        
        if start_date:
            query += f" AND date >= '{start_date.date()}'"
        
        if end_date:
            query += f" AND date <= '{end_date.date()}'"
        
        query += " ORDER BY date"
        
        df = pd.read_sql_query(query, self.conn)
        
        if df.empty:
            return pd.DataFrame()
        
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Rename columns to match expected format
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        return df
    
    def prepare_backtest_data(self, start_date: datetime, 
                             end_date: datetime) -> Tuple[Dict, Dict, Dict]:
        """
        Prepare complete data for backtesting with Nifty sector mapping
        
        Returns:
            Tuple of (sector_prices, stocks_data, stocks_prices)
        """
        
        logger.info(f"Preparing backtest data: {start_date.date()} to {end_date.date()}")
        
        # 1. Get all stocks with sector info
        query = """
        SELECT symbol, sector, industry 
        FROM companies 
        WHERE sector IS NOT NULL
        """
        
        companies_df = pd.read_sql_query(query, self.conn)
        
        # 2. Get sector prices (create indices from stocks)
        sector_prices = {}
        nifty_sectors = self.get_available_sectors()
        
        for nifty_sector in nifty_sectors:
            stocks_in_sector = []
            
            # Get all stocks in this Nifty sector
            for _, row in companies_df.iterrows():
                mapped_sector = self._map_sector(row['sector'], row['industry'])
                if mapped_sector == nifty_sector:
                    df = self.get_stock_prices(row['symbol'], start_date, end_date)
                    if not df.empty:
                        stocks_in_sector.append(df['Close'])
            
            if stocks_in_sector:
                # Create sector index as average
                sector_df = pd.concat(stocks_in_sector, axis=1)
                sector_close = sector_df.mean(axis=1)
                
                sector_prices[nifty_sector] = pd.DataFrame({
                    'Close': sector_close,
                    'Open': sector_close * 0.998,
                    'High': sector_close * 1.005,
                    'Low': sector_close * 0.995,
                    'Volume': 1000000
                })
        
        logger.info(f"✓ Created {len(sector_prices)} Nifty sector indices")
        
        # 3. Get all stock prices
        stocks_prices = {}
        for _, row in companies_df.iterrows():
            df = self.get_stock_prices(row['symbol'], start_date, end_date)
            if not df.empty:
                stocks_prices[row['symbol']] = df
        
        logger.info(f"✓ Loaded {len(stocks_prices)} stocks with price data")
        
        # 4. Create stocks data with mapped sectors
        stocks_data = {}
        for _, row in companies_df.iterrows():
            if row['symbol'] in stocks_prices:
                nifty_sector = self._map_sector(row['sector'], row['industry'])
                
                stocks_data[row['symbol']] = {
                    'sector': nifty_sector,
                    'yfinance_sector': row['sector'],
                    'yfinance_industry': row['industry'],
                    'market_cap': 1e10,  # Default
                    # Synthetic fundamentals
                    'pe_ratio': np.random.uniform(15, 30),
                    'pb_ratio': np.random.uniform(2, 8),
                    'roe': np.random.uniform(0.12, 0.25),
                    'debt_to_equity': np.random.uniform(0.3, 1.2),
                    'current_ratio': np.random.uniform(1.2, 2.5)
                }
        
        logger.info(f"✓ Prepared data for {len(stocks_data)} stocks")
        
        return sector_prices, stocks_data, stocks_prices
    
    def get_date_range(self) -> Tuple[datetime, datetime]:
        """Get available date range"""
        
        query = """
        SELECT MIN(date) as min_date, MAX(date) as max_date
        FROM ohlc
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
    print("NSE DATA BRIDGE DEMO - DYNAMIC SECTOR MAPPING")
    print("="*80)
    
    try:
        # Initialize bridge
        bridge = NSEDataBridge()
        
        # Show available data
        print("\n📊 AVAILABLE DATA:")
        print("-" * 80)
        
        sectors = bridge.get_available_sectors()
        print(f"\nNifty Sectors: {len(sectors)}")
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
        
        print("\n" + "="*80)
        print("✅ Bridge is working! Ready for backtesting with dynamic sectors.")
        print("="*80)
        print("\nNext: streamlit run dashboard/streamlit_app.py")
        print("="*80 + "\n")
        
        bridge.close()
        
    except FileNotFoundError as e:
        print(f"\n{e}\n")
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_bridge()
