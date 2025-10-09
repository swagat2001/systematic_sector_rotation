"""
Backtesting Engine for Systematic Sector Rotation Strategy

Performs walk-forward simulation on historical data:
- Monthly rebalancing with realistic execution
- Transaction cost modeling
- Performance tracking over time
- Portfolio value calculation
- Trade execution simulation
- Event-driven architecture

Integrates with:
- Portfolio Manager (strategy logic)
- Paper Trading Engine (execution simulation)
- Performance Analyzer (metrics calculation)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from config import Config
from strategy.dual_approach_portfolio import DualApproachPortfolioManager
from execution.paper_trading import PaperTradingEngine
from utils.logger import setup_logger
from utils.helpers import calculate_returns, calculate_cagr

logger = setup_logger(__name__)


class BacktestEngine:
    """
    Historical simulation engine for strategy validation
    """
    
    def __init__(self, initial_capital: float = None,
                 start_date: datetime = None,
                 end_date: datetime = None):
        """
        Initialize backtest engine
        
        Args:
            initial_capital: Starting capital (default: 10 Lakh)
            start_date: Backtest start date
            end_date: Backtest end date
        """
        self.config = Config()
        
        # Portfolio and execution engines
        self.portfolio_manager = DualApproachPortfolioManager()
        self.paper_trader = PaperTradingEngine(initial_capital)
        
        # Backtest parameters
        self.initial_capital = initial_capital or Config.PAPER_TRADING['initial_capital']
        self.start_date = start_date
        self.end_date = end_date or datetime.now()
        self.rebalance_frequency = Config.REBALANCING_CONFIG['frequency']  # MONTHLY
        
        # Results tracking
        self.equity_curve = []
        self.monthly_returns = []
        self.rebalance_dates = []
        self.portfolio_snapshots = []
        self.trade_log = []
        
        # Performance cache
        self.daily_values = pd.Series(dtype=float)
        self.benchmark_values = pd.Series(dtype=float)
        
        logger.info(f"BacktestEngine initialized: ₹{self.initial_capital:,.0f}")
        logger.info(f"Period: {start_date} to {end_date}")
    
    def run_backtest(self,
                    sector_prices: Dict[str, pd.DataFrame],
                    stocks_data: Dict[str, Dict],
                    stocks_prices: Dict[str, pd.DataFrame],
                    benchmark_data: pd.DataFrame = None,
                    sector_mapping: Dict[str, str] = None) -> Dict:
        """
        Run complete backtest simulation
        
        Args:
            sector_prices: Historical sector index prices
            stocks_data: Stock fundamental data
            stocks_prices: Historical stock prices
            benchmark_data: Benchmark prices for comparison
            sector_mapping: Stock-to-sector mapping
            
        Returns:
            Dict with backtest results
        """
        logger.info("=" * 80)
        logger.info("STARTING BACKTEST SIMULATION")
        logger.info("=" * 80)
        
        try:
            # Validate data
            if not self._validate_data(sector_prices, stocks_prices):
                return {'success': False, 'error': 'Data validation failed'}
            
            # Determine backtest period
            if self.start_date is None:
                self.start_date = self._get_earliest_date(sector_prices, stocks_prices)
            
            # Generate rebalancing dates (monthly)
            rebalance_dates = self._generate_rebalance_dates(
                self.start_date,
                self.end_date
            )
            
            logger.info(f"Backtest period: {self.start_date.date()} to {self.end_date.date()}")
            logger.info(f"Rebalancing dates: {len(rebalance_dates)} months")
            
            # Run monthly rebalancing loop
            last_portfolio = {}
            for i, rebal_date in enumerate(rebalance_dates):
                logger.info(f"\n{'=' * 60}")
                logger.info(f"Rebalancing {i+1}/{len(rebalance_dates)}: {rebal_date.date()}")
                logger.info(f"{'=' * 60}")
                
                # Get data up to rebalance date
                sector_data_slice = self._slice_data_to_date(sector_prices, rebal_date)
                stocks_data_slice = stocks_data  # Fundamentals don't change
                stocks_prices_slice = self._slice_data_to_date(stocks_prices, rebal_date)
                benchmark_slice = self._slice_data_to_date_single(benchmark_data, rebal_date) if benchmark_data is not None else None
                
                # Run portfolio rebalancing
                rebal_result = self.portfolio_manager.rebalance_portfolio(
                    sector_data_slice,      # sector_prices
                    stocks_data_slice,      # stocks_data
                    stocks_prices_slice,    # stocks_prices
                    as_of_date=rebal_date   # as_of_date
                )
                
                if not rebal_result['success']:
                    logger.error(f"Rebalancing failed: {rebal_result.get('error')}")
                    continue
                
                # ==================== FIX: Pass WEIGHTS, not CAPITAL ====================
                # Build combined portfolio with WEIGHTS (0-1), not capital amounts
                # Paper trading engine expects weights and will multiply by portfolio value
                
                combined_portfolio = {}
                
                # Option 1: Use the combined_positions from rebalance_portfolio result
                # This already has the correct format with weights
                if 'combined_positions' in rebal_result:
                    for symbol, position_data in rebal_result['combined_positions'].items():
                        # position_data = {'weight': 0.071, 'sector': 'Nifty IT', 'allocation_type': 'core'}
                        combined_portfolio[symbol] = position_data['weight']  # ✓ Keep as weight (0-1)
                else:
                    # Option 2: Manually combine core and satellite (fallback)
                    if 'core' in rebal_result and 'positions' in rebal_result['core']:
                        for symbol, position_data in rebal_result['core']['positions'].items():
                            combined_portfolio[symbol] = combined_portfolio.get(symbol, 0) + position_data['weight']
                    
                    if 'satellite' in rebal_result and 'positions' in rebal_result['satellite']:
                        for symbol, position_data in rebal_result['satellite']['positions'].items():
                            combined_portfolio[symbol] = combined_portfolio.get(symbol, 0) + position_data['weight']
                
                # Validate and normalize weights to 100%
                total_weight = sum(combined_portfolio.values())
                if total_weight <= 0:
                    logger.error("Total portfolio weight is zero or negative; skipping execution for this rebalance")
                    continue
                
                if abs(total_weight - 1.0) > 0.01:
                    logger.warning(f"Portfolio weights sum to {total_weight*100:.1f}%, normalizing to 100%")
                    normalization_factor = 1.0 / total_weight
                    for symbol in list(combined_portfolio.keys()):
                        combined_portfolio[symbol] = max(0.0, combined_portfolio[symbol] * normalization_factor)
                    total_weight = sum(combined_portfolio.values())
                
                logger.info(f"Combined portfolio: {len(combined_portfolio)} positions, total weight: {total_weight*100:.1f}%")
                # =============================================================================
                
                # Store for later use
                last_portfolio = combined_portfolio
                
                # Get current prices for execution
                current_prices = self._get_current_prices(
                    sector_data_slice,
                    stocks_prices_slice,
                    rebal_date
                )
                
                # Execute trades in paper trading
                # paper_trader.rebalance_portfolio expects weights (0-1)
                execution_result = self.paper_trader.rebalance_portfolio(
                    combined_portfolio,  # Dict[symbol, weight] where weight is 0-1
                    current_prices,
                    rebal_date
                )
                
                # Record snapshot
                portfolio_value = self.paper_trader.get_portfolio_value_dict(current_prices)
                self.portfolio_snapshots.append({
                    'date': rebal_date,
                    'portfolio_value': portfolio_value,
                    'positions': self.paper_trader.positions.copy(),
                    'cash': self.paper_trader.cash,
                    'num_trades': len(execution_result['executed'])
                })
                
                # Track equity point
                self.equity_curve.append({
                    'date': rebal_date,
                    'value': portfolio_value
                })
                
                logger.info(f"Portfolio value: ₹{portfolio_value:,.0f}")
                logger.info(f"Trades executed: {len(execution_result['executed'])}")
                
                # Calculate daily values between rebalancing dates
                if i < len(rebalance_dates) - 1:
                    next_rebal = rebalance_dates[i + 1]
                    self._calculate_daily_values(
                        rebal_date,
                        next_rebal,
                        combined_portfolio,
                        stocks_prices,
                        sector_prices
                    )
            
            # Final calculations
            self._finalize_results(benchmark_data)
            
            result = {
                'success': True,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'num_rebalances': len(rebalance_dates),
                'initial_capital': self.initial_capital,
                'final_value': self.equity_curve[-1]['value'] if self.equity_curve else self.initial_capital,
                'equity_curve': self.equity_curve,
                'portfolio_snapshots': self.portfolio_snapshots,
                'daily_values': self.daily_values,
                'final_portfolio': self.portfolio_snapshots[-1]['positions'] if self.portfolio_snapshots else {},
                'portfolio': last_portfolio  # Add for backward compatibility
            }
            
            logger.info("\n" + "=" * 80)
            logger.info("BACKTEST COMPLETE")
            logger.info("=" * 80)
            logger.info(f"Final value: ₹{result['final_value']:,.0f}")
            logger.info(f"Total return: {((result['final_value']/self.initial_capital - 1) * 100):.2f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _validate_data(self, sector_prices: Dict, stocks_prices: Dict) -> bool:
        """Validate input data"""
        if not sector_prices and not stocks_prices:
            logger.error("No price data provided")
            return False
        
        # Check for empty dataframes
        empty_sectors = [k for k, v in sector_prices.items() if v.empty]
        empty_stocks = [k for k, v in stocks_prices.items() if v.empty]
        
        if empty_sectors:
            logger.warning(f"Empty sector data: {empty_sectors}")
        if empty_stocks:
            logger.warning(f"Empty stock data: {len(empty_stocks)} stocks")
        
        return True
    
    def _get_earliest_date(self, sector_prices: Dict, stocks_prices: Dict) -> datetime:
        """Get earliest date from all data"""
        dates = []
        
        for df in sector_prices.values():
            if not df.empty:
                dates.append(df.index[0])
        
        for df in stocks_prices.values():
            if not df.empty:
                dates.append(df.index[0])
        
        if not dates:
            return datetime.now() - timedelta(days=365)
        
        earliest = min(dates)
        # Start from at least 6 months in to have lookback data
        return earliest + timedelta(days=126)  # 6 months
    
    def _generate_rebalance_dates(self, start: datetime, end: datetime) -> List[datetime]:
        """Generate monthly rebalancing dates"""
        dates = []
        current = start
        
        while current <= end:
            dates.append(current)
            current = current + relativedelta(months=1)
        
        return dates
    
    def _slice_data_to_date(self, data_dict: Dict[str, pd.DataFrame],
                           date: datetime) -> Dict[str, pd.DataFrame]:
        """Slice all dataframes up to date"""
        sliced = {}
        for symbol, df in data_dict.items():
            if df.empty:
                sliced[symbol] = df
            else:
                sliced[symbol] = df[df.index <= date]
        return sliced
    
    def _slice_data_to_date_single(self, df: pd.DataFrame, date: datetime) -> pd.DataFrame:
        """Slice single dataframe to date"""
        if df is None or df.empty:
            return df
        return df[df.index <= date]
    
    def _get_current_prices(self, sector_data: Dict[str, pd.DataFrame],
                           stock_data: Dict[str, pd.DataFrame],
                           date: datetime) -> Dict[str, float]:
        """Get current prices at date"""
        prices = {}
        
        # Sector prices
        for sector, df in sector_data.items():
            if not df.empty and 'Close' in df.columns:
                try:
                    prices[f"SECTOR:{sector}"] = df['Close'].iloc[-1]
                except:
                    pass
        
        # Stock prices
        for symbol, df in stock_data.items():
            if not df.empty and 'Close' in df.columns:
                try:
                    prices[symbol] = df['Close'].iloc[-1]
                except:
                    pass
        
        return prices
    
    def _calculate_daily_values(self, start_date: datetime, end_date: datetime,
                               portfolio: Dict[str, float],
                               stocks_prices: Dict[str, pd.DataFrame],
                               sector_prices: Dict[str, pd.DataFrame]):
        """Calculate daily portfolio values between rebalancing"""
        # Get all trading days in period
        all_dates = set()
        
        for df in stocks_prices.values():
            if not df.empty:
                dates_in_range = df[(df.index > start_date) & (df.index <= end_date)].index
                all_dates.update(dates_in_range)
        
        for df in sector_prices.values():
            if not df.empty:
                dates_in_range = df[(df.index > start_date) & (df.index <= end_date)].index
                all_dates.update(dates_in_range)
        
        # Calculate value for each day
        for date in sorted(all_dates):
            current_prices = self._get_current_prices(
                self._slice_data_to_date(sector_prices, date),
                self._slice_data_to_date(stocks_prices, date),
                date
            )
            
            portfolio_value = self.paper_trader.get_portfolio_value_dict(current_prices)
            self.daily_values[date] = portfolio_value
    
    def _finalize_results(self, benchmark_data: pd.DataFrame = None):
        """Finalize results and calculations"""
        # Convert equity curve to series
        if self.equity_curve:
            dates = [point['date'] for point in self.equity_curve]
            values = [point['value'] for point in self.equity_curve]
            
            # If we don't have daily values, use monthly
            if self.daily_values.empty:
                self.daily_values = pd.Series(values, index=dates)
        
        # Process benchmark if provided
        if benchmark_data is not None and not benchmark_data.empty:
            # Align benchmark to our dates
            benchmark_slice = benchmark_data[
                (benchmark_data.index >= self.start_date) &
                (benchmark_data.index <= self.end_date)
            ]
            
            if not benchmark_slice.empty and 'Close' in benchmark_slice.columns:
                # Normalize to initial capital
                first_price = benchmark_slice['Close'].iloc[0]
                self.benchmark_values = (benchmark_slice['Close'] / first_price) * self.initial_capital
    
    def get_equity_curve_df(self) -> pd.DataFrame:
        """Get equity curve as DataFrame"""
        if self.daily_values.empty:
            return pd.DataFrame()
        
        df = pd.DataFrame({
            'portfolio_value': self.daily_values
        })
        
        if not self.benchmark_values.empty:
            df['benchmark_value'] = self.benchmark_values
        
        return df
    
    def generate_backtest_report(self, result: Dict) -> str:
        """Generate comprehensive backtest report"""
        if not result.get('success'):
            return f"Backtest failed: {result.get('error')}"
        
        total_return = (result['final_value'] / result['initial_capital'] - 1) * 100
        
        report = f"\n{'=' * 80}\n"
        report += f"BACKTEST RESULTS\n"
        report += f"{'=' * 80}\n\n"
        
        report += f"BACKTEST PARAMETERS:\n"
        report += f"  Period: {result['start_date'].date()} to {result['end_date'].date()}\n"
        report += f"  Initial Capital: ₹{result['initial_capital']:,.0f}\n"
        report += f"  Rebalancing: Monthly ({result['num_rebalances']} times)\n\n"
        
        report += f"PERFORMANCE SUMMARY:\n"
        report += f"  Final Value: ₹{result['final_value']:,.0f}\n"
        report += f"  Total Return: {total_return:.2f}%\n"
        report += f"  Total P&L: ₹{(result['final_value'] - result['initial_capital']):,.0f}\n\n"
        
        # Trading activity
        total_trades = sum(snapshot['num_trades'] for snapshot in result['portfolio_snapshots'])
        report += f"TRADING ACTIVITY:\n"
        report += f"  Total Rebalances: {result['num_rebalances']}\n"
        report += f"  Total Trades: {total_trades}\n"
        report += f"  Avg Trades per Rebalance: {total_trades/max(result['num_rebalances'],1):.1f}\n\n"
        
        report += f"{'=' * 80}\n"
        
        return report
