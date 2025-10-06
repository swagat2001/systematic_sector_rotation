"""
Technical Scoring Model for Systematic Sector Rotation Strategy

Implements the technical scoring component with 35% weight in final score:
- Momentum Score (50%): 12-1 month price momentum excluding most recent month
- Trend Score (30%): Golden Cross confirmation (50DMA > 200DMA with price > 200DMA)
- Relative Strength Score (20%): Price ratio vs NIFTY showing improving trends

Formula: T_i = 0.5*Mom + 0.3*Trend + 0.2*RS

Additional consideration for recent range expansion with controlled Average True Range (ATR)
to identify breakout candidates while managing volatility exposure.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from config import Config, TechnicalIndicators
from utils.logger import setup_logger
from utils.helpers import (
    calculate_momentum, 
    calculate_moving_average,
    calculate_returns,
    safe_divide
)

logger = setup_logger(__name__)


class TechnicalScorer:
    """
    Calculates technical scores for stocks based on momentum, trend, 
    and relative strength indicators
    """
    
    def __init__(self):
        self.config = Config()
        self.indicators = TechnicalIndicators()
        
        # Scoring weights (from client requirements)
        self.weights = {
            'momentum': 0.50,
            'trend': 0.30,
            'relative_strength': 0.20
        }
        
        logger.info("TechnicalScorer initialized")
    
    def calculate_technical_score(self, price_data: pd.DataFrame,
                                 benchmark_data: pd.DataFrame = None) -> Dict[str, float]:
        """
        Calculate composite technical score for a stock
        
        Args:
            price_data: DataFrame with OHLCV data for the stock
            benchmark_data: DataFrame with OHLCV data for NIFTY (for relative strength)
        
        Returns:
            Dict with component scores and final technical score
        """
        if price_data.empty or len(price_data) < 252:
            logger.warning("Insufficient price data for technical analysis")
            return self._empty_score()
        
        try:
            # Calculate component scores
            momentum_score = self._calculate_momentum_score(price_data)
            trend_score = self._calculate_trend_score(price_data)
            relative_strength_score = self._calculate_relative_strength_score(
                price_data, 
                benchmark_data
            )
            
            # Calculate ATR for breakout detection (bonus consideration)
            atr_signal = self._calculate_atr_signal(price_data)
            
            # Calculate weighted composite score
            technical_score = (
                self.weights['momentum'] * momentum_score +
                self.weights['trend'] * trend_score +
                self.weights['relative_strength'] * relative_strength_score
            )
            
            # Apply ATR bonus (max 10% boost for range expansion)
            technical_score = technical_score * (1 + atr_signal * 0.10)
            technical_score = min(technical_score, 1.0)  # Cap at 1.0
            
            return {
                'momentum_score': momentum_score,
                'trend_score': trend_score,
                'relative_strength_score': relative_strength_score,
                'atr_signal': atr_signal,
                'technical_score': technical_score
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical score: {e}")
            return self._empty_score()
    
    def _calculate_momentum_score(self, price_data: pd.DataFrame) -> float:
        """
        Calculate Momentum Score (50% of technical score)
        
        Method: 12-1 month price momentum excluding most recent month
        """
        try:
            if len(price_data) < 252:
                return 0.5
            
            prices = price_data['Close']
            
            # Calculate 12-1 month momentum
            momentum_period = 252  # 12 months
            exclude_period = 21    # 1 month
            
            if len(prices) < (momentum_period + exclude_period):
                return 0.5
            
            current_price = prices.iloc[-(exclude_period + 1)]
            past_price = prices.iloc[-(momentum_period + exclude_period + 1)]
            
            momentum = (current_price / past_price) - 1
            
            # Normalize momentum to 0-1 score
            if momentum > 0.30:
                score = 1.0
            elif momentum > 0:
                score = 0.5 + (momentum / 0.60)
            elif momentum > -0.20:
                score = 0.5 + (momentum / 0.40)
            else:
                score = 0.0
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating momentum score: {e}")
            return 0.5
    
    def _calculate_trend_score(self, price_data: pd.DataFrame) -> float:
        """
        Calculate Trend Score (30% of technical score)
        
        Method: Golden Cross confirmation (50DMA > 200DMA with price > 200DMA)
        """
        try:
            if len(price_data) < 200:
                return 0.5
            
            prices = price_data['Close']
            
            # Calculate moving averages
            sma_50 = calculate_moving_average(prices, 50)
            sma_200 = calculate_moving_average(prices, 200)
            
            if sma_50.empty or sma_200.empty:
                return 0.5
            
            current_price = prices.iloc[-1]
            current_sma_50 = sma_50.iloc[-1]
            current_sma_200 = sma_200.iloc[-1]
            
            # Check Golden Cross
            golden_cross = current_sma_50 > current_sma_200
            price_above_200 = current_price > current_sma_200
            
            if golden_cross and price_above_200:
                score = 1.0
            elif price_above_200:
                ma_distance = (current_sma_50 - current_sma_200) / current_sma_200
                score = 0.8 if ma_distance > -0.02 else 0.7
            elif golden_cross:
                price_distance = (current_price - current_sma_200) / current_sma_200
                score = 0.5 + (price_distance * 2) if price_distance > -0.05 else 0.4
            else:
                price_distance = (current_price - current_sma_200) / current_sma_200
                if price_distance > -0.10:
                    score = 0.3
                elif price_distance > -0.20:
                    score = 0.2
                else:
                    score = 0.0
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating trend score: {e}")
            return 0.5
    
    def _calculate_relative_strength_score(self, price_data: pd.DataFrame,
                                          benchmark_data: pd.DataFrame = None) -> float:
        """
        Calculate Relative Strength Score (20% of technical score)
        
        Method: Price ratio vs NIFTY showing improving relative performance
        """
        try:
            if benchmark_data is None or benchmark_data.empty:
                return 0.5
            
            if len(price_data) < 126 or len(benchmark_data) < 126:
                return 0.5
            
            # Align data
            common_dates = price_data.index.intersection(benchmark_data.index)
            if len(common_dates) < 126:
                return 0.5
            
            stock_prices = price_data.loc[common_dates, 'Close']
            benchmark_prices = benchmark_data.loc[common_dates, 'Close']
            
            # Calculate relative strength ratio
            rs_ratio = stock_prices / benchmark_prices
            
            # Calculate trend in RS ratio (6-month)
            period = min(126, len(rs_ratio))
            
            current_rs = rs_ratio.iloc[-1]
            past_rs = rs_ratio.iloc[-period]
            
            rs_change = (current_rs / past_rs) - 1
            
            # Recent RS trend (1 month)
            recent_period = min(21, len(rs_ratio))
            recent_rs = rs_ratio.iloc[-recent_period]
            recent_rs_change = (current_rs / recent_rs) - 1
            
            # Score based on RS improvement
            if rs_change > 0.20:  # Strong outperformance
                score = 1.0
            elif rs_change > 0.10:
                score = 0.8
            elif rs_change > 0:
                score = 0.6
            elif rs_change > -0.10:
                score = 0.4
            else:
                score = 0.2
            
            # Bonus for recent improvement
            if recent_rs_change > 0.05:
                score = min(1.0, score + 0.1)
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating relative strength score: {e}")
            return 0.5
    
    def _calculate_atr_signal(self, price_data: pd.DataFrame) -> float:
        """
        Calculate ATR signal for range expansion and breakout detection
        
        Method:
        1. Calculate ATR (14-period Average True Range)
        2. Compare current ATR to 3-month average
        3. Check for range expansion (ATR increasing)
        4. Identify breakout candidates (high ATR + price near highs)
        
        Returns signal from 0 to 1 indicating breakout potential with volatility control
        """
        try:
            if len(price_data) < 63:  # Need 3 months of data
                return 0.0
            
            # Calculate True Range components
            high = price_data['High']
            low = price_data['Low']
            close = price_data['Close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Calculate ATR (14 period standard)
            atr = true_range.rolling(window=14, min_periods=14).mean()
            
            if atr.empty or len(atr) < 63:
                return 0.0
            
            # Current vs historical ATR analysis
            current_atr = atr.iloc[-1]
            avg_atr_3m = atr.iloc[-63:].mean()  # 3-month average
            std_atr_3m = atr.iloc[-63:].std()
            
            # Normalized ATR expansion
            atr_ratio = safe_divide(current_atr, avg_atr_3m, 1.0)
            atr_z_score = safe_divide(current_atr - avg_atr_3m, std_atr_3m, 0.0)
            
            # Check if price is breaking out (near recent highs)
            recent_high = high.iloc[-21:].max()  # 1-month high
            current_price = close.iloc[-1]
            breakout_proximity = current_price / recent_high
            
            # Volatility control: penalize excessive volatility
            price_returns = close.pct_change()
            recent_volatility = price_returns.iloc[-21:].std() * np.sqrt(252)  # Annualized
            
            # Controlled range expansion signal
            if atr_ratio > 1.5 and breakout_proximity > 0.95 and recent_volatility < 0.50:
                # Strong breakout: high ATR + near highs + controlled volatility
                signal = 1.0
            elif atr_ratio > 1.3 and breakout_proximity > 0.90 and recent_volatility < 0.60:
                # Moderate breakout potential
                signal = 0.7
            elif atr_ratio > 1.2 and atr_z_score > 0.5:
                # Range expanding but need confirmation
                signal = 0.5
            elif atr_ratio > 1.1:
                # Mild expansion
                signal = 0.3
            elif recent_volatility > 0.70:
                # Excessive volatility - negative signal
                signal = -0.2
            else:
                # Normal range
                signal = 0.0
            
            return max(-0.2, min(1.0, signal))
            
        except Exception as e:
            logger.error(f"Error calculating ATR signal: {e}")
            return 0.0
    
    def _empty_score(self) -> Dict[str, float]:
        """Return neutral scores when calculation fails"""
        return {
            'momentum_score': 0.5,
            'trend_score': 0.5,
            'relative_strength_score': 0.5,
            'atr_signal': 0.0,
            'technical_score': 0.5
        }
    
    def batch_score_stocks(self, stocks_prices: Dict[str, pd.DataFrame],
                          benchmark_data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Calculate technical scores for multiple stocks
        
        Args:
            stocks_prices: Dict mapping stock symbols to price DataFrames
            benchmark_data: DataFrame with NIFTY price data
        
        Returns:
            DataFrame with technical scores for all stocks
        """
        results = []
        
        for symbol, price_data in stocks_prices.items():
            scores = self.calculate_technical_score(price_data, benchmark_data)
            scores['symbol'] = symbol
            results.append(scores)
        
        df = pd.DataFrame(results)
        df.set_index('symbol', inplace=True)
        
        logger.info(f"Calculated technical scores for {len(df)} stocks")
        
        return df


if __name__ == "__main__":
    # Test the technical scorer
    scorer = TechnicalScorer()
    
    # Generate sample price data
    dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='B')
    
    # Uptrending stock
    prices = 100 * (1 + np.random.randn(len(dates)).cumsum() * 0.01)
    test_data = pd.DataFrame({
        'Open': prices,
        'High': prices * 1.02,
        'Low': prices * 0.98,
        'Close': prices,
        'Volume': np.random.uniform(1000000, 5000000, len(dates))
    }, index=dates)
    
    scores = scorer.calculate_technical_score(test_data)
    
    print("\nTechnical Score Test:")
    print("=" * 50)
    for key, value in scores.items():
        print(f"{key}: {value:.4f}")
    print("=" * 50)
