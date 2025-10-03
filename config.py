"""
Configuration file for Systematic Sector Rotation Strategy
CLIENT SPECIFICATION: 60/40 Dual-Approach Strategy
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
    STRATEGY_NAME = "Systematic Sector Rotation - Dual Approach"
    VERSION = "1.0.0"
    DESCRIPTION = "60% Core Sector Rotation + 40% Satellite Stock Selection"
    
    # Directory Paths
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    LOG_DIR = LOG_DIR
    DATABASE_DIR = DATABASE_DIR
    
    # ==================== IMPLEMENTATION CHOICE ====================
    # CLIENT SPECIFICATION: Choose between ETF or Individual Stock implementation
    
    IMPLEMENTATION_MODE = 'INDIVIDUAL_STOCKS'  # Options: 'SECTOR_ETFS' or 'INDIVIDUAL_STOCKS'
    
    # ETF Implementation Settings (if IMPLEMENTATION_MODE = 'SECTOR_ETFS')
    ETF_CONFIG = {
        'enabled': False,
        'etf_universe': 'NSE_SECTOR_ETFS',  # Use NSE sector ETFs
        'advantages': [
            'Immediate sector exposure',
            'Lower tracking error', 
            'Reduced transaction costs',
            'Simplified portfolio management'
        ]
    }
    
    # Individual Stocks Implementation (if IMPLEMENTATION_MODE = 'INDIVIDUAL_STOCKS')
    INDIVIDUAL_STOCKS_CONFIG = {
        'enabled': True,
        'advantages': [
            'Enhanced alpha potential',
            'Greater portfolio customization',
            'Factor exposure control',
            'Pure equity implementation'
        ]
    }
    
    # ==================== DUAL-APPROACH ALLOCATION ====================
    # CLIENT SPECIFICATION: 60/40 Split
    CORE_ALLOCATION = 0.60      # 60% for sector rotation (core)
    SATELLITE_ALLOCATION = 0.40  # 40% for stock selection (satellite)
    
    # ==================== CORE: SECTOR ROTATION (60%) ====================
    # Monthly rebalanced top-K sectors based on 6-month momentum with trend confirmation
    
    CORE_CONFIG = {
        'top_sectors': 3,                # Top K sectors to invest in
        'rebalance_frequency': 'monthly',
        
        # Momentum Calculation (6-month focus)
        'momentum_periods': {
            '1m': {'days': 21, 'weight': 0.25},   # 1-month momentum (25%)
            '3m': {'days': 63, 'weight': 0.35},   # 3-month momentum (35%)
            '6m': {'days': 126, 'weight': 0.40},  # 6-month momentum (40%) - PRIMARY
        },
        
        # Trend Confirmation Filters
        'trend_confirmation': {
            'enabled': True,
            'ma_fast': 50,                # 50-day MA
            'ma_slow': 200,               # 200-day MA
            'require_uptrend': True,      # Only select sectors in uptrend
            'min_trend_strength': 0.02,   # Minimum 2% above MA for confirmation
        },
        
        # Sector Allocation (within 60%)
        'equal_weight_sectors': True,     # Equal weight across top K sectors
        'stocks_per_sector': 5,           # Number of stocks per selected sector
    }
    
    # ==================== SATELLITE: STOCK SELECTION (40%) ====================
    # Multi-factor scoring model combining fundamental, technical, and statistical metrics
    
    SATELLITE_CONFIG = {
        'universe': 'ALL_STOCKS',         # Select from entire universe
        'top_stocks': 15,                 # Number of stocks to select
        'exclude_core_stocks': False,     # Can overlap with core holdings
        
        # Multi-Factor Scoring Weights
        'scoring_weights': {
            'fundamental': 0.35,          # 35% fundamental metrics
            'technical': 0.40,            # 40% technical metrics
            'statistical': 0.25,          # 25% statistical metrics
        },
        
        # Stock Filters
        'filters': {
            'min_market_cap': 1000,       # Minimum 1000 Cr market cap
            'min_liquidity': 1000000,     # Minimum daily volume
            'max_volatility': 0.50,       # Maximum 50% annualized volatility
        }
    }
    
    # ==================== SCORING MODELS ====================
    
    # Fundamental Scoring
    FUNDAMENTAL_METRICS = {
        'pe_ratio': {
            'weight': 0.25,
            'lower_better': True,
            'threshold_good': 15,
            'threshold_bad': 40
        },
        'roe': {
            'weight': 0.30,
            'lower_better': False,
            'threshold_good': 0.15,
            'threshold_bad': 0.05
        },
        'debt_to_equity': {
            'weight': 0.25,
            'lower_better': True,
            'threshold_good': 0.5,
            'threshold_bad': 2.0
        },
        'current_ratio': {
            'weight': 0.20,
            'lower_better': False,
            'threshold_good': 1.5,
            'threshold_bad': 0.8
        }
    }
    
    # Technical Scoring
    TECHNICAL_METRICS = {
        'rsi': {
            'weight': 0.30,
            'period': 14,
            'optimal_range': (40, 70)
        },
        'macd': {
            'weight': 0.35,
            'fast': 12,
            'slow': 26,
            'signal': 9
        },
        'bollinger_position': {
            'weight': 0.20,
            'period': 20,
            'std_dev': 2
        },
        'ma_trend': {
            'weight': 0.15,
            'fast_ma': 50,
            'slow_ma': 200
        }
    }
    
    # Statistical Scoring
    STATISTICAL_METRICS = {
        'sharpe_ratio': {
            'weight': 0.40,
            'lookback': 252,
            'risk_free_rate': 0.06
        },
        'volatility': {
            'weight': 0.30,
            'lookback': 252,
            'lower_better': True
        },
        'beta': {
            'weight': 0.30,
            'lookback': 252,
            'benchmark': 'NIFTY50'
        }
    }
    
    # ==================== RISK MANAGEMENT ====================
    
    RISK_CONFIG = {
        # Position Sizing
        'max_position_size': 0.10,        # Max 10% per stock
        'min_position_size': 0.02,        # Min 2% per stock
        
        # Sector Limits
        'max_sector_exposure': 0.30,      # Max 30% per sector
        
        # Stop Loss / Take Profit
        'stop_loss': 0.15,                # 15% stop loss
        'take_profit': 0.30,              # 30% take profit
        'trailing_stop': 0.10,            # 10% trailing stop
        
        # Volatility Control
        'max_portfolio_volatility': 0.20,  # 20% max portfolio vol
        'volatility_target': 0.15,         # 15% target volatility
    }
    
    # ==================== REBALANCING ====================
    
    REBALANCING_CONFIG = {
        'frequency': 'MONTHLY',           # Monthly rebalancing
        'day_of_month': 1,                # First trading day of month
        'time': '09:30',                  # 9:30 AM IST
        
        # Rebalancing Triggers
        'drift_threshold': 0.05,          # Rebalance if drift > 5%
        'min_holding_period': 30,         # Minimum 30 days holding
        
        # Transaction Settings
        'batch_orders': True,             # Batch orders for efficiency
        'partial_rebalance': True,        # Allow partial rebalancing
    }
    
    # ==================== TRANSACTION COSTS ====================
    
    TRANSACTION_COSTS = {
        'commission': 0.0003,             # 0.03% brokerage
        'slippage': 0.001,                # 0.1% slippage
        'market_impact': 0.0005,          # 0.05% market impact
        'stt': 0.001,                     # 0.1% STT (Securities Transaction Tax)
    }
    
    # ==================== DATA CONFIGURATION ====================
    
    DATA_CONFIG = {
        'source': 'NSE_SCRAPED',          # Use scraped NSE data
        'database': 'nse_cash.db',        # SQLite database
        'start_date': datetime(2021, 10, 1),
        'end_date': datetime.now(),
        
        # Fallback sources
        'fallback_sources': ['yfinance', 'web_scraping']
    }
    
    # ==================== BACKTESTING ====================
    
    BACKTEST_CONFIG = {
        'initial_capital': 1000000,       # 10 Lakh initial capital
        'benchmark': 'NIFTY50',           # Compare against Nifty 50
        
        # Metrics to Calculate
        'calculate_metrics': [
            'total_return',
            'cagr',
            'sharpe_ratio',
            'sortino_ratio',
            'max_drawdown',
            'win_rate',
            'profit_factor'
        ]
    }
    
    # ==================== LOGGING ====================
    
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"


class NSESectors:
    """NSE Sectoral Indices Configuration"""
    
    # Available sectors for rotation (dynamically fetched from database)
    AVAILABLE_SECTORS = [
        'Nifty Auto',
        'Nifty Bank',
        'Nifty Energy',
        'Nifty Financial Services',
        'Nifty FMCG',
        'Nifty IT',
        'Nifty Media',
        'Nifty Metal',
        'Nifty Pharma',
        'Nifty Realty',
        'Nifty Commodities',
        'Nifty Consumption',
        'Nifty Infrastructure',
        'Nifty Healthcare'
    ]


class TechnicalIndicators:
    """Technical Analysis Parameters (for backward compatibility)"""
    
    # Momentum Parameters
    MOMENTUM_SHORT_PERIOD = 21
    MOMENTUM_LONG_PERIOD = 252
    MOMENTUM_EXCLUDE = 21
    
    # Moving Averages
    SMA_FAST = 50
    SMA_SLOW = 200
    EMA_FAST = 12
    EMA_SLOW = 26
    
    # Oscillators
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    
    # Other Indicators
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    BOLLINGER_PERIOD = 20
    BOLLINGER_STD = 2


class NSESectors:
    """NSE Sectoral Indices Configuration"""
    
    # Available sectors for rotation (dynamically fetched from database)
    AVAILABLE_SECTORS = [
        'Nifty Auto',
        'Nifty Bank',
        'Nifty Energy',
        'Nifty Financial Services',
        'Nifty FMCG',
        'Nifty IT',
        'Nifty Media',
        'Nifty Metal',
        'Nifty Pharma',
        'Nifty Realty',
        'Nifty Commodities',
        'Nifty Consumption',
        'Nifty Infrastructure',
        'Nifty Healthcare'
    ]


# Environment Variables
ENV_VARS = {
    'DB_PATH': str(BASE_DIR / 'NSE_sector_wise_data' / 'nse_cash.db'),
    'LOG_LEVEL': 'INFO'
}

for key, default_value in ENV_VARS.items():
    os.environ.setdefault(key, str(default_value))

print(f"Configuration loaded: {Config.STRATEGY_NAME} v{Config.VERSION}")
print(f"Strategy: {Config.DESCRIPTION}")
print(f"Core Allocation: {Config.CORE_ALLOCATION*100:.0f}% | Satellite Allocation: {Config.SATELLITE_ALLOCATION*100:.0f}%")
