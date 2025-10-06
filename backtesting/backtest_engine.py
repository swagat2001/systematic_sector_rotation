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
from strategy.portfolio_manager import PortfolioManager
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
        self.portfolio_manager = PortfolioManager()
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
                    sector_data_slice,
                    stocks_data_slice,
                    stocks_prices_slice,
                    benchmark_slice,
                    sector_mapping,
                    as_of_date=rebal_date
                )
                
                if not rebal_result['success']:
                    logger.error(f"Rebalancing failed: {rebal_result.get('error')}")
                    continue
                
                # Store the portfolio for later use
                last_portfolio = rebal_result.get('portfolio', {})
                
                # Get current prices for execution
                current_prices = self._get_current_prices(
                    sector_data_slice,
                    stocks_prices_slice,
                    rebal_date
                )
                
                # Execute trades in paper trading
                execution_result = self.paper_trader.rebalance_portfolio(
                    rebal_result['portfolio'],
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
                        rebal_result['portfolio'],
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
                'portfolio': last_portfolio
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
        # Start from at least 1 year in to have lookback data
        return earliest + timedelta(days=252)
    
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


if __name__ == "__main__":
    # Test backtest engine
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Generate sample data
    dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='B')
    
    test_sectors = {}
    for sector in ['Nifty IT', 'Nifty Bank', 'Nifty Auto']:
        prices = 1000 * (1 + pd.Series(np.random.randn(len(dates)) * 0.01 + 0.0003).cumsum())
        test_sectors[sector] = pd.DataFrame({
            'Close': prices.values,
            'Volume': 10000000
        }, index=dates)
    
    test_stocks = {}
    test_fundamentals = {}
    for symbol in ['INFY', 'TCS', 'WIPRO']:
        prices = 1000 * (1 + pd.Series(np.random.randn(len(dates)) * 0.015 + 0.0005).cumsum())
        test_stocks[symbol] = pd.DataFrame({
            'Close': prices.values,
            'Volume': 5000000
        }, index=dates)
        
        test_fundamentals[symbol] = {
            'roe': 0.25,
            'market_cap': 100000000000
        }
    
    # Run backtest
    engine = BacktestEngine(
        initial_capital=1000000,
        start_date=datetime(2021, 1, 1),
        end_date=datetime(2023, 12, 31)
    )
    
    result = engine.run_backtest(
        test_sectors,
        test_fundamentals,
        test_stocks
    )
    
    if result['success']:
        print(engine.generate_backtest_report(result))
