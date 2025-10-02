"""
Test Script for Phase 4 Execution & Paper Trading

Tests paper trading engine and order manager with realistic scenarios
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from execution.paper_trading import PaperTradingEngine
from execution.order_manager import OrderManager, OrderType


def test_paper_trading_engine():
    """Test paper trading engine"""
    print("\n" + "="*80)
    print("TESTING PAPER TRADING ENGINE")
    print("="*80)
    
    # Initialize
    engine = PaperTradingEngine(initial_capital=1000000)
    
    print(f"\nInitial capital: ₹{engine.initial_capital:,.0f}")
    print(f"Initial cash: ₹{engine.cash:,.0f}")
    
    # Test single order execution
    print("\n--- Test 1: Single Buy Order ---")
    result = engine.execute_order("INFY", "BUY", 0.30, 1500.0)
    
    assert result['status'] == 'executed', "Order should execute"
    assert 'INFY' in engine.positions, "Position should be created"
    print(f"[PASS] Buy order executed")
    print(f"  Cash remaining: ₹{engine.cash:,.0f}")
    print(f"  Position value: ₹{engine.position_values.get('INFY', 0):,.0f}")
    
    # Test portfolio rebalancing
    print("\n--- Test 2: Portfolio Rebalancing ---")
    target_weights = {
        'INFY': 0.25,
        'TCS': 0.25,
        'WIPRO': 0.25,
        'HCLTECH': 0.25
    }
    
    current_prices = {
        'INFY': 1500,
        'TCS': 3500,
        'WIPRO': 450,
        'HCLTECH': 1200
    }
    
    result = engine.rebalance_portfolio(target_weights, current_prices)
    
    assert len(result['executed']) > 0, "Should have executed trades"
    print(f"[PASS] Portfolio rebalanced")
    print(f"  Executed: {len(result['executed'])} orders")
    print(f"  Portfolio value: ₹{engine.get_portfolio_value_dict(current_prices):,.0f}")
    
    # Test P&L calculation
    print("\n--- Test 3: P&L Calculation ---")
    pnl = engine.calculate_pnl(current_prices)
    
    print(f"[PASS] P&L calculated")
    print(f"  Total P&L: ₹{pnl['total_pnl']:,.0f}")
    print(f"  Return: {pnl['total_return_pct']:.2f}%")
    print(f"  Total costs: ₹{pnl['total_costs']:,.2f}")
    
    # Test position summary
    print("\n--- Test 4: Position Summary ---")
    positions_df = engine.get_positions_summary(current_prices)
    
    assert not positions_df.empty, "Should have positions"
    print(f"[PASS] Position summary generated")
    print(f"\n{positions_df.to_string()}")
    
    # Test performance report
    print("\n--- Test 5: Performance Report ---")
    report = engine.generate_performance_report(current_prices)
    print(report)
    
    print("\n[PASS] Paper Trading Engine Test Complete")
    return True


def test_order_manager():
    """Test order manager"""
    print("\n" + "="*80)
    print("TESTING ORDER MANAGER")
    print("="*80)
    
    manager = OrderManager()
    
    # Test order creation
    print("\n--- Test 1: Order Creation ---")
    order1 = manager.create_order("INFY", 100, OrderType.MARKET)
    order2 = manager.create_order("TCS", -50, OrderType.MARKET)
    order3 = manager.create_order("WIPRO", 200, OrderType.LIMIT, limit_price=450)
    
    assert len(manager.pending_orders) == 3, "Should have 3 pending orders"
    print(f"[PASS] Created 3 orders")
    print(f"  Order 1: {order1}")
    print(f"  Order 2: {order2}")
    print(f"  Order 3: {order3}")
    
    # Test order validation
    print("\n--- Test 2: Order Validation ---")
    is_valid, error = manager.validate_order(order1, 200000, 1500)
    
    assert is_valid, f"Order should be valid: {error}"
    print(f"[PASS] Order validation passed")
    
    # Test insufficient cash
    is_valid, error = manager.validate_order(order1, 1000, 1500)
    assert not is_valid, "Should fail with insufficient cash"
    print(f"[PASS] Insufficient cash detected: {error}")
    
    # Test order execution
    print("\n--- Test 3: Order Execution ---")
    success = manager.execute_order(order1, 1502.5)
    
    assert success, "Order should execute"
    assert order1.status.value == 'EXECUTED', "Order should be marked executed"
    assert len(manager.executed_orders) == 1, "Should have 1 executed order"
    print(f"[PASS] Order executed successfully")
    print(f"  Execution price: ₹{order1.execution_price:.2f}")
    
    # Test order failure
    print("\n--- Test 4: Order Failure ---")
    manager.fail_order(order2, "Insufficient liquidity")
    
    assert order2.status.value == 'FAILED', "Order should be marked failed"
    assert len(manager.failed_orders) == 1, "Should have 1 failed order"
    print(f"[PASS] Order marked as failed")
    print(f"  Failure reason: {order2.failure_reason}")
    
    # Test order cancellation
    print("\n--- Test 5: Order Cancellation ---")
    manager.cancel_order(order3)
    
    assert order3.status.value == 'CANCELLED', "Order should be cancelled"
    print(f"[PASS] Order cancelled")
    
    # Test order history
    print("\n--- Test 6: Order History ---")
    history_df = manager.get_order_history()
    
    assert len(history_df) == 3, "Should have 3 orders in history"
    print(f"[PASS] Order history retrieved")
    print(f"\n{history_df.to_string()}")
    
    # Test execution summary
    print("\n--- Test 7: Execution Summary ---")
    summary = manager.get_execution_summary()
    
    print(f"[PASS] Execution summary generated")
    print(f"  Total: {summary['total_orders']}")
    print(f"  Executed: {summary['executed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Rate: {summary['execution_rate']:.1f}%")
    
    # Test order report
    print("\n--- Test 8: Order Report ---")
    report = manager.generate_order_report()
    print(report)
    
    print("\n[PASS] Order Manager Test Complete")
    return True


def test_integrated_workflow():
    """Test integrated workflow with both components"""
    print("\n" + "="*80)
    print("TESTING INTEGRATED WORKFLOW")
    print("="*80)
    
    # Initialize both
    engine = PaperTradingEngine(initial_capital=1000000)
    manager = OrderManager()
    
    print("\n--- Test: Complete Trading Workflow ---")
    
    # Step 1: Create orders
    symbols = ['INFY', 'TCS', 'WIPRO']
    prices = {'INFY': 1500, 'TCS': 3500, 'WIPRO': 450}
    
    for symbol in symbols:
        order = manager.create_order(symbol, 50, OrderType.MARKET)
        
        # Validate
        is_valid, error = manager.validate_order(order, engine.cash, prices[symbol])
        
        if is_valid:
            # Execute in paper trading
            result = engine.execute_order(symbol, "BUY", 0.10, prices[symbol])
            
            if result['status'] == 'executed':
                # Mark order as executed
                manager.execute_order(order, prices[symbol] * 1.001)
                print(f"  ✓ {symbol} executed")
        else:
            manager.fail_order(order, error)
            print(f"  ✗ {symbol} failed: {error}")
    
    # Step 2: Generate combined report
    print("\n--- Combined Performance ---")
    
    pnl = engine.calculate_pnl(prices)
    order_summary = manager.get_execution_summary()
    
    print(f"\nPortfolio:")
    print(f"  Value: ₹{pnl['current_value']:,.0f}")
    print(f"  P&L: ₹{pnl['total_pnl']:,.0f} ({pnl['total_return_pct']:.2f}%)")
    
    print(f"\nOrders:")
    print(f"  Total: {order_summary['total_orders']}")
    print(f"  Executed: {order_summary['executed']}")
    print(f"  Rate: {order_summary['execution_rate']:.1f}%")
    
    print("\n[PASS] Integrated Workflow Test Complete")
    return True


def main():
    """Run all Phase 4 tests"""
    print("\n" + "="*80)
    print("PHASE 4 EXECUTION & PAPER TRADING - COMPREHENSIVE TEST")
    print("="*80)
    
    tests_passed = 0
    tests_failed = 0
    
    tests = [
        ("Paper Trading Engine", test_paper_trading_engine),
        ("Order Manager", test_order_manager),
        ("Integrated Workflow", test_integrated_workflow)
    ]
    
    for test_name, test_func in tests:
        try:
            if test_func():
                tests_passed += 1
        except Exception as e:
            print(f"\n[FAIL] {test_name}: {e}")
            import traceback
            traceback.print_exc()
            tests_failed += 1
    
    # Summary
    print("\n" + "="*80)
    print("PHASE 4 TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {tests_passed + tests_failed}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    
    if tests_failed == 0:
        print("\n[SUCCESS] All Phase 4 tests passed!")
        print("Ready to proceed to Phase 5: Backtesting")
    else:
        print(f"\n[WARNING] {tests_failed} test(s) failed")
    
    print("="*80 + "\n")
    
    return 0 if tests_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
