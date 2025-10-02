"""
Sector Rotation Engine for Systematic Sector Rotation Strategy

Implements the core sector rotation logic:
- Monthly ranking of NIFTY sectoral indices by 6-month momentum
- 1-month tiebreaker for enhanced precision
- Optional 200-day MA trend filter
- Selection of top-K sectors (default K=3)
- Equal weight allocation across selected sectors (60% total / K per sector)
- Monthly rebalancing with sector transition tracking

The 60% core allocation rotates between top-performing sectors based on
momentum with trend confirmation, providing systematic exposure to
sector-level momentum while managing concentration risk.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from config import Config, NSESectors
from utils.logger import setup_logger
from utils.helpers import calculate_momentum, calculate_moving_average

logger = setup_logger(__name__)


class SectorRotationEngine:
    """
    Manages sector rotation strategy for the 60% core allocation
    """
    
    def __init__(self):
        self.config = Config()
        
        # Strategy parameters
        self.top_k = Config.TOP_SECTORS_COUNT  # Default: 3 sectors
        self.momentum_period = Config.MOMENTUM_PERIOD  # 6 months (126 days)
        self.tiebreaker_period = Config.TIEBREAKER_PERIOD  # 1 month (21 days)
        self.use_ma_filter = True  # Optional 200-day MA filter
        
        # Allocation
        self.sector_allocation = Config.SECTOR_ALLOCATION  # 60%
        self.weight_per_sector = self.sector_allocation / self.top_k  # 20% each
        
        # Track current selections
        self.current_sectors = []
        self.sector_weights = {}
        self.last_rebalance_date = None
        
        logger.info(f"SectorRotationEngine initialized: top-{self.top_k} sectors, {self.weight_per_sector:.1%} each")
    
    def rank_sectors(self, sector_prices: Dict[str, pd.DataFrame],
                     as_of_date: datetime = None) -> pd.DataFrame:
        """
        Rank all sectors by momentum with tiebreaker
        
        Args:
            sector_prices: Dict mapping sector names to price DataFrames
            as_of_date: Date to calculate rankings (default: latest available)
        
        Returns:
            DataFrame with sector rankings, sorted by score (descending)
        """
        logger.info("Ranking sectors by momentum...")
        
        results = []
        
        for sector_name, price_data in sector_prices.items():
            if price_data.empty or len(price_data) < 252:
                logger.warning(f"Insufficient data for {sector_name}, skipping")
                continue
            
            try:
                # Filter data up to as_of_date if specified
                if as_of_date:
                    price_data = price_data[price_data.index <= as_of_date]
                
                if len(price_data) < 252:
                    continue
                
                prices = price_data['Close']
                
                # Calculate 6-month momentum (primary ranking)
                momentum_6m = self._calculate_sector_momentum(
                    prices, 
                    period=self.momentum_period
                )
                
                # Calculate 1-month momentum (tiebreaker)
                momentum_1m = self._calculate_sector_momentum(
                    prices,
                    period=self.tiebreaker_period
                )
                
                # Check 200-day MA filter if enabled
                ma_filter_pass = True
                if self.use_ma_filter:
                    ma_filter_pass = self._check_ma_filter(prices)
                
                # Composite score: 6-month momentum + small tiebreaker weight
                # Tiebreaker weight: 10% of score to maintain precision
                composite_score = momentum_6m + (0.1 * momentum_1m)
                
                results.append({
                    'sector': sector_name,
                    'momentum_6m': momentum_6m,
                    'momentum_1m': momentum_1m,
                    'composite_score': composite_score,
                    'ma_filter_pass': ma_filter_pass,
                    'current_price': prices.iloc[-1],
                    'price_6m_ago': prices.iloc[-self.momentum_period] if len(prices) >= self.momentum_period else None
                })
                
            except Exception as e:
                logger.error(f"Error ranking {sector_name}: {e}")
                continue
        
        # Create DataFrame
        df = pd.DataFrame(results)
        
        if df.empty:
            logger.warning("No sectors ranked")
            return df
        
        # Apply MA filter if enabled
        if self.use_ma_filter:
            df = df[df['ma_filter_pass'] == True].copy()
            logger.info(f"MA filter applied: {len(df)} sectors pass")
        
        # Sort by composite score (descending)
        df.sort_values('composite_score', ascending=False, inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        # Add rank column
        df['rank'] = range(1, len(df) + 1)
        
        logger.info(f"Ranked {len(df)} sectors")
        if len(df) > 0:
            logger.info(f"Top sector: {df.iloc[0]['sector']} (score: {df.iloc[0]['composite_score']:.4f})")
        
        return df
    
    def select_top_sectors(self, rankings_df: pd.DataFrame) -> List[str]:
        """
        Select top-K sectors from rankings
        
        Args:
            rankings_df: DataFrame with sector rankings
        
        Returns:
            List of top-K sector names
        """
        if rankings_df.empty:
            logger.warning("No rankings available for selection")
            return []
        
        # Select top K sectors
        top_sectors = rankings_df.head(self.top_k)['sector'].tolist()
        
        logger.info(f"Selected top-{self.top_k} sectors: {top_sectors}")
        
        return top_sectors
    
    def calculate_sector_weights(self, selected_sectors: List[str]) -> Dict[str, float]:
        """
        Calculate equal weights for selected sectors
        
        Args:
            selected_sectors: List of selected sector names
        
        Returns:
            Dict mapping sector names to weights
        """
        if not selected_sectors:
            return {}
        
        # Equal weight allocation
        weight_per_sector = self.sector_allocation / len(selected_sectors)
        
        weights = {sector: weight_per_sector for sector in selected_sectors}
        
        logger.info(f"Sector weights calculated: {weight_per_sector:.1%} per sector")
        
        return weights
    
    def rebalance_sectors(self, sector_prices: Dict[str, pd.DataFrame],
                         as_of_date: datetime = None) -> Dict:
        """
        Execute monthly sector rebalancing
        
        Args:
            sector_prices: Dict mapping sector names to price DataFrames
            as_of_date: Rebalancing date
        
        Returns:
            Dict with rebalancing results
        """
        logger.info("=" * 60)
        logger.info("EXECUTING SECTOR REBALANCING")
        logger.info("=" * 60)
        
        # Rank sectors
        rankings = self.rank_sectors(sector_prices, as_of_date)
        
        if rankings.empty:
            logger.error("Cannot rebalance: no sector rankings available")
            return {
                'success': False,
                'error': 'No sector rankings available'
            }
        
        # Select top sectors
        new_sectors = self.select_top_sectors(rankings)
        
        # Calculate weights
        new_weights = self.calculate_sector_weights(new_sectors)
        
        # Identify transitions
        sectors_added = [s for s in new_sectors if s not in self.current_sectors]
        sectors_removed = [s for s in self.current_sectors if s not in new_sectors]
        sectors_maintained = [s for s in new_sectors if s in self.current_sectors]
        
        # Log transitions
        if sectors_added:
            logger.info(f"Sectors ADDED: {sectors_added}")
        if sectors_removed:
            logger.info(f"Sectors REMOVED: {sectors_removed}")
        if sectors_maintained:
            logger.info(f"Sectors MAINTAINED: {sectors_maintained}")
        
        # Update state
        self.current_sectors = new_sectors
        self.sector_weights = new_weights
        self.last_rebalance_date = as_of_date or datetime.now()
        
        # Prepare results
        result = {
            'success': True,
            'date': self.last_rebalance_date,
            'selected_sectors': new_sectors,
            'weights': new_weights,
            'sectors_added': sectors_added,
            'sectors_removed': sectors_removed,
            'sectors_maintained': sectors_maintained,
            'rankings': rankings.to_dict('records')
        }
        
        logger.info("Sector rebalancing complete")
        logger.info("=" * 60)
        
        return result
    
    def _calculate_sector_momentum(self, prices: pd.Series, period: int) -> float:
        """
        Calculate total return over period
        
        Args:
            prices: Price series
            period: Lookback period in days
        
        Returns:
            Total return as decimal
        """
        if len(prices) < period:
            return 0.0
        
        try:
            end_price = prices.iloc[-1]
            start_price = prices.iloc[-period]
            
            momentum = (end_price / start_price) - 1
            
            return momentum
            
        except Exception as e:
            logger.error(f"Error calculating momentum: {e}")
            return 0.0
    
    def _check_ma_filter(self, prices: pd.Series) -> bool:
        """
        Check if sector passes 200-day MA filter
        
        Args:
            prices: Price series
        
        Returns:
            True if price > 200-day MA, False otherwise
        """
        if len(prices) < 200:
            return True  # Pass if insufficient data
        
        try:
            ma_200 = calculate_moving_average(prices, 200)
            
            if ma_200.empty:
                return True
            
            current_price = prices.iloc[-1]
            current_ma = ma_200.iloc[-1]
            
            return current_price > current_ma
            
        except Exception as e:
            logger.error(f"Error checking MA filter: {e}")
            return True  # Pass on error
    
    def get_current_allocation(self) -> Dict:
        """
        Get current sector allocation
        
        Returns:
            Dict with current allocation details
        """
        return {
            'sectors': self.current_sectors,
            'weights': self.sector_weights,
            'last_rebalance': self.last_rebalance_date,
            'total_allocation': sum(self.sector_weights.values()) if self.sector_weights else 0.0
        }
    
    def generate_rotation_report(self, rankings_df: pd.DataFrame) -> str:
        """
        Generate sector rotation report
        
        Args:
            rankings_df: DataFrame with sector rankings
        
        Returns:
            Formatted report string
        """
        report = f"\n{'=' * 80}\n"
        report += f"SECTOR ROTATION REPORT - {datetime.now().strftime('%Y-%m-%d')}\n"
        report += f"{'=' * 80}\n\n"
        
        report += f"Strategy Parameters:\n"
        report += f"  Top K Sectors: {self.top_k}\n"
        report += f"  Momentum Period: {self.momentum_period} days (6 months)\n"
        report += f"  Tiebreaker Period: {self.tiebreaker_period} days (1 month)\n"
        report += f"  MA Filter: {'Enabled' if self.use_ma_filter else 'Disabled'}\n"
        report += f"  Weight per Sector: {self.weight_per_sector:.1%}\n\n"
        
        if not rankings_df.empty:
            report += f"SECTOR RANKINGS:\n"
            report += f"{'-' * 80}\n"
            report += f"{'Rank':<6}{'Sector':<30}{'6M Mom':<12}{'1M Mom':<12}{'Score':<12}{'Filter':<8}\n"
            report += f"{'-' * 80}\n"
            
            for _, row in rankings_df.head(10).iterrows():
                report += f"{row['rank']:<6}{row['sector']:<30}"
                report += f"{row['momentum_6m']:<12.2%}{row['momentum_1m']:<12.2%}"
                report += f"{row['composite_score']:<12.4f}"
                report += f"{'PASS' if row['ma_filter_pass'] else 'FAIL':<8}\n"
            
            report += f"{'-' * 80}\n\n"
        
        if self.current_sectors:
            report += f"CURRENT ALLOCATION:\n"
            report += f"  Selected Sectors: {', '.join(self.current_sectors)}\n"
            for sector, weight in self.sector_weights.items():
                report += f"    {sector}: {weight:.1%}\n"
            report += f"  Last Rebalance: {self.last_rebalance_date}\n"
        
        report += f"\n{'=' * 80}\n"
        
        return report


if __name__ == "__main__":
    # Test the sector rotation engine
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    engine = SectorRotationEngine()
    
    # Generate sample sector data
    dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='B')
    
    test_sectors = {}
    for i, sector in enumerate(list(NSESectors.SECTOR_TICKERS.keys())[:5]):
        # Different momentum levels for different sectors
        returns = np.random.randn(len(dates)) * 0.01 + (0.0003 * (5-i))
        prices = 1000 * (1 + pd.Series(returns)).cumprod()
        
        test_sectors[sector] = pd.DataFrame({
            'Open': prices.values,
            'High': prices.values * 1.01,
            'Low': prices.values * 0.99,
            'Close': prices.values,
            'Volume': np.random.uniform(10000000, 50000000, len(dates))
        }, index=dates)
    
    # Test ranking and selection
    result = engine.rebalance_sectors(test_sectors)
    
    if result['success']:
        rankings_df = pd.DataFrame(result['rankings'])
        report = engine.generate_rotation_report(rankings_df)
        print(report)
    else:
        print(f"Rebalancing failed: {result.get('error')}")
