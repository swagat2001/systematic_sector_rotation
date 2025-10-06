"""
Backtesting package for systematic sector rotation
Contains backtest engine and performance analysis tools
"""

from .backtest_engine import BacktestEngine
from .performance_analyzer import PerformanceAnalyzer

__all__ = ['BacktestEngine', 'PerformanceAnalyzer']
