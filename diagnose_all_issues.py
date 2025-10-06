"""
Comprehensive Diagnostic Script for Systematic Sector Rotation Strategy

This script analyzes the entire codebase to identify all integration issues,
API mismatches, missing methods, and data flow problems.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import inspect
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

# Import all key components
from config import Config
from strategy.sector_rotation import SectorRotationEngine
from strategy.stock_selection import StockSelectionEngine
from strategy.dual_approach_portfolio import DualApproachPortfolioManager
from models.composite_scorer import CompositeScorer
from backtesting.backtest_engine import BacktestEngine
from execution.paper_trading import PaperTradingEngine

print("=" * 100)
print("COMPREHENSIVE SYSTEM DIAGNOSTIC")
print("=" * 100)

# ============================================================================
# PHASE 1: Method Signature Analysis
# ============================================================================
print("\n" + "=" * 100)
print("PHASE 1: METHOD SIGNATURE ANALYSIS")
print("=" * 100)

def get_method_signature(obj, method_name):
    """Get method signature details"""
    try:
        method = getattr(obj, method_name)
        sig = inspect.signature(method)
        return {
            'exists': True,
            'params': list(sig.parameters.keys()),
            'signature': str(sig)
        }
    except AttributeError:
        return {'exists': False, 'error': 'Method not found'}

# Check SectorRotationEngine
print("\n1. SectorRotationEngine")
print("-" * 100)
sector_engine = SectorRotationEngine()
print(f"  rebalance_sectors: {get_method_signature(sector_engine, 'rebalance_sectors')}")
print(f"  calculate_sector_weights: {get_method_signature(sector_engine, 'calculate_sector_weights')}")

# Check StockSelectionEngine
print("\n2. StockSelectionEngine")
print("-" * 100)
stock_engine = StockSelectionEngine()
sig = get_method_signature(stock_engine, 'select_stocks')
print(f"  select_stocks: {sig}")
if sig['exists']:
    print(f"    Expected params: stocks_data (Dict), stocks_prices (Dict), benchmark_data, sector_mapping, previous_holdings")
    print(f"    Actual params: {sig['params']}")

# Check CompositeScorer
print("\n3. CompositeScorer")
print("-" * 100)
scorer = CompositeScorer()
sig = get_method_signature(scorer, 'batch_calculate_scores')
print(f"  batch_calculate_scores: {sig}")
if sig['exists']:
    print(f"    Expected params: stocks_data (Dict), stocks_prices (Dict), benchmark_data, sector_mapping")
    print(f"    Actual params: {sig['params']}")

# Check DualApproachPortfolioManager
print("\n4. DualApproachPortfolioManager")
print("-" * 100)
portfolio_mgr = DualApproachPortfolioManager()
sig = get_method_signature(portfolio_mgr, 'rebalance_portfolio')
print(f"  rebalance_portfolio: {sig}")
if sig['exists']:
    print(f"    Expected params: sector_prices, stocks_data, stocks_prices, total_capital, as_of_date")
    print(f"    Actual params: {sig['params']}")

sig = get_method_signature(portfolio_mgr, '_rebalance_core')
print(f"  _rebalance_core: {sig}")

sig = get_method_signature(portfolio_mgr, '_rebalance_satellite')
print(f"  _rebalance_satellite: {sig}")

# Check BacktestEngine
print("\n5. BacktestEngine")
print("-" * 100)
try:
    backtest_engine = BacktestEngine(initial_capital=1000000)
    sig = get_method_signature(backtest_engine.portfolio_manager, 'rebalance_portfolio')
    print(f"  portfolio_manager type: {type(backtest_engine.portfolio_manager).__name__}")
    print(f"  portfolio_manager.rebalance_portfolio: {sig}")
except Exception as e:
    print(f"  ERROR initializing BacktestEngine: {e}")

# ============================================================================
# PHASE 2: Return Value Analysis
# ============================================================================
print("\n\n" + "=" * 100)
print("PHASE 2: RETURN VALUE ANALYSIS")
print("=" * 100)

# Test with minimal data
dates = pd.date_range(start='2022-01-01', end='2024-01-01', freq='B')

test_sector_prices = {}
for sector in ['Nifty IT', 'Nifty Bank', 'Nifty Auto']:
    prices = 1000 * (1 + pd.Series(np.random.randn(len(dates)) * 0.01).cumsum())
    test_sector_prices[sector] = pd.DataFrame({
        'Close': prices.values,
        'Volume': 10000000
    }, index=dates)

test_stocks_data = {}
test_stocks_prices = {}
for symbol in ['INFY', 'TCS', 'WIPRO']:
    test_stocks_data[symbol] = {
        'sector': 'Nifty IT',
        'roe': 0.25,
        'market_cap': 100000000000
    }
    prices = 1000 * (1 + pd.Series(np.random.randn(len(dates)) * 0.015).cumsum())
    test_stocks_prices[symbol] = pd.DataFrame({
        'Close': prices.values,
        'Volume': 5000000
    }, index=dates)

# Test SectorRotationEngine
print("\n1. Testing SectorRotationEngine.rebalance_sectors()")
print("-" * 100)
try:
    sector_result = sector_engine.rebalance_sectors(test_sector_prices, datetime(2023, 6, 1))
    print(f"  Success: {sector_result.get('success')}")
    print(f"  Keys returned: {list(sector_result.keys())}")
    print(f"  Selected sectors: {sector_result.get('selected_sectors')}")
    print(f"  Weights: {sector_result.get('weights')}")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test StockSelectionEngine
print("\n2. Testing StockSelectionEngine.select_stocks()")
print("-" * 100)
try:
    stock_result = stock_engine.select_stocks(
        stocks_data=test_stocks_data,
        stocks_prices=test_stocks_prices,
        benchmark_data=None,
        sector_mapping=None,
        previous_holdings=None
    )
    print(f"  Success: {stock_result.get('success')}")
    print(f"  Keys returned: {list(stock_result.keys())}")
    print(f"  Selected stocks: {stock_result.get('selected_stocks')}")
    print(f"  Weights: {stock_result.get('weights')}")
    print(f"  Number of stocks: {stock_result.get('num_stocks')}")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test DualApproachPortfolioManager
print("\n3. Testing DualApproachPortfolioManager.rebalance_portfolio()")
print("-" * 100)
try:
    portfolio_result = portfolio_mgr.rebalance_portfolio(
        sector_prices=test_sector_prices,
        stocks_data=test_stocks_data,
        stocks_prices=test_stocks_prices,
        total_capital=1000000,
        as_of_date=datetime(2023, 6, 1)
    )
    print(f"  Success: {portfolio_result.get('success')}")
    print(f"  Keys returned: {list(portfolio_result.keys())}")
    if portfolio_result.get('success'):
        print(f"  Core allocation: {portfolio_result['core']['allocation']}")
        print(f"  Core selected sectors: {portfolio_result['core'].get('selected_sectors')}")
        print(f"  Core stocks: {len(portfolio_result['core']['stocks'])}")
        print(f"  Satellite stocks: {len(portfolio_result['satellite']['stocks'])}")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# PHASE 3: Data Flow Analysis
# ============================================================================
print("\n\n" + "=" * 100)
print("PHASE 3: DATA FLOW TRACE")
print("=" * 100)

print("\nExpected data flow:")
print("1. BacktestEngine calls DualApproachPortfolioManager.rebalance_portfolio()")
print("   → Expects: sector_prices, stocks_data, stocks_prices, total_capital, as_of_date")
print("2. DualApproachPortfolioManager._rebalance_core()")
print("   → Calls: SectorRotationEngine.rebalance_sectors()")
print("   → Returns: {'success', 'selected_sectors', 'weights', ...}")
print("3. DualApproachPortfolioManager._rebalance_satellite()")
print("   → Calls: StockSelectionEngine.select_stocks()")
print("   → Returns: {'success', 'selected_stocks', 'weights', ...}")

# ============================================================================
# PHASE 4: Configuration Check
# ============================================================================
print("\n\n" + "=" * 100)
print("PHASE 4: CONFIGURATION VALIDATION")
print("=" * 100)

print(f"\nCore Allocation: {Config.CORE_ALLOCATION}")
print(f"Satellite Allocation: {Config.SATELLITE_ALLOCATION}")
print(f"Core Config: {Config.CORE_CONFIG}")
print(f"Satellite Config: {Config.SATELLITE_CONFIG}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n\n" + "=" * 100)
print("DIAGNOSTIC SUMMARY")
print("=" * 100)

print("\nCRITICAL ISSUES FOUND:")
print("1. Check if StockSelectionEngine.select_stocks() returns {'success', 'selected_stocks', 'weights'}")
print("2. Check if SectorRotationEngine.rebalance_sectors() returns {'selected_sectors', 'weights'}")
print("3. Check if _rebalance_core properly handles sector_result keys")
print("4. Check if _rebalance_satellite properly handles stock_result keys")
print("5. Check liquidity filter settings - may be filtering out all stocks")

print("\nRUN THIS SCRIPT TO SEE EXACT ERROR LOCATIONS")
print("=" * 100)
