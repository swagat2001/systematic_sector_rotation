"""
Composite Scoring Model for Systematic Sector Rotation Strategy

Integrates all three scoring models to calculate final composite Z-scores:
- Fundamental Score (45% weight)
- Technical Score (35% weight)  
- Statistical Score (20% weight)

Final Formula: Z_i = 0.45*F_i + 0.35*T_i + 0.20*S_i

This composite score is used for stock selection in the 40% satellite portfolio,
where stocks are ranked and the top decile is selected subject to liquidity
filters and hysteresis rules.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from config import Config
from models.enhanced_fundamental_scorer import EnhancedFundamentalScorer
from models.technical_scorer import TechnicalScorer
from models.statistical_scorer import StatisticalScorer
from utils.logger import setup_logger
from utils.helpers import z_score_normalize

logger = setup_logger(__name__)


class CompositeScorer:
    """
    Combines fundamental, technical, and statistical scores into final composite score
    """
    
    def __init__(self):
        self.config = Config()
        
        # Initialize component scorers (using enhanced fundamental scorer)
        self.fundamental_scorer = EnhancedFundamentalScorer()
        self.technical_scorer = TechnicalScorer()
        self.statistical_scorer = StatisticalScorer()
        
        # Weights from client requirements
        self.weights = {
            'fundamental': 0.45,
            'technical': 0.35,
            'statistical': 0.20
        }
        
        logger.info("CompositeScorer initialized with weights: F=45%, T=35%, S=20%")
    
    def calculate_composite_score(self, 
                                  symbol: str,
                                  fundamentals: Dict,
                                  price_data: pd.DataFrame,
                                  benchmark_data: pd.DataFrame = None,
                                  sector_fundamentals: List[Dict] = None) -> Dict[str, float]:
        """
        Calculate composite score for a single stock
        
        Args:
            symbol: Stock symbol
            fundamentals: Dict with fundamental metrics
            price_data: DataFrame with OHLCV data
            benchmark_data: DataFrame with benchmark OHLCV data
            sector_fundamentals: List of fundamental dicts for sector peers
        
        Returns:
            Dict with all component scores and final composite score
        """
        try:
            # Calculate component scores
            fund_scores = self.fundamental_scorer.calculate_fundamental_score(
                fundamentals, 
                sector_fundamentals
            )
            
            tech_scores = self.technical_scorer.calculate_technical_score(
                price_data,
                benchmark_data
            )
            
            stat_scores = self.statistical_scorer.calculate_statistical_score(
                price_data,
                benchmark_data
            )
            
            # Extract normalized scores (0-1 range)
            F = fund_scores['fundamental_score']
            T = tech_scores['technical_score']
            S = stat_scores['statistical_score']
            
            # Calculate weighted composite score
            Z = (
                self.weights['fundamental'] * F +
                self.weights['technical'] * T +
                self.weights['statistical'] * S
            )
            
            # Compile results
            result = {
                'symbol': symbol,
                
                # Component scores
                'fundamental_score': F,
                'technical_score': T,
                'statistical_score': S,
                
                # Sub-component scores
                'quality_score': fund_scores['quality_score'],
                'growth_score': fund_scores['growth_score'],
                'valuation_score': fund_scores['valuation_score'],
                'balance_sheet_score': fund_scores['balance_sheet_score'],
                
                'momentum_score': tech_scores['momentum_score'],
                'trend_score': tech_scores['trend_score'],
                'relative_strength_score': tech_scores['relative_strength_score'],
                
                'sharpe_ratio': stat_scores['sharpe_ratio'],
                'beta': stat_scores['beta'],
                'volatility_ratio': stat_scores['volatility_ratio'],
                
                # Final composite score
                'composite_score': Z
            }
            
            logger.info(f"{symbol}: Z={Z:.4f} (F={F:.4f}, T={T:.4f}, S={S:.4f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating composite score for {symbol}: {e}")
            return self._empty_score(symbol)
    
    def batch_calculate_scores(self,
                              stocks_data: Dict[str, Dict],
                              stocks_prices: Dict[str, pd.DataFrame],
                              benchmark_data: pd.DataFrame = None,
                              sector_mapping: Dict[str, str] = None) -> pd.DataFrame:
        """
        Calculate composite scores for multiple stocks
        
        Args:
            stocks_data: Dict mapping symbols to fundamental data
            stocks_prices: Dict mapping symbols to price DataFrames
            benchmark_data: DataFrame with benchmark prices
            sector_mapping: Dict mapping symbols to sector names
        
        Returns:
            DataFrame with composite scores, sorted by score (descending)
        """
        logger.info(f"Calculating composite scores for {len(stocks_data)} stocks...")
        
        results = []
        
        # Group stocks by sector for peer comparison
        sector_groups = {}
        if sector_mapping:
            for symbol, sector in sector_mapping.items():
                if sector not in sector_groups:
                    sector_groups[sector] = []
                sector_groups[sector].append(symbol)
        
        # Calculate scores for each stock
        for symbol in stocks_data.keys():
            try:
                # Get data
                fundamentals = stocks_data.get(symbol, {})
                price_data = stocks_prices.get(symbol, pd.DataFrame())
                
                if price_data.empty:
                    logger.warning(f"No price data for {symbol}, skipping")
                    continue
                
                # Get sector peers for fundamental comparison
                sector_fundamentals = None
                if sector_mapping and symbol in sector_mapping:
                    sector = sector_mapping[symbol]
                    if sector in sector_groups:
                        sector_fundamentals = [
                            stocks_data[s]
                            for s in sector_groups[sector]
                            if s in stocks_data and s != symbol
                        ]
                
                # Calculate composite score
                score_result = self.calculate_composite_score(
                    symbol,
                    fundamentals,
                    price_data,
                    benchmark_data,
                    sector_fundamentals
                )
                
                results.append(score_result)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        # Create DataFrame
        df = pd.DataFrame(results)
        
        if df.empty:
            logger.warning("No scores calculated")
            return df
        
        df.set_index('symbol', inplace=True)
        
        # Sort by composite score (descending)
        df.sort_values('composite_score', ascending=False, inplace=True)
        
        # Calculate percentile ranks
        df['percentile_rank'] = df['composite_score'].rank(pct=True)
        
        logger.info(f"✓ Calculated scores for {len(df)} stocks")
        logger.info(f"  Top score: {df['composite_score'].max():.4f}")
        logger.info(f"  Bottom score: {df['composite_score'].min():.4f}")
        logger.info(f"  Mean score: {df['composite_score'].mean():.4f}")
        
        return df
    
    def get_top_decile(self, scores_df: pd.DataFrame, 
                      liquidity_filter: bool = True,
                      min_volume: float = 1000000,
                      min_market_cap: float = 1000000000) -> pd.DataFrame:
        """
        Get top decile of stocks by composite score
        
        Args:
            scores_df: DataFrame with composite scores
            liquidity_filter: Whether to apply liquidity filters
            min_volume: Minimum average daily volume
            min_market_cap: Minimum market cap (in rupees)
        
        Returns:
            DataFrame with top decile stocks
        """
        if scores_df.empty:
            return pd.DataFrame()
        
        # Calculate decile threshold
        decile_threshold = scores_df['composite_score'].quantile(0.90)
        
        # Select top decile
        top_decile = scores_df[scores_df['composite_score'] >= decile_threshold].copy()
        
        logger.info(f"Top decile: {len(top_decile)} stocks (threshold: {decile_threshold:.4f})")
        
        # Apply liquidity filters if requested
        if liquidity_filter:
            # Note: These filters would need actual volume/market cap data
            # For now, just log that filtering would happen
            logger.info(f"Liquidity filters: min_volume={min_volume:,}, min_market_cap=₹{min_market_cap:,}")
        
        return top_decile
    
    def apply_hysteresis(self, current_scores: pd.DataFrame,
                        previous_holdings: List[str],
                        previous_scores: pd.DataFrame = None,
                        consecutive_months: int = 2) -> Tuple[List[str], List[str]]:
        """
        Apply hysteresis rules to reduce turnover
        
        Stocks are only dropped if Z-score falls below median for 2 consecutive months
        
        Args:
            current_scores: DataFrame with current month scores
            previous_holdings: List of symbols held in previous period
            previous_scores: DataFrame with previous month scores
            consecutive_months: Number of months below median before drop
        
        Returns:
            Tuple of (stocks_to_keep, stocks_to_drop)
        """
        if current_scores.empty:
            return [], previous_holdings
        
        median_score = current_scores['composite_score'].median()
        
        stocks_to_keep = []
        stocks_to_drop = []
        
        for symbol in previous_holdings:
            if symbol not in current_scores.index:
                # Stock no longer in universe
                stocks_to_drop.append(symbol)
                continue
            
            current_score = current_scores.loc[symbol, 'composite_score']
            
            # Check if below median
            if current_score >= median_score:
                # Above median, keep
                stocks_to_keep.append(symbol)
            else:
                # Below median, check previous month
                if previous_scores is not None and symbol in previous_scores.index:
                    previous_score = previous_scores.loc[symbol, 'composite_score']
                    previous_median = previous_scores['composite_score'].median()
                    
                    if previous_score < previous_median:
                        # Below median for 2 consecutive months, drop
                        stocks_to_drop.append(symbol)
                    else:
                        # First month below median, give one more month
                        stocks_to_keep.append(symbol)
                else:
                    # No previous data, keep for now
                    stocks_to_keep.append(symbol)
        
        logger.info(f"Hysteresis: keeping {len(stocks_to_keep)}, dropping {len(stocks_to_drop)}")
        
        return stocks_to_keep, stocks_to_drop
    
    def _empty_score(self, symbol: str) -> Dict[str, float]:
        """Return neutral scores when calculation fails"""
        return {
            'symbol': symbol,
            'fundamental_score': 0.5,
            'technical_score': 0.5,
            'statistical_score': 0.5,
            'quality_score': 0.5,
            'growth_score': 0.5,
            'valuation_score': 0.5,
            'balance_sheet_score': 0.5,
            'momentum_score': 0.5,
            'trend_score': 0.5,
            'relative_strength_score': 0.5,
            'sharpe_ratio': 0.0,
            'beta': 1.0,
            'volatility_ratio': 1.0,
            'composite_score': 0.5
        }
    
    def generate_score_report(self, scores_df: pd.DataFrame,
                             top_n: int = 20) -> str:
        """
        Generate a text report of scores
        
        Args:
            scores_df: DataFrame with scores
            top_n: Number of top stocks to include in report
        
        Returns:
            Formatted report string
        """
        if scores_df.empty:
            return "No scores available"
        
        report = f"\n{'=' * 80}\n"
        report += f"COMPOSITE SCORE REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"{'=' * 80}\n\n"
        
        report += f"Total Stocks Scored: {len(scores_df)}\n"
        report += f"Score Range: {scores_df['composite_score'].min():.4f} to {scores_df['composite_score'].max():.4f}\n"
        report += f"Mean Score: {scores_df['composite_score'].mean():.4f}\n"
        report += f"Median Score: {scores_df['composite_score'].median():.4f}\n\n"
        
        report += f"TOP {top_n} STOCKS BY COMPOSITE SCORE:\n"
        report += f"{'-' * 80}\n"
        report += f"{'Rank':<6}{'Symbol':<12}{'Z-Score':<10}{'F-Score':<10}{'T-Score':<10}{'S-Score':<10}\n"
        report += f"{'-' * 80}\n"
        
        top_stocks = scores_df.head(top_n)
        for rank, (symbol, row) in enumerate(top_stocks.iterrows(), 1):
            report += f"{rank:<6}{symbol:<12}{row['composite_score']:<10.4f}"
            report += f"{row['fundamental_score']:<10.4f}{row['technical_score']:<10.4f}"
            report += f"{row['statistical_score']:<10.4f}\n"
        
        report += f"{'-' * 80}\n"
        
        # Score distribution
        report += f"\nSCORE DISTRIBUTION:\n"
        report += f"  90th percentile: {scores_df['composite_score'].quantile(0.90):.4f}\n"
        report += f"  75th percentile: {scores_df['composite_score'].quantile(0.75):.4f}\n"
        report += f"  50th percentile: {scores_df['composite_score'].quantile(0.50):.4f}\n"
        report += f"  25th percentile: {scores_df['composite_score'].quantile(0.25):.4f}\n"
        report += f"  10th percentile: {scores_df['composite_score'].quantile(0.10):.4f}\n"
        
        report += f"\n{'=' * 80}\n"
        
        return report


if __name__ == "__main__":
    # Test the composite scorer
    scorer = CompositeScorer()
    
    # Sample data for testing
    test_fundamentals = {
        'INFY': {
            'roe': 0.25, 'gross_margin': 0.40, 'operating_margin': 0.25,
            'current_ratio': 2.5, 'earnings_growth': 0.15, 'revenue_growth': 0.12,
            'pe_ratio': 22, 'pb_ratio': 3.5, 'debt_to_equity': 0.1,
            'interest_coverage': 15.0
        },
        'TCS': {
            'roe': 0.30, 'gross_margin': 0.45, 'operating_margin': 0.28,
            'current_ratio': 2.8, 'earnings_growth': 0.18, 'revenue_growth': 0.14,
            'pe_ratio': 28, 'pb_ratio': 8.0, 'debt_to_equity': 0.05,
            'interest_coverage': 20.0
        }
    }
    
    # Generate sample price data
    dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='B')
    
    test_prices = {}
    for symbol in ['INFY', 'TCS']:
        prices = 100 * (1 + np.random.randn(len(dates)).cumsum() * 0.01)
        test_prices[symbol] = pd.DataFrame({
            'Open': prices,
            'High': prices * 1.02,
            'Low': prices * 0.98,
            'Close': prices,
            'Volume': np.random.uniform(1000000, 5000000, len(dates))
        }, index=dates)
    
    # Calculate scores
    scores_df = scorer.batch_calculate_scores(
        test_fundamentals,
        test_prices
    )
    
    # Generate report
    report = scorer.generate_score_report(scores_df)
    print(report)
