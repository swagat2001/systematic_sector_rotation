"""
Order Manager for Systematic Sector Rotation Strategy

Manages order lifecycle:
- Order validation (sufficient cash, valid quantity)
- Order routing logic
- Execution price calculation
- Position tracking and updates
- Transaction logging
- Order status management
- Partial fills handling

Works with Paper Trading Engine to execute portfolio changes.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class OrderType(Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Order:
    """Represents a single order"""
    
    def __init__(self, symbol: str, quantity: float, order_type: OrderType = OrderType.MARKET,
                 limit_price: float = None, date: datetime = None):
        self.order_id = self._generate_order_id()
        self.symbol = symbol
        self.quantity = quantity  # Positive for buy, negative for sell
        self.order_type = order_type
        self.limit_price = limit_price
        self.date = date or datetime.now()
        
        self.status = OrderStatus.PENDING
        self.executed_quantity = 0.0
        self.execution_price = None
        self.execution_date = None
        self.failure_reason = None
    
    @staticmethod
    def _generate_order_id() -> str:
        """Generate unique order ID"""
        return f"ORD{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    def __repr__(self):
        action = "BUY" if self.quantity > 0 else "SELL"
        return f"Order({self.order_id}, {action} {abs(self.quantity):.2f} {self.symbol} @ {self.order_type.value})"


class OrderManager:
    """
    Manages order execution and tracking
    """
    
    def __init__(self):
        self.config = Config()
        
        # Order tracking
        self.pending_orders = []
        self.executed_orders = []
        self.failed_orders = []
        
        # Order history
        self.order_history = []
        
        logger.info("OrderManager initialized")
    
    def create_order(self, symbol: str, quantity: float, 
                    order_type: OrderType = OrderType.MARKET,
                    limit_price: float = None,
                    date: datetime = None) -> Order:
        """
        Create a new order
        
        Args:
            symbol: Stock/sector symbol
            quantity: Order quantity (positive=buy, negative=sell)
            order_type: Market or limit order
            limit_price: Limit price (for limit orders)
            date: Order date
        
        Returns:
            Order object
        """
        order = Order(symbol, quantity, order_type, limit_price, date)
        self.pending_orders.append(order)
        
        action = "BUY" if quantity > 0 else "SELL"
        logger.info(f"Order created: {action} {abs(quantity):.2f} {symbol}")
        
        return order
    
    def create_orders_from_trades(self, trades: List[Dict], date: datetime = None) -> List[Order]:
        """
        Create orders from trade list
        
        Args:
            trades: List of trade dicts from portfolio manager
            date: Order date
        
        Returns:
            List of created orders
        """
        orders = []
        
        for trade in trades:
            symbol = trade['symbol']
            action = trade['action']
            
            # Calculate quantity based on action
            if action == 'BUY':
                # New position
                quantity = trade['new_weight'] * 1000000 / 1000  # Simplified
            elif action == 'SELL':
                # Close position
                quantity = -abs(trade.get('quantity', 0))
            else:  # REBALANCE
                # Adjust position
                quantity = trade['change'] * 1000000 / 1000  # Simplified
            
            if abs(quantity) > 0.01:  # Ignore tiny orders
                order = self.create_order(symbol, quantity, date=date)
                orders.append(order)
        
        logger.info(f"Created {len(orders)} orders from {len(trades)} trades")
        
        return orders
    
    def validate_order(self, order: Order, available_cash: float, 
                      current_price: float) -> Tuple[bool, Optional[str]]:
        """
        Validate order before execution
        
        Args:
            order: Order to validate
            available_cash: Available cash balance
            current_price: Current market price
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check quantity
        if order.quantity == 0:
            return False, "Zero quantity"
        
        # Check price availability
        if current_price is None or current_price <= 0:
            return False, "Invalid price"
        
        # For buy orders, check sufficient cash
        if order.quantity > 0:
            required_cash = abs(order.quantity) * current_price * 1.002  # Including costs
            if required_cash > available_cash:
                return False, f"Insufficient cash: need ₹{required_cash:,.0f}, have ₹{available_cash:,.0f}"
        
        # For limit orders, check price
        if order.order_type == OrderType.LIMIT:
            if order.limit_price is None:
                return False, "Limit price not specified"
            
            if order.quantity > 0 and current_price > order.limit_price:
                return False, f"Price {current_price} above limit {order.limit_price}"
            elif order.quantity < 0 and current_price < order.limit_price:
                return False, f"Price {current_price} below limit {order.limit_price}"
        
        return True, None
    
    def execute_order(self, order: Order, execution_price: float,
                     date: datetime = None) -> bool:
        """
        Execute an order
        
        Args:
            order: Order to execute
            execution_price: Execution price
            date: Execution date
        
        Returns:
            True if executed successfully
        """
        if order.status != OrderStatus.PENDING:
            logger.warning(f"Order {order.order_id} already {order.status.value}")
            return False
        
        try:
            # Mark as executed
            order.status = OrderStatus.EXECUTED
            order.executed_quantity = order.quantity
            order.execution_price = execution_price
            order.execution_date = date or datetime.now()
            
            # Move to executed list
            if order in self.pending_orders:
                self.pending_orders.remove(order)
            self.executed_orders.append(order)
            self.order_history.append(order)
            
            action = "BUY" if order.quantity > 0 else "SELL"
            logger.info(f"Order executed: {action} {abs(order.quantity):.2f} {order.symbol} @ ₹{execution_price:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing order {order.order_id}: {e}")
            self.fail_order(order, str(e))
            return False
    
    def fail_order(self, order: Order, reason: str):
        """
        Mark order as failed
        
        Args:
            order: Order that failed
            reason: Failure reason
        """
        order.status = OrderStatus.FAILED
        order.failure_reason = reason
        
        if order in self.pending_orders:
            self.pending_orders.remove(order)
        self.failed_orders.append(order)
        self.order_history.append(order)
        
        logger.warning(f"Order failed: {order.order_id} - {reason}")
    
    def cancel_order(self, order: Order):
        """
        Cancel a pending order
        
        Args:
            order: Order to cancel
        """
        if order.status != OrderStatus.PENDING:
            logger.warning(f"Cannot cancel order {order.order_id} with status {order.status.value}")
            return
        
        order.status = OrderStatus.CANCELLED
        
        if order in self.pending_orders:
            self.pending_orders.remove(order)
        self.order_history.append(order)
        
        logger.info(f"Order cancelled: {order.order_id}")
    
    def get_pending_orders(self) -> List[Order]:
        """Get all pending orders"""
        return self.pending_orders.copy()
    
    def get_order_history(self, symbol: str = None, 
                         start_date: datetime = None,
                         end_date: datetime = None) -> pd.DataFrame:
        """
        Get order history as DataFrame
        
        Args:
            symbol: Filter by symbol
            start_date: Filter by start date
            end_date: Filter by end date
        
        Returns:
            DataFrame with order history
        """
        if not self.order_history:
            return pd.DataFrame()
        
        orders_data = []
        
        for order in self.order_history:
            # Apply filters
            if symbol and order.symbol != symbol:
                continue
            if start_date and order.date < start_date:
                continue
            if end_date and order.date > end_date:
                continue
            
            action = "BUY" if order.quantity > 0 else "SELL"
            
            orders_data.append({
                'order_id': order.order_id,
                'date': order.date,
                'symbol': order.symbol,
                'action': action,
                'quantity': abs(order.quantity),
                'order_type': order.order_type.value,
                'status': order.status.value,
                'execution_price': order.execution_price,
                'execution_date': order.execution_date,
                'failure_reason': order.failure_reason
            })
        
        return pd.DataFrame(orders_data)
    
    def get_execution_summary(self) -> Dict:
        """
        Get summary of order executions
        
        Returns:
            Dict with execution statistics
        """
        total_orders = len(self.order_history)
        executed = len(self.executed_orders)
        failed = len(self.failed_orders)
        pending = len(self.pending_orders)
        
        execution_rate = (executed / total_orders * 100) if total_orders > 0 else 0
        
        return {
            'total_orders': total_orders,
            'executed': executed,
            'failed': failed,
            'pending': pending,
            'execution_rate': execution_rate
        }
    
    def generate_order_report(self) -> str:
        """
        Generate order management report
        
        Returns:
            Formatted report string
        """
        summary = self.get_execution_summary()
        history_df = self.get_order_history()
        
        report = f"\n{'=' * 80}\n"
        report += f"ORDER MANAGEMENT REPORT\n"
        report += f"{'=' * 80}\n\n"
        
        report += f"EXECUTION SUMMARY:\n"
        report += f"  Total Orders: {summary['total_orders']}\n"
        report += f"  Executed: {summary['executed']}\n"
        report += f"  Failed: {summary['failed']}\n"
        report += f"  Pending: {summary['pending']}\n"
        report += f"  Execution Rate: {summary['execution_rate']:.1f}%\n\n"
        
        if not history_df.empty:
            # Recent executed orders
            recent_executed = history_df[history_df['status'] == 'EXECUTED'].tail(10)
            
            if not recent_executed.empty:
                report += f"RECENT EXECUTIONS (Last 10):\n"
                report += f"{'-' * 80}\n"
                report += f"{'Date':<20}{'Symbol':<15}{'Action':<10}{'Qty':<12}{'Price':<12}\n"
                report += f"{'-' * 80}\n"
                
                for _, row in recent_executed.iterrows():
                    report += f"{str(row['date']):<20}{row['symbol']:<15}{row['action']:<10}"
                    report += f"{row['quantity']:<12.2f}₹{row['execution_price']:<11.2f}\n"
                
                report += f"{'-' * 80}\n\n"
            
            # Failed orders
            failed_orders = history_df[history_df['status'] == 'FAILED']
            
            if not failed_orders.empty:
                report += f"FAILED ORDERS ({len(failed_orders)}):\n"
                report += f"{'-' * 80}\n"
                
                for _, row in failed_orders.iterrows():
                    report += f"  {row['symbol']}: {row['failure_reason']}\n"
                
                report += f"{'-' * 80}\n"
        
        report += f"\n{'=' * 80}\n"
        
        return report
    
    def reset(self):
        """Reset order manager"""
        self.pending_orders = []
        self.executed_orders = []
        self.failed_orders = []
        self.order_history = []
        
        logger.info("Order manager reset")


if __name__ == "__main__":
    # Test order manager
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    manager = OrderManager()
    
    # Create some test orders
    order1 = manager.create_order("INFY", 100, OrderType.MARKET)
    order2 = manager.create_order("TCS", -50, OrderType.MARKET)
    order3 = manager.create_order("WIPRO", 200, OrderType.LIMIT, limit_price=450)
    
    # Validate and execute
    is_valid, error = manager.validate_order(order1, 200000, 1500)
    print(f"Order 1 valid: {is_valid}, Error: {error}")
    
    if is_valid:
        manager.execute_order(order1, 1502.5)
    
    # Generate report
    print(manager.generate_order_report())
