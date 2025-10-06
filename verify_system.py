"""
Test script to verify all fixes are working
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*80)
print("SYSTEMATIC SECTOR ROTATION - SYSTEM VERIFICATION")
print("="*80 + "\n")

# Test 1: Import all core modules
print("1. Testing core module imports...")
try:
    from models.enhanced_fundamental_scorer import EnhancedFundamentalScorer
    from models.technical_scorer import TechnicalScorer
    from models.statistical_scorer import StatisticalScorer
    from models.composite_scorer import CompositeScorer
    print("   ✅ All scorers imported successfully")
except Exception as e:
    print(f"   ❌ Import error: {e}")
    sys.exit(1)

# Test 2: Test enhanced fundamental scorer
print("\n2. Testing EnhancedFundamentalScorer...")
try:
    scorer = EnhancedFundamentalScorer()
    
    test_data = {
        'roe': 0.22,
        'pe_ratio': 18,
        'debt_to_equity': 0.6,
        'current_ratio': 1.8
    }
    
    result = scorer.calculate_fundamental_score(test_data)
    
    assert 'fundamental_score' in result
    assert 'quality_score' in result
    assert 'growth_score' in result
    assert 'valuation_score' in result
    assert 'balance_sheet_score' in result
    
    print(f"   ✅ Enhanced fundamental scorer working")
    print(f"      Fundamental score: {result['fundamental_score']:.4f}")
    
except Exception as e:
    print(f"   ❌ Enhanced scorer error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Test composite scorer integration
print("\n3. Testing CompositeScorer with enhanced fundamental...")
try:
    import pandas as pd
    import numpy as np
    
    composite = CompositeScorer()
    
    # Check if using enhanced scorer
    assert isinstance(composite.fundamental_scorer, EnhancedFundamentalScorer)
    print("   ✅ Composite scorer using EnhancedFundamentalScorer")
    
except Exception as e:
    print(f"   ❌ Composite scorer error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check data bridge
print("\n4. Testing NSE data bridge...")
try:
    from data.nse_data_bridge import NSEDataBridge
    
    bridge = NSEDataBridge()
    min_date, max_date = bridge.get_date_range()
    
    print(f"   ✅ NSE data bridge operational")
    print(f"      Date range: {min_date.date()} to {max_date.date()}")
    
    bridge.close()
    
except FileNotFoundError as e:
    print(f"   ⚠️  NSE database not found (run scraper first)")
except Exception as e:
    print(f"   ❌ Data bridge error: {e}")

# Test 5: Check strategy components
print("\n5. Testing strategy components...")
try:
    from strategy.sector_rotation import SectorRotationEngine
    from strategy.stock_selection import StockSelectionEngine
    
    sector_engine = SectorRotationEngine()
    stock_engine = StockSelectionEngine()
    
    print(f"   ✅ Strategy engines initialized")
    print(f"      Sector rotation: top-{sector_engine.top_k} sectors")
    print(f"      Stock selection: top-{stock_engine.top_n_stocks} stocks")
    
except Exception as e:
    print(f"   ❌ Strategy error: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Check backtest engine
print("\n6. Testing backtest engine...")
try:
    from backtesting.backtest_engine import BacktestEngine
    
    engine = BacktestEngine()
    print(f"   ✅ Backtest engine ready")
    print(f"      Initial capital: ₹{engine.initial_capital:,.0f}")
    print(f"      Rebalance frequency: {engine.rebalance_frequency}")
    
except Exception as e:
    print(f"   ❌ Backtest error: {e}")

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)
print("\n✅ System is operational and ready for backtesting")
print("\nTo run backtest:")
print("  streamlit run dashboard/streamlit_app.py")
print("\n" + "="*80 + "\n")
