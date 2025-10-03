"""
Dual-Approach Portfolio Manager

Implements CLIENT SPECIFICATION: 60/40 Strategy
- 60% Core: Sector rotation based on momentum with trend confirmation
- 40% Satellite: Multi-factor stock selection for alpha generation

This combines sector-level momentum capture with individual stock alpha,
providing both systematic exposure and active selection benefits.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from config import Config
from utils.logger import setup_logger
from strategy.sector_rotation import SectorRotationEngine
from strategy.stock_selection import StockSelectionEngine
from strategy.implementation_mode import ImplementationModeHandler

logger = setup_logger(__name__)


class DualApproachPortfolioManager:
    """
    Manages the dual-approach portfolio with 60% core and 40% satellite
    """
    
    def __init__(self):
        self.config = Config()
        
        # Allocation split
        self.core_allocation = Config.CORE_ALLOCATION      # 60%
        self.satellite_allocation = Config.SATELLITE_ALLOCATION  # 40%
        
        # Strategy engines
        self.sector_engine = SectorRotationEngine()
        self.stock_selector = StockSelectionEngine()
        self.implementation = ImplementationModeHandler()
        
        logger.info(f"Implementation Mode: {self.implementation.mode}")
        
        # Current holdings
        self.core_holdings = {}      # Sector-based stocks (60%)
        self.satellite_holdings = {} # Alpha stocks (40%)
        
        # Capital tracking
        self.total_capital = 0
        self.core_capital = 0
        self.satellite_capital = 0
        
        logger.info(f"DualApproachPortfolioManager initialized")
        logger.info(f"Core: {self.core_allocation:.0%} | Satellite: {self.satellite_allocation:.0%}")
    
    def rebalance_portfolio(self,
                           sector_prices: Dict[str, pd.DataFrame],
                           stocks_data: Dict[str, Dict],
                           stocks_prices: Dict[str, pd.DataFrame],
                           total_capital: float,
                           as_of_date: datetime = None) -> Dict:
        """
        Execute full portfolio rebalance using dual-approach
        
        Args:
            sector_prices: Price data for sectors
            stocks_data: Fundamental and metadata for stocks
            stocks_prices: Price data for individual stocks
            total_capital: Total portfolio capital
            as_of_date: Rebalancing date
        
        Returns:
            Dict with rebalancing results and orders
        """
        logger.info("=" * 80)
        logger.info("DUAL-APPROACH PORTFOLIO REBALANCING")
        logger.info("=" * 80)
        
        self.total_capital = total_capital
        self.core_capital = total_capital * self.core_allocation
        self.satellite_capital = total_capital * self.satellite_allocation
        
        logger.info(f"Total Capital: ₹{total_capital:,.0f}")
        logger.info(f"Core Capital (60%): ₹{self.core_capital:,.0f}")
        logger.info(f"Satellite Capital (40%): ₹{self.satellite_capital:,.0f}")
        
        # PART 1: Core Allocation (60%) - Sector Rotation
        logger.info("\n" + "-" * 80)
        logger.info("PART 1: CORE ALLOCATION (60%) - SECTOR ROTATION")
        logger.info("-" * 80)
        
        core_result = self._rebalance_core(
            sector_prices, stocks_data, stocks_prices, as_of_date
        )
        
        # PART 2: Satellite Allocation (40%) - Stock Selection
        logger.info("\n" + "-" * 80)
        logger.info("PART 2: SATELLITE ALLOCATION (40%) - STOCK SELECTION")
        logger.info("-" * 80)
        
        satellite_result = self._rebalance_satellite(
            stocks_data, stocks_prices, as_of_date
        )
        
        # Combine results
        result = {
            'success': True,
            'date': as_of_date or datetime.now(),
            'total_capital': total_capital,
            
            # Core results
            'core': {
                'allocation': self.core_allocation,
                'capital': self.core_capital,
                'selected_sectors': core_result['selected_sectors'],
                'stocks': core_result['stocks'],
                'positions': core_result['positions']
            },
            
            # Satellite results
            'satellite': {
                'allocation': self.satellite_allocation,
                'capital': self.satellite_capital,
                'stocks': satellite_result['stocks'],
                'positions': satellite_result['positions']
            },
            
            # Combined orders
            'orders': self._generate_orders(core_result, satellite_result, stocks_prices)
        }
        
        logger.info("\n" + "=" * 80)
        logger.info("REBALANCING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Core Stocks: {len(core_result['stocks'])}")
        logger.info(f"Satellite Stocks: {len(satellite_result['stocks'])}")
        logger.info(f"Total Positions: {len(core_result['stocks']) + len(satellite_result['stocks'])}")
        logger.info(f"Orders Generated: {len(result['orders'])}")
        
        return result
    
    def _rebalance_core(self,
                       sector_prices: Dict[str, pd.DataFrame],
                       stocks_data: Dict[str, Dict],
                       stocks_prices: Dict[str, pd.DataFrame],
                       as_of_date: datetime) -> Dict:
        """
        Rebalance core allocation (60%) using sector rotation
        
        Strategy:
        1. Select top K sectors (default: 3) based on momentum
        2. Within each sector, select top stocks
        3. Equal weight across sectors, equal weight within sectors
        """
        
        # Get top sectors
        sector_result = self.sector_engine.rebalance_sectors(sector_prices, as_of_date)
        
        if not sector_result['success']:
            logger.error("Core rebalancing failed: sector selection failed")
            return {'stocks': [], 'positions': {}}
        
        selected_sectors = sector_result['selected_sectors']
        stocks_per_sector = Config.CORE_CONFIG['stocks_per_sector']
        
        logger.info(f"Selected Sectors: {selected_sectors}")
        logger.info(f"Stocks per Sector: {stocks_per_sector}")
        
        # For each sector, select top stocks
        core_stocks = []
        sector_allocations = {}
        
        capital_per_sector = self.core_capital / len(selected_sectors)
        
        for sector in selected_sectors:
            # Get stocks in this sector
            sector_stocks = {
                symbol: data for symbol, data in stocks_data.items()
                if data.get('sector') == sector
            }
            
            if not sector_stocks:
                logger.warning(f"No stocks found for sector: {sector}")
                continue
            
            # Score and rank stocks in this sector
            # StockSelectionEngine expects list of symbols
            sector_symbols = list(sector_stocks.keys())
            scored_stocks = self.stock_selector.select_stocks(
                sector_symbols, stocks_data, stocks_prices
            )
            
            # Select top N stocks
            top_stocks = scored_stocks.head(stocks_per_sector)['symbol'].tolist()
            
            # Equal weight within sector
            weight_per_stock = capital_per_sector / len(top_stocks)
            
            for symbol in top_stocks:
                core_stocks.append({
                    'symbol': symbol,
                    'sector': sector,
                    'capital': weight_per_stock,
                    'weight': weight_per_stock / self.total_capital,
                    'type': 'core'
                })
            
            sector_allocations[sector] = {
                'capital': capital_per_sector,
                'stocks': top_stocks
            }
            
            logger.info(f"  {sector}: {len(top_stocks)} stocks, ₹{weight_per_stock:,.0f} per stock")
        
        # Create positions dict
        positions = {
            stock['symbol']: stock['capital']
            for stock in core_stocks
        }
        
        return {
            'selected_sectors': selected_sectors,
            'stocks': core_stocks,
            'positions': positions,
            'sector_allocations': sector_allocations
        }
    
    def _rebalance_satellite(self,
                            stocks_data: Dict[str, Dict],
                            stocks_prices: Dict[str, pd.DataFrame],
                            as_of_date: datetime) -> Dict:
        """
        Rebalance satellite allocation (40%) using multi-factor selection
        
        Strategy:
        1. Score ALL stocks using multi-factor model
        2. Select top N stocks (default: 15)
        3. Equal weight across selected stocks
        """
        
        num_stocks = Config.SATELLITE_CONFIG['top_stocks']
        
        logger.info(f"Selecting top {num_stocks} stocks from entire universe")
        
        # Score all stocks
        all_symbols = list(stocks_data.keys())
        scored_stocks = self.stock_selector.select_stocks(
            all_symbols, stocks_data, stocks_prices
        )
        
        if scored_stocks.empty:
            logger.error("Satellite rebalancing failed: no stocks scored")
            return {'stocks': [], 'positions': {}}
        
        # Select top N stocks
        top_stocks = scored_stocks.head(num_stocks)
        
        # Equal weight allocation
        capital_per_stock = self.satellite_capital / num_stocks
        
        satellite_stocks = []
        for _, row in top_stocks.iterrows():
            satellite_stocks.append({
                'symbol': row['symbol'],
                'sector': stocks_data[row['symbol']].get('sector', 'Unknown'),
                'capital': capital_per_stock,
                'weight': capital_per_stock / self.total_capital,
                'composite_score': row['composite_score'],
                'type': 'satellite'
            })
        
        # Create positions dict
        positions = {
            stock['symbol']: stock['capital']
            for stock in satellite_stocks
        }
        
        logger.info(f"Selected {len(satellite_stocks)} satellite stocks")
        logger.info(f"Capital per stock: ₹{capital_per_stock:,.0f}")
        
        return {
            'stocks': satellite_stocks,
            'positions': positions
        }
    
    def _generate_orders(self,
                        core_result: Dict,
                        satellite_result: Dict,
                        stocks_prices: Dict[str, pd.DataFrame]) -> List[Dict]:
        """
        Generate buy/sell orders for rebalancing
        
        Args:
            core_result: Core allocation results
            satellite_result: Satellite allocation results
            stocks_prices: Current stock prices
        
        Returns:
            List of order dictionaries
        """
        orders = []
        
        # Combine target positions
        target_positions = {}
        target_positions.update(core_result['positions'])
        
        # For satellite, handle overlaps
        for symbol, capital in satellite_result['positions'].items():
            if symbol in target_positions:
                # Stock in both core and satellite - combine capital
                target_positions[symbol] += capital
            else:
                target_positions[symbol] = capital
        
        # Generate sell orders (stocks to exit)
        current_symbols = set(list(self.core_holdings.keys()) + list(self.satellite_holdings.keys()))
        target_symbols = set(target_positions.keys())
        
        symbols_to_sell = current_symbols - target_symbols
        
        for symbol in symbols_to_sell:
            current_holding = self.core_holdings.get(symbol, 0) + self.satellite_holdings.get(symbol, 0)
            
            if current_holding > 0:
                orders.append({
                    'action': 'SELL',
                    'symbol': symbol,
                    'amount': current_holding,
                    'reason': 'Exit position'
                })
        
        # Generate buy orders (new positions or increases)
        for symbol, target_capital in target_positions.items():
            current_holding = self.core_holdings.get(symbol, 0) + self.satellite_holdings.get(symbol, 0)
            
            if target_capital > current_holding:
                # Need to buy
                amount_to_buy = target_capital - current_holding
                
                orders.append({
                    'action': 'BUY',
                    'symbol': symbol,
                    'amount': amount_to_buy,
                    'target_capital': target_capital,
                    'reason': 'Enter/Increase position'
                })
            elif target_capital < current_holding:
                # Need to reduce
                amount_to_sell = current_holding - target_capital
                
                orders.append({
                    'action': 'SELL',
                    'symbol': symbol,
                    'amount': amount_to_sell,
                    'target_capital': target_capital,
                    'reason': 'Reduce position'
                })
        
        logger.info(f"Generated {len(orders)} orders ({sum(1 for o in orders if o['action']=='BUY')} BUY, {sum(1 for o in orders if o['action']=='SELL')} SELL)")
        
        return orders
    
    def update_holdings(self, executed_orders: List[Dict]):
        """
        Update holdings after order execution
        
        Args:
            executed_orders: List of executed orders with final amounts
        """
        for order in executed_orders:
            symbol = order['symbol']
            action = order['action']
            amount = order['amount']
            order_type = order.get('type', 'core')  # core or satellite
            
            if order_type == 'core':
                holdings = self.core_holdings
            else:
                holdings = self.satellite_holdings
            
            if action == 'BUY':
                holdings[symbol] = holdings.get(symbol, 0) + amount
            elif action == 'SELL':
                holdings[symbol] = max(0, holdings.get(symbol, 0) - amount)
                if holdings[symbol] == 0:
                    del holdings[symbol]
        
        logger.info("Holdings updated after order execution")
    
    def get_portfolio_summary(self) -> Dict:
        """
        Get current portfolio summary
        
        Returns:
            Dict with portfolio details
        """
        total_core = sum(self.core_holdings.values())
        total_satellite = sum(self.satellite_holdings.values())
        total = total_core + total_satellite
        
        return {
            'total_value': total,
            'core': {
                'value': total_core,
                'allocation': total_core / total if total > 0 else 0,
                'num_positions': len(self.core_holdings)
            },
            'satellite': {
                'value': total_satellite,
                'allocation': total_satellite / total if total > 0 else 0,
                'num_positions': len(self.satellite_holdings)
            },
            'total_positions': len(self.core_holdings) + len(self.satellite_holdings)
        }
    
    def generate_report(self, rebalance_result: Dict) -> str:
        """
        Generate detailed portfolio report
        
        Args:
            rebalance_result: Results from rebalance_portfolio()
        
        Returns:
            Formatted report string
        """
        report = f"\n{'=' * 100}\n"
        report += f"DUAL-APPROACH PORTFOLIO REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"{'=' * 100}\n\n"
        
        # Summary
        report += f"PORTFOLIO SUMMARY:\n"
        report += f"{'-' * 100}\n"
        report += f"Total Capital: ₹{rebalance_result['total_capital']:,.0f}\n\n"
        
        # Core allocation
        core = rebalance_result['core']
        report += f"CORE ALLOCATION ({core['allocation']:.0%}):\n"
        report += f"  Capital: ₹{core['capital']:,.0f}\n"
        report += f"  Selected Sectors: {', '.join(core['selected_sectors'])}\n"
        report += f"  Number of Stocks: {len(core['stocks'])}\n"
        report += f"  Positions:\n"
        
        for stock in core['stocks'][:10]:  # Show first 10
            report += f"    {stock['symbol']:<15} {stock['sector']:<25} ₹{stock['capital']:>12,.0f} ({stock['weight']:.2%})\n"
        
        if len(core['stocks']) > 10:
            report += f"    ... and {len(core['stocks']) - 10} more stocks\n"
        
        report += f"\n"
        
        # Satellite allocation
        satellite = rebalance_result['satellite']
        report += f"SATELLITE ALLOCATION ({satellite['allocation']:.0%}):\n"
        report += f"  Capital: ₹{satellite['capital']:,.0f}\n"
        report += f"  Number of Stocks: {len(satellite['stocks'])}\n"
        report += f"  Positions:\n"
        
        for stock in satellite['stocks'][:10]:  # Show first 10
            report += f"    {stock['symbol']:<15} {stock['sector']:<25} ₹{stock['capital']:>12,.0f} ({stock['weight']:.2%})\n"
        
        if len(satellite['stocks']) > 10:
            report += f"    ... and {len(satellite['stocks']) - 10} more stocks\n"
        
        report += f"\n{'-' * 100}\n"
        
        # Orders summary
        orders = rebalance_result['orders']
        buy_orders = [o for o in orders if o['action'] == 'BUY']
        sell_orders = [o for o in orders if o['action'] == 'SELL']
        
        report += f"\nORDERS SUMMARY:\n"
        report += f"  Total Orders: {len(orders)}\n"
        report += f"  Buy Orders: {len(buy_orders)}\n"
        report += f"  Sell Orders: {len(sell_orders)}\n"
        
        report += f"\n{'=' * 100}\n"
        
        return report


if __name__ == "__main__":
    # Test the dual-approach manager
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    manager = DualApproachPortfolioManager()
    
    print("Dual-Approach Portfolio Manager initialized successfully!")
    print(f"Core Allocation: {manager.core_allocation:.0%}")
    print(f"Satellite Allocation: {manager.satellite_allocation:.0%}")
    
    summary = manager.get_portfolio_summary()
    print(f"\nPortfolio Summary: {summary}")
