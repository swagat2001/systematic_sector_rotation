"""
Execution package for systematic sector rotation
Handles paper trading and order management
"""

from .paper_trading import PaperTradingEngine
from .order_manager import OrderManager

__all__ = ['PaperTradingEngine', 'OrderManager']
