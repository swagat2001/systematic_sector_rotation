"""
Portfolio Manager for Systematic Sector Rotation Strategy

Manages the complete portfolio combining:
- 60% Sector Rotation (core allocation)
- 40% Stock Selection (satellite allocation)

Responsibilities:
1. Position sizing using risk adjustment (Z+/σ)
2. Risk management (beta/volatility penalties, position limits)
3. Rebalancing logic (monthly schedule)
4. Portfolio weight calculation
5. Trade list generation (buy/sell/hold)
6. Performance tracking and attribution

This module integrates sector rotation and stock selection engines to create
a unified portfolio with proper risk controls and rebalancing discipline.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from config import Config
from strategy.sector_rotation import SectorRotationEngine
from strategy.stock_selection import StockSelectionEngine
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PortfolioManager:
    """
    Manages the complete portfolio with sector rotation and stock selection
    """
    
    def __init__(self):
        self.config = Config()
        
        # Initialize strategy engines
        self.sector_engine = SectorRotationEngine()
        self.stock_engine = StockSelectionEngine()
        
        # Portfolio allocation (NEW CONFIG STRUCTURE)
        self.sector_allocation = Config.CORE_ALLOCATION  # 60%
        self.stock_allocation = Config.SATELLITE_ALLOCATION  # 40%
        
        # Risk limits (with fallbacks for old config)
        self.max_position_size = getattr(Config, 'MAX_POSITION_SIZE', 
                                         Config.RISK_CONFIG.get('max_position_size', 0.10))
        self.max_sector_exposure = getattr(Config, 'MAX_SECTOR_EXPOSURE',
                                           Config.RISK_CONFIG.get('max_sector_exposure', 0.30))
        
        # Current portfolio state
        self.current_portfolio = {}
        self.last_rebalance_date = None
        self.portfolio_history = []
        
        logger.info("PortfolioManager initialized")
        logger.info(f"  Sector allocation: {self.sector_allocation:.0%}")
        logger.info(f"  Stock allocation: {self.stock_allocation:.0%}")
    
    def rebalance_portfolio(self,
                           sector_prices: Dict[str, pd.DataFrame],
                           stocks_data: Dict[str, Dict],
                           stocks_prices: Dict[str, pd.DataFrame],
                           benchmark_data: pd.DataFrame = None,
                           sector_mapping: Dict[str, str] = None,
                           as_of_date: datetime = None) -> Dict:
        """
        Execute complete portfolio rebalancing
        
        Args:
            sector_prices: Dict of sector index prices
            stocks_data: Dict of stock fundamental data
            stocks_prices: Dict of stock prices
            benchmark_data: Benchmark price data
            sector_mapping: Stock-to-sector mapping
            as_of_date: Rebalancing date
        
        Returns:
            Dict with rebalancing results
        """
        logger.info("=" * 80)
        logger.info("EXECUTING PORTFOLIO REBALANCING")
        logger.info("=" * 80)
        
        rebalance_date = as_of_date or datetime.now()
        
        try:
            # Step 1: Sector rotation (60% allocation)
            logger.info("\nStep 1: Sector Rotation (60% allocation)")
            logger.info("-" * 80)
            sector_result = self.sector_engine.rebalance_sectors(
                sector_prices,
                as_of_date
            )
            
            if not sector_result['success']:
                return {'success': False, 'error': 'Sector rotation failed'}
            
            # Step 2: Stock selection (40% allocation)
            logger.info("\nStep 2: Stock Selection (40% allocation)")
            logger.info("-" * 80)
            stock_result = self.stock_engine.select_stocks(
                stocks_data,
                stocks_prices,
                benchmark_data,
                sector_mapping,
                previous_holdings=self.stock_engine.current_holdings
            )
            
            if not stock_result['success']:
                return {'success': False, 'error': 'Stock selection failed'}
            
            # Step 3: Combine allocations
            logger.info("\nStep 3: Combining Portfolio Allocations")
            logger.info("-" * 80)
            new_portfolio = self._combine_allocations(
                sector_result,
                stock_result
            )
            
            # Step 4: Apply risk controls
            logger.info("\nStep 4: Applying Risk Controls")
            logger.info("-" * 80)
            new_portfolio = self._apply_risk_controls(new_portfolio)
            
            # Step 5: Generate trade list
            logger.info("\nStep 5: Generating Trade List")
            logger.info("-" * 80)
            trades = self._generate_trades(new_portfolio)
            
            # Step 6: Update portfolio state
            old_portfolio = self.current_portfolio.copy()
            self.current_portfolio = new_portfolio
            self.last_rebalance_date = rebalance_date
            
            # Add to history
            self.portfolio_history.append({
                'date': rebalance_date,
                'portfolio': new_portfolio.copy(),
                'sector_result': sector_result,
                'stock_result': stock_result
            })
            
            # Prepare results
            result = {
                'success': True,
                'date': rebalance_date,
                'portfolio': new_portfolio,
                'old_portfolio': old_portfolio,
                'trades': trades,
                'sector_result': sector_result,
                'stock_result': stock_result,
                'num_positions': len(new_portfolio),
                'total_weight': sum(new_portfolio.values())
            }
            
            logger.info(f"\nPortfolio rebalancing complete:")
            logger.info(f"  Total positions: {result['num_positions']}")
            logger.info(f"  Total weight: {result['total_weight']:.1%}")
            logger.info(f"  Trades generated: {len(trades)}")
            logger.info("=" * 80)
            
            return result
            
        except Exception as e:
            logger.error(f"Portfolio rebalancing failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _combine_allocations(self, sector_result: Dict, stock_result: Dict) -> Dict[str, float]:
        """Combine sector and stock allocations"""
        portfolio = {}
        
        # Add sector allocations
        sector_weights = sector_result.get('weights', {})
        for sector, weight in sector_weights.items():
            portfolio[f"SECTOR:{sector}"] = weight
        
        # Add stock allocations
        stock_weights = stock_result.get('weights', {})
        for symbol, weight in stock_weights.items():
            portfolio[symbol] = weight
        
        logger.info(f"Combined portfolio: {len(sector_weights)} sectors + {len(stock_weights)} stocks")
        
        return portfolio
    
    def _apply_risk_controls(self, portfolio: Dict[str, float]) -> Dict[str, float]:
        """Apply risk limits"""
        adjusted = portfolio.copy()
        
        positions_capped = 0
        for symbol, weight in adjusted.items():
            if weight > self.max_position_size:
                logger.warning(f"Position {symbol} capped: {weight:.1%} -> {self.max_position_size:.1%}")
                adjusted[symbol] = self.max_position_size
                positions_capped += 1
        
        if positions_capped > 0:
            total_weight = sum(adjusted.values())
            if total_weight > 0:
                scale_factor = 1.0 / total_weight
                for symbol in adjusted:
                    adjusted[symbol] *= scale_factor
            
            logger.info(f"  {positions_capped} positions capped and renormalized")
        
        return adjusted
    
    def _generate_trades(self, new_portfolio: Dict[str, float]) -> List[Dict]:
        """Generate trade list"""
        trades = []
        
        all_symbols = set(list(self.current_portfolio.keys()) + list(new_portfolio.keys()))
        
        for symbol in all_symbols:
            old_weight = self.current_portfolio.get(symbol, 0.0)
            new_weight = new_portfolio.get(symbol, 0.0)
            weight_change = new_weight - old_weight
            
            if abs(weight_change) < 0.0001:
                continue
            
            action = 'BUY' if old_weight == 0 else ('SELL' if new_weight == 0 else 'REBALANCE')
            
            trades.append({
                'symbol': symbol,
                'action': action,
                'old_weight': old_weight,
                'new_weight': new_weight,
                'change': weight_change
            })
        
        trades.sort(key=lambda x: abs(x['change']), reverse=True)
        
        logger.info(f"Generated {len(trades)} trades")
        
        return trades
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        if not self.current_portfolio:
            return {'positions': 0, 'total_weight': 0.0}
        
        sector_positions = [k for k in self.current_portfolio.keys() if k.startswith('SECTOR:')]
        stock_positions = [k for k in self.current_portfolio.keys() if not k.startswith('SECTOR:')]
        
        return {
            'total_positions': len(self.current_portfolio),
            'sector_positions': len(sector_positions),
            'stock_positions': len(stock_positions),
            'total_weight': sum(self.current_portfolio.values()),
            'last_rebalance': self.last_rebalance_date
        }
    
    def generate_portfolio_report(self, result: Dict) -> str:
        """Generate portfolio report"""
        if not result.get('success'):
            return f"Rebalancing failed: {result.get('error')}"
        
        report = f"\n{'=' * 100}\n"
        report += f"PORTFOLIO REPORT - {result['date'].strftime('%Y-%m-%d')}\n"
        report += f"{'=' * 100}\n\n"
        
        report += f"Total positions: {result['num_positions']}\n"
        report += f"Total weight: {result['total_weight']:.1%}\n\n"
        
        # Sector allocation
        report += f"SECTOR ALLOCATION (60%):\n"
        for sector, weight in result['sector_result']['weights'].items():
            report += f"  {sector:<40}{weight:>10.2%}\n"
        
        report += f"\nSTOCK ALLOCATION (40%):\n"
        report += f"  {result['stock_result']['num_stocks']} stocks selected\n"
        
        report += f"\nTRADES: {len(result['trades'])}\n"
        
        report += f"\n{'=' * 100}\n"
        
        return report


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from config import NSESectors
    
    manager = PortfolioManager()
    
    # Test with sample data
    dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='B')
    
    test_sectors = {}
    for sector in list(NSESectors.SECTOR_TICKERS.keys())[:3]:
        prices = 1000 * (1 + pd.Series(np.random.randn(len(dates)) * 0.01).cumsum())
        test_sectors[sector] = pd.DataFrame({
            'Close': prices.values,
            'Volume': 10000000
        }, index=dates)
    
    test_stocks = {'INFY': {'roe': 0.25, 'market_cap': 100000000000}}
    test_prices = {'INFY': pd.DataFrame({
        'Close': 1000 * (1 + pd.Series(np.random.randn(len(dates)) * 0.01).cumsum()).values,
        'Volume': 5000000
    }, index=dates)}
    
    result = manager.rebalance_portfolio(test_sectors, test_stocks, test_prices)
    
    if result['success']:
        print(manager.generate_portfolio_report(result))
