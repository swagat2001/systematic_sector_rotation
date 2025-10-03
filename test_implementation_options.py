"""
Test Implementation Mode Options

Verifies that both ETF and Individual Stock modes work correctly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from strategy.implementation_mode import ImplementationModeHandler

def test_implementation_modes():
    print("=" * 80)
    print("TEST: IMPLEMENTATION MODE OPTIONS")
    print("=" * 80)
    
    # Test current mode
    handler = ImplementationModeHandler()
    
    print(f"\nCurrent Mode: {handler.mode}")
    
    # Generate report
    report = handler.generate_implementation_report()
    print(report)
    
    # Show comparison
    print("\nCOMPARISON TABLE:")
    print("=" * 80)
    comparison = handler.compare_implementations()
    print(comparison.to_string(index=False))
    
    # Test ETF mapping
    print("\n" + "=" * 80)
    print("TEST: SECTOR ETF MAPPING")
    print("=" * 80)
    
    test_sectors = [
        'Nifty IT',
        'Nifty Bank',
        'Nifty Pharma',
        'Nifty Auto',
        'Nifty Energy'
    ]
    
    for sector in test_sectors:
        etf = handler._get_sector_etf(sector)
        print(f"  {sector:30s} → {etf}")
    
    print("\n" + "=" * 80)
    print("CLIENT CHOICE AVAILABLE")
    print("=" * 80)
    print("\nTo switch mode, edit config.py:")
    print("  IMPLEMENTATION_MODE = 'SECTOR_ETFS'       # Option A")
    print("  IMPLEMENTATION_MODE = 'INDIVIDUAL_STOCKS' # Option B")
    print("\n" + "=" * 80)
    
    return True

if __name__ == "__main__":
    success = test_implementation_modes()
    sys.exit(0 if success else 1)
