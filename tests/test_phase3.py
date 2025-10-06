"""
Test Script for Phase 3 Strategy Components

This script properly tests all Phase 3 strategy modules with correct imports
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from datetime import datetime

from strategy.sector_rotation import SectorRotationEngine
from strategy.stock_selection import StockSelectionEngine
from strategy.portfolio_manager import PortfolioManager
from config import NSESectors


def generate_sample_data():
    """Generate sample data for testing"""
    dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='B')
    
    # Sample sector data
    sector_prices = {}
    for i, sector in enumerate(list(NSESectors.SECTOR_TICKERS.keys())[:5]):
        # Different momentum levels
        returns = np.random.randn(len(dates)) * 0.01 + (0.0003 * (5-i))
        prices = 1000 * (1 + pd.Series(returns)).cumprod()
        
        sector_prices[sector] = pd.DataFrame({
            'Open': prices.values,
            'High': prices.values * 1.01,
            'Low': prices.values * 0.99,
            'Close': prices.values,
            'Volume': np.random.uniform(10000000, 50000000, len(dates))
        }, index=dates)
    
    # Sample stock data
    test_stocks = ['INFY', 'TCS', 'WIPRO', 'HCLTECH', 'TECHM']
    
    stocks_fundamentals = {}
    stocks_prices = {}
    sector_mapping = {}
    
    for symbol in test_stocks:
        # Fundamentals
        stocks_fundamentals[symbol] = {
            'roe': np.random.uniform(0.15, 0.30),
            'gross_margin': np.random.uniform(0.35, 0.50),
            'operating_margin': np.random.uniform(0.20, 0.30),
            'current_ratio': np.random.uniform(1.5, 3.0),
            'earnings_growth': np.random.uniform(0.10, 0.20),
            'revenue_growth': np.random.uniform(0.08, 0.18),
            'pe_ratio': np.random.uniform(20, 30),
            'pb_ratio': np.random.uniform(3, 8),
            'ev_ebitda': np.random.uniform(10, 15),
            'debt_to_equity': np.random.uniform(0.0, 0.5),
            'interest_coverage': np.random.uniform(8, 20),
            'quick_ratio': np.random.uniform(1.0, 2.0),
            'market_cap': np.random.uniform(50000000000, 200000000000)
        }
        
        # Prices
        returns = np.random.randn(len(dates)) * 0.015 + 0.0005
        prices = 1000 * (1 + pd.Series(returns)).cumprod()
        
        stocks_prices[symbol] = pd.DataFrame({
            'Open': prices.values,
            'High': prices.values * 1.02,
            'Low': prices.values * 0.98,
            'Close': prices.values,
            'Volume': np.random.uniform(5000000, 10000000, len(dates))
        }, index=dates)
        
        # Sector mapping
        sector_mapping[symbol] = 'Nifty IT'
    
    # Benchmark data
    benchmark_returns = np.random.randn(len(dates)) * 0.01 + 0.0003
    benchmark_prices = 10000 * (1 + pd.Series(benchmark_returns)).cumprod()
    
    benchmark_data = pd.DataFrame({
        'Open': benchmark_prices.values,
        'High': benchmark_prices.values * 1.005,
        'Low': benchmark_prices.values * 0.995,
        'Close': benchmark_prices.values,
        'Volume': np.random.uniform(100000000, 500000000, len(dates))
    }, index=dates)
    
    return sector_prices, stocks_fundamentals, stocks_prices, sector_mapping, benchmark_data


def test_sector_rotation():
    """Test sector rotation engine"""
    print("\n" + "="*80)
    print("TESTING SECTOR ROTATION ENGINE")
    print("="*80)
    
    engine = SectorRotationEngine()
    
    sector_prices, _, _, _, _ = generate_sample_data()
    
    # Test ranking and rebalancing
    result = engine.rebalance_sectors(sector_prices)
    
    if result['success']:
        rankings_df = pd.DataFrame(result['rankings'])
        report = engine.generate_rotation_report(rankings_df)
        print(report)
        print("\n[PASS] Sector Rotation Engine Test")
        return True
    else:
        print(f"\n[FAIL] Sector rotation failed: {result.get('error')}")
        return False


def test_stock_selection():
    """Test stock selection engine"""
    print("\n" + "="*80)
    print("TESTING STOCK SELECTION ENGINE")
    print("="*80)
    
    engine = StockSelectionEngine()
    
    _, stocks_fundamentals, stocks_prices, sector_mapping, benchmark_data = generate_sample_data()
    
    # Test stock selection
    result = engine.select_stocks(
        stocks_fundamentals,
        stocks_prices,
        benchmark_data,
        sector_mapping
    )
    
    if result['success']:
        report = engine.generate_selection_report(result)
        print(report)
        print("\n[PASS] Stock Selection Engine Test")
        return True
    else:
        print(f"\n[FAIL] Stock selection failed: {result.get('error')}")
        return False


def test_portfolio_manager():
    """Test portfolio manager"""
    print("\n" + "="*80)
    print("TESTING PORTFOLIO MANAGER")
    print("="*80)
    
    manager = PortfolioManager()
    
    sector_prices, stocks_fundamentals, stocks_prices, sector_mapping, benchmark_data = generate_sample_data()
    
    # Test portfolio rebalancing
    result = manager.rebalance_portfolio(
        sector_prices,
        stocks_fundamentals,
        stocks_prices,
        benchmark_data,
        sector_mapping
    )
    
    if result['success']:
        report = manager.generate_portfolio_report(result)
        print(report)
        
        # Portfolio summary
        summary = manager.get_portfolio_summary()
        print("\nPortfolio Summary:")
        print(f"  Total positions: {summary['total_positions']}")
        print(f"  Sector positions: {summary['sector_positions']}")
        print(f"  Stock positions: {summary['stock_positions']}")
        print(f"  Total weight: {summary['total_weight']:.1%}")
        
        print("\n[PASS] Portfolio Manager Test")
        return True
    else:
        print(f"\n[FAIL] Portfolio rebalancing failed: {result.get('error')}")
        return False


def main():
    """Run all Phase 3 tests"""
    print("\n" + "="*80)
    print("PHASE 3 STRATEGY IMPLEMENTATION - COMPREHENSIVE TEST")
    print("="*80)
    
    tests_passed = 0
    tests_failed = 0
    
    tests = [
        ("Sector Rotation Engine", test_sector_rotation),
        ("Stock Selection Engine", test_stock_selection),
        ("Portfolio Manager", test_portfolio_manager)
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
    print("PHASE 3 TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {tests_passed + tests_failed}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    
    if tests_failed == 0:
        print("\n[SUCCESS] All Phase 3 tests passed!")
        print("Ready to proceed to Phase 4: Execution & Paper Trading")
    else:
        print(f"\n[WARNING] {tests_failed} test(s) failed")
    
    print("="*80 + "\n")
    
    return 0 if tests_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
