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
    VERSION = "2.0.0"
    DESCRIPTION = "60% Core Sector Rotation + 40% Satellite Stock Selection"
    
    # Directory Paths
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    LOG_DIR = LOG_DIR
    DATABASE_DIR = DATABASE_DIR
    
    # ==================== DUAL-APPROACH ALLOCATION ====================
    CORE_ALLOCATION = 0.60      # 60% for sector rotation (core)
    SATELLITE_ALLOCATION = 0.40  # 40% for stock selection (satellite)
    
    # ==================== CORE: SECTOR ROTATION (60%) ====================
    CORE_CONFIG = {
        'top_sectors': 3,
        'rebalance_frequency': 'monthly',
        
        'momentum_periods': {
            '1m': {'days': 21, 'weight': 0.25},
            '3m': {'days': 63, 'weight': 0.35},
            '6m': {'days': 126, 'weight': 0.40},
        },
        
        'trend_confirmation': {
            'enabled': False,  # Disabled for testing
            'ma_fast': 50,
            'ma_slow': 200,
            'require_uptrend': False,  # Disabled
            'min_trend_strength': 0.02,
        },
        
        'equal_weight_sectors': True,
        'stocks_per_sector': 5,
    }
    
    # ==================== SATELLITE: STOCK SELECTION (40%) ====================
    SATELLITE_CONFIG = {
        'universe': 'ALL_STOCKS',
        'top_stocks': 15,
        'exclude_core_stocks': False,
        
        'scoring_weights': {
            'fundamental': 0.45,
            'technical': 0.35,
            'statistical': 0.20,
        },
        
        'filters': {
            'min_market_cap': 1000,
            'min_liquidity': 1000000,
            'max_volatility': 0.50,
        }
    }
    
    # ==================== SCORING MODELS ====================
    
    FUNDAMENTAL_METRICS = {
        'pe_ratio': {'weight': 0.25},
        'roe': {'weight': 0.30},
        'debt_to_equity': {'weight': 0.25},
        'current_ratio': {'weight': 0.20}
    }
    
    TECHNICAL_METRICS = {
        'rsi': {'weight': 0.30, 'period': 14},
        'macd': {'weight': 0.35, 'fast': 12, 'slow': 26, 'signal': 9},
        'bollinger_position': {'weight': 0.20, 'period': 20},
        'ma_trend': {'weight': 0.15, 'fast_ma': 50, 'slow_ma': 200}
    }
    
    STATISTICAL_METRICS = {
        'sharpe_ratio': {'weight': 0.40, 'lookback': 252, 'risk_free_rate': 0.06},
        'volatility': {'weight': 0.30, 'lookback': 252},
        'beta': {'weight': 0.30, 'lookback': 252}
    }
    
    # ==================== RISK MANAGEMENT ====================
    
    RISK_CONFIG = {
        'max_position_size': 0.10,
        'max_sector_exposure': 0.30,
        'stop_loss': 0.15,
        'max_portfolio_volatility': 0.20,
    }
    
    # ==================== REBALANCING ====================
    
    REBALANCING_CONFIG = {
        'frequency': 'MONTHLY',
        'day_of_month': 1,
        'drift_threshold': 0.05,
        'min_holding_period': 30,
    }
    
    # ==================== TRANSACTION COSTS ====================
    
    TRANSACTION_COSTS = {
        'commission': 0.0003,
        'slippage': 0.001,
        'market_impact': 0.0005,
        'stt': 0.001,
    }
    
    # ==================== DATA CONFIGURATION ====================
    
    DATA_CONFIG = {
        'source': 'NSE_SCRAPED',
        'database': 'nse_cash.db',
        'start_date': datetime(2021, 10, 1),
        'end_date': datetime.now(),
    }
    
    # ==================== BACKTESTING ====================
    
    BACKTEST_CONFIG = {
        'initial_capital': 1000000,
        'benchmark': 'NIFTY50',
    }
    
    # ==================== PAPER TRADING ====================
    
    PAPER_TRADING = {
        'initial_capital': 1000000,
        'transaction_cost': 0.001,
        'slippage': 0.0005,
        'market_impact': 0.0002
    }
    
    # ==================== LOGGING ====================
    
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"


class NSESectors:
    """NSE Sectoral Indices Configuration"""
    
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
    """Technical Analysis Parameters"""
    
    MOMENTUM_SHORT_PERIOD = 21
    MOMENTUM_LONG_PERIOD = 252
    MOMENTUM_EXCLUDE = 21
    
    SMA_FAST = 50
    SMA_SLOW = 200
    EMA_FAST = 12
    EMA_SLOW = 26
    
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    BOLLINGER_PERIOD = 20
    BOLLINGER_STD = 2


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