"""
Performance Analyzer for Systematic Sector Rotation Strategy

Calculates comprehensive performance metrics:
- Returns (daily, monthly, annual, CAGR)
- Risk metrics (Sharpe, Sortino, Max DD, Volatility, Beta, Information Ratio)
- Attribution analysis (sector vs stock contribution)
- Trade statistics (win rate, avg win/loss, turnover)
- Benchmark comparison (vs NIFTY 50, NIFTY 500)
- Drawdown analysis

Provides statistical validation of backtest results.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from utils.logger import setup_logger
from utils.helpers import (
    calculate_returns, calculate_cagr, calculate_sharpe_ratio,
    calculate_max_drawdown, calculate_volatility
)

logger = setup_logger(__name__)


class PerformanceAnalyzer:
    """
    Analyzes backtest performance and generates metrics
    """
    
    def __init__(self, risk_free_rate: float = 0.065):
        """
        Initialize performance analyzer
        
        Args:
            risk_free_rate: Annual risk-free rate (default: 6.5% - India)
        """
        self.risk_free_rate = risk_free_rate
        self.daily_rf = (1 + risk_free_rate) ** (1/252) - 1
        
        logger.info(f"PerformanceAnalyzer initialized (rf={risk_free_rate:.2%})")
    
    def analyze(self, backtest_result: Dict, 
                benchmark_returns: pd.Series = None) -> Dict:
        """
        Perform comprehensive performance analysis
        
        Args:
            backtest_result: Results from backtest engine
            benchmark_returns: Benchmark returns for comparison
        
        Returns:
            Dict with all performance metrics
        """
        if not backtest_result.get('success'):
            logger.error("Cannot analyze failed backtest")
            return {}
        
        logger.info("=" * 60)
        logger.info("ANALYZING BACKTEST PERFORMANCE")
        logger.info("=" * 60)
        
        # Extract data
        daily_values = backtest_result.get('daily_values', pd.Series())
        
        if daily_values.empty:
            logger.warning("No daily values available")
            return {}
        
        # Calculate returns
        returns_metrics = self._calculate_returns_metrics(daily_values, backtest_result)
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(daily_values, benchmark_returns)
        
        # Calculate drawdown metrics
        drawdown_metrics = self._calculate_drawdown_metrics(daily_values)
        
        # Calculate trade statistics
        trade_stats = self._calculate_trade_statistics(backtest_result)
        
        # Benchmark comparison
        benchmark_metrics = {}
        if benchmark_returns is not None:
            benchmark_metrics = self._compare_to_benchmark(daily_values, benchmark_returns)
        
        # Combine all metrics
        analysis = {
            'returns': returns_metrics,
            'risk': risk_metrics,
            'drawdown': drawdown_metrics,
            'trades': trade_stats,
            'benchmark': benchmark_metrics,
            'period': {
                'start': backtest_result['start_date'],
                'end': backtest_result['end_date'],
                'days': len(daily_values),
                'years': len(daily_values) / 252
            }
        }
        
        logger.info("Performance analysis complete")
        
        return analysis
    
    def _calculate_returns_metrics(self, daily_values: pd.Series, 
                                   backtest_result: Dict) -> Dict:
        """Calculate return metrics"""
        logger.info("Calculating return metrics...")
        
        initial = backtest_result['initial_capital']
        final = backtest_result['final_value']
        
        # Calculate returns series
        daily_returns = daily_values.pct_change().dropna()
        
        # Total return
        total_return = (final / initial - 1) * 100
        
        # CAGR
        years = len(daily_values) / 252
        cagr = calculate_cagr(initial, final, years)
        
        # Periodic returns
        daily_return = daily_returns.mean() * 100
        monthly_return = daily_returns.mean() * 21 * 100
        annual_return = daily_returns.mean() * 252 * 100
        
        # Return statistics
        positive_days = (daily_returns > 0).sum()
        negative_days = (daily_returns < 0).sum()
        
        metrics = {
            'total_return': total_return,
            'cagr': cagr,
            'daily_return': daily_return,
            'monthly_return': monthly_return,
            'annual_return': annual_return,
            'best_day': daily_returns.max() * 100,
            'worst_day': daily_returns.min() * 100,
            'positive_days': positive_days,
            'negative_days': negative_days,
            'positive_pct': (positive_days / len(daily_returns) * 100) if len(daily_returns) > 0 else 0
        }
        
        logger.info(f"  Total Return: {metrics['total_return']:.2f}%")
        logger.info(f"  CAGR: {metrics['cagr']:.2f}%")
        
        return metrics
    
    def _calculate_risk_metrics(self, daily_values: pd.Series,
                                benchmark_returns: pd.Series = None) -> Dict:
        """Calculate risk metrics"""
        logger.info("Calculating risk metrics...")
        
        daily_returns = daily_values.pct_change().dropna()
        
        # Volatility (annualized)
        volatility = calculate_volatility(daily_values)
        
        # Sharpe Ratio
        excess_returns = daily_returns - self.daily_rf
        sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252) if excess_returns.std() > 0 else 0
        
        # Sortino Ratio (downside deviation)
        downside_returns = daily_returns[daily_returns < self.daily_rf]
        downside_std = downside_returns.std()
        sortino = (excess_returns.mean() / downside_std) * np.sqrt(252) if downside_std > 0 else 0
        
        # Calmar Ratio
        max_dd = calculate_max_drawdown(daily_values)
        annual_return = daily_returns.mean() * 252
        calmar = (annual_return / abs(max_dd)) if max_dd != 0 else 0
        
        metrics = {
            'volatility': volatility * 100,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'downside_deviation': downside_std * np.sqrt(252) * 100
        }
        
        # Beta and Information Ratio (if benchmark provided)
        if benchmark_returns is not None:
            # Align returns
            aligned_returns, aligned_benchmark = daily_returns.align(
                benchmark_returns, join='inner'
            )
            
            if len(aligned_returns) > 0:
                # Beta
                covariance = np.cov(aligned_returns, aligned_benchmark)[0][1]
                benchmark_var = np.var(aligned_benchmark)
                beta = covariance / benchmark_var if benchmark_var > 0 else 1.0
                
                # Alpha (excess return over benchmark)
                portfolio_return = aligned_returns.mean() * 252
                benchmark_return = aligned_benchmark.mean() * 252
                alpha = (portfolio_return - self.risk_free_rate) - beta * (benchmark_return - self.risk_free_rate)
                
                # Information Ratio
                tracking_error = (aligned_returns - aligned_benchmark).std() * np.sqrt(252)
                info_ratio = ((portfolio_return - benchmark_return) / tracking_error) if tracking_error > 0 else 0
                
                metrics['beta'] = beta
                metrics['alpha'] = alpha * 100
                metrics['information_ratio'] = info_ratio
                metrics['tracking_error'] = tracking_error * 100
        
        logger.info(f"  Volatility: {metrics['volatility']:.2f}%")
        logger.info(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        
        return metrics
    
    def _calculate_drawdown_metrics(self, daily_values: pd.Series) -> Dict:
        """Calculate drawdown metrics"""
        logger.info("Calculating drawdown metrics...")
        
        # Calculate drawdown series
        running_max = daily_values.expanding().max()
        drawdown_series = (daily_values - running_max) / running_max
        
        # Maximum drawdown
        max_dd = drawdown_series.min() * 100
        max_dd_date = drawdown_series.idxmin()
        
        # Average drawdown
        avg_dd = drawdown_series[drawdown_series < 0].mean() * 100 if (drawdown_series < 0).any() else 0
        
        # Drawdown duration
        in_drawdown = drawdown_series < -0.01  # More than 1% drawdown
        if in_drawdown.any():
            # Find longest drawdown period
            drawdown_periods = []
            start = None
            
            for date, is_dd in in_drawdown.items():
                if is_dd and start is None:
                    start = date
                elif not is_dd and start is not None:
                    drawdown_periods.append((date - start).days)
                    start = None
            
            if start is not None:
                drawdown_periods.append((in_drawdown.index[-1] - start).days)
            
            longest_dd_days = max(drawdown_periods) if drawdown_periods else 0
            avg_dd_days = np.mean(drawdown_periods) if drawdown_periods else 0
        else:
            longest_dd_days = 0
            avg_dd_days = 0
        
        metrics = {
            'max_drawdown': max_dd,
            'max_dd_date': max_dd_date,
            'avg_drawdown': avg_dd,
            'longest_dd_days': longest_dd_days,
            'avg_dd_days': avg_dd_days,
            'drawdown_series': drawdown_series
        }
        
        logger.info(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%")
        logger.info(f"  Max DD Date: {metrics['max_dd_date']}")
        
        return metrics
    
    def _calculate_trade_statistics(self, backtest_result: Dict) -> Dict:
        """Calculate trade statistics"""
        logger.info("Calculating trade statistics...")
        
        snapshots = backtest_result.get('portfolio_snapshots', [])
        
        if not snapshots:
            return {}
        
        # Total trades
        total_trades = sum(s['num_trades'] for s in snapshots)
        
        # Average trades per rebalance
        avg_trades = total_trades / len(snapshots) if snapshots else 0
        
        metrics = {
            'total_rebalances': len(snapshots),
            'total_trades': total_trades,
            'avg_trades_per_rebalance': avg_trades,
            'rebalancing_frequency': 'Monthly'
        }
        
        logger.info(f"  Total Trades: {metrics['total_trades']}")
        logger.info(f"  Avg Trades/Rebalance: {metrics['avg_trades_per_rebalance']:.1f}")
        
        return metrics
    
    def _compare_to_benchmark(self, daily_values: pd.Series,
                              benchmark_returns: pd.Series) -> Dict:
        """Compare strategy to benchmark"""
        logger.info("Comparing to benchmark...")
        
        strategy_returns = daily_values.pct_change().dropna()
        
        # Align dates
        aligned_strategy, aligned_benchmark = strategy_returns.align(
            benchmark_returns, join='inner'
        )
        
        if len(aligned_strategy) == 0:
            return {}
        
        # Calculate cumulative returns
        strategy_cumulative = (1 + aligned_strategy).cumprod()
        benchmark_cumulative = (1 + aligned_benchmark).cumprod()
        
        # Final returns
        strategy_total = (strategy_cumulative.iloc[-1] - 1) * 100
        benchmark_total = (benchmark_cumulative.iloc[-1] - 1) * 100
        
        # Outperformance
        outperformance = strategy_total - benchmark_total
        
        # Win rate (days strategy beat benchmark)
        win_days = (aligned_strategy > aligned_benchmark).sum()
        win_rate = (win_days / len(aligned_strategy) * 100) if len(aligned_strategy) > 0 else 0
        
        # Correlation
        correlation = aligned_strategy.corr(aligned_benchmark)
        
        metrics = {
            'strategy_return': strategy_total,
            'benchmark_return': benchmark_total,
            'outperformance': outperformance,
            'win_rate': win_rate,
            'correlation': correlation
        }
        
        logger.info(f"  Outperformance: {metrics['outperformance']:.2f}%")
        logger.info(f"  Win Rate: {metrics['win_rate']:.1f}%")
        
        return metrics
    
    def generate_performance_report(self, analysis: Dict) -> str:
        """
        Generate comprehensive performance report
        
        Args:
            analysis: Output from analyze() method
        
        Returns:
            Formatted report string
        """
        if not analysis:
            return "No analysis data available"
        
        report = f"\n{'=' * 80}\n"
        report += f"PERFORMANCE ANALYSIS REPORT\n"
        report += f"{'=' * 80}\n\n"
        
        # Period
        period = analysis.get('period', {})
        report += f"ANALYSIS PERIOD:\n"
        report += f"  Start Date: {period.get('start', 'N/A')}\n"
        report += f"  End Date: {period.get('end', 'N/A')}\n"
        report += f"  Trading Days: {period.get('days', 0)}\n"
        report += f"  Years: {period.get('years', 0):.2f}\n\n"
        
        # Returns
        returns = analysis.get('returns', {})
        if returns:
            report += f"RETURN METRICS:\n"
            report += f"  Total Return: {returns.get('total_return', 0):.2f}%\n"
            report += f"  CAGR: {returns.get('cagr', 0):.2f}%\n"
            report += f"  Average Daily: {returns.get('daily_return', 0):.3f}%\n"
            report += f"  Average Monthly: {returns.get('monthly_return', 0):.2f}%\n"
            report += f"  Best Day: {returns.get('best_day', 0):.2f}%\n"
            report += f"  Worst Day: {returns.get('worst_day', 0):.2f}%\n"
            report += f"  Positive Days: {returns.get('positive_days', 0)} ({returns.get('positive_pct', 0):.1f}%)\n\n"
        
        # Risk
        risk = analysis.get('risk', {})
        if risk:
            report += f"RISK METRICS:\n"
            report += f"  Volatility (Annual): {risk.get('volatility', 0):.2f}%\n"
            report += f"  Sharpe Ratio: {risk.get('sharpe_ratio', 0):.2f}\n"
            report += f"  Sortino Ratio: {risk.get('sortino_ratio', 0):.2f}\n"
            report += f"  Calmar Ratio: {risk.get('calmar_ratio', 0):.2f}\n"
            
            if 'beta' in risk:
                report += f"  Beta: {risk.get('beta', 0):.2f}\n"
                report += f"  Alpha: {risk.get('alpha', 0):.2f}%\n"
                report += f"  Information Ratio: {risk.get('information_ratio', 0):.2f}\n"
                report += f"  Tracking Error: {risk.get('tracking_error', 0):.2f}%\n"
            
            report += "\n"
        
        # Drawdown
        drawdown = analysis.get('drawdown', {})
        if drawdown:
            report += f"DRAWDOWN METRICS:\n"
            report += f"  Maximum Drawdown: {drawdown.get('max_drawdown', 0):.2f}%\n"
            report += f"  Max DD Date: {drawdown.get('max_dd_date', 'N/A')}\n"
            report += f"  Average Drawdown: {drawdown.get('avg_drawdown', 0):.2f}%\n"
            report += f"  Longest DD Period: {drawdown.get('longest_dd_days', 0)} days\n"
            report += f"  Average DD Duration: {drawdown.get('avg_dd_days', 0):.1f} days\n\n"
        
        # Trades
        trades = analysis.get('trades', {})
        if trades:
            report += f"TRADING STATISTICS:\n"
            report += f"  Total Rebalances: {trades.get('total_rebalances', 0)}\n"
            report += f"  Total Trades: {trades.get('total_trades', 0)}\n"
            report += f"  Avg Trades/Rebalance: {trades.get('avg_trades_per_rebalance', 0):.1f}\n"
            report += f"  Frequency: {trades.get('rebalancing_frequency', 'N/A')}\n\n"
        
        # Benchmark comparison
        benchmark = analysis.get('benchmark', {})
        if benchmark:
            report += f"BENCHMARK COMPARISON:\n"
            report += f"  Strategy Return: {benchmark.get('strategy_return', 0):.2f}%\n"
            report += f"  Benchmark Return: {benchmark.get('benchmark_return', 0):.2f}%\n"
            report += f"  Outperformance: {benchmark.get('outperformance', 0):.2f}%\n"
            report += f"  Win Rate: {benchmark.get('win_rate', 0):.1f}%\n"
            report += f"  Correlation: {benchmark.get('correlation', 0):.2f}\n\n"
        
        report += f"{'=' * 80}\n"
        
        return report
    
    def generate_monthly_returns_table(self, daily_values: pd.Series) -> pd.DataFrame:
        """Generate monthly returns table"""
        if daily_values.empty:
            return pd.DataFrame()
        
        # Calculate returns
        returns = daily_values.pct_change()
        
        # Resample to monthly
        monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
        
        # Create pivot table (years vs months)
        monthly_returns_df = monthly_returns.to_frame('return')
        monthly_returns_df['year'] = monthly_returns_df.index.year
        monthly_returns_df['month'] = monthly_returns_df.index.month
        
        pivot = monthly_returns_df.pivot(
            index='year',
            columns='month',
            values='return'
        )
        
        # Format as percentages
        pivot = pivot * 100
        
        # Add yearly total
        yearly_returns = daily_values.resample('Y').apply(
            lambda x: (x.iloc[-1] / x.iloc[0] - 1) if len(x) > 0 else 0
        )
        
        if not yearly_returns.empty:
            pivot['Year'] = yearly_returns.values * 100
        
        return pivot


if __name__ == "__main__":
    # Test performance analyzer
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Create sample backtest result
    dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='B')
    returns = np.random.randn(len(dates)) * 0.01 + 0.0005
    values = 1000000 * (1 + pd.Series(returns, index=dates)).cumprod()
    
    backtest_result = {
        'success': True,
        'start_date': dates[0],
        'end_date': dates[-1],
        'initial_capital': 1000000,
        'final_value': values.iloc[-1],
        'daily_values': values,
        'portfolio_snapshots': [
            {'num_trades': 10} for _ in range(48)  # 48 months
        ]
    }
    
    # Benchmark
    benchmark_returns = pd.Series(
        np.random.randn(len(dates)) * 0.008 + 0.0003,
        index=dates
    )
    
    # Analyze
    analyzer = PerformanceAnalyzer()
    analysis = analyzer.analyze(backtest_result, benchmark_returns)
    
    # Generate report
    print(analyzer.generate_performance_report(analysis))
    
    # Monthly returns table
    monthly_table = analyzer.generate_monthly_returns_table(values)
    print("\nMONTHLY RETURNS TABLE:")
    print(monthly_table.round(2))
