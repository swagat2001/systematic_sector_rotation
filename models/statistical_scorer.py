"""
Statistical Risk Scoring Model for Systematic Sector Rotation Strategy

Implements the statistical scoring component with 20% weight in final score:
- Sharpe Ratio Assessment: 6-12 month calculation using excess returns over T-bill rates
- Beta Penalty Framework: Penalty applied when |β_i - 1| > 0.3
- Volatility Control: Penalty for stocks with σ_i/σ_NIFTY > 1.5

Formula: S_i = Sharpe_{6-12m} - 0.5*|β_i - 1| - 0.3*max(0, σ_i/σ_NIFTY - 1.5)

This component focuses on risk-adjusted performance metrics and portfolio-level
risk management considerations crucial for institutional implementations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from config import Config
from utils.logger import setup_logger
from utils.helpers import (
    calculate_sharpe_ratio,
    calculate_beta,
    calculate_volatility,
    calculate_returns,
    safe_divide
)

logger = setup_logger(__name__)


class StatisticalScorer:
    """
    Calculates statistical risk scores for stocks based on risk-adjusted returns,
    beta, and volatility characteristics
    """
    
    def __init__(self, risk_free_rate: float = 0.06):
        """
        Initialize Statistical Scorer
        
        Args:
            risk_free_rate: Annual risk-free rate (default 6% for India)
        """
        self.config = Config()
        self.risk_free_rate = risk_free_rate
        
        # Penalty coefficients (from client requirements)
        self.beta_penalty_coef = 0.5
        self.volatility_penalty_coef = 0.3
        
        # Thresholds
        self.beta_threshold = 0.3  # |β - 1| > 0.3 triggers penalty
        self.volatility_multiplier = 1.5  # σ/σ_market > 1.5 triggers penalty
        
        logger.info(f"StatisticalScorer initialized (risk-free rate: {risk_free_rate:.1%})")
    
    def calculate_statistical_score(self, price_data: pd.DataFrame,
                                    benchmark_data: pd.DataFrame = None) -> Dict[str, float]:
        """
        Calculate composite statistical score for a stock
        
        Args:
            price_data: DataFrame with OHLCV data for the stock
            benchmark_data: DataFrame with OHLCV data for NIFTY
        
        Returns:
            Dict with component scores and final statistical score
        """
        if price_data.empty or len(price_data) < 252:
            logger.warning("Insufficient price data for statistical analysis")
            return self._empty_score()
        
        try:
            # Calculate base Sharpe ratio (6-12 month period)
            sharpe_score = self._calculate_sharpe_score(price_data)
            
            # Calculate beta penalty
            beta_penalty = self._calculate_beta_penalty(price_data, benchmark_data)
            
            # Calculate volatility penalty
            volatility_penalty = self._calculate_volatility_penalty(
                price_data, 
                benchmark_data
            )
            
            # Apply formula: S_i = Sharpe - 0.5*|β-1| - 0.3*max(0, σ/σ_N - 1.5)
            statistical_score = sharpe_score - beta_penalty - volatility_penalty
            
            # Normalize to 0-1 range (Sharpe can be negative, so adjust)
            # Typical Sharpe range: -2 to +3, map to 0 to 1
            statistical_score = (statistical_score + 2) / 5
            statistical_score = max(0.0, min(1.0, statistical_score))
            
            return {
                'sharpe_ratio': self._calculate_sharpe_ratio(price_data),
                'sharpe_score': sharpe_score,
                'beta': self._calculate_beta_value(price_data, benchmark_data),
                'beta_penalty': beta_penalty,
                'volatility_ratio': self._calculate_volatility_ratio(price_data, benchmark_data),
                'volatility_penalty': volatility_penalty,
                'statistical_score': statistical_score
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistical score: {e}")
            return self._empty_score()
    
    def _calculate_sharpe_ratio(self, price_data: pd.DataFrame, 
                               period_months: int = 12) -> float:
        """
        Calculate Sharpe ratio for the stock
        
        Args:
            price_data: DataFrame with price data
            period_months: Period in months (6-12 recommended)
        
        Returns:
            Annualized Sharpe ratio
        """
        try:
            # Use 6-12 month period
            period_days = period_months * 21  # Approximate trading days
            
            if len(price_data) < period_days:
                period_days = len(price_data)
            
            prices = price_data['Close'].iloc[-period_days:]
            returns = calculate_returns(prices)
            
            if returns.empty:
                return 0.0
            
            sharpe = calculate_sharpe_ratio(returns, self.risk_free_rate)
            
            return sharpe
            
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0
    
    def _calculate_sharpe_score(self, price_data: pd.DataFrame) -> float:
        """
        Calculate Sharpe-based score (before penalties)
        
        Uses 6-12 month Sharpe ratio as base score
        """
        try:
            # Calculate both 6-month and 12-month Sharpe
            sharpe_12m = self._calculate_sharpe_ratio(price_data, period_months=12)
            sharpe_6m = self._calculate_sharpe_ratio(price_data, period_months=6)
            
            # Weight more recent period slightly higher
            sharpe_score = 0.4 * sharpe_6m + 0.6 * sharpe_12m
            
            return sharpe_score
            
        except Exception as e:
            logger.error(f"Error calculating Sharpe score: {e}")
            return 0.0
    
    def _calculate_beta_value(self, price_data: pd.DataFrame,
                             benchmark_data: pd.DataFrame = None) -> float:
        """Calculate stock beta vs benchmark"""
        try:
            if benchmark_data is None or benchmark_data.empty:
                return 1.0  # Assume market beta if no benchmark
            
            # Align data
            common_dates = price_data.index.intersection(benchmark_data.index)
            if len(common_dates) < 63:  # Need at least 3 months
                return 1.0
            
            # Use last 12 months for beta calculation
            period_days = min(252, len(common_dates))
            common_dates = common_dates[-period_days:]
            
            stock_prices = price_data.loc[common_dates, 'Close']
            benchmark_prices = benchmark_data.loc[common_dates, 'Close']
            
            stock_returns = calculate_returns(stock_prices)
            benchmark_returns = calculate_returns(benchmark_prices)
            
            beta = calculate_beta(stock_returns, benchmark_returns)
            
            return beta
            
        except Exception as e:
            logger.error(f"Error calculating beta: {e}")
            return 1.0
    
    def _calculate_beta_penalty(self, price_data: pd.DataFrame,
                               benchmark_data: pd.DataFrame = None) -> float:
        """
        Calculate beta penalty: 0.5 * |β_i - 1| if |β_i - 1| > 0.3
        
        This penalizes stocks with beta significantly different from 1.0,
        managing systematic risk exposure and maintaining portfolio beta
        characteristics aligned with mandate requirements.
        """
        try:
            beta = self._calculate_beta_value(price_data, benchmark_data)
            
            beta_deviation = abs(beta - 1.0)
            
            if beta_deviation > self.beta_threshold:
                penalty = self.beta_penalty_coef * beta_deviation
            else:
                penalty = 0.0
            
            return penalty
            
        except Exception as e:
            logger.error(f"Error calculating beta penalty: {e}")
            return 0.0
    
    def _calculate_volatility_ratio(self, price_data: pd.DataFrame,
                                   benchmark_data: pd.DataFrame = None) -> float:
        """Calculate stock volatility relative to benchmark"""
        try:
            if benchmark_data is None or benchmark_data.empty:
                return 1.0
            
            # Align data
            common_dates = price_data.index.intersection(benchmark_data.index)
            if len(common_dates) < 63:
                return 1.0
            
            # Use last 6 months for volatility calculation
            period_days = min(126, len(common_dates))
            common_dates = common_dates[-period_days:]
            
            stock_prices = price_data.loc[common_dates, 'Close']
            benchmark_prices = benchmark_data.loc[common_dates, 'Close']
            
            stock_returns = calculate_returns(stock_prices)
            benchmark_returns = calculate_returns(benchmark_prices)
            
            stock_vol = calculate_volatility(stock_returns, annualize=True)
            benchmark_vol = calculate_volatility(benchmark_returns, annualize=True)
            
            vol_ratio = safe_divide(stock_vol, benchmark_vol, 1.0)
            
            return vol_ratio
            
        except Exception as e:
            logger.error(f"Error calculating volatility ratio: {e}")
            return 1.0
    
    def _calculate_volatility_penalty(self, price_data: pd.DataFrame,
                                     benchmark_data: pd.DataFrame = None) -> float:
        """
        Calculate volatility penalty: 0.3 * max(0, σ_i/σ_NIFTY - 1.5)
        
        This penalizes stocks with volatility exceeding 1.5x NIFTY volatility,
        ensuring position-level risk doesn't compromise portfolio-wide risk
        budgets and maintaining suitable volatility characteristics.
        """
        try:
            vol_ratio = self._calculate_volatility_ratio(price_data, benchmark_data)
            
            excess_volatility = max(0, vol_ratio - self.volatility_multiplier)
            
            penalty = self.volatility_penalty_coef * excess_volatility
            
            return penalty
            
        except Exception as e:
            logger.error(f"Error calculating volatility penalty: {e}")
            return 0.0
    
    def calculate_max_drawdown(self, price_data: pd.DataFrame) -> float:
        """
        Calculate maximum drawdown over the period
        
        Additional risk metric (not used in scoring but useful for analysis)
        """
        try:
            prices = price_data['Close']
            returns = calculate_returns(prices)
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_dd = drawdown.min()
            
            return max_dd
            
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return 0.0
    
    def calculate_downside_deviation(self, price_data: pd.DataFrame,
                                    mar: float = 0.0) -> float:
        """
        Calculate downside deviation (for Sortino ratio)
        
        Args:
            price_data: DataFrame with price data
            mar: Minimum Acceptable Return (default 0%)
        
        Returns:
            Annualized downside deviation
        """
        try:
            prices = price_data['Close']
            returns = calculate_returns(prices)
            
            if returns.empty:
                return 0.0
            
            # Only consider returns below MAR
            downside_returns = returns[returns < mar]
            
            if len(downside_returns) == 0:
                return 0.0
            
            # Calculate downside deviation
            downside_dev = np.sqrt(np.mean(downside_returns ** 2))
            
            # Annualize
            downside_dev_annual = downside_dev * np.sqrt(252)
            
            return downside_dev_annual
            
        except Exception as e:
            logger.error(f"Error calculating downside deviation: {e}")
            return 0.0
    
    def calculate_sortino_ratio(self, price_data: pd.DataFrame,
                               mar: float = 0.0) -> float:
        """
        Calculate Sortino ratio (alternative to Sharpe focusing on downside risk)
        
        Args:
            price_data: DataFrame with price data
            mar: Minimum Acceptable Return
        
        Returns:
            Sortino ratio
        """
        try:
            prices = price_data['Close']
            returns = calculate_returns(prices)
            
            if returns.empty:
                return 0.0
            
            # Calculate excess return
            excess_return = returns.mean() - (mar / 252)
            
            # Calculate downside deviation
            downside_dev = self.calculate_downside_deviation(price_data, mar) / np.sqrt(252)
            
            if downside_dev == 0:
                return 0.0
            
            sortino = np.sqrt(252) * excess_return / downside_dev
            
            return sortino
            
        except Exception as e:
            logger.error(f"Error calculating Sortino ratio: {e}")
            return 0.0
    
    def _empty_score(self) -> Dict[str, float]:
        """Return neutral scores when calculation fails"""
        return {
            'sharpe_ratio': 0.0,
            'sharpe_score': 0.0,
            'beta': 1.0,
            'beta_penalty': 0.0,
            'volatility_ratio': 1.0,
            'volatility_penalty': 0.0,
            'statistical_score': 0.5
        }
    
    def batch_score_stocks(self, stocks_prices: Dict[str, pd.DataFrame],
                          benchmark_data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Calculate statistical scores for multiple stocks
        
        Args:
            stocks_prices: Dict mapping stock symbols to price DataFrames
            benchmark_data: DataFrame with NIFTY price data
        
        Returns:
            DataFrame with statistical scores for all stocks
        """
        results = []
        
        for symbol, price_data in stocks_prices.items():
            scores = self.calculate_statistical_score(price_data, benchmark_data)
            scores['symbol'] = symbol
            
            # Add additional risk metrics
            scores['max_drawdown'] = self.calculate_max_drawdown(price_data)
            scores['sortino_ratio'] = self.calculate_sortino_ratio(price_data)
            
            results.append(scores)
        
        df = pd.DataFrame(results)
        df.set_index('symbol', inplace=True)
        
        logger.info(f"Calculated statistical scores for {len(df)} stocks")
        
        return df


if __name__ == "__main__":
    # Test the statistical scorer
    scorer = StatisticalScorer(risk_free_rate=0.06)
    
    # Generate sample price data
    dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='B')
    
    # Stock with moderate volatility
    returns = np.random.randn(len(dates)) * 0.015 + 0.0005  # 1.5% daily vol, positive drift
    prices = 100 * (1 + pd.Series(returns)).cumprod()
    
    test_data = pd.DataFrame({
        'Open': prices,
        'High': prices * 1.01,
        'Low': prices * 0.99,
        'Close': prices,
        'Volume': np.random.uniform(1000000, 5000000, len(dates))
    }, index=dates)
    
    # Benchmark data (lower volatility)
    benchmark_returns = np.random.randn(len(dates)) * 0.01 + 0.0003
    benchmark_prices = 100 * (1 + pd.Series(benchmark_returns)).cumprod()
    
    benchmark_data = pd.DataFrame({
        'Open': benchmark_prices,
        'High': benchmark_prices * 1.005,
        'Low': benchmark_prices * 0.995,
        'Close': benchmark_prices,
        'Volume': np.random.uniform(10000000, 50000000, len(dates))
    }, index=dates)
    
    scores = scorer.calculate_statistical_score(test_data, benchmark_data)
    
    print("\nStatistical Score Test:")
    print("=" * 50)
    for key, value in scores.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")
    print("=" * 50)
