"""
Data Pipeline Integration Script

This script integrates all Phase 1 components:
- DataCollector: Fetches data from sources
- DataValidator: Validates data quality
- DataStorage: Persists data to database

Usage:
    python data_pipeline.py [--full-refresh] [--validate-only]
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.data_collector import DataCollector
from data.data_validator import DataValidator
from data.data_storage import DataStorage
from config import Config, NSESectors
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DataPipeline:
    """
    Orchestrates the complete data pipeline
    """
    
    def __init__(self, full_refresh: bool = False):
        """
        Initialize data pipeline
        
        Args:
            full_refresh: If True, ignore cache and fetch fresh data
        """
        self.collector = DataCollector()
        self.validator = DataValidator()
        self.storage = DataStorage()
        self.full_refresh = full_refresh
        
        self.stats = {
            'start_time': datetime.now(),
            'sectors_loaded': 0,
            'stocks_loaded': 0,
            'prices_saved': 0,
            'fundamentals_saved': 0,
            'validation_errors': 0,
            'validation_warnings': 0
        }
        
        logger.info("Data pipeline initialized")
    
    async def run_full_pipeline(self):
        """
        Run the complete data pipeline
        
        Steps:
        1. Initialize database schema
        2. Collect sector and stock data
        3. Validate all data
        4. Store in database
        5. Generate summary report
        """
        logger.info("=" * 60)
        logger.info("STARTING FULL DATA PIPELINE")
        logger.info("=" * 60)
        
        try:
            # Step 1: Initialize database
            await self._initialize_database()
            
            # Step 2: Collect data
            await self._collect_all_data()
            
            # Step 3: Validate data
            await self._validate_all_data()
            
            # Step 4: Store data
            await self._store_all_data()
            
            # Step 5: Generate report
            self._generate_summary_report()
            
            logger.info("=" * 60)
            logger.info("DATA PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return False
        
        finally:
            self.storage.close()
    
    async def _initialize_database(self):
        """Initialize database with sectors"""
        logger.info("Step 1: Initializing database...")
        
        # Load all sectors into database
        self.storage.bulk_load_sectors(NSESectors.SECTOR_TICKERS)
        
        sectors = self.storage.get_all_sectors()
        self.stats['sectors_loaded'] = len(sectors)
        
        logger.info(f"[OK] Database initialized with {len(sectors)} sectors")
    
    async def _collect_all_data(self):
        """Collect all market data"""
        logger.info("Step 2: Collecting market data...")
        
        # Collect sector indices data
        logger.info("  -> Fetching sector indices...")
        await self.collector.fetch_sector_indices_data()
        
        # Collect sector constituents
        logger.info("  -> Fetching sector constituents...")
        await self.collector.fetch_sector_constituents()
        
        # Collect stock OHLC data
        logger.info("  -> Fetching stock OHLC data (this may take a while)...")
        await self.collector.fetch_stock_ohlc_data()
        
        # Collect fundamental data
        logger.info("  -> Fetching fundamental data...")
        await self.collector.fetch_fundamental_data()
        
        self.stats['stocks_loaded'] = len(self.collector.stock_data)
        
        logger.info(f"[OK] Data collection complete:")
        logger.info(f"  - Sectors: {len(self.collector.sector_data)}")
        logger.info(f"  - Stocks: {len(self.collector.stock_data)}")
        logger.info(f"  - Fundamentals: {len(self.collector.fundamental_data)}")
    
    async def _validate_all_data(self):
        """Validate all collected data"""
        logger.info("Step 3: Validating data quality...")
        
        # Validate sector data
        logger.info("  -> Validating sector indices...")
        sector_summary = self.validator.batch_validate(self.collector.sector_data)
        
        logger.info(f"    Sectors: {sector_summary['valid']}/{sector_summary['total']} valid")
        
        # Validate stock data
        logger.info("  -> Validating stock data...")
        stock_summary = self.validator.batch_validate(self.collector.stock_data)
        
        logger.info(f"    Stocks: {stock_summary['valid']}/{stock_summary['total']} valid")
        
        # Validate fundamentals
        logger.info("  -> Validating fundamental data...")
        fundamental_errors = 0
        fundamental_warnings = 0
        
        for symbol, fundamentals in self.collector.fundamental_data.items():
            result = self.validator.validate_fundamental_data(fundamentals, symbol)
            if not result['is_valid']:
                fundamental_errors += 1
            fundamental_warnings += len(result.get('warnings', []))
        
        logger.info(f"    Fundamentals: {len(self.collector.fundamental_data) - fundamental_errors}/{len(self.collector.fundamental_data)} valid")
        
        # Update stats
        self.stats['validation_errors'] = sector_summary['invalid'] + stock_summary['invalid'] + fundamental_errors
        self.stats['validation_warnings'] = sector_summary['warnings'] + stock_summary['warnings'] + fundamental_warnings
        
        logger.info(f"[OK] Validation complete:")
        logger.info(f"  - Errors: {self.stats['validation_errors']}")
        logger.info(f"  - Warnings: {self.stats['validation_warnings']}")
    
    async def _store_all_data(self):
        """Store all data in database"""
        logger.info("Step 4: Storing data in database...")
        
        # Store sector prices
        logger.info("  -> Storing sector prices...")
        for sector_name, df in self.collector.sector_data.items():
            if not df.empty:
                try:
                    self.storage.save_sector_prices(sector_name, df)
                    self.stats['prices_saved'] += len(df)
                except Exception as e:
                    logger.error(f"Error saving sector {sector_name}: {e}")
        
        # Store stocks and their data
        logger.info("  -> Storing stocks and prices...")
        stock_sector_mapping = self.collector.get_stock_sector_mapping()
        
        for symbol, df in self.collector.stock_data.items():
            if df.empty:
                continue
            
            try:
                # Add stock if not exists
                stock = self.storage.get_stock_by_symbol(symbol)
                if not stock:
                    sector_name = stock_sector_mapping.get(symbol)
                    fundamentals = self.collector.fundamental_data.get(symbol, {})
                    
                    self.storage.add_stock(
                        symbol=symbol,
                        sector_name=sector_name,
                        market_cap=fundamentals.get('market_cap')
                    )
                
                # Save prices
                self.storage.save_stock_prices(symbol, df)
                self.stats['prices_saved'] += len(df)
                
            except Exception as e:
                logger.error(f"Error saving stock {symbol}: {e}")
        
        # Store fundamental data
        logger.info("  -> Storing fundamental data...")
        for symbol, fundamentals in self.collector.fundamental_data.items():
            if not fundamentals:
                continue
            
            try:
                self.storage.save_fundamental_data(symbol, fundamentals)
                self.stats['fundamentals_saved'] += 1
            except Exception as e:
                logger.error(f"Error saving fundamentals for {symbol}: {e}")
        
        logger.info(f"[OK] Data storage complete:")
        logger.info(f"  - Price records: {self.stats['prices_saved']}")
        logger.info(f"  - Fundamental records: {self.stats['fundamentals_saved']}")
    
    def _generate_summary_report(self):
        """Generate summary report of pipeline execution"""
        end_time = datetime.now()
        duration = (end_time - self.stats['start_time']).total_seconds()
        
        # Get database summary
        db_summary = self.storage.get_data_summary()
        
        report = f"""
{'=' * 60}
DATA PIPELINE SUMMARY REPORT
{'=' * 60}

Execution Time: {duration:.2f} seconds ({duration/60:.2f} minutes)
Start: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
End: {end_time.strftime('%Y-%m-%d %H:%M:%S')}

DATA COLLECTION:
  [OK] Sectors loaded: {self.stats['sectors_loaded']}
  [OK] Stocks loaded: {self.stats['stocks_loaded']}
  [OK] Price records saved: {self.stats['prices_saved']:,}
  [OK] Fundamental records saved: {self.stats['fundamentals_saved']}

DATA VALIDATION:
  [!] Validation errors: {self.stats['validation_errors']}
  [!] Validation warnings: {self.stats['validation_warnings']}

DATABASE STATUS:
  * Total sectors: {db_summary.get('sectors', 0)}
  * Total stocks: {db_summary.get('stocks', 0)}
  * Stock price records: {db_summary.get('stock_price_records', 0):,}
  * Sector price records: {db_summary.get('sector_price_records', 0):,}
  * Fundamental records: {db_summary.get('fundamental_records', 0)}
  * Latest price date: {db_summary.get('latest_price_date', 'N/A')}

DATABASE LOCATION:
  {self.storage.db_path}

CACHE LOCATION:
  {self.collector.cache_dir}

{'=' * 60}
"""
        
        logger.info(report)
        
        # Save report to file with UTF-8 encoding
        report_path = Config.LOG_DIR / f"pipeline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Report saved to: {report_path}")
    
    async def validate_only(self):
        """Run validation on existing cached data without redownloading"""
        logger.info("Running validation-only mode...")
        
        # Load data from cache
        await self.collector.load_all_data()
        
        # Validate
        await self._validate_all_data()
        
        logger.info("Validation complete")
    
    async def quick_test(self):
        """Quick test with limited data"""
        logger.info("Running quick test mode...")
        
        # Test with just one sector
        test_sector = "Nifty IT"
        
        logger.info(f"Testing with sector: {test_sector}")
        
        # Fetch one sector
        sector_data = await self.collector.fetch_sector_indices_data()
        
        if test_sector in sector_data:
            logger.info(f"[OK] Successfully fetched {test_sector}")
            
            # Validate
            result = self.validator.validate_ohlc_data(sector_data[test_sector], test_sector)
            logger.info(self.validator.generate_validation_report(test_sector))
            
            # Store
            self.storage.bulk_load_sectors({test_sector: NSESectors.SECTOR_TICKERS[test_sector]})
            self.storage.save_sector_prices(test_sector, sector_data[test_sector])
            
            logger.info("[OK] Quick test passed!")
        else:
            logger.error(f"Failed to fetch {test_sector}")
        
        self.storage.close()


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Data Pipeline for Systematic Sector Rotation')
    parser.add_argument('--full-refresh', action='store_true', 
                       help='Force fresh data download, ignore cache')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate existing data, do not download')
    parser.add_argument('--quick-test', action='store_true',
                       help='Quick test with limited data')
    
    args = parser.parse_args()
    
    pipeline = DataPipeline(full_refresh=args.full_refresh)
    
    if args.quick_test:
        await pipeline.quick_test()
    elif args.validate_only:
        await pipeline.validate_only()
    else:
        success = await pipeline.run_full_pipeline()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
