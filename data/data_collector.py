"""
Data Collection Module for Systematic Sector Rotation Strategy

This module handles:
1. Fetching NSE sectoral indices data
2. Downloading constituent stocks from NSE
3. Collecting 4 years of OHLC data
4. Mapping stocks to sectors/themes
5. Collecting fundamental data
"""

import pandas as pd
import numpy as np
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
from pathlib import Path
import json

from config import Config, NSESectors
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DataCollector:
    """
    Collects market data from various sources for the strategy
    """
    
    def __init__(self):
        self.config = Config()
        self.nse_sectors = NSESectors()
        self.cache_dir = Config.DATA_DIR / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Data storage
        self.sector_data = {}
        self.stock_data = {}
        self.sector_constituents = {}
        self.fundamental_data = {}
        
        logger.info("DataCollector initialized")
    
    async def load_all_data(self):
        """Load all required data for the strategy"""
        logger.info("Starting comprehensive data load...")
        
        try:
            # Step 1: Load sector indices data
            await self.fetch_sector_indices_data()
            
            # Step 2: Load sector constituents (stock mapping)
            await self.fetch_sector_constituents()
            
            # Step 3: Load stock OHLC data
            await self.fetch_stock_ohlc_data()
            
            # Step 4: Load fundamental data
            await self.fetch_fundamental_data()
            
            logger.info("All data loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    async def fetch_sector_indices_data(self) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for all NSE sectoral indices
        
        Returns:
            Dict mapping sector names to DataFrames with OHLC data
        """
        logger.info("Fetching NSE sectoral indices data...")
        
        start_date = Config.DATA_START_DATE
        end_date = Config.DATA_END_DATE
        
        for sector_name, ticker in self.nse_sectors.SECTOR_TICKERS.items():
            try:
                logger.info(f"Downloading {sector_name} ({ticker})...")
                
                # Check cache first
                cache_file = self.cache_dir / f"{sector_name.replace(' ', '_')}_index.csv"
                
                if cache_file.exists():
                    # Load from cache if recent (less than 1 day old)
                    if (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).days < 1:
                        logger.info(f"Loading {sector_name} from cache")
                        df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                        self.sector_data[sector_name] = df
                        continue
                
                # Download from yfinance
                data = yf.download(
                    ticker,
                    start=start_date,
                    end=end_date,
                    progress=False,
                    auto_adjust=True
                )
                
                if data.empty:
                    logger.warning(f"No data received for {sector_name}")
                    continue
                
                # Save to cache
                data.to_csv(cache_file)
                self.sector_data[sector_name] = data
                
                logger.info(f"✓ {sector_name}: {len(data)} days of data")
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error fetching {sector_name}: {e}")
                continue
        
        logger.info(f"Sector indices data loaded: {len(self.sector_data)} sectors")
        return self.sector_data
    
    async def fetch_sector_constituents(self) -> Dict[str, List[str]]:
        """
        Fetch constituent stocks for each sector from NSE website
        
        Returns:
            Dict mapping sector names to lists of stock symbols
        """
        logger.info("Fetching sector constituents from NSE...")
        
        for sector_name, url in self.nse_sectors.CONSTITUENT_URLS.items():
            try:
                logger.info(f"Fetching constituents for {sector_name}...")
                
                # Check cache first
                cache_file = self.cache_dir / f"{sector_name.replace(' ', '_')}_constituents.json"
                
                if cache_file.exists():
                    if (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).days < 7:
                        logger.info(f"Loading {sector_name} constituents from cache")
                        with open(cache_file, 'r') as f:
                            self.sector_constituents[sector_name] = json.load(f)
                        continue
                
                # Download constituent CSV from NSE
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                # Parse CSV
                from io import StringIO
                df = pd.read_csv(StringIO(response.text))
                
                # Extract symbols (usually in 'Symbol' column)
                if 'Symbol' in df.columns:
                    symbols = df['Symbol'].tolist()
                elif 'symbol' in df.columns:
                    symbols = df['symbol'].tolist()
                else:
                    # Try first column
                    symbols = df.iloc[:, 0].tolist()
                
                # Clean symbols
                symbols = [s.strip() for s in symbols if pd.notna(s)]
                
                # Save to cache
                with open(cache_file, 'w') as f:
                    json.dump(symbols, f)
                
                self.sector_constituents[sector_name] = symbols
                logger.info(f"✓ {sector_name}: {len(symbols)} stocks")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error fetching constituents for {sector_name}: {e}")
                # Fallback to hardcoded major stocks if available
                continue
        
        # Also fetch NIFTY 500 universe for satellite portfolio
        await self._fetch_nifty500_constituents()
        
        logger.info(f"Sector constituents loaded: {len(self.sector_constituents)} sectors")
        return self.sector_constituents
    
    async def _fetch_nifty500_constituents(self):
        """Fetch NIFTY 500 constituent stocks"""
        logger.info("Fetching NIFTY 500 constituents...")
        
        try:
            cache_file = self.cache_dir / "nifty500_constituents.json"
            
            if cache_file.exists():
                if (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).days < 7:
                    with open(cache_file, 'r') as f:
                        self.sector_constituents['NIFTY500'] = json.load(f)
                    logger.info(f"Loaded NIFTY 500 from cache: {len(self.sector_constituents['NIFTY500'])} stocks")
                    return
            
            url = "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            if 'Symbol' in df.columns:
                symbols = df['Symbol'].tolist()
            else:
                symbols = df.iloc[:, 2].tolist()  # Usually 3rd column
            
            symbols = [s.strip() for s in symbols if pd.notna(s)]
            
            with open(cache_file, 'w') as f:
                json.dump(symbols, f)
            
            self.sector_constituents['NIFTY500'] = symbols
            logger.info(f"✓ NIFTY 500: {len(symbols)} stocks")
            
        except Exception as e:
            logger.error(f"Error fetching NIFTY 500: {e}")
    
    async def fetch_stock_ohlc_data(self) -> Dict[str, pd.DataFrame]:
        """
        Fetch 4 years of OHLC data for all stocks in the universe
        
        Returns:
            Dict mapping stock symbols to DataFrames with OHLC data
        """
        logger.info("Fetching OHLC data for all stocks...")
        
        # Get all unique stocks across sectors
        all_stocks = set()
        for sector, stocks in self.sector_constituents.items():
            all_stocks.update(stocks)
        
        logger.info(f"Total unique stocks to download: {len(all_stocks)}")
        
        start_date = Config.DATA_START_DATE
        end_date = Config.DATA_END_DATE
        
        # Download in batches to avoid overwhelming yfinance
        stocks_list = list(all_stocks)
        batch_size = 50
        
        for i in range(0, len(stocks_list), batch_size):
            batch = stocks_list[i:i+batch_size]
            logger.info(f"Downloading batch {i//batch_size + 1}/{(len(stocks_list)-1)//batch_size + 1}...")
            
            for symbol in batch:
                try:
                    # Check cache first
                    cache_file = self.cache_dir / f"{symbol}_ohlc.csv"
                    
                    if cache_file.exists():
                        if (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).days < 1:
                            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                            self.stock_data[symbol] = df
                            continue
                    
                    # Add .NS suffix for NSE stocks
                    ticker = f"{symbol}.NS"
                    
                    data = yf.download(
                        ticker,
                        start=start_date,
                        end=end_date,
                        progress=False,
                        auto_adjust=True
                    )
                    
                    if data.empty:
                        logger.warning(f"No data for {symbol}")
                        continue
                    
                    # Save to cache
                    data.to_csv(cache_file)
                    self.stock_data[symbol] = data
                    
                except Exception as e:
                    logger.error(f"Error downloading {symbol}: {e}")
                    continue
            
            # Rate limiting between batches
            time.sleep(2)
        
        logger.info(f"Stock OHLC data loaded: {len(self.stock_data)} stocks")
        return self.stock_data
    
    async def fetch_fundamental_data(self) -> Dict[str, Dict]:
        """
        Fetch fundamental data for all stocks
        
        Returns:
            Dict mapping stock symbols to fundamental metrics
        """
        logger.info("Fetching fundamental data for all stocks...")
        
        for symbol in self.stock_data.keys():
            try:
                cache_file = self.cache_dir / f"{symbol}_fundamentals.json"
                
                # Check cache (update weekly)
                if cache_file.exists():
                    if (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).days < 7:
                        with open(cache_file, 'r') as f:
                            self.fundamental_data[symbol] = json.load(f)
                        continue
                
                # Fetch from yfinance
                ticker = yf.Ticker(f"{symbol}.NS")
                info = ticker.info
                
                # Extract relevant fundamental metrics
                fundamentals = {
                    # Quality metrics
                    'roe': info.get('returnOnEquity', None),
                    'roce': None,  # Not directly available in yfinance
                    'gross_margin': info.get('grossMargins', None),
                    'operating_margin': info.get('operatingMargins', None),
                    'net_margin': info.get('profitMargins', None),
                    
                    # Growth metrics
                    'eps': info.get('trailingEps', None),
                    'revenue': info.get('totalRevenue', None),
                    'revenue_growth': info.get('revenueGrowth', None),
                    'earnings_growth': info.get('earningsGrowth', None),
                    
                    # Valuation metrics
                    'pe_ratio': info.get('trailingPE', None),
                    'forward_pe': info.get('forwardPE', None),
                    'pb_ratio': info.get('priceToBook', None),
                    'ev_ebitda': info.get('enterpriseToEbitda', None),
                    'price_to_sales': info.get('priceToSalesTrailing12Months', None),
                    
                    # Balance sheet metrics
                    'debt_to_equity': info.get('debtToEquity', None),
                    'current_ratio': info.get('currentRatio', None),
                    'quick_ratio': info.get('quickRatio', None),
                    'total_debt': info.get('totalDebt', None),
                    'total_cash': info.get('totalCash', None),
                    
                    # Other metrics
                    'market_cap': info.get('marketCap', None),
                    'beta': info.get('beta', None),
                    'dividend_yield': info.get('dividendYield', None),
                    'sector': info.get('sector', None),
                    'industry': info.get('industry', None),
                }
                
                # Save to cache
                with open(cache_file, 'w') as f:
                    json.dump(fundamentals, f)
                
                self.fundamental_data[symbol] = fundamentals
                
                time.sleep(0.2)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error fetching fundamentals for {symbol}: {e}")
                continue
        
        logger.info(f"Fundamental data loaded: {len(self.fundamental_data)} stocks")
        return self.fundamental_data
    
    def get_sector_data(self, sector_name: str) -> Optional[pd.DataFrame]:
        """Get OHLC data for a specific sector index"""
        return self.sector_data.get(sector_name)
    
    def get_stock_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get OHLC data for a specific stock"""
        return self.stock_data.get(symbol)
    
    def get_stock_fundamentals(self, symbol: str) -> Optional[Dict]:
        """Get fundamental metrics for a specific stock"""
        return self.fundamental_data.get(symbol)
    
    def get_sector_constituents(self, sector_name: str) -> List[str]:
        """Get list of stocks in a specific sector"""
        return self.sector_constituents.get(sector_name, [])
    
    def get_all_stocks(self) -> List[str]:
        """Get list of all stocks in the universe"""
        return list(self.stock_data.keys())
    
    def calculate_sector_returns(self, period: int = 126) -> pd.Series:
        """
        Calculate returns for all sectors over specified period
        
        Args:
            period: Lookback period in trading days (default 126 = 6 months)
        
        Returns:
            Series with sector returns
        """
        returns = {}
        
        for sector_name, data in self.sector_data.items():
            if len(data) < period:
                logger.warning(f"Insufficient data for {sector_name}")
                continue
            
            try:
                # Calculate total return over period
                end_price = data['Close'].iloc[-1]
                start_price = data['Close'].iloc[-period]
                
                returns[sector_name] = (end_price / start_price) - 1
                
            except Exception as e:
                logger.error(f"Error calculating return for {sector_name}: {e}")
                continue
        
        return pd.Series(returns)
    
    def get_stock_sector_mapping(self) -> Dict[str, str]:
        """
        Create mapping of stocks to their sectors
        
        Returns:
            Dict mapping stock symbols to sector names
        """
        stock_to_sector = {}
        
        for sector, stocks in self.sector_constituents.items():
            for stock in stocks:
                stock_to_sector[stock] = sector
        
        return stock_to_sector
    
    def refresh_data(self, force: bool = False):
        """
        Refresh all data (useful for daily updates)
        
        Args:
            force: If True, ignore cache and force fresh download
        """
        logger.info("Refreshing data...")
        
        if force:
            # Clear cache
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(exist_ok=True)
            logger.info("Cache cleared")
        
        # Reload all data
        import asyncio
        asyncio.run(self.load_all_data())
        
        logger.info("Data refresh complete")


if __name__ == "__main__":
    # Test the data collector
    import asyncio
    
    async def test():
        collector = DataCollector()
        await collector.load_all_data()
        
        print(f"\n✓ Sectors loaded: {len(collector.sector_data)}")
        print(f"✓ Stocks loaded: {len(collector.stock_data)}")
        print(f"✓ Fundamentals loaded: {len(collector.fundamental_data)}")
        
        # Calculate sector returns
        returns = collector.calculate_sector_returns(period=126)
        print(f"\n6-Month Sector Returns:")
        print(returns.sort_values(ascending=False))
    
    asyncio.run(test())
