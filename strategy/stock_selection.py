"""
Stock Selection Engine for Systematic Sector Rotation Strategy

Implements the stock selection logic for the 40% satellite portfolio:
1. Calculate composite Z-scores for all eligible stocks
2. Apply Sharpe Ratio filter (positive over 6-12 months vs T-bill)
3. Apply trend confirmation filters
4. Select top decile stocks
5. Apply liquidity screening (minimum volume & market cap)
6. Implement hysteresis rules (2-month period)

The satellite portfolio complements the sector rotation core by selecting
individual alpha-generating stocks through systematic multi-factor scoring,
while maintaining proper risk controls and reducing unnecessary turnover.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from config import Config
from models.composite_scorer import CompositeScorer
from utils.logger import setup_logger
from utils.helpers import calculate_sharpe_ratio, calculate_returns

logger = setup_logger(__name__)


class StockSelectionEngine:
    """
    Manages stock selection for the 40% satellite allocation
    """
    
    def __init__(self):
        self.config = Config()
        self.scorer = CompositeScorer()
        
        # Strategy parameters (from new dual-approach config)
        self.stock_allocation = Config.SATELLITE_ALLOCATION  # 40%
        self.top_n_stocks = Config.SATELLITE_CONFIG.get('top_stocks', 15)  # Top N stocks
        self.hysteresis_period = 60  # 2 months in days
        
        # Liquidity filters
        self.min_daily_volume = 1_000_000  # 10 Lakh shares
        self.min_market_cap = 1_000_000_000  # 1000 Cr (1 Billion)
        
        # Track selections
        self.current_holdings = []
        self.stock_weights = {}
        self.last_rebalance_date = None
        self.previous_scores = None
        
        logger.info(f"StockSelectionEngine initialized: top {self.top_n_stocks} stocks selection")
    
    def select_stocks(self, 
                     stocks_data: Dict[str, Dict],
                     stocks_prices: Dict[str, pd.DataFrame],
                     benchmark_data: pd.DataFrame = None,
                     sector_mapping: Dict[str, str] = None,
                     previous_holdings: List[str] = None) -> Dict:
        """
        Execute complete stock selection process
        
        Args:
            stocks_data: Dict mapping symbols to fundamental data
            stocks_prices: Dict mapping symbols to price DataFrames
            benchmark_data: DataFrame with benchmark prices
            sector_mapping: Dict mapping symbols to sector names
            previous_holdings: List of previously held stock symbols
        
        Returns:
            Dict with selection results
        """
        logger.info("=" * 60)
        logger.info("EXECUTING STOCK SELECTION")
        logger.info("=" * 60)
        
        try:
            # Step 1: Calculate composite scores
            logger.info("Step 1: Calculating composite scores...")
            scores_df = self.scorer.batch_calculate_scores(
                stocks_data,
                stocks_prices,
                benchmark_data,
                sector_mapping
            )
            
            if scores_df.empty:
                logger.error("No scores calculated")
                return {'success': False, 'error': 'No scores calculated'}
            
            # Step 2: Apply Sharpe ratio filter
            logger.info("Step 2: Applying Sharpe ratio filter...")
            scores_df = self._apply_sharpe_filter(scores_df, stocks_prices, benchmark_data)
            
            # Step 3: Apply trend confirmation
            logger.info("Step 3: Applying trend confirmation...")
            scores_df = self._apply_trend_filter(scores_df)
            
            # Step 4: Select top decile
            logger.info("Step 4: Selecting top decile...")
            top_decile = self._select_top_decile(scores_df)
            
            # Step 5: Apply liquidity screening
            logger.info("Step 5: Applying liquidity filters...")
            liquid_stocks = self._apply_liquidity_filter(
                top_decile,
                stocks_prices,
                stocks_data
            )
            
            # Step 6: Apply hysteresis if we have previous holdings
            if previous_holdings and self.previous_scores is not None:
                logger.info("Step 6: Applying hysteresis rules...")
                final_stocks = self._apply_hysteresis(
                    liquid_stocks,
                    previous_holdings,
                    scores_df
                )
            else:
                final_stocks = liquid_stocks.index.tolist()
            
            # Calculate weights
            weights = self._calculate_stock_weights(
                final_stocks,
                scores_df
            )
            
            # Update state
            self.current_holdings = final_stocks
            self.stock_weights = weights
            self.previous_scores = scores_df
            self.last_rebalance_date = datetime.now()
            
            # Prepare results
            result = {
                'success': True,
                'date': self.last_rebalance_date,
                'selected_stocks': final_stocks,
                'weights': weights,
                'num_stocks': len(final_stocks),
                'avg_score': scores_df.loc[final_stocks, 'composite_score'].mean() if final_stocks else 0,
                'score_range': (
                    scores_df.loc[final_stocks, 'composite_score'].min(),
                    scores_df.loc[final_stocks, 'composite_score'].max()
                ) if final_stocks else (0, 0),
                'all_scores': scores_df
            }
            
            logger.info(f"Stock selection complete: {len(final_stocks)} stocks selected")
            logger.info("=" * 60)
            
            return result
            
        except Exception as e:
            logger.error(f"Stock selection failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _apply_sharpe_filter(self, scores_df: pd.DataFrame,
                            stocks_prices: Dict[str, pd.DataFrame],
                            benchmark_data: pd.DataFrame = None) -> pd.DataFrame:
        """Filter stocks requiring positive Sharpe ratio"""
        if scores_df.empty:
            return scores_df
        
        filtered = scores_df[scores_df['sharpe_ratio'] > 0].copy()
        logger.info(f"Sharpe filter: {len(filtered)}/{len(scores_df)} stocks pass")
        
        return filtered
    
    def _apply_trend_filter(self, scores_df: pd.DataFrame,
                           min_trend_score: float = 0.5) -> pd.DataFrame:
        """Apply trend confirmation filter"""
        if scores_df.empty:
            return scores_df
        
        filtered = scores_df[scores_df['trend_score'] >= min_trend_score].copy()
        logger.info(f"Trend filter: {len(filtered)}/{len(scores_df)} stocks pass")
        
        return filtered
    
    def _select_top_decile(self, scores_df: pd.DataFrame) -> pd.DataFrame:
        """Select top decile (10%) of stocks"""
        if scores_df.empty:
            return scores_df
        
        threshold = scores_df['composite_score'].quantile(1 - self.top_percentile)
        top_decile = scores_df[scores_df['composite_score'] >= threshold].copy()
        
        logger.info(f"Top decile: {len(top_decile)} stocks (threshold: {threshold:.4f})")
        
        return top_decile
    
    def _apply_liquidity_filter(self, scores_df: pd.DataFrame,
                                stocks_prices: Dict[str, pd.DataFrame],
                                stocks_data: Dict[str, Dict]) -> pd.DataFrame:
        """Apply minimum volume and market cap thresholds"""
        if scores_df.empty:
            return scores_df
        
        liquid_stocks = []
        
        for symbol in scores_df.index:
            # Check volume
            if symbol in stocks_prices:
                price_df = stocks_prices[symbol]
                if not price_df.empty and 'Volume' in price_df.columns:
                    avg_volume = price_df['Volume'].tail(21).mean()
                    
                    if avg_volume < self.min_daily_volume:
                        continue
            
            # Check market cap
            if symbol in stocks_data:
                fundamentals = stocks_data[symbol]
                market_cap = fundamentals.get('market_cap')
                
                if market_cap and market_cap < self.min_market_cap:
                    continue
            
            liquid_stocks.append(symbol)
        
        filtered = scores_df.loc[liquid_stocks].copy()
        
        logger.info(f"Liquidity filter: {len(filtered)}/{len(scores_df)} stocks pass")
        
        return filtered
    
    def _apply_hysteresis(self, current_candidates: pd.DataFrame,
                         previous_holdings: List[str],
                         current_scores: pd.DataFrame) -> List[str]:
        """Apply hysteresis rules to reduce turnover"""
        if not previous_holdings or self.previous_scores is None:
            return current_candidates.index.tolist()
        
        median_score = current_scores['composite_score'].median()
        previous_median = self.previous_scores['composite_score'].median()
        
        stocks_to_keep = []
        stocks_to_drop = []
        
        for symbol in previous_holdings:
            if symbol not in current_scores.index:
                stocks_to_drop.append(symbol)
                continue
            
            current_score = current_scores.loc[symbol, 'composite_score']
            
            if current_score >= median_score:
                stocks_to_keep.append(symbol)
                continue
            
            if symbol in self.previous_scores.index:
                previous_score = self.previous_scores.loc[symbol, 'composite_score']
                
                if previous_score < previous_median:
                    stocks_to_drop.append(symbol)
                else:
                    stocks_to_keep.append(symbol)
            else:
                stocks_to_keep.append(symbol)
        
        new_additions = [s for s in current_candidates.index if s not in previous_holdings]
        final_stocks = stocks_to_keep + new_additions
        
        logger.info(f"Hysteresis: kept {len(stocks_to_keep)}, dropped {len(stocks_to_drop)}, added {len(new_additions)}")
        
        return final_stocks
    
    def _calculate_stock_weights(self, selected_stocks: List[str],
                                scores_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate risk-adjusted weights (Z+/volatility)"""
        if not selected_stocks:
            return {}
        
        weights = {}
        risk_adjusted_scores = {}
        total_risk_adjusted_score = 0
        
        for symbol in selected_stocks:
            if symbol not in scores_df.index:
                continue
            
            z_score = scores_df.loc[symbol, 'composite_score']
            vol_ratio = scores_df.loc[symbol, 'volatility_ratio']
            
            risk_adjusted = z_score / max(vol_ratio, 0.5)
            risk_adjusted_scores[symbol] = risk_adjusted
            total_risk_adjusted_score += risk_adjusted
        
        if total_risk_adjusted_score > 0:
            for symbol, risk_adj_score in risk_adjusted_scores.items():
                weight = (risk_adj_score / total_risk_adjusted_score) * self.stock_allocation
                weights[symbol] = weight
        
        logger.info(f"Calculated weights for {len(weights)} stocks, total: {sum(weights.values()):.1%}")
        
        return weights
    
    def get_current_holdings(self) -> Dict:
        """Get current stock holdings"""
        return {
            'stocks': self.current_holdings,
            'weights': self.stock_weights,
            'last_rebalance': self.last_rebalance_date,
            'num_holdings': len(self.current_holdings),
            'total_allocation': sum(self.stock_weights.values()) if self.stock_weights else 0.0
        }
    
    def generate_selection_report(self, result: Dict) -> str:
        """Generate stock selection report"""
        if not result.get('success'):
            return f"Stock selection failed: {result.get('error', 'Unknown error')}"
        
        report = f"\n{'=' * 80}\n"
        report += f"STOCK SELECTION REPORT - {result['date'].strftime('%Y-%m-%d')}\n"
        report += f"{'=' * 80}\n\n"
        
        report += f"Selection Summary:\n"
        report += f"  Total stocks selected: {result['num_stocks']}\n"
        report += f"  Average Z-score: {result['avg_score']:.4f}\n"
        report += f"  Score range: {result['score_range'][0]:.4f} to {result['score_range'][1]:.4f}\n\n"
        
        if result['selected_stocks']:
            report += f"SELECTED STOCKS:\n"
            report += f"{'-' * 80}\n"
            report += f"{'Symbol':<12}{'Weight':<10}{'Z-Score':<10}{'F-Score':<10}{'T-Score':<10}{'S-Score':<10}\n"
            report += f"{'-' * 80}\n"
            
            scores_df = result['all_scores']
            weights = result['weights']
            
            for symbol in result['selected_stocks'][:20]:  # Top 20
                weight = weights.get(symbol, 0)
                if symbol in scores_df.index:
                    row = scores_df.loc[symbol]
                    report += f"{symbol:<12}{weight:<10.2%}{row['composite_score']:<10.4f}"
                    report += f"{row['fundamental_score']:<10.4f}{row['technical_score']:<10.4f}"
                    report += f"{row['statistical_score']:<10.4f}\n"
            
            if len(result['selected_stocks']) > 20:
                report += f"... and {len(result['selected_stocks']) - 20} more\n"
            
            report += f"{'-' * 80}\n"
        
        report += f"\n{'=' * 80}\n"
        
        return report


if __name__ == "__main__":
    # Test stock selection
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    engine = StockSelectionEngine()
    
    # Generate sample data
    dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='B')
    
    test_stocks = ['INFY', 'TCS', 'WIPRO', 'HCLTECH', 'TECHM']
    test_fundamentals = {}
    test_prices = {}
    
    for symbol in test_stocks:
        test_fundamentals[symbol] = {
            'roe': np.random.uniform(0.15, 0.30),
            'pe_ratio': np.random.uniform(20, 30),
            'market_cap': 100000000000
        }
        
        returns = np.random.randn(len(dates)) * 0.015 + 0.0005
        prices = 1000 * (1 + pd.Series(returns)).cumprod()
        
        test_prices[symbol] = pd.DataFrame({
            'Close': prices.values,
            'Volume': np.random.uniform(5000000, 10000000, len(dates))
        }, index=dates)
    
    result = engine.select_stocks(test_fundamentals, test_prices)
    
    if result['success']:
        report = engine.generate_selection_report(result)
        print(report)
