"""
Test Script for Phase 5 Backtesting

Tests backtest engine and performance analyzer with sample data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from backtesting.backtest_engine import BacktestEngine
from backtesting.performance_analyzer import PerformanceAnalyzer


def generate_test_data():
    """Generate sample data for backtesting"""
    dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='B')
    
    # Sector data
    sectors = {}
    for i, sector in enumerate(['Nifty IT', 'Nifty Bank', 'Nifty Auto', 'Nifty Pharma', 'Nifty FMCG']):
        # Different momentum characteristics
        base_return = 0.0003 + (0.0002 * (5-i) / 5)
        returns = np.random.randn(len(dates)) * 0.01 + base_return
        prices = 10000 * (1 + pd.Series(returns)).cumprod()
        
        sectors[sector] = pd.DataFrame({
            'Open': prices.values * 0.995,
            'High': prices.values * 1.005,
            'Low': prices.values * 0.995,
            'Close': prices.values,
            'Volume': np.random.uniform(10000000, 50000000, len(dates))
        }, index=dates)
    
    # Stock data
    stocks = {}
    fundamentals = {}
    for i, symbol in enumerate(['INFY', 'TCS', 'WIPRO', 'HCLTECH', 'TECHM']):
        # Different performance levels
        base_return = 0.0005 + (0.0003 * (5-i) / 5)
        returns = np.random.randn(len(dates)) * 0.015 + base_return
        prices = 1000 * (1 + pd.Series(returns)).cumprod()
        
        stocks[symbol] = pd.DataFrame({
            'Open': prices.values * 0.99,
            'High': prices.values * 1.02,
            'Low': prices.values * 0.98,
            'Close': prices.values,
            'Volume': np.random.uniform(5000000, 10000000, len(dates))
        }, index=dates)
        
        fundamentals[symbol] = {
            'roe': np.random.uniform(0.15, 0.30),
            'gross_margin': np.random.uniform(0.35, 0.50),
            'pe_ratio': np.random.uniform(20, 30),
            'market_cap': np.random.uniform(50000000000, 200000000000)
        }
    
    # Benchmark
    benchmark_returns = np.random.randn(len(dates)) * 0.008 + 0.0003
    benchmark_prices = 10000 * (1 + pd.Series(benchmark_returns)).cumprod()
    
    benchmark = pd.DataFrame({
        'Open': benchmark_prices.values * 0.998,
        'High': benchmark_prices.values * 1.002,
        'Low': benchmark_prices.values * 0.998,
        'Close': benchmark_prices.values,
        'Volume': np.random.uniform(100000000, 500000000, len(dates))
    }, index=dates)
    
    return sectors, fundamentals, stocks, benchmark


def test_backtest_engine():
    """Test backtest engine"""
    print("\n" + "="*80)
    print("TESTING BACKTEST ENGINE")
    print("="*80)
    
    # Generate data
    sectors, fundamentals, stocks, benchmark = generate_test_data()
    
    # Initialize engine
    engine = BacktestEngine(
        initial_capital=1000000,
        start_date=datetime(2021, 1, 1),
        end_date=datetime(2023, 12, 31)
    )
    
    print(f"\nInitial capital: ₹{engine.initial_capital:,.0f}")
    print(f"Period: {engine.start_date.date()} to {engine.end_date.date()}")
    
    # Run backtest
    print("\n--- Running Backtest ---")
    result = engine.run_backtest(
        sectors,
        fundamentals,
        stocks,
        benchmark
    )
    
    assert result['success'], "Backtest should succeed"
    assert result['num_rebalances'] > 0, "Should have rebalances"
    assert len(result['equity_curve']) > 0, "Should have equity curve"
    
    print(f"\n[PASS] Backtest completed successfully")
    print(f"  Rebalances: {result['num_rebalances']}")
    print(f"  Final value: ₹{result['final_value']:,.0f}")
    print(f"  Return: {((result['final_value']/result['initial_capital'] - 1) * 100):.2f}%")
    
    # Generate report
    print("\n--- Generating Report ---")
    report = engine.generate_backtest_report(result)
    print(report)
    
    print("\n[PASS] Backtest Engine Test Complete")
    return result


def test_performance_analyzer(backtest_result):
    """Test performance analyzer"""
    print("\n" + "="*80)
    print("TESTING PERFORMANCE ANALYZER")
    print("="*80)
    
    # Initialize analyzer
    analyzer = PerformanceAnalyzer(risk_free_rate=0.065)
    
    # Generate benchmark returns
    daily_values = backtest_result['daily_values']
    benchmark_returns = pd.Series(
        np.random.randn(len(daily_values)) * 0.008 + 0.0003,
        index=daily_values.index
    )
    
    # Analyze
    print("\n--- Test 1: Complete Analysis ---")
    analysis = analyzer.analyze(backtest_result, benchmark_returns)
    
    assert 'returns' in analysis, "Should have return metrics"
    assert 'risk' in analysis, "Should have risk metrics"
    assert 'drawdown' in analysis, "Should have drawdown metrics"
    
    print(f"[PASS] Analysis completed")
    print(f"  Return metrics: {len(analysis['returns'])} items")
    print(f"  Risk metrics: {len(analysis['risk'])} items")
    print(f"  Drawdown metrics: {len(analysis['drawdown'])} items")
    
    # Test return metrics
    print("\n--- Test 2: Return Metrics ---")
    returns = analysis['returns']
    
    print(f"  CAGR: {returns.get('cagr', 0):.2f}%")
    print(f"  Total Return: {returns.get('total_return', 0):.2f}%")
    print(f"  Positive Days: {returns.get('positive_pct', 0):.1f}%")
    print(f"[PASS] Return metrics validated")
    
    # Test risk metrics
    print("\n--- Test 3: Risk Metrics ---")
    risk = analysis['risk']
    
    print(f"  Sharpe Ratio: {risk.get('sharpe_ratio', 0):.2f}")
    print(f"  Volatility: {risk.get('volatility', 0):.2f}%")
    print(f"  Beta: {risk.get('beta', 1.0):.2f}")
    print(f"[PASS] Risk metrics validated")
    
    # Test drawdown metrics
    print("\n--- Test 4: Drawdown Metrics ---")
    drawdown = analysis['drawdown']
    
    print(f"  Max Drawdown: {drawdown.get('max_drawdown', 0):.2f}%")
    print(f"  Longest DD: {drawdown.get('longest_dd_days', 0)} days")
    print(f"[PASS] Drawdown metrics validated")
    
    # Test benchmark comparison
    print("\n--- Test 5: Benchmark Comparison ---")
    benchmark = analysis.get('benchmark', {})
    
    if benchmark:
        print(f"  Outperformance: {benchmark.get('outperformance', 0):.2f}%")
        print(f"  Win Rate: {benchmark.get('win_rate', 0):.1f}%")
        print(f"[PASS] Benchmark comparison validated")
    
    # Generate comprehensive report
    print("\n--- Test 6: Performance Report ---")
    report = analyzer.generate_performance_report(analysis)
    print(report)
    
    # Monthly returns table
    print("\n--- Test 7: Monthly Returns Table ---")
    monthly_table = analyzer.generate_monthly_returns_table(daily_values)
    
    if not monthly_table.empty:
        print("\nMonthly Returns (%):")
        print(monthly_table.round(2).head())
        print(f"[PASS] Monthly returns table generated")
    
    print("\n[PASS] Performance Analyzer Test Complete")
    return analysis


def test_integrated_backtesting():
    """Test complete integrated backtesting workflow"""
    print("\n" + "="*80)
    print("TESTING INTEGRATED BACKTESTING WORKFLOW")
    print("="*80)
    
    # Generate data
    print("\n--- Step 1: Generating test data ---")
    sectors, fundamentals, stocks, benchmark = generate_test_data()
    print(f"  Sectors: {len(sectors)}")
    print(f"  Stocks: {len(stocks)}")
    print(f"  Data points: {len(list(sectors.values())[0])}")
    
    # Run backtest
    print("\n--- Step 2: Running backtest ---")
    engine = BacktestEngine(
        initial_capital=1000000,
        start_date=datetime(2021, 1, 1),
        end_date=datetime(2023, 12, 31)
    )
    
    result = engine.run_backtest(sectors, fundamentals, stocks, benchmark)
    
    assert result['success'], "Backtest should succeed"
    print(f"  Status: SUCCESS")
    print(f"  Equity curve points: {len(result['equity_curve'])}")
    
    # Analyze performance
    print("\n--- Step 3: Analyzing performance ---")
    analyzer = PerformanceAnalyzer()
    
    benchmark_returns = benchmark['Close'].pct_change().dropna()
    analysis = analyzer.analyze(result, benchmark_returns)
    
    print(f"  Metrics calculated: {len(analysis)} categories")
    
    # Generate final report
    print("\n--- Step 4: Generating final report ---")
    
    print("\n" + "="*80)
    print("INTEGRATED BACKTEST RESULTS")
    print("="*80)
    
    # Key metrics summary
    returns = analysis.get('returns', {})
    risk = analysis.get('risk', {})
    drawdown = analysis.get('drawdown', {})
    
    print(f"\nKEY METRICS:")
    print(f"  Initial Capital: ₹{result['initial_capital']:,.0f}")
    print(f"  Final Value: ₹{result['final_value']:,.0f}")
    print(f"  Total Return: {returns.get('total_return', 0):.2f}%")
    print(f"  CAGR: {returns.get('cagr', 0):.2f}%")
    print(f"  Sharpe Ratio: {risk.get('sharpe_ratio', 0):.2f}")
    print(f"  Max Drawdown: {drawdown.get('max_drawdown', 0):.2f}%")
    print(f"  Volatility: {risk.get('volatility', 0):.2f}%")
    
    benchmark_comp = analysis.get('benchmark', {})
    if benchmark_comp:
        print(f"\nVS BENCHMARK:")
        print(f"  Outperformance: {benchmark_comp.get('outperformance', 0):.2f}%")
        print(f"  Win Rate: {benchmark_comp.get('win_rate', 0):.1f}%")
    
    print("\n[PASS] Integrated Backtesting Workflow Complete")
    
    return result, analysis


def main():
    """Run all Phase 5 tests"""
    print("\n" + "="*80)
    print("PHASE 5 BACKTESTING - COMPREHENSIVE TEST")
    print("="*80)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test backtest engine
    try:
        backtest_result = test_backtest_engine()
        tests_passed += 1
    except Exception as e:
        print(f"\n[FAIL] Backtest Engine: {e}")
        import traceback
        traceback.print_exc()
        tests_failed += 1
        return 1
    
    # Test performance analyzer
    try:
        analysis = test_performance_analyzer(backtest_result)
        tests_passed += 1
    except Exception as e:
        print(f"\n[FAIL] Performance Analyzer: {e}")
        import traceback
        traceback.print_exc()
        tests_failed += 1
    
    # Test integrated workflow
    try:
        test_integrated_backtesting()
        tests_passed += 1
    except Exception as e:
        print(f"\n[FAIL] Integrated Workflow: {e}")
        import traceback
        traceback.print_exc()
        tests_failed += 1
    
    # Summary
    print("\n" + "="*80)
    print("PHASE 5 TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {tests_passed + tests_failed}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    
    if tests_failed == 0:
        print("\n[SUCCESS] All Phase 5 tests passed!")
        print("Ready to proceed to Phase 6: Dashboard & Visualization")
    else:
        print(f"\n[WARNING] {tests_failed} test(s) failed")
    
    print("="*80 + "\n")
    
    return 0 if tests_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
