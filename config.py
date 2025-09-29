"""
Configuration file for Systematic Sector Rotation Strategy
"""

import os
from pathlib import Path
from datetime import datetime, timedelta

# Base project directory
BASE_DIR = Path(__file__).parent

# Define essential directories
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
DATABASE_DIR = BASE_DIR / "database"

# Create directories if they don't exist
for directory in [DATA_DIR, LOG_DIR, DATABASE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class Config:
    """Main configuration class"""
    
    # Strategy Info
    STRATEGY_NAME = "Systematic Sector Rotation"
    VERSION = "1.0.0"
    
    # Directory Paths
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    LOG_DIR = LOG_DIR
    DATABASE_DIR = DATABASE_DIR
    
    # Portfolio Allocation
    SECTOR_ALLOCATION = 0.60  # 60% for sector rotation
    STOCK_ALLOCATION = 0.40   # 40% for stock selection
    
    # Sector Rotation Settings
    TOP_SECTORS_COUNT = 3     # Top 3 sectors to select
    MOMENTUM_PERIOD = 6       # 6-month momentum calculation
    TIEBREAKER_PERIOD = 1     # 1-month tiebreaker
    MA_FILTER_PERIOD = 200    # 200-day moving average filter
    
    # Stock Selection Settings
    STOCK_UNIVERSE = "NIFTY500"
    TOP_PERCENTILE = 0.10     # Top 10% stocks (top decile)
    HYSTERESIS_PERIOD = 2     # 2-month hysteresis for exits
    
    # Scoring Weights
    FUNDAMENTAL_WEIGHT = 0.40 # 40% fundamental score
    TECHNICAL_WEIGHT = 0.35   # 35% technical score  
    STATISTICAL_WEIGHT = 0.25 # 25% statistical score
    
    # Risk Management
    MAX_POSITION_SIZE = 0.05  # Maximum 5% per position
    MAX_SECTOR_EXPOSURE = 0.25 # Maximum 25% per sector
    BETA_THRESHOLD = 0.3      # Beta penalty threshold
    VOLATILITY_MULTIPLIER = 1.5 # Volatility penalty multiplier
    
    # Rebalancing
    REBALANCING_FREQUENCY = "MONTHLY"
    REBALANCING_DAY = 1       # 1st day of month
    REBALANCING_TIME = "09:30" # 9:30 AM IST
    
    # Data Configuration
    DATA_START_DATE = datetime.now() - timedelta(days=5*365)  # 5 years
    DATA_END_DATE = datetime.now()
    
    # Data Sources (Open Source)
    DATA_SOURCES = {
        'stock_prices': 'yfinance',
        'fundamentals': 'yfinance_info',
        'sectors': 'yfinance_sectors',
        'backup': 'web_scraping'
    }
    
    # Paper Trading Configuration
    PAPER_TRADING = {
        'initial_capital': 1000000,  # 10 Lakh initial capital
        'transaction_cost': 0.001,   # 0.1% transaction cost
        'slippage': 0.0005,         # 0.05% slippage
        'market_impact': 0.0002     # 0.02% market impact
    }
    
    # Logging Configuration
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"


class NSESectors:
    """NSE Sectoral Indices Configuration"""
    
    # Yahoo Finance tickers for NSE sectoral indices
    SECTOR_TICKERS = {
        'Nifty Auto': '^CNXAUTO',
        'Nifty Bank': '^NSEBANK',
        'Nifty Energy': '^CNXENERGY', 
        'Nifty Financial Services': '^CNXFINANCE',
        'Nifty FMCG': '^CNXFMCG',
        'Nifty IT': '^CNXIT',
        'Nifty Media': '^CNXMEDIA',
        'Nifty Metal': '^CNXMETAL',
        'Nifty Pharma': '^CNXPHARMA',
        'Nifty PSU Bank': '^CNXPSUBANK',
        'Nifty Realty': '^CNXREALTY',
        'Nifty Commodities': '^CNXCOMMODITIES',
        'Nifty Consumption': '^CNXCONSUMPTION',
        'Nifty CPSE': '^CNXCPSE',
        'Nifty Infrastructure': '^CNXINFRA',
        'Nifty MNC': '^CNXMNC',
        'Nifty PSE': '^CNXPSE'
    }
    
    # Sector constituent URLs (for stock selection)
    CONSTITUENT_URLS = {
        'Nifty Auto': 'https://www.niftyindices.com/IndexConstituent/ind_niftyautolist.csv',
        'Nifty Bank': 'https://www.niftyindices.com/IndexConstituent/ind_niftybanklist.csv',
        'Nifty Energy': 'https://www.niftyindices.com/IndexConstituent/ind_niftyenergylist.csv',
        'Nifty Financial Services': 'https://www.niftyindices.com/IndexConstituent/ind_niftyfinancelist.csv',
        'Nifty FMCG': 'https://www.niftyindices.com/IndexConstituent/ind_niftyfmcglist.csv',
        'Nifty IT': 'https://www.niftyindices.com/IndexConstituent/ind_niftyitlist.csv',
        'Nifty Media': 'https://www.niftyindices.com/IndexConstituent/ind_niftymedialist.csv',
        'Nifty Metal': 'https://www.niftyindices.com/IndexConstituent/ind_niftymetallist.csv',
        'Nifty Pharma': 'https://www.niftyindices.com/IndexConstituent/ind_niftypharmalist.csv',
        'Nifty PSU Bank': 'https://www.niftyindices.com/IndexConstituent/ind_niftypsubanklist.csv',
        'Nifty Realty': 'https://www.niftyindices.com/IndexConstituent/ind_niftyrealtylist.csv'
    }


class TechnicalIndicators:
    """Technical Analysis Parameters"""
    
    # Momentum Parameters
    MOMENTUM_SHORT_PERIOD = 21    # 1 month
    MOMENTUM_LONG_PERIOD = 252    # 1 year  
    MOMENTUM_EXCLUDE = 21         # Exclude last 1 month
    
    # Moving Averages
    SMA_FAST = 50                 # 50-day SMA
    SMA_SLOW = 200                # 200-day SMA
    EMA_FAST = 12                 # 12-day EMA
    EMA_SLOW = 26                 # 26-day EMA
    
    # Oscillators
    RSI_PERIOD = 14               # 14-day RSI
    RSI_OVERSOLD = 30            # RSI oversold level
    RSI_OVERBOUGHT = 70          # RSI overbought level
    
    # Other Indicators
    MACD_FAST = 12               # MACD fast period
    MACD_SLOW = 26               # MACD slow period  
    MACD_SIGNAL = 9              # MACD signal period
    BOLLINGER_PERIOD = 20        # Bollinger Band period
    BOLLINGER_STD = 2            # Bollinger Band standard deviations


# Environment Variables with defaults
ENV_VARS = {
    'DB_HOST': 'localhost',
    'DB_PORT': '5432',
    'DB_NAME': 'sector_rotation',
    'DB_USER': 'postgres', 
    'DB_PASSWORD': 'password',
    'LOG_LEVEL': 'INFO'
}

# Set environment variables if not already set
for key, default_value in ENV_VARS.items():
    os.environ.setdefault(key, str(default_value))

print(f"Configuration loaded: {Config.STRATEGY_NAME} v{Config.VERSION}")
