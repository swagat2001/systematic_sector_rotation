"""
Phase 1 Completion Test Script

Tests all Phase 1 components to ensure they work correctly:
1. Configuration loading
2. Logger functionality
3. Helper functions
4. Data collector
5. Data validator
6. Data storage
7. Full pipeline integration

Run this to verify Phase 1 is complete before moving to Phase 2
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config, NSESectors
from utils.logger import setup_logger
from utils.helpers import *
from data.data_collector import DataCollector
from data.data_validator import DataValidator
from data.data_storage import DataStorage

logger = setup_logger(__name__)


class Phase1Tester:
    """Comprehensive testing for Phase 1 components"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        try:
            logger.info(f"Running: {test_name}")
            test_func()
            self.tests_passed += 1
            self.test_results.append((test_name, "PASS", None))
            logger.info(f"[PASS] {test_name}")
        except Exception as e:
            self.tests_failed += 1
            self.test_results.append((test_name, "FAIL", str(e)))
            logger.error(f"[FAIL] {test_name}: {e}")
    
    def test_config(self):
        """Test configuration loading"""
        assert Config.STRATEGY_NAME == "Systematic Sector Rotation"
        assert Config.SECTOR_ALLOCATION == 0.60
        assert Config.STOCK_ALLOCATION == 0.40
        assert Config.TOP_SECTORS_COUNT == 3
        assert len(NSESectors.SECTOR_TICKERS) > 0
        logger.info(f"  Config loaded: {len(NSESectors.SECTOR_TICKERS)} sectors configured")
    
    def test_logger(self):
        """Test logger functionality"""
        test_logger = setup_logger("test_logger")
        test_logger.info("Test info message")
        test_logger.warning("Test warning message")
        test_logger.error("Test error message")
        assert test_logger is not None
        logger.info("  Logger working correctly")
    
    def test_helpers(self):
        """Test helper functions"""
        # Test returns calculation
        prices = pd.Series([100, 105, 103, 108, 110])
        returns = calculate_returns(prices)
        assert len(returns) == 4
        
        # Test Sharpe ratio
        returns = pd.Series(np.random.randn(252) * 0.01)
        sharpe = calculate_sharpe_ratio(returns)
        assert isinstance(sharpe, float)
        
        # Test volatility
        vol = calculate_volatility(returns)
        assert vol > 0
        
        # Test z-score normalization
        series = pd.Series([1, 2, 3, 4, 5])
        z_scores = z_score_normalize(series)
        assert abs(z_scores.mean()) < 0.01  # Should be close to 0
        
        # Test momentum calculation
        prices = pd.Series(range(100, 200))
        momentum = calculate_momentum(prices, period=50, exclude_recent=10)
        assert isinstance(momentum, float)
        
        logger.info("  All helper functions working")
    
    def test_data_collector(self):
        """Test data collector"""
        collector = DataCollector()
        
        # Just test initialization, not actual data fetch
        assert hasattr(collector, 'sector_data')
        assert hasattr(collector, 'stock_data')
        assert hasattr(collector, 'fundamental_data')
        
        logger.info("  Data collector initialized correctly")
    
    def test_data_validator(self):
        """Test data validator"""
        validator = DataValidator()
        
        # Create sample OHLC data
        dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='B')
        sample_data = pd.DataFrame({
            'Open': np.random.uniform(100, 110, len(dates)),
            'High': np.random.uniform(110, 120, len(dates)),
            'Low': np.random.uniform(90, 100, len(dates)),
            'Close': np.random.uniform(100, 110, len(dates)),
            'Volume': np.random.uniform(1000000, 10000000, len(dates))
        }, index=dates)
        
        # Validate
        results = validator.validate_ohlc_data(sample_data, 'TEST')
        assert results['is_valid'] == True
        assert 'metrics' in results
        
        # Test outlier detection
        outliers = validator.detect_outliers(sample_data, column='Close')
        assert isinstance(outliers, pd.Series)
        
        # Test fundamental validation
        fundamentals = {
            'roe': 0.15,
            'pe_ratio': 25.0,
            'debt_to_equity': 0.5,
            'market_cap': 1000000000
        }
        fund_results = validator.validate_fundamental_data(fundamentals, 'TEST')
        assert 'is_valid' in fund_results
        
        logger.info("  Data validator working correctly")
    
    def test_data_storage(self):
        """Test data storage"""
        # Use a temporary database
        test_db = Config.DATABASE_DIR / "test_strategy_temp.db"
        
        # Delete if exists
        if test_db.exists():
            test_db.unlink()
        
        storage = DataStorage(db_path=test_db)
        
        try:
            # Test sector operations
            sector_id = storage.add_sector("Test Sector", "TEST", "Test Description")
            assert sector_id > 0
            
            sector = storage.get_sector_by_name("Test Sector")
            assert sector is not None
            assert sector.ticker == "TEST"
            
            # Test stock operations
            stock_id = storage.add_stock("TESTSTOCK", "Test Stock Ltd", "Test Sector")
            assert stock_id > 0
            
            stock = storage.get_stock_by_symbol("TESTSTOCK")
            assert stock is not None
            
            # Test price storage
            dates = pd.date_range(start='2024-01-01', periods=10, freq='B')
            test_prices = pd.DataFrame({
                'Open': range(100, 110),
                'High': range(105, 115),
                'Low': range(95, 105),
                'Close': range(100, 110),
                'Volume': [1000000] * 10
            }, index=dates)
            
            count = storage.save_stock_prices("TESTSTOCK", test_prices)
            assert count == 10
            
            # Retrieve prices
            retrieved = storage.get_stock_prices("TESTSTOCK")
            assert len(retrieved) == 10
            
            # Test fundamental storage
            fundamentals = {
                'roe': 0.15,
                'pe_ratio': 25.0,
                'market_cap': 1000000000
            }
            fund_id = storage.save_fundamental_data("TESTSTOCK", fundamentals)
            assert fund_id > 0
            
            # Get summary
            summary = storage.get_data_summary()
            assert summary['sectors'] >= 1
            assert summary['stocks'] >= 1
            
            logger.info("  Data storage working correctly")
            
        finally:
            # Close connection
            storage.close()
            
            # Clean up test database
            import time
            time.sleep(0.5)  # Wait for file handle to release
            if test_db.exists():
                try:
                    test_db.unlink()
                except:
                    pass  # Ignore cleanup errors
    
    def test_pipeline_integration(self):
        """Quick test of pipeline initialization"""
        from data.data_pipeline import DataPipeline
        
        pipeline = DataPipeline()
        assert pipeline is not None
        assert pipeline.collector is not None
        assert pipeline.validator is not None
        assert pipeline.storage is not None
        
        pipeline.storage.close()
        
        logger.info("  Pipeline integration working")
    
    def generate_report(self):
        """Generate test report"""
        total_tests = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total_tests * 100) if total_tests > 0 else 0
        
        report = f"\n{'=' * 60}\n"
        report += f"PHASE 1 TESTING REPORT\n"
        report += f"{'=' * 60}\n\n"
        
        report += f"Total Tests: {total_tests}\n"
        report += f"Passed: {self.tests_passed}\n"
        report += f"Failed: {self.tests_failed}\n"
        report += f"Pass Rate: {pass_rate:.1f}%\n\n"
        
        report += f"DETAILED RESULTS:\n"
        
        for test_name, status, error in self.test_results:
            symbol = "[PASS]" if status == "PASS" else "[FAIL]"
            report += f"\n{symbol} {test_name}: {status}"
            if error:
                report += f"\n  Error: {error}"
        
        report += f"\n\n{'=' * 60}\n"
        
        if self.tests_failed == 0:
            report += "PHASE 1 COMPLETE - ALL TESTS PASSED!\n"
            report += "Ready to proceed to Phase 2 (Scoring Models)\n"
        else:
            report += "PHASE 1 INCOMPLETE - SOME TESTS FAILED\n"
            report += "Please fix errors before proceeding to Phase 2\n"
        
        report += f"{'=' * 60}\n"
        
        return report


def main():
    """Main test execution"""
    print("\n" + "=" * 60)
    print("PHASE 1 COMPLETION TESTING")
    print("=" * 60 + "\n")
    
    tester = Phase1Tester()
    
    # Run all tests
    tester.run_test("Configuration Loading", tester.test_config)
    tester.run_test("Logger Functionality", tester.test_logger)
    tester.run_test("Helper Functions", tester.test_helpers)
    tester.run_test("Data Collector", tester.test_data_collector)
    tester.run_test("Data Validator", tester.test_data_validator)
    tester.run_test("Data Storage", tester.test_data_storage)
    tester.run_test("Pipeline Integration", tester.test_pipeline_integration)
    
    # Generate and print report
    report = tester.generate_report()
    print(report)
    logger.info(report)
    
    # Save report with UTF-8 encoding
    report_path = Config.LOG_DIR / f"phase1_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_path}")
    
    # Return exit code
    return 0 if tester.tests_failed == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
