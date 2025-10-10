"""
Helper functions and utilities for the systematic sector rotation strategy
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union

def validate_date_range(start_date: str, end_date: str) -> bool:
    """Validate date range inputs"""
    try:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        return start < end and end <= datetime.now()
    except:
        return False

def calculate_returns(prices: pd.Series) -> pd.Series:
    """Calculate percentage returns from price series"""
    return prices.pct_change().dropna()

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.06) -> float:
    """
    Calculate annualized Sharpe ratio
    
    DEPRECATED: This function uses geometric mean of daily returns.
    For production use, prefer PerformanceAnalyzer._calculate_risk_metrics()
    which uses actual CAGR for consistency.
    
    This function is kept for backward compatibility and simple calculations.
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    
    excess_returns = returns - (risk_free_rate / 252)
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

def calculate_cagr(initial_value: float, final_value: float, years: float) -> float:
    """Calculate Compound Annual Growth Rate (CAGR)"""
    if initial_value <= 0 or final_value <= 0 or years <= 0:
        return 0.0
    
    try:
        cagr = ((final_value / initial_value) ** (1 / years) - 1) * 100
        return cagr
    except (ValueError, ZeroDivisionError):
        return 0.0

def calculate_max_drawdown(prices: pd.Series) -> float:
    """Calculate maximum drawdown from price series"""
    if len(prices) == 0:
        return 0.0
    
    returns = calculate_returns(prices)
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.expanding().max()
    drawdown = (cumulative - rolling_max) / rolling_max
    return drawdown.min()

def calculate_volatility(returns: pd.Series, annualize: bool = True) -> float:
    """Calculate volatility (standard deviation) of returns"""
    if len(returns) == 0:
        return 0.0
    
    vol = returns.std()
    if annualize:
        vol = vol * np.sqrt(252)
    
    return vol

def z_score_normalize(series: pd.Series) -> pd.Series:
    """Z-score normalization of a series"""
    if series.std() == 0:
        return pd.Series(0, index=series.index)
    
    return (series - series.mean()) / series.std()

def percentile_rank(series: pd.Series, ascending: bool = True) -> pd.Series:
    """Calculate percentile rank of each value in series"""
    return series.rank(ascending=ascending, pct=True)

def format_currency(amount: float, currency: str = "₹") -> str:
    """Format currency with Indian formatting"""
    return f"{currency}{amount:,.0f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage with specified decimals"""
    return f"{value * 100:.{decimals}f}%"

def get_trading_days_between(start_date: str, end_date: str) -> int:
    """Get number of trading days between two dates"""
    try:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        date_range = pd.date_range(start=start, end=end, freq='D')
        trading_days = date_range[date_range.weekday < 5]
        
        return len(trading_days)
    except:
        return 0

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default value for zero denominator"""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default

def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> Dict[str, Any]:
    """Validate DataFrame has required columns and data"""
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': []
    }
    
    if df.empty:
        validation_result['is_valid'] = False
        validation_result['errors'].append("DataFrame is empty")
        return validation_result
    
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        validation_result['is_valid'] = False
        validation_result['errors'].append(f"Missing columns: {missing_columns}")
    
    if required_columns:
        null_counts = df[required_columns].isnull().sum()
        if null_counts.any():
            validation_result['warnings'].append(f"Null values found: {null_counts[null_counts > 0].to_dict()}")
    
    return validation_result

def calculate_momentum(prices: pd.Series, period: int = 252, exclude_recent: int = 21) -> float:
    """Calculate momentum (total return over period excluding recent days)"""
    if len(prices) < period:
        return 0.0
    
    try:
        end_price = prices.iloc[-(exclude_recent + 1)]
        start_price = prices.iloc[-(period + exclude_recent + 1)]
        
        momentum = (end_price / start_price) - 1
        return momentum
    except (IndexError, ZeroDivisionError):
        return 0.0

def calculate_moving_average(prices: pd.Series, period: int) -> pd.Series:
    """Calculate simple moving average"""
    return prices.rolling(window=period, min_periods=1).mean()

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI)"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_beta(stock_returns: pd.Series, market_returns: pd.Series) -> float:
    """Calculate beta of stock relative to market"""
    if len(stock_returns) == 0 or len(market_returns) == 0:
        return 1.0
    
    try:
        aligned_data = pd.concat([stock_returns, market_returns], axis=1).dropna()
        if len(aligned_data) < 10:
            return 1.0
        
        stock_aligned = aligned_data.iloc[:, 0]
        market_aligned = aligned_data.iloc[:, 1]
        
        covariance = np.cov(stock_aligned, market_aligned)[0][1]
        market_variance = np.var(market_aligned)
        
        if market_variance == 0:
            return 1.0
        
        beta = covariance / market_variance
        return beta
    except:
        return 1.0

def winsorize_series(series: pd.Series, lower_percentile: float = 0.05, upper_percentile: float = 0.95) -> pd.Series:
    """Winsorize a series by capping extreme values"""
    lower_bound = series.quantile(lower_percentile)
    upper_bound = series.quantile(upper_percentile)
    
    return series.clip(lower=lower_bound, upper=upper_bound)

def calculate_information_ratio(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Calculate Information Ratio"""
    if len(portfolio_returns) == 0 or len(benchmark_returns) == 0:
        return 0.0
    
    try:
        aligned_data = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
        if len(aligned_data) < 10:
            return 0.0
        
        portfolio_aligned = aligned_data.iloc[:, 0]
        benchmark_aligned = aligned_data.iloc[:, 1]
        
        active_returns = portfolio_aligned - benchmark_aligned
        
        if active_returns.std() == 0:
            return 0.0
        
        info_ratio = np.sqrt(252) * active_returns.mean() / active_returns.std()
        return info_ratio
    except:
        return 0.0

def create_date_range(start_date: str, end_date: str, freq: str = 'D') -> List[str]:
    """Create a list of dates between start and end date"""
    try:
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
        return [date.strftime('%Y-%m-%d') for date in date_range]
    except:
        return []

def calculate_macd(prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, pd.Series]:
    """Calculate MACD"""
    ema_fast = prices.ewm(span=fast_period).mean()
    ema_slow = prices.ewm(span=slow_period).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period).mean()
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }

def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
    """Calculate Bollinger Bands"""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    return {
        'upper': upper_band,
        'middle': sma,
        'lower': lower_band
    }

print("Helper functions loaded successfully")
