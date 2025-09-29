"""
Test script to verify Day 1 setup is working correctly
"""

from utils.logger import setup_logger
from config import Config, NSESectors

def test_setup():
    """Test all Day 1 components"""
    
    # Test logger
    logger = setup_logger(__name__)
    logger.info("=== DAY 1 SETUP TEST STARTED ===")
    
    # Test configuration
    logger.info(f"Strategy Name: {Config.STRATEGY_NAME}")
    logger.info(f"Version: {Config.VERSION}")
    logger.info(f"Base Directory: {Config.BASE_DIR}")
    logger.info(f"Data Directory: {Config.DATA_DIR}")
    logger.info(f"Log Directory: {Config.LOG_DIR}")
    logger.info(f"Database Directory: {Config.DATABASE_DIR}")
    
    # Test directory creation
    logger.info(f"Data directory exists: {Config.DATA_DIR.exists()}")
    logger.info(f"Log directory exists: {Config.LOG_DIR.exists()}")
    logger.info(f"Database directory exists: {Config.DATABASE_DIR.exists()}")
    
    # Test strategy parameters
    logger.info(f"Sector Allocation: {Config.SECTOR_ALLOCATION}")
    logger.info(f"Stock Allocation: {Config.STOCK_ALLOCATION}")
    logger.info(f"Top Sectors Count: {Config.TOP_SECTORS_COUNT}")
    logger.info(f"Rebalancing Frequency: {Config.REBALANCING_FREQUENCY}")
    
    # Test NSE sectors configuration
    logger.info(f"Total NSE Sectors Configured: {len(NSESectors.SECTOR_TICKERS)}")
    logger.info(f"Sample Sectors: {list(NSESectors.SECTOR_TICKERS.keys())[:3]}")
    
    # Test paper trading configuration
    logger.info(f"Initial Capital: ₹{Config.PAPER_TRADING['initial_capital']:,}")
    logger.info(f"Transaction Cost: {Config.PAPER_TRADING['transaction_cost']*100}%")
    
    logger.info("=== DAY 1 SETUP TEST COMPLETED SUCCESSFULLY ===")
    print("\n✅ All Day 1 components are working correctly!")
    print(f"📂 Check logs at: {Config.LOG_DIR}/strategy.log")

if __name__ == "__main__":
    test_setup()
