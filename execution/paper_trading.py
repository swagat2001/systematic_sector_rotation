"""
Paper Trading Engine for Systematic Sector Rotation Strategy

Simulates portfolio execution without real money:
- Initialize portfolio with starting capital
- Execute buy/sell/rebalance orders
- Apply realistic transaction costs (0.1%)
- Apply slippage (0.05%)
- Apply market impact (0.02%)
- Track positions and cash balance
- Calculate portfolio value and P&L
- Maintain transaction history

This enables realistic strategy testing before live deployment.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PaperTradingEngine:
    """
    Simulates portfolio execution with realistic costs
    """
    
    def __init__(self, initial_capital: float = None):
        """
        Initialize paper trading engine
        
        Args:
            initial_capital: Starting capital (default: 10 Lakh from config)
        """
        self.config = Config()
        
        # Portfolio state
        self.initial_capital = initial_capital or Config.PAPER_TRADING['initial_capital']
        self.cash = self.initial_capital
        self.positions = {}  # symbol -> quantity
        self.position_values = {}  # symbol -> current value
        
        # Cost parameters
        self.transaction_cost = Config.PAPER_TRADING['transaction_cost']  # 0.1%
        self.slippage = Config.PAPER_TRADING['slippage']  # 0.05%
        self.market_impact = Config.PAPER_TRADING['market_impact']  # 0.02%
        
        # History tracking
        self.transaction_history = []
        self.portfolio_history = []
        self.pnl_history = []
        
        # Performance metrics
        self.total_transactions = 0
        self.total_costs = 0.0
        
        logger.info(f"PaperTradingEngine initialized with ₹{self.initial_capital:,.0f}")
    
    def execute_order(self, symbol: str, action: str, weight: float,
                     current_price: float, date: datetime = None) -> Dict:
        """
        Execute a single order
        
        Args:
            symbol: Stock/sector symbol
            action: 'BUY', 'SELL', or 'REBALANCE'
            weight: Target portfolio weight (0-1)
            current_price: Current market price
            date: Execution date
        
        Returns:
            Dict with execution details
        """
        if date is None:
            date = datetime.now()
        
        portfolio_value = self.get_portfolio_value(current_price, symbol)
        target_value = weight * portfolio_value
        
        current_value = self.position_values.get(symbol, 0.0)
        value_change = target_value - current_value
        
        if abs(value_change) < 100:  # Ignore tiny changes
            return {'status': 'skipped', 'reason': 'change too small'}
        
        # Calculate quantity
        quantity_change = value_change / current_price
        
        # Apply costs
        execution_price = self._calculate_execution_price(
            current_price, 
            quantity_change
        )
        
        gross_value = abs(quantity_change * execution_price)
        transaction_cost = gross_value * self.transaction_cost
        
        total_cost = gross_value + transaction_cost
        
        # Check if we have enough cash for buys
        if quantity_change > 0 and total_cost > self.cash:
            logger.warning(f"Insufficient cash for {symbol}: need ₹{total_cost:,.0f}, have ₹{self.cash:,.0f}")
            return {'status': 'failed', 'reason': 'insufficient cash'}
        
        # Execute trade
        if symbol not in self.positions:
            self.positions[symbol] = 0.0
        
        self.positions[symbol] += quantity_change
        
        # Update cash
        if quantity_change > 0:  # Buy
            self.cash -= total_cost
        else:  # Sell
            self.cash += (gross_value - transaction_cost)
        
        # Update position value
        self.position_values[symbol] = self.positions[symbol] * current_price
        
        # Record transaction
        transaction = {
            'date': date,
            'symbol': symbol,
            'action': action,
            'quantity': quantity_change,
            'price': execution_price,
            'gross_value': gross_value,
            'transaction_cost': transaction_cost,
            'total_cost': total_cost
        }
        
        self.transaction_history.append(transaction)
        self.total_transactions += 1
        self.total_costs += transaction_cost
        
        logger.info(f"{action} {symbol}: {abs(quantity_change):.2f} shares @ ₹{execution_price:.2f}, cost: ₹{transaction_cost:.2f}")
        
        return {
            'status': 'executed',
            'transaction': transaction
        }
    
    def rebalance_portfolio(self, target_weights: Dict[str, float],
                           current_prices: Dict[str, float],
                           date: datetime = None) -> Dict:
        """
        Rebalance entire portfolio to target weights
        
        Args:
            target_weights: Dict mapping symbols to target weights
            current_prices: Dict mapping symbols to current prices
            date: Rebalancing date
        
        Returns:
            Dict with rebalancing results
        """
        logger.info("=" * 60)
        logger.info("EXECUTING PORTFOLIO REBALANCING")
        logger.info("=" * 60)
        
        if date is None:
            date = datetime.now()
        
        results = {
            'date': date,
            'executed': [],
            'failed': [],
            'skipped': []
        }
        
        # First, sell positions not in target
        symbols_to_sell = [s for s in self.positions.keys() if s not in target_weights and self.positions[s] > 0]
        
        for symbol in symbols_to_sell:
            if symbol not in current_prices:
                logger.warning(f"No price available for {symbol}, skipping")
                continue
            
            result = self.execute_order(
                symbol, 'SELL', 0.0, 
                current_prices[symbol], date
            )
            
            if result['status'] == 'executed':
                results['executed'].append(result['transaction'])
            elif result['status'] == 'failed':
                results['failed'].append({'symbol': symbol, 'reason': result['reason']})
        
        # Then, buy/rebalance target positions
        for symbol, weight in target_weights.items():
            if symbol not in current_prices:
                logger.warning(f"No price available for {symbol}, skipping")
                results['skipped'].append(symbol)
                continue
            
            action = 'BUY' if symbol not in self.positions else 'REBALANCE'
            
            result = self.execute_order(
                symbol, action, weight,
                current_prices[symbol], date
            )
            
            if result['status'] == 'executed':
                results['executed'].append(result['transaction'])
            elif result['status'] == 'failed':
                results['failed'].append({'symbol': symbol, 'reason': result['reason']})
            elif result['status'] == 'skipped':
                results['skipped'].append(symbol)
        
        # Clean up zero positions
        self.positions = {s: q for s, q in self.positions.items() if abs(q) > 0.001}
        
        # Record portfolio state
        portfolio_value = self.get_portfolio_value_dict(current_prices)
        self.portfolio_history.append({
            'date': date,
            'portfolio_value': portfolio_value,
            'cash': self.cash,
            'positions': self.positions.copy()
        })
        
        logger.info(f"Rebalancing complete:")
        logger.info(f"  Executed: {len(results['executed'])} orders")
        logger.info(f"  Failed: {len(results['failed'])} orders")
        logger.info(f"  Skipped: {len(results['skipped'])} orders")
        logger.info(f"  Portfolio value: ₹{portfolio_value:,.0f}")
        logger.info(f"  Cash: ₹{self.cash:,.0f}")
        logger.info("=" * 60)
        
        return results
    
    def _calculate_execution_price(self, market_price: float, quantity: float) -> float:
        """
        Calculate execution price including slippage and market impact
        
        Args:
            market_price: Current market price
            quantity: Order quantity (positive for buy, negative for sell)
        
        Returns:
            Execution price
        """
        # Slippage: constant percentage
        slippage_factor = 1 + self.slippage if quantity > 0 else 1 - self.slippage
        
        # Market impact: proportional to order size
        impact_factor = 1 + (self.market_impact * abs(quantity) / 1000)
        if quantity < 0:
            impact_factor = 2 - impact_factor
        
        execution_price = market_price * slippage_factor * impact_factor
        
        return execution_price
    
    def get_portfolio_value(self, current_price: float = None, symbol: str = None) -> float:
        """
        Calculate total portfolio value
        
        Args:
            current_price: Price for specific symbol (optional)
            symbol: Symbol being priced (optional)
        
        Returns:
            Total portfolio value
        """
        positions_value = sum(self.position_values.values())
        
        # Add unrealized value for symbol being priced
        if symbol and current_price and symbol in self.positions:
            positions_value += (current_price - self.position_values.get(symbol, 0) / max(self.positions[symbol], 1))
        
        return self.cash + positions_value
    
    def get_portfolio_value_dict(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate portfolio value with updated prices
        
        Args:
            current_prices: Dict of current prices
        
        Returns:
            Total portfolio value
        """
        positions_value = 0.0
        
        for symbol, quantity in self.positions.items():
            if symbol in current_prices:
                positions_value += quantity * current_prices[symbol]
        
        return self.cash + positions_value
    
    def calculate_pnl(self, current_prices: Dict[str, float] = None) -> Dict:
        """
        Calculate profit and loss
        
        Args:
            current_prices: Current market prices
        
        Returns:
            Dict with P&L metrics
        """
        current_value = self.get_portfolio_value_dict(current_prices) if current_prices else self.get_portfolio_value()
        
        total_pnl = current_value - self.initial_capital
        total_return = (total_pnl / self.initial_capital) * 100
        
        return {
            'initial_capital': self.initial_capital,
            'current_value': current_value,
            'cash': self.cash,
            'positions_value': current_value - self.cash,
            'total_pnl': total_pnl,
            'total_return_pct': total_return,
            'total_costs': self.total_costs,
            'total_transactions': self.total_transactions
        }
    
    def get_positions_summary(self, current_prices: Dict[str, float] = None) -> pd.DataFrame:
        """
        Get summary of current positions
        
        Args:
            current_prices: Current market prices
        
        Returns:
            DataFrame with position details
        """
        if not self.positions:
            return pd.DataFrame()
        
        positions_data = []
        
        for symbol, quantity in self.positions.items():
            if abs(quantity) < 0.001:
                continue
            
            current_price = current_prices.get(symbol) if current_prices else None
            current_value = quantity * current_price if current_price else self.position_values.get(symbol, 0)
            
            positions_data.append({
                'symbol': symbol,
                'quantity': quantity,
                'current_price': current_price,
                'current_value': current_value,
                'weight': current_value / self.get_portfolio_value_dict(current_prices) if current_prices else 0
            })
        
        return pd.DataFrame(positions_data)
    
    def generate_performance_report(self, current_prices: Dict[str, float] = None) -> str:
        """
        Generate performance report
        
        Args:
            current_prices: Current market prices
        
        Returns:
            Formatted report string
        """
        pnl = self.calculate_pnl(current_prices)
        positions_df = self.get_positions_summary(current_prices)
        
        report = f"\n{'=' * 80}\n"
        report += f"PAPER TRADING PERFORMANCE REPORT\n"
        report += f"{'=' * 80}\n\n"
        
        report += f"PORTFOLIO SUMMARY:\n"
        report += f"  Initial Capital: ₹{pnl['initial_capital']:,.0f}\n"
        report += f"  Current Value: ₹{pnl['current_value']:,.0f}\n"
        report += f"  Cash: ₹{pnl['cash']:,.0f}\n"
        report += f"  Positions Value: ₹{pnl['positions_value']:,.0f}\n"
        report += f"  Total P&L: ₹{pnl['total_pnl']:,.0f} ({pnl['total_return_pct']:.2f}%)\n\n"
        
        report += f"TRADING COSTS:\n"
        report += f"  Total Transactions: {pnl['total_transactions']}\n"
        report += f"  Total Costs: ₹{pnl['total_costs']:,.2f}\n"
        report += f"  Cost as % of Capital: {(pnl['total_costs']/pnl['initial_capital']*100):.3f}%\n\n"
        
        if not positions_df.empty:
            report += f"CURRENT POSITIONS ({len(positions_df)}):\n"
            report += f"{'-' * 80}\n"
            report += f"{'Symbol':<15}{'Quantity':<15}{'Price':<15}{'Value':<15}{'Weight':<15}\n"
            report += f"{'-' * 80}\n"
            
            for _, row in positions_df.iterrows():
                report += f"{row['symbol']:<15}{row['quantity']:<15.2f}"
                report += f"₹{row['current_price']:<14.2f}" if row['current_price'] else f"{'N/A':<15}"
                report += f"₹{row['current_value']:<14,.0f}{row['weight']:<15.2%}\n"
            
            report += f"{'-' * 80}\n"
        
        report += f"\n{'=' * 80}\n"
        
        return report
    
    def reset(self):
        """Reset portfolio to initial state"""
        self.cash = self.initial_capital
        self.positions = {}
        self.position_values = {}
        self.transaction_history = []
        self.portfolio_history = []
        self.pnl_history = []
        self.total_transactions = 0
        self.total_costs = 0.0
        
        logger.info("Portfolio reset to initial state")


if __name__ == "__main__":
    # Test paper trading engine
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    engine = PaperTradingEngine(initial_capital=1000000)
    
    # Simulate some trades
    prices = {'INFY': 1500, 'TCS': 3500, 'WIPRO': 450}
    weights = {'INFY': 0.4, 'TCS': 0.4, 'WIPRO': 0.2}
    
    result = engine.rebalance_portfolio(weights, prices)
    
    print(engine.generate_performance_report(prices))

