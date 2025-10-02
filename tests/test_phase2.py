"""
Test Script for Phase 2 Scoring Models

This script properly tests all scoring models with correct imports
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from datetime import datetime

from models.fundamental_scorer import FundamentalScorer
from models.technical_scorer import TechnicalScorer
from models.statistical_scorer import StatisticalScorer
from models.composite_scorer import CompositeScorer


def test_fundamental_scorer():
    """Test fundamental scorer"""
    print("\n" + "="*60)
    print("TESTING FUNDAMENTAL SCORER")
    print("="*60)
    
    scorer = FundamentalScorer()
    
    # Sample fundamental data
    test_fundamentals = {
        'roe': 0.20,
        'gross_margin': 0.45,
        'operating_margin': 0.25,
        'current_ratio': 2.0,
        'earnings_growth': 0.18,
        'revenue_growth': 0.15,
        'pe_ratio': 22.0,
        'pb_ratio': 3.5,
        'ev_ebitda': 12.0,
        'debt_to_equity': 0.6,
        'interest_coverage': 8.0,
        'quick_ratio': 1.2
    }
    
    scores = scorer.calculate_fundamental_score(test_fundamentals)
    
    print("\nFundamental Scores:")
    for key, value in scores.items():
        print(f"  {key}: {value:.4f}")
    
    print("\n[PASS] Fundamental Scorer Test")
    return True


def test_technical_scorer():
    """Test technical scorer"""
    print("\n" + "="*60)
    print("TESTING TECHNICAL SCORER")
    print("="*60)
    
    scorer = TechnicalScorer()
    
    # Generate sample price data
    dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='B')
    prices = 100 * (1 + np.random.randn(len(dates)).cumsum() * 0.01)
    
    test_data = pd.DataFrame({
        'Open': prices,
        'High': prices * 1.02,
        'Low': prices * 0.98,
        'Close': prices,
        'Volume': np.random.uniform(1000000, 5000000, len(dates))
    }, index=dates)
    
    scores = scorer.calculate_technical_score(test_data)
    
    print("\nTechnical Scores:")
    for key, value in scores.items():
        print(f"  {key}: {value:.4f}")
    
    print("\n[PASS] Technical Scorer Test")
    return True


def test_statistical_scorer():
    """Test statistical scorer"""
    print("\n" + "="*60)
    print("TESTING STATISTICAL SCORER")
    print("="*60)
    
    scorer = StatisticalScorer(risk_free_rate=0.06)
    
    # Generate sample price data
    dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='B')
    
    # Stock with moderate volatility
    returns = np.random.randn(len(dates)) * 0.015 + 0.0005
    prices = 100 * (1 + pd.Series(returns)).cumprod()
    
    test_data = pd.DataFrame({
        'Open': prices.values,
        'High': prices.values * 1.01,
        'Low': prices.values * 0.99,
        'Close': prices.values,
        'Volume': np.random.uniform(1000000, 5000000, len(dates))
    }, index=dates)
    
    # Benchmark data
    benchmark_returns = np.random.randn(len(dates)) * 0.01 + 0.0003
    benchmark_prices = 100 * (1 + pd.Series(benchmark_returns)).cumprod()
    
    benchmark_data = pd.DataFrame({
        'Open': benchmark_prices.values,
        'High': benchmark_prices.values * 1.005,
        'Low': benchmark_prices.values * 0.995,
        'Close': benchmark_prices.values,
        'Volume': np.random.uniform(10000000, 50000000, len(dates))
    }, index=dates)
    
    scores = scorer.calculate_statistical_score(test_data, benchmark_data)
    
    print("\nStatistical Scores:")
    for key, value in scores.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
    
    print("\n[PASS] Statistical Scorer Test")
    return True


def test_composite_scorer():
    """Test composite scorer"""
    print("\n" + "="*60)
    print("TESTING COMPOSITE SCORER")
    print("="*60)
    
    scorer = CompositeScorer()
    
    # Sample data for testing
    test_fundamentals = {
        'INFY': {
            'roe': 0.25, 'gross_margin': 0.40, 'operating_margin': 0.25,
            'current_ratio': 2.5, 'earnings_growth': 0.15, 'revenue_growth': 0.12,
            'pe_ratio': 22, 'pb_ratio': 3.5, 'debt_to_equity': 0.1,
            'interest_coverage': 15.0
        },
        'TCS': {
            'roe': 0.30, 'gross_margin': 0.45, 'operating_margin': 0.28,
            'current_ratio': 2.8, 'earnings_growth': 0.18, 'revenue_growth': 0.14,
            'pe_ratio': 28, 'pb_ratio': 8.0, 'debt_to_equity': 0.05,
            'interest_coverage': 20.0
        }
    }
    
    # Generate sample price data
    dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='B')
    
    test_prices = {}
    for symbol in ['INFY', 'TCS']:
        prices = 100 * (1 + np.random.randn(len(dates)).cumsum() * 0.01)
        test_prices[symbol] = pd.DataFrame({
            'Open': prices,
            'High': prices * 1.02,
            'Low': prices * 0.98,
            'Close': prices,
            'Volume': np.random.uniform(1000000, 5000000, len(dates))
        }, index=dates)
    
    # Calculate scores
    scores_df = scorer.batch_calculate_scores(
        test_fundamentals,
        test_prices
    )
    
    # Generate report
    report = scorer.generate_score_report(scores_df)
    print(report)
    
    print("[PASS] Composite Scorer Test")
    return True


def main():
    """Run all Phase 2 tests"""
    print("\n" + "="*60)
    print("PHASE 2 SCORING MODELS - COMPREHENSIVE TEST")
    print("="*60)
    
    tests_passed = 0
    tests_failed = 0
    
    tests = [
        ("Fundamental Scorer", test_fundamental_scorer),
        ("Technical Scorer", test_technical_scorer),
        ("Statistical Scorer", test_statistical_scorer),
        ("Composite Scorer", test_composite_scorer)
    ]
    
    for test_name, test_func in tests:
        try:
            if test_func():
                tests_passed += 1
        except Exception as e:
            print(f"\n[FAIL] {test_name}: {e}")
            tests_failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("PHASE 2 TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {tests_passed + tests_failed}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    
    if tests_failed == 0:
        print("\n[SUCCESS] All Phase 2 tests passed!")
        print("Ready to proceed to Phase 3")
    else:
        print(f"\n[WARNING] {tests_failed} test(s) failed")
    
    print("="*60 + "\n")
    
    return 0 if tests_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
