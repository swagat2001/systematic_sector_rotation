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

logger = setup_logger(__name__)


class DualApproachPortfolioManager:
    """
    Manages the dual-approach portfolio with 60% core and 40% satellite
    """
    
    def __init__(self):
        self.config = Config()
        
        # Allocation split
        self.core_allocation = Config.CORE_ALLOCATION  # 60%
        self.satellite_allocation = Config.SATELLITE_ALLOCATION  # 40%
        
        # Initialize strategy engines
        self.sector_engine = SectorRotationEngine()
        self.stock_selector = StockSelectionEngine()
        
        # Portfolio state
        self.current_positions = {}
        self.last_rebalance_date = None
        
        logger.info(f"Initialized DualApproachPortfolioManager")
        logger.info(f"Core allocation: {self.core_allocation*100}%")
        logger.info(f"Satellite allocation: {self.satellite_allocation*100}%")
    
    def rebalance_portfolio(self, 
                          sector_prices: Dict[str, pd.DataFrame],
                          stocks_data: Dict[str, Dict],
                          stocks_prices: Dict[str, pd.DataFrame],
                          as_of_date: datetime) -> Dict:
        """
        Execute complete portfolio rebalancing
        
        Args:
            sector_prices: Dict of {sector_name: price_df}
            stocks_data: Dict of {symbol: fundamental_data_dict}
            stocks_prices: Dict of {symbol: price_df}
            as_of_date: Rebalancing date
            
        Returns:
            Dict with rebalancing results
        """
        try:
            logger.info("=" * 60)
            logger.info(f"PORTFOLIO REBALANCING: {as_of_date.date()}")
            logger.info("=" * 60)
            
            # 1. Core Portfolio (60%): Sector rotation
            core_result = self._rebalance_core(
                sector_prices, stocks_data, stocks_prices, as_of_date
            )
            
            # 2. Satellite Portfolio (40%): Stock selection
            satellite_result = self._rebalance_satellite(
                stocks_data, stocks_prices, as_of_date
            )
            
            # 3. Combine portfolios
            combined_positions = self._combine_portfolios(
                core_result['positions'],
                satellite_result['positions']
            )
            
            # 4. Generate order list
            orders = self._generate_orders(
                combined_positions,
                self.current_positions
            )
            
            # Update state
            self.current_positions = combined_positions
            self.last_rebalance_date = as_of_date
            
            result = {
                'success': True,
                'date': as_of_date,
                'core': core_result,
                'satellite': satellite_result,
                'combined_positions': combined_positions,
                'orders': orders,
                'total_positions': len(combined_positions)
            }
            
            logger.info(f"Rebalancing complete: {len(combined_positions)} total positions")
            logger.info(f"Orders generated: {len(orders)} trades")
            
            return result
            
        except Exception as e:
            logger.error(f"Portfolio rebalancing failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'date': as_of_date
            }
    
    def _rebalance_core(self,
                       sector_prices: Dict[str, pd.DataFrame],
                       stocks_data: Dict[str, Dict],
                       stocks_prices: Dict[str, pd.DataFrame],
                       as_of_date: datetime) -> Dict:
        """
        Rebalance core 60% allocation using sector rotation
        
        FIXED VERSION - Uses correct method signatures and parameter names
        """
        try:
            logger.info("EXECUTING CORE ALLOCATION (60%)")
            logger.info("=" * 60)
            
            # Step 1: Rank sectors
            logger.info("Step 1: Ranking sectors by momentum...")
            
            # rank_sectors() returns DataFrame
            rankings_df = self.sector_engine.rank_sectors(
                sector_prices,
                as_of_date=as_of_date
            )
            
            # Check if DataFrame is empty
                        # Check if DataFrame is empty
            if rankings_df.empty:
                logger.warning("No sectors ranked - insufficient data, skipping core allocation")
                return {
                    'success': True,
                    'positions': {},
                    'sectors': [],
                    'allocation': self.core_allocation
                }

            
            # Get top sectors from the DataFrame
            top_k = Config.CORE_CONFIG['top_sectors']  # Default: 3
            
            # Select top sectors by composite_score
            if 'composite_score' in rankings_df.columns:
                top_sectors_df = rankings_df.nlargest(top_k, 'composite_score')
            elif 'momentum_6m' in rankings_df.columns:
                # Fallback to 6-month momentum
                top_sectors_df = rankings_df.nlargest(top_k, 'momentum_6m')
            else:
                # Use first top_k rows
                top_sectors_df = rankings_df.head(top_k)
            
            # Extract sector names
            if 'sector' in top_sectors_df.columns:
                top_sectors = top_sectors_df['sector'].tolist()
            elif 'name' in top_sectors_df.columns:
                top_sectors = top_sectors_df['name'].tolist()
            else:
                # Use index as sector names
                top_sectors = top_sectors_df.index.tolist()
            
            if not top_sectors:
                raise ValueError("No top sectors selected")
                
            logger.info(f"Selected sectors: {top_sectors}")
            
            # Calculate per-sector allocation
            core_capital = self.core_allocation  # 60% as weight
            per_sector_weight = core_capital / len(top_sectors)
            stocks_per_sector = Config.CORE_CONFIG['stocks_per_sector']
            
            logger.info(f"Per-sector weight: {per_sector_weight*100:.2f}%")
            logger.info(f"Stocks per sector: {stocks_per_sector}")
            
            # Step 2: Select top stocks within each sector
            core_positions = {}
            
            for sector in top_sectors:
                logger.info(f"\nProcessing sector: {sector}")
                
                # Get stocks in this sector
                sector_stocks = {
                    symbol: data for symbol, data in stocks_data.items()
                    if data.get('sector') == sector
                }
                
                if not sector_stocks:
                    logger.warning(f"No stocks found for sector {sector}")
                    continue
                
                logger.info(f"  Found {len(sector_stocks)} stocks in {sector}")
                
                # Filter stocks that have price data
                sector_stocks_with_prices = {
                    symbol: data for symbol, data in sector_stocks.items()
                    if symbol in stocks_prices and not stocks_prices[symbol].empty
                }
                
                if not sector_stocks_with_prices:
                    logger.warning(f"No stocks with price data for {sector}")
                    continue
                
                # Create proper dictionary for stocks_prices filtered to this sector
                sector_stocks_prices = {
                    symbol: prices for symbol, prices in stocks_prices.items()
                    if symbol in sector_stocks_with_prices
                }
                
                # ==================== FIX: Use correct parameters ====================
                # StockSelectionEngine.select_stocks() signature:
                # def select_stocks(stocks_data, stocks_prices, benchmark_data=None, 
                #                   sector_mapping=None, previous_holdings=None)
                
                selection_result = self.stock_selector.select_stocks(
                    sector_stocks_with_prices,  # stocks_data: Dict[str, Dict]
                    sector_stocks_prices,        # stocks_prices: Dict[str, pd.DataFrame]
                    benchmark_data=None,
                    sector_mapping=None,
                    previous_holdings=None
                )
                # ====================================================================
                
                if not selection_result['success']:
                    logger.warning(f"Stock selection failed for {sector}")
                    continue
                
                # Extract selected stocks and limit to stocks_per_sector
                selected_stocks = selection_result.get('selected_stocks', [])
                all_scores_df = selection_result.get('all_scores', pd.DataFrame())
                
                # Limit to stocks_per_sector
                if len(selected_stocks) > stocks_per_sector:
                    if not all_scores_df.empty and 'composite_score' in all_scores_df.columns:
                        # Use 'symbol' column if it exists, otherwise use index
                        if 'symbol' in all_scores_df.columns:
                            # Filter to only selected stocks
                            selected_scores = all_scores_df[all_scores_df['symbol'].isin(selected_stocks)]
                            top_stocks_df = selected_scores.nlargest(stocks_per_sector, 'composite_score')
                            selected_stocks = top_stocks_df['symbol'].tolist()
                        else:
                            # Use index
                            selected_scores = all_scores_df.loc[all_scores_df.index.isin(selected_stocks)]
                            top_stocks_df = selected_scores.nlargest(stocks_per_sector, 'composite_score')
                            selected_stocks = top_stocks_df.index.tolist()
                    else:
                        # Just take first N
                        selected_stocks = selected_stocks[:stocks_per_sector]
                
                logger.info(f"  Selected {len(selected_stocks)} stocks: {selected_stocks}")
                
                # Equal weight within sector
                if len(selected_stocks) > 0:
                    per_stock_weight = per_sector_weight / len(selected_stocks)
                    
                    for symbol in selected_stocks:
                        core_positions[symbol] = {
                            'weight': per_stock_weight,
                            'sector': sector,
                            'allocation_type': 'core'
                        }
                        logger.info(f"    {symbol}: {per_stock_weight*100:.2f}%")
            
            logger.info(f"\nCore portfolio: {len(core_positions)} positions")
            
            return {
                'success': True,
                'positions': core_positions,
                'sectors': top_sectors,
                'allocation': core_capital
            }
            
        except Exception as e:
            logger.error(f"Core rebalancing failed: {str(e)}", exc_info=True)
            raise
    
    def _rebalance_satellite(self,
                           stocks_data: Dict[str, Dict],
                           stocks_prices: Dict[str, pd.DataFrame],
                           as_of_date: datetime) -> Dict:
        """
        Rebalance satellite 40% allocation using multi-factor stock selection
        
        FIXED VERSION - Uses correct method signature
        """
        try:
            logger.info("\nEXECUTING SATELLITE ALLOCATION (40%)")
            logger.info("=" * 60)
            
            satellite_capital = self.satellite_allocation  # 40% as weight
            top_n_stocks = Config.SATELLITE_CONFIG['top_stocks']
            
            logger.info(f"Satellite capital: {satellite_capital*100}%")
            logger.info(f"Target stocks: {top_n_stocks}")
            
            # ==================== FIX: Use correct parameters ====================
            # StockSelectionEngine.select_stocks() signature:
            # def select_stocks(stocks_data, stocks_prices, benchmark_data=None, 
            #                   sector_mapping=None, previous_holdings=None)
            
            # Select top stocks across all sectors
            selection_result = self.stock_selector.select_stocks(
                stocks_data,
                stocks_prices,
                benchmark_data=None,
                sector_mapping=None,
                previous_holdings=list(self.current_positions.keys()) if self.current_positions else None
            )
            # ====================================================================
            
            if not selection_result['success']:
                raise ValueError("Satellite stock selection failed")
            
            selected_stocks = selection_result['selected_stocks']
            stock_weights = selection_result.get('weights', {})
            all_scores_df = selection_result.get('all_scores', pd.DataFrame())
            
            # ✓ SAFETY CHECK: Handle case when no stocks are selected
            if not selected_stocks:
                logger.warning("No stocks selected for satellite - returning empty positions")
                return {
                    'success': True,
                    'positions': {},
                    'allocation': satellite_capital
                }
            
            # Limit to top_n_stocks
            if len(selected_stocks) > top_n_stocks:
                if not all_scores_df.empty and 'composite_score' in all_scores_df.columns:
                    # Use 'symbol' column if it exists, otherwise use index
                    if 'symbol' in all_scores_df.columns:
                        selected_scores = all_scores_df[all_scores_df['symbol'].isin(selected_stocks)]
                        top_stocks_df = selected_scores.nlargest(top_n_stocks, 'composite_score')
                        selected_stocks = top_stocks_df['symbol'].tolist()
                    else:
                        selected_scores = all_scores_df.loc[all_scores_df.index.isin(selected_stocks)]
                        top_stocks_df = selected_scores.nlargest(top_n_stocks, 'composite_score')
                        selected_stocks = top_stocks_df.index.tolist()
                else:
                    selected_stocks = selected_stocks[:top_n_stocks]
            
            logger.info(f"Selected {len(selected_stocks)} stocks for satellite")
            
            # Normalize weights to sum to satellite_capital
            if stock_weights:
                # Filter weights to only selected stocks
                filtered_weights = {k: v for k, v in stock_weights.items() if k in selected_stocks}
                total_weight = sum(filtered_weights.values())
                
                if total_weight > 0:
                    normalized_weights = {
                        symbol: (weight / total_weight) * satellite_capital
                        for symbol, weight in filtered_weights.items()
                    }
                else:
                    # Fallback to equal weight
                    per_stock_weight = satellite_capital / len(selected_stocks)
                    normalized_weights = {symbol: per_stock_weight for symbol in selected_stocks}
            else:
                # Equal weight if no weights provided
                per_stock_weight = satellite_capital / len(selected_stocks)
                normalized_weights = {symbol: per_stock_weight for symbol in selected_stocks}
            
            satellite_positions = {}
            for symbol in selected_stocks:
                satellite_positions[symbol] = {
                    'weight': normalized_weights.get(symbol, 0),
                    'sector': stocks_data.get(symbol, {}).get('sector', 'Unknown'),
                    'allocation_type': 'satellite'
                }
                logger.info(f"  {symbol}: {normalized_weights.get(symbol, 0)*100:.2f}%")
            
            logger.info(f"\nSatellite portfolio: {len(satellite_positions)} positions")
            
            return {
                'success': True,
                'positions': satellite_positions,
                'allocation': satellite_capital
            }
            
        except Exception as e:
            logger.error(f"Satellite rebalancing failed: {str(e)}", exc_info=True)
            raise
    
    def _combine_portfolios(self,
                           core_positions: Dict,
                           satellite_positions: Dict) -> Dict:
        """
        Combine core and satellite positions, handling overlaps
        
        If a stock appears in both core and satellite, combine weights
        """
        combined = {}
        
        # Add all core positions
        for symbol, data in core_positions.items():
            combined[symbol] = data.copy()
        
        # Add satellite positions (or combine if overlap)
        for symbol, data in satellite_positions.items():
            if symbol in combined:
                # Stock is in both - combine weights
                combined[symbol]['weight'] += data['weight']
                combined[symbol]['allocation_type'] = 'core+satellite'
                logger.info(f"Combined position: {symbol} "
                          f"({combined[symbol]['weight']*100:.2f}%)")
            else:
                combined[symbol] = data.copy()
        
        # Validate total weight
        total_weight = sum(pos['weight'] for pos in combined.values())
        logger.info(f"\nTotal portfolio weight: {total_weight*100:.2f}%")
        
        if abs(total_weight - 1.0) > 0.01:  # Allow 1% tolerance
            logger.warning(f"Portfolio weight {total_weight*100:.2f}% != 100%")
        
        return combined
    
    def _generate_orders(self,
                        target_positions: Dict,
                        current_positions: Dict) -> List[Dict]:
        """
        Generate buy/sell orders to transition from current to target
        """
        orders = []
        
        # Sells: positions to exit
        for symbol in current_positions:
            if symbol not in target_positions:
                orders.append({
                    'symbol': symbol,
                    'action': 'SELL',
                    'current_weight': current_positions[symbol]['weight'],
                    'target_weight': 0
                })
        
        # Buys and adjustments
        for symbol, target_data in target_positions.items():
            current_weight = current_positions.get(symbol, {}).get('weight', 0)
            target_weight = target_data['weight']
            
            if abs(target_weight - current_weight) > 0.001:  # 0.1% threshold
                action = 'BUY' if target_weight > current_weight else 'SELL'
                orders.append({
                    'symbol': symbol,
                    'action': action,
                    'current_weight': current_weight,
                    'target_weight': target_weight,
                    'sector': target_data['sector']
                })
        
        return orders
    
    def get_portfolio_summary(self) -> Dict:
        """
        Get current portfolio summary statistics
        """
        if not self.current_positions:
            return {'positions': 0, 'total_weight': 0}
        
        total_weight = sum(pos['weight'] for pos in self.current_positions.values())
        
        # Count by allocation type
        core_count = sum(1 for pos in self.current_positions.values()
                        if 'core' in pos.get('allocation_type', ''))
        satellite_count = sum(1 for pos in self.current_positions.values()
                             if pos.get('allocation_type') == 'satellite')
        
        # Group by sector
        sector_weights = {}
        for symbol, data in self.current_positions.items():
            sector = data.get('sector', 'Unknown')
            sector_weights[sector] = sector_weights.get(sector, 0) + data['weight']
        
        return {
            'total_positions': len(self.current_positions),
            'core_positions': core_count,
            'satellite_positions': satellite_count,
            'total_weight': total_weight,
            'sector_weights': sector_weights,
            'last_rebalance': self.last_rebalance_date
        }
