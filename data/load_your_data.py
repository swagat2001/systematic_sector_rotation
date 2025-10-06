"""
Custom Data Loader for Your Downloaded Data

Since you have 1800+ stocks with 4 years of OHLC data already downloaded,
this script will help you load it into the database.

INSTRUCTIONS:
1. Place your data files in: data/your_data/
2. Expected format:
   - CSV files with columns: Date, Open, High, Low, Close, Volume
   - OR separate folders per sector/stock
3. Run: python data/load_your_data.py

This bypasses yfinance and NSE website issues.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime
from config import Config, NSESectors
from data.data_storage import DataStorage
from utils.logger import setup_logger

logger = setup_logger(__name__)


class CustomDataLoader:
    """Load your pre-downloaded data into the database"""
    
    def __init__(self):
        self.storage = DataStorage()
        self.data_dir = Config.DATA_DIR / "your_data"
        self.data_dir.mkdir(exist_ok=True)
        
        logger.info("CustomDataLoader initialized")
        logger.info(f"Looking for data in: {self.data_dir}")
    
    def load_from_csv_folder(self, folder_path: Path):
        """
        Load data from a folder structure like:
        your_data/
          ├── sectors/
          │   ├── NIFTY_AUTO.csv
          │   ├── NIFTY_BANK.csv
          │   └── ...
          ├── stocks/
          │   ├── INFY.csv
          │   ├── TCS.csv
          │   └── ...
        """
        logger.info("Loading data from CSV folder structure...")
        
        # Initialize sectors
        self.storage.bulk_load_sectors(NSESectors.SECTOR_TICKERS)
        
        stats = {
            'sectors_loaded': 0,
            'stocks_loaded': 0,
            'price_records': 0
        }
        
        # Load sector data
        sector_folder = folder_path / "sectors"
        if sector_folder.exists():
            for csv_file in sector_folder.glob("*.csv"):
                try:
                    sector_name = csv_file.stem.replace('_', ' ').title()
                    df = pd.read_csv(csv_file, parse_dates=['Date'], index_col='Date')
                    
                    # Save to database
                    self.storage.save_sector_prices(sector_name, df)
                    stats['sectors_loaded'] += 1
                    stats['price_records'] += len(df)
                    
                    logger.info(f"Loaded {sector_name}: {len(df)} records")
                except Exception as e:
                    logger.error(f"Error loading {csv_file}: {e}")
        
        # Load stock data
        stock_folder = folder_path / "stocks"
        if stock_folder.exists():
            for csv_file in stock_folder.glob("*.csv"):
                try:
                    symbol = csv_file.stem
                    df = pd.read_csv(csv_file, parse_dates=['Date'], index_col='Date')
                    
                    # Add stock if not exists
                    stock = self.storage.get_stock_by_symbol(symbol)
                    if not stock:
                        self.storage.add_stock(symbol)
                    
                    # Save prices
                    self.storage.save_stock_prices(symbol, df)
                    stats['stocks_loaded'] += 1
                    stats['price_records'] += len(df)
                    
                    if stats['stocks_loaded'] % 100 == 0:
                        logger.info(f"Loaded {stats['stocks_loaded']} stocks...")
                        
                except Exception as e:
                    logger.error(f"Error loading {csv_file}: {e}")
        
        logger.info(f"Loading complete:")
        logger.info(f"  Sectors: {stats['sectors_loaded']}")
        logger.info(f"  Stocks: {stats['stocks_loaded']}")
        logger.info(f"  Total price records: {stats['price_records']:,}")
        
        return stats
    
    def load_from_single_file(self, file_path: Path):
        """
        Load data from a single CSV/Excel file with format:
        Symbol, Date, Open, High, Low, Close, Volume, Sector (optional)
        """
        logger.info(f"Loading data from single file: {file_path}")
        
        # Read file
        if file_path.suffix == '.csv':
            df = pd.read_csv(file_path)
        elif file_path.suffix in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            logger.error(f"Unsupported file type: {file_path.suffix}")
            return
        
        # Group by symbol
        symbols = df['Symbol'].unique()
        logger.info(f"Found {len(symbols)} unique symbols")
        
        self.storage.bulk_load_sectors(NSESectors.SECTOR_TICKERS)
        
        for i, symbol in enumerate(symbols):
            try:
                stock_df = df[df['Symbol'] == symbol].copy()
                stock_df['Date'] = pd.to_datetime(stock_df['Date'])
                stock_df.set_index('Date', inplace=True)
                
                # Add stock
                stock = self.storage.get_stock_by_symbol(symbol)
                if not stock:
                    sector = stock_df['Sector'].iloc[0] if 'Sector' in stock_df.columns else None
                    self.storage.add_stock(symbol, sector_name=sector)
                
                # Save prices
                price_df = stock_df[['Open', 'High', 'Low', 'Close', 'Volume']]
                self.storage.save_stock_prices(symbol, price_df)
                
                if (i + 1) % 100 == 0:
                    logger.info(f"Loaded {i + 1}/{len(symbols)} stocks...")
                    
            except Exception as e:
                logger.error(f"Error loading {symbol}: {e}")
        
        logger.info(f"Loading complete: {len(symbols)} stocks")
    
    def show_instructions(self):
        """Show instructions for data format"""
        instructions = """
========================================================================
DATA LOADING INSTRUCTIONS
========================================================================

You have 1800+ stocks downloaded. To load them into the database:

OPTION 1: Folder Structure
---------------------------
Organize your data like this:

  data/your_data/
    ├── sectors/
    │   ├── NIFTY_AUTO.csv
    │   ├── NIFTY_BANK.csv
    │   └── ... (17 sector files)
    └── stocks/
        ├── INFY.csv
        ├── TCS.csv
        └── ... (1800+ stock files)

Each CSV should have columns: Date, Open, High, Low, Close, Volume

OPTION 2: Single File
---------------------
Create one CSV/Excel with all data:
  Symbol, Date, Open, High, Low, Close, Volume, Sector (optional)

OPTION 3: Custom Format
-----------------------
If your data is in a different format, modify this script's
load_from_custom() method to match your format.

TO RUN:
-------
1. Organize your data as above
2. Run: python data/load_your_data.py --folder data/your_data
   OR:   python data/load_your_data.py --file data/your_data/all_data.csv

========================================================================
"""
        print(instructions)
        logger.info("Instructions displayed")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Load your downloaded data')
    parser.add_argument('--folder', type=str, help='Folder containing sector/stock CSVs')
    parser.add_argument('--file', type=str, help='Single file with all data')
    parser.add_argument('--instructions', action='store_true', help='Show format instructions')
    
    args = parser.parse_args()
    
    loader = CustomDataLoader()
    
    if args.instructions or (not args.folder and not args.file):
        loader.show_instructions()
        return
    
    if args.folder:
        folder_path = Path(args.folder)
        if not folder_path.exists():
            logger.error(f"Folder not found: {folder_path}")
            return
        
        stats = loader.load_from_csv_folder(folder_path)
        
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return
        
        loader.load_from_single_file(file_path)
    
    loader.storage.close()
    logger.info("Data loading complete!")


if __name__ == "__main__":
    main()
