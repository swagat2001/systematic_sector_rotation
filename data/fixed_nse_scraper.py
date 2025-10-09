"""
Enhanced NSE Data Scraper with Proper CSV Export
Fixes the column structure issue and exports data in the required format
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
import time
import logging
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NSEDataScraperFixed:
    """
    Fixed NSE data scraper that downloads and saves data with proper CSV structure
    Column order: Date, Adj Close, Close, High, Low, Open, Volume
    """
    
    def __init__(self, 
                 output_dir: str = "nse_data",
                 years: int = 4):
        """
        Initialize the scraper
        
        Args:
            output_dir: Directory to save CSV files
            years: Number of years of historical data to fetch
        """
        self.output_dir = output_dir
        self.years = years
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=years * 365)
        
        # Create output directory structure
        self._setup_directories()
        
        # Define sector mappings
        self.sectors = self._get_sector_mappings()
        
        logger.info(f"Initialized scraper: {self.start_date.date()} to {self.end_date.date()}")
    
    def _setup_directories(self):
        """Create directory structure for organized data storage"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "stocks"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "sectors"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "combined"), exist_ok=True)
    
    def _get_sector_mappings(self) -> Dict[str, List[str]]:
        """Get NSE sector to stock mappings"""
        return {
            'NIFTY_IT': [
                'TCS', 'INFY', 'HCLTECH', 'WIPRO', 'TECHM', 'LTIM',
                'PERSISTENT', 'COFORGE', 'MPHASIS', 'LTTS'
            ],
            'NIFTY_BANK': [
                'HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'SBIN', 'AXISBANK',
                'INDUSINDBK', 'BANDHANBNK', 'FEDERALBNK', 'IDFCFIRSTB', 'PNB'
            ],
            'NIFTY_AUTO': [
                'MARUTI', 'TATAMOTORS', 'M&M', 'BAJAJ-AUTO', 'HEROMOTOCO',
                'EICHERMOT', 'TVSMOTOR', 'ASHOKLEY', 'BALKRISIND'
            ],
            'NIFTY_PHARMA': [
                'SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'AUROPHARMA',
                'LUPIN', 'TORNTPHARM', 'ALKEM', 'BIOCON', 'GLAND'
            ],
            'NIFTY_FMCG': [
                'HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR',
                'MARICO', 'TATACONSUM', 'GODREJCP', 'COLPAL', 'EMAMILTD'
            ],
            'NIFTY_METAL': [
                'TATASTEEL', 'HINDALCO', 'JSWSTEEL', 'COALINDIA', 'VEDL',
                'JINDALSTEL', 'SAIL', 'NMDC', 'NATIONALUM'
            ],
            'NIFTY_REALTY': [
                'DLF', 'GODREJPROP', 'OBEROIRLTY', 'PHOENIXLTD', 'PRESTIGE',
                'BRIGADE', 'SOBHA', 'MAHLIFE', 'IBREALEST'
            ],
            'NIFTY_ENERGY': [
                'RELIANCE', 'ONGC', 'POWERGRID', 'NTPC', 'COALINDIA',
                'IOC', 'BPCL', 'GAIL', 'ADANIGREEN', 'ADANITRANS'
            ]
        }
    
    def _format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Format DataFrame to match required column structure
        Required: Date, Adj Close, Close, High, Low, Open, Volume
        
        Args:
            df: Raw DataFrame from yfinance
            
        Returns:
            Formatted DataFrame with proper column order
        """
        if df.empty:
            return pd.DataFrame()
        
        # Ensure we have all required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        
        # Check if columns exist (handle different yfinance formats)
        for col in required_cols:
            if col not in df.columns:
                # Try lowercase
                lowercase_col = col.lower().replace(' ', '_')
                if lowercase_col in df.columns:
                    df[col] = df[lowercase_col]
                else:
                    logger.warning(f"Column {col} not found, using Close as fallback")
                    if col == 'Adj Close':
                        df[col] = df.get('Close', 0)
                    else:
                        df[col] = 0
        
        # Reset index to get Date as a column
        df_formatted = df.reset_index()
        
        # Rename index column to Date
        if 'index' in df_formatted.columns:
            df_formatted.rename(columns={'index': 'Date'}, inplace=True)
        elif 'Datetime' in df_formatted.columns:
            df_formatted.rename(columns={'Datetime': 'Date'}, inplace=True)
        
        # Format Date column
        df_formatted['Date'] = pd.to_datetime(df_formatted['Date']).dt.strftime('%Y-%m-%d')
        
        # Select and reorder columns as required
        final_columns = ['Date', 'Adj Close', 'Close', 'High', 'Low', 'Open', 'Volume']
        
        # Create final dataframe with proper column order
        df_final = pd.DataFrame()
        for col in final_columns:
            if col in df_formatted.columns:
                df_final[col] = df_formatted[col]
            else:
                logger.warning(f"Column {col} missing, adding with default values")
                df_final[col] = 0
        
        # Convert numeric columns to proper types
        numeric_cols = ['Adj Close', 'Close', 'High', 'Low', 'Open', 'Volume']
        for col in numeric_cols:
            df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)
        
        # Round price columns to 2 decimal places
        price_cols = ['Adj Close', 'Close', 'High', 'Low', 'Open']
        for col in price_cols:
            df_final[col] = df_final[col].round(2)
        
        # Volume should be integer
        df_final['Volume'] = df_final['Volume'].astype(int)
        
        return df_final
    
    def download_stock(self, symbol: str, sector: str = None) -> Optional[pd.DataFrame]:
        """
        Download data for a single stock
        
        Args:
            symbol: Stock symbol (without .NS)
            sector: Sector name (optional)
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            ticker = f"{symbol}.NS"
            logger.info(f"Downloading {symbol} ({sector})")
            
            # Download data using yfinance
            stock = yf.Ticker(ticker)
            df = stock.history(
                start=self.start_date,
                end=self.end_date,
                auto_adjust=False  # Keep both Close and Adj Close
            )
            
            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return None
            
            # Format the dataframe
            df_formatted = self._format_dataframe(df)
            
            # Save to CSV
            if not df_formatted.empty:
                filename = f"{symbol}.csv"
                filepath = os.path.join(self.output_dir, "stocks", filename)
                df_formatted.to_csv(filepath, index=False)
                logger.info(f"Saved {symbol} data to {filepath} ({len(df_formatted)} rows)")
            
            return df_formatted
            
        except Exception as e:
            logger.error(f"Error downloading {symbol}: {e}")
            return None
    
    def download_sector_stocks(self, sector_name: str, stock_list: List[str]) -> pd.DataFrame:
        """
        Download all stocks in a sector
        
        Args:
            sector_name: Name of the sector
            stock_list: List of stock symbols in the sector
            
        Returns:
            Combined DataFrame of all stocks in sector
        """
        logger.info(f"\nDownloading {sector_name} stocks ({len(stock_list)} stocks)")
        logger.info("=" * 60)
        
        sector_data = []
        success_count = 0
        
        for symbol in stock_list:
            df = self.download_stock(symbol, sector_name)
            if df is not None and not df.empty:
                df['Symbol'] = symbol
                df['Sector'] = sector_name
                sector_data.append(df)
                success_count += 1
            
            # Rate limiting
            time.sleep(0.5)
        
        logger.info(f"Successfully downloaded {success_count}/{len(stock_list)} stocks in {sector_name}")
        
        # Combine and save sector data
        if sector_data:
            combined_df = pd.concat(sector_data, ignore_index=True)
            
            # Save sector combined file
            sector_file = os.path.join(self.output_dir, "sectors", f"{sector_name}.csv")
            combined_df.to_csv(sector_file, index=False)
            logger.info(f"Saved combined sector data to {sector_file}")
            
            return combined_df
        
        return pd.DataFrame()
    
    def download_all_sectors(self):
        """Download data for all sectors"""
        logger.info("\n" + "=" * 80)
        logger.info("STARTING NSE DATA DOWNLOAD")
        logger.info("=" * 80)
        
        all_data = []
        
        for sector_name, stock_list in self.sectors.items():
            sector_df = self.download_sector_stocks(sector_name, stock_list)
            if not sector_df.empty:
                all_data.append(sector_df)
        
        # Save master combined file
        if all_data:
            master_df = pd.concat(all_data, ignore_index=True)
            master_file = os.path.join(self.output_dir, "combined", "all_stocks.csv")
            master_df.to_csv(master_file, index=False)
            logger.info(f"\nSaved master file with all stocks to {master_file}")
            
            # Create summary
            self._create_summary(master_df)
    
    def _create_summary(self, df: pd.DataFrame):
        """Create a summary of downloaded data"""
        summary = {
            'Total Records': len(df),
            'Unique Stocks': df['Symbol'].nunique() if 'Symbol' in df.columns else 0,
            'Unique Sectors': df['Sector'].nunique() if 'Sector' in df.columns else 0,
            'Date Range': f"{df['Date'].min()} to {df['Date'].max()}",
            'Data Columns': ', '.join(df.columns.tolist())
        }
        
        # Save summary
        summary_file = os.path.join(self.output_dir, "download_summary.txt")
        with open(summary_file, 'w') as f:
            f.write("NSE Data Download Summary\n")
            f.write("=" * 50 + "\n\n")
            for key, value in summary.items():
                f.write(f"{key}: {value}\n")
        
        logger.info("\n" + "=" * 80)
        logger.info("DOWNLOAD SUMMARY")
        logger.info("=" * 80)
        for key, value in summary.items():
            logger.info(f"{key}: {value}")
    
    def verify_csv_structure(self, csv_path: str):
        """
        Verify that a CSV has the correct structure
        
        Args:
            csv_path: Path to CSV file to verify
        """
        try:
            df = pd.read_csv(csv_path)
            expected_columns = ['Date', 'Adj Close', 'Close', 'High', 'Low', 'Open', 'Volume']
            
            logger.info(f"\nVerifying {csv_path}")
            logger.info(f"Columns found: {df.columns.tolist()}")
            logger.info(f"Expected columns: {expected_columns}")
            
            if list(df.columns) == expected_columns:
                logger.info("✅ CSV structure is correct!")
            else:
                logger.warning("❌ CSV structure mismatch!")
                missing = set(expected_columns) - set(df.columns)
                extra = set(df.columns) - set(expected_columns)
                if missing:
                    logger.warning(f"Missing columns: {missing}")
                if extra:
                    logger.warning(f"Extra columns: {extra}")
            
            # Show sample data
            logger.info("\nSample data (first 3 rows):")
            print(df.head(3).to_string())
            
            return df
            
        except Exception as e:
            logger.error(f"Error verifying CSV: {e}")
            return None


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fixed NSE Data Scraper')
    parser.add_argument('--output', default='nse_data', help='Output directory')
    parser.add_argument('--years', type=int, default=4, help='Years of historical data')
    parser.add_argument('--verify', type=str, help='Verify CSV file structure')
    parser.add_argument('--symbol', type=str, help='Download single symbol')
    
    args = parser.parse_args()
    
    scraper = NSEDataScraperFixed(
        output_dir=args.output,
        years=args.years
    )
    
    if args.verify:
        # Verify mode
        scraper.verify_csv_structure(args.verify)
    elif args.symbol:
        # Single stock download
        df = scraper.download_stock(args.symbol)
        if df is not None:
            logger.info(f"Successfully downloaded {args.symbol}")
            scraper.verify_csv_structure(
                os.path.join(args.output, "stocks", f"{args.symbol}.csv")
            )
    else:
        # Full download
        scraper.download_all_sectors()
        
        # Verify a sample file
        sample_file = os.path.join(args.output, "stocks", "TCS.csv")
        if os.path.exists(sample_file):
            scraper.verify_csv_structure(sample_file)


if __name__ == "__main__":
    main()
