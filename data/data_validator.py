"""
Data Validation Module for Systematic Sector Rotation Strategy

This module handles:
1. OHLC data completeness validation
2. Missing value detection and handling
3. Corporate action detection (splits, bonuses)
4. Data quality checks
5. Outlier detection
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings

from config import Config
from utils.logger import setup_logger
from utils.helpers import validate_dataframe

logger = setup_logger(__name__)


class DataValidator:
    """
    Validates market data for quality and completeness
    """
    
    def __init__(self):
        self.config = Config()
        self.validation_results = {}
        
        logger.info("DataValidator initialized")
    
    def validate_ohlc_data(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Validate OHLC data for a stock or index
        
        Args:
            df: DataFrame with OHLC data
            symbol: Stock/index symbol
        
        Returns:
            Dict with validation results
        """
        results = {
            'symbol': symbol,
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'metrics': {}
        }
        
        # Check if DataFrame is empty
        if df.empty:
            results['is_valid'] = False
            results['errors'].append("DataFrame is empty")
            return results
        
        # Check required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            results['is_valid'] = False
            results['errors'].append(f"Missing columns: {missing_cols}")
            return results
        
        # Check for null values
        null_counts = df[required_cols].isnull().sum()
        if null_counts.any():
            results['warnings'].append(f"Null values found: {null_counts[null_counts > 0].to_dict()}")
        
        # Validate OHLC relationships (High >= Low, Close between High and Low)
        invalid_hl = (df['High'] < df['Low']).sum()
        if invalid_hl > 0:
            results['warnings'].append(f"{invalid_hl} days with High < Low")
        
        invalid_close = ((df['Close'] > df['High']) | (df['Close'] < df['Low'])).sum()
        if invalid_close > 0:
            results['warnings'].append(f"{invalid_close} days with Close outside High-Low range")
        
        # Check for zero or negative values
        zero_volume = (df['Volume'] <= 0).sum()
        if zero_volume > 0:
            results['warnings'].append(f"{zero_volume} days with zero/negative volume")
        
        zero_prices = ((df['Close'] <= 0) | (df['Open'] <= 0)).sum()
        if zero_prices > 0:
            results['errors'].append(f"{zero_prices} days with zero/negative prices")
            results['is_valid'] = False
        
        # Check data continuity (gaps)
        date_gaps = self._check_date_gaps(df)
        if date_gaps:
            results['warnings'].append(f"Found {len(date_gaps)} gaps in data > 5 days")
        
        # Detect potential stock splits
        splits = self._detect_stock_splits(df)
        if splits:
            results['warnings'].append(f"Potential stock splits detected: {splits}")
        
        # Calculate metrics
        results['metrics'] = {
            'total_days': len(df),
            'date_range': f"{df.index[0]} to {df.index[-1]}",
            'null_percentage': (df[required_cols].isnull().sum().sum() / (len(df) * len(required_cols))) * 100,
            'avg_volume': df['Volume'].mean(),
            'price_range': f"₹{df['Close'].min():.2f} - ₹{df['Close'].max():.2f}"
        }
        
        self.validation_results[symbol] = results
        return results
    
    def _check_date_gaps(self, df: pd.DataFrame, max_gap_days: int = 5) -> List[Tuple]:
        """
        Check for gaps in time series data
        
        Args:
            df: DataFrame with datetime index
            max_gap_days: Maximum acceptable gap in trading days
        
        Returns:
            List of tuples (start_date, end_date, gap_days)
        """
        gaps = []
        
        if len(df) < 2:
            return gaps
        
        # Calculate differences between consecutive dates
        date_diffs = df.index.to_series().diff()
        
        # Find gaps larger than threshold (accounting for weekends)
        for i, diff in enumerate(date_diffs):
            if pd.notna(diff) and diff.days > max_gap_days:
                gaps.append((
                    df.index[i-1].strftime('%Y-%m-%d'),
                    df.index[i].strftime('%Y-%m-%d'),
                    diff.days
                ))
        
        return gaps
    
    def _detect_stock_splits(self, df: pd.DataFrame, threshold: float = 0.3) -> List[str]:
        """
        Detect potential stock splits based on large price jumps
        
        Args:
            df: DataFrame with OHLC data
            threshold: Minimum price change ratio to flag as potential split
        
        Returns:
            List of dates where splits may have occurred
        """
        splits = []
        
        if len(df) < 2:
            return splits
        
        # Calculate day-to-day price changes
        price_changes = df['Close'].pct_change().abs()
        
        # Flag large changes that might indicate splits
        potential_splits = price_changes[price_changes > threshold]
        
        for date, change in potential_splits.items():
            splits.append(f"{date.strftime('%Y-%m-%d')} ({change*100:.1f}% change)")
        
        return splits
    
    def detect_outliers(self, df: pd.DataFrame, column: str = 'Close', 
                       method: str = 'iqr', multiplier: float = 3.0) -> pd.Series:
        """
        Detect outliers in data using IQR or Z-score method
        
        Args:
            df: DataFrame with data
            column: Column to check for outliers
            method: 'iqr' or 'zscore'
            multiplier: Multiplier for IQR or Z-score threshold
        
        Returns:
            Boolean Series indicating outliers
        """
        if column not in df.columns:
            logger.warning(f"Column {column} not found")
            return pd.Series(False, index=df.index)
        
        if method == 'iqr':
            # Interquartile Range method
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - multiplier * IQR
            upper_bound = Q3 + multiplier * IQR
            
            outliers = (df[column] < lower_bound) | (df[column] > upper_bound)
            
        elif method == 'zscore':
            # Z-score method
            mean = df[column].mean()
            std = df[column].std()
            
            z_scores = np.abs((df[column] - mean) / std)
            outliers = z_scores > multiplier
            
        else:
            logger.error(f"Unknown outlier detection method: {method}")
            return pd.Series(False, index=df.index)
        
        return outliers
    
    def handle_missing_values(self, df: pd.DataFrame, method: str = 'forward_fill') -> pd.DataFrame:
        """
        Handle missing values in OHLC data
        
        Args:
            df: DataFrame with potential missing values
            method: Method to handle missing data ('forward_fill', 'interpolate', 'drop')
        
        Returns:
            DataFrame with missing values handled
        """
        df_clean = df.copy()
        
        if method == 'forward_fill':
            # Forward fill then backward fill for any remaining NaN
            df_clean = df_clean.fillna(method='ffill').fillna(method='bfill')
            
        elif method == 'interpolate':
            # Linear interpolation
            df_clean = df_clean.interpolate(method='linear', limit_direction='both')
            
        elif method == 'drop':
            # Drop rows with any missing values
            df_clean = df_clean.dropna()
            
        else:
            logger.error(f"Unknown missing value handling method: {method}")
        
        return df_clean
    
    def validate_fundamental_data(self, fundamentals: Dict, symbol: str) -> Dict:
        """
        Validate fundamental data for a stock
        
        Args:
            fundamentals: Dict with fundamental metrics
            symbol: Stock symbol
        
        Returns:
            Dict with validation results
        """
        results = {
            'symbol': symbol,
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'metrics': {}
        }
        
        # Check if fundamentals dict is empty
        if not fundamentals:
            results['is_valid'] = False
            results['errors'].append("No fundamental data available")
            return results
        
        # Count available metrics
        available_metrics = sum(1 for v in fundamentals.values() if v is not None)
        total_metrics = len(fundamentals)
        
        results['metrics']['data_completeness'] = f"{available_metrics}/{total_metrics} ({available_metrics/total_metrics*100:.1f}%)"
        
        # Check for critical metrics
        critical_metrics = ['market_cap', 'pe_ratio', 'roe', 'debt_to_equity']
        missing_critical = [m for m in critical_metrics if fundamentals.get(m) is None]
        
        if missing_critical:
            results['warnings'].append(f"Missing critical metrics: {missing_critical}")
        
        # Validate metric ranges
        if fundamentals.get('roe') is not None:
            if fundamentals['roe'] < -1 or fundamentals['roe'] > 5:
                results['warnings'].append(f"Unusual ROE value: {fundamentals['roe']}")
        
        if fundamentals.get('pe_ratio') is not None:
            if fundamentals['pe_ratio'] < 0 or fundamentals['pe_ratio'] > 500:
                results['warnings'].append(f"Unusual P/E ratio: {fundamentals['pe_ratio']}")
        
        if fundamentals.get('debt_to_equity') is not None:
            if fundamentals['debt_to_equity'] < 0:
                results['warnings'].append(f"Negative debt-to-equity: {fundamentals['debt_to_equity']}")
        
        return results
    
    def validate_data_completeness(self, data_dict: Dict[str, pd.DataFrame], 
                                   min_days: int = 504) -> Dict:
        """
        Validate that all stocks have sufficient data
        
        Args:
            data_dict: Dict mapping symbols to DataFrames
            min_days: Minimum required trading days (default 504 = 2 years)
        
        Returns:
            Dict with validation summary
        """
        results = {
            'total_stocks': len(data_dict),
            'valid_stocks': 0,
            'insufficient_data': [],
            'empty_data': []
        }
        
        for symbol, df in data_dict.items():
            if df.empty:
                results['empty_data'].append(symbol)
            elif len(df) < min_days:
                results['insufficient_data'].append({
                    'symbol': symbol,
                    'days': len(df),
                    'required': min_days
                })
            else:
                results['valid_stocks'] += 1
        
        logger.info(f"Data completeness: {results['valid_stocks']}/{results['total_stocks']} stocks valid")
        
        return results
    
    def check_data_freshness(self, df: pd.DataFrame, max_age_days: int = 7) -> bool:
        """
        Check if data is recent enough
        
        Args:
            df: DataFrame with datetime index
            max_age_days: Maximum acceptable age of latest data point
        
        Returns:
            True if data is fresh, False otherwise
        """
        if df.empty:
            return False
        
        latest_date = df.index[-1]
        age_days = (datetime.now() - latest_date).days
        
        if age_days > max_age_days:
            logger.warning(f"Data is {age_days} days old (max: {max_age_days})")
            return False
        
        return True
    
    def validate_returns(self, df: pd.DataFrame, max_daily_return: float = 0.20) -> Dict:
        """
        Validate that returns are within reasonable bounds
        
        Args:
            df: DataFrame with OHLC data
            max_daily_return: Maximum acceptable daily return (default 20%)
        
        Returns:
            Dict with validation results
        """
        results = {
            'is_valid': True,
            'extreme_returns': [],
            'metrics': {}
        }
        
        # Calculate daily returns
        returns = df['Close'].pct_change().dropna()
        
        # Find extreme returns
        extreme_returns = returns[returns.abs() > max_daily_return]
        
        if len(extreme_returns) > 0:
            results['extreme_returns'] = [
                {
                    'date': date.strftime('%Y-%m-%d'),
                    'return': f"{ret*100:.2f}%"
                }
                for date, ret in extreme_returns.items()
            ]
        
        # Calculate return metrics
        results['metrics'] = {
            'mean_return': returns.mean(),
            'std_return': returns.std(),
            'min_return': returns.min(),
            'max_return': returns.max(),
            'extreme_count': len(extreme_returns)
        }
        
        return results
    
    def generate_validation_report(self, symbol: str) -> str:
        """
        Generate a text report of validation results
        
        Args:
            symbol: Stock/index symbol
        
        Returns:
            Formatted validation report
        """
        if symbol not in self.validation_results:
            return f"No validation results found for {symbol}"
        
        results = self.validation_results[symbol]
        
        report = f"\n{'='*60}\n"
        report += f"VALIDATION REPORT: {symbol}\n"
        report += f"{'='*60}\n\n"
        
        report += f"Status: {'✓ VALID' if results['is_valid'] else '✗ INVALID'}\n\n"
        
        if results['errors']:
            report += "ERRORS:\n"
            for error in results['errors']:
                report += f"  ✗ {error}\n"
            report += "\n"
        
        if results['warnings']:
            report += "WARNINGS:\n"
            for warning in results['warnings']:
                report += f"  ⚠ {warning}\n"
            report += "\n"
        
        if results['metrics']:
            report += "METRICS:\n"
            for key, value in results['metrics'].items():
                report += f"  • {key}: {value}\n"
        
        report += f"\n{'='*60}\n"
        
        return report
    
    def batch_validate(self, data_dict: Dict[str, pd.DataFrame]) -> Dict:
        """
        Validate multiple stocks/indices at once
        
        Args:
            data_dict: Dict mapping symbols to DataFrames
        
        Returns:
            Summary of validation results
        """
        logger.info(f"Batch validating {len(data_dict)} instruments...")
        
        summary = {
            'total': len(data_dict),
            'valid': 0,
            'invalid': 0,
            'warnings': 0,
            'invalid_symbols': []
        }
        
        for symbol, df in data_dict.items():
            results = self.validate_ohlc_data(df, symbol)
            
            if results['is_valid']:
                summary['valid'] += 1
            else:
                summary['invalid'] += 1
                summary['invalid_symbols'].append(symbol)
            
            if results['warnings']:
                summary['warnings'] += len(results['warnings'])
        
        logger.info(f"Validation complete: {summary['valid']}/{summary['total']} valid")
        
        return summary


if __name__ == "__main__":
    # Test the validator
    validator = DataValidator()
    
    # Create sample data
    dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='B')
    sample_data = pd.DataFrame({
        'Open': np.random.uniform(100, 200, len(dates)),
        'High': np.random.uniform(150, 250, len(dates)),
        'Low': np.random.uniform(50, 150, len(dates)),
        'Close': np.random.uniform(100, 200, len(dates)),
        'Volume': np.random.uniform(1000000, 10000000, len(dates))
    }, index=dates)
    
    # Validate
    results = validator.validate_ohlc_data(sample_data, 'TEST')
    print(validator.generate_validation_report('TEST'))
