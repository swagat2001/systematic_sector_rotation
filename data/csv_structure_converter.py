"""
CSV Structure Converter for NSE Data
Converts various CSV formats to the required structure:
Date, Adj Close, Close, High, Low, Open, Volume
"""

import pandas as pd
import os
from pathlib import Path
import sqlite3
from typing import Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSVStructureConverter:
    """Convert NSE data to proper CSV structure"""
    
    def __init__(self, output_dir: str = "converted_data"):
        """
        Initialize converter
        
        Args:
            output_dir: Directory to save converted CSV files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Common column mappings from different sources
        self.column_mappings = {
            # yfinance style
            'Date': ['Date', 'date', 'DATE', 'Datetime', 'TIMESTAMP'],
            'Open': ['Open', 'open', 'OPEN', 'OPEN_PRICE', 'opening'],
            'High': ['High', 'high', 'HIGH', 'HIGH_PRICE', 'highest'],
            'Low': ['Low', 'low', 'LOW', 'LOW_PRICE', 'lowest'],
            'Close': ['Close', 'close', 'CLOSE', 'CLOSE_PRICE', 'closing', 'LAST'],
            'Adj Close': ['Adj Close', 'adj close', 'ADJ_CLOSE', 'Adjusted Close', 'PREVCLOSE'],
            'Volume': ['Volume', 'volume', 'VOLUME', 'TOTTRDQTY', 'Traded Quantity', 'No. of Shares']
        }
    
    def detect_and_map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect and map columns from various formats to standard format
        
        Args:
            df: Input DataFrame with unknown column structure
            
        Returns:
            DataFrame with standardized columns
        """
        # Create a new dataframe with standardized columns
        result = pd.DataFrame()
        
        # Log original columns
        logger.info(f"Original columns: {df.columns.tolist()}")
        
        # Map each required column
        for std_col, possible_names in self.column_mappings.items():
            found = False
            for col_name in possible_names:
                if col_name in df.columns:
                    result[std_col] = df[col_name]
                    found = True
                    logger.info(f"Mapped '{col_name}' to '{std_col}'")
                    break
            
            if not found:
                if std_col == 'Adj Close' and 'Close' in result.columns:
                    # Use Close as Adj Close if not available
                    result['Adj Close'] = result['Close']
                    logger.info(f"Using Close values for Adj Close")
                elif std_col == 'Volume':
                    # Default volume to 0 if not found
                    result['Volume'] = 0
                    logger.warning(f"No volume data found, defaulting to 0")
                else:
                    logger.warning(f"Column '{std_col}' not found in source data")
        
        return result
    
    def convert_csv_file(self, input_path: str, output_path: Optional[str] = None) -> bool:
        """
        Convert a single CSV file to the required structure
        
        Args:
            input_path: Path to input CSV file
            output_path: Path to save converted file (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"\nConverting {input_path}")
            
            # Read the CSV file
            df = pd.read_csv(input_path)
            
            if df.empty:
                logger.warning("Empty dataframe")
                return False
            
            # Detect and map columns
            converted_df = self.detect_and_map_columns(df)
            
            # Ensure Date column is properly formatted
            if 'Date' in converted_df.columns:
                converted_df['Date'] = pd.to_datetime(converted_df['Date']).dt.strftime('%Y-%m-%d')
            else:
                # Try to use index as date if it's datetime
                if isinstance(df.index, pd.DatetimeIndex):
                    converted_df['Date'] = df.index.strftime('%Y-%m-%d')
                else:
                    logger.error("No date column found")
                    return False
            
            # Reorder columns to match required structure
            required_columns = ['Date', 'Adj Close', 'Close', 'High', 'Low', 'Open', 'Volume']
            
            # Add missing columns with default values
            for col in required_columns:
                if col not in converted_df.columns:
                    if col == 'Adj Close' and 'Close' in converted_df.columns:
                        converted_df['Adj Close'] = converted_df['Close']
                    else:
                        converted_df[col] = 0
            
            # Select and reorder columns
            final_df = converted_df[required_columns]
            
            # Clean numeric columns
            numeric_cols = ['Adj Close', 'Close', 'High', 'Low', 'Open', 'Volume']
            for col in numeric_cols:
                final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0)
            
            # Round price columns
            price_cols = ['Adj Close', 'Close', 'High', 'Low', 'Open']
            for col in price_cols:
                final_df[col] = final_df[col].round(2)
            
            # Volume as integer
            final_df['Volume'] = final_df['Volume'].astype(int)
            
            # Determine output path
            if output_path is None:
                filename = os.path.basename(input_path)
                output_path = os.path.join(self.output_dir, filename)
            
            # Save converted file
            final_df.to_csv(output_path, index=False)
            logger.info(f"✅ Saved converted file to {output_path}")
            logger.info(f"   Shape: {final_df.shape}, Columns: {final_df.columns.tolist()}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error converting {input_path}: {e}")
            return False
    
    def convert_from_database(self, 
                            db_path: str, 
                            symbol: str = None,
                            output_dir: str = None) -> Dict[str, Any]:
        """
        Convert data from SQLite database to CSV files
        
        Args:
            db_path: Path to SQLite database
            symbol: Specific symbol to convert (optional, converts all if None)
            output_dir: Directory to save CSV files
            
        Returns:
            Dictionary with conversion statistics
        """
        try:
            if output_dir is None:
                output_dir = self.output_dir
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Connect to database
            conn = sqlite3.connect(db_path)
            
            # Get list of symbols
            if symbol:
                symbols = [symbol]
            else:
                query = "SELECT DISTINCT symbol FROM ohlc"
                symbols_df = pd.read_sql_query(query, conn)
                symbols = symbols_df['symbol'].tolist()
            
            logger.info(f"Found {len(symbols)} symbols to convert")
            
            stats = {
                'total_symbols': len(symbols),
                'converted': 0,
                'failed': 0,
                'files_created': []
            }
            
            # Convert each symbol
            for sym in symbols:
                try:
                    # Query data for symbol
                    query = f"""
                    SELECT date, open, high, low, close, 
                           COALESCE(adj_close, close) as adj_close, 
                           volume
                    FROM ohlc
                    WHERE symbol = '{sym}'
                    ORDER BY date
                    """
                    
                    df = pd.read_sql_query(query, conn)
                    
                    if df.empty:
                        logger.warning(f"No data for {sym}")
                        stats['failed'] += 1
                        continue
                    
                    # Format the dataframe
                    df_formatted = pd.DataFrame({
                        'Date': pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d'),
                        'Adj Close': df['adj_close'].round(2),
                        'Close': df['close'].round(2),
                        'High': df['high'].round(2),
                        'Low': df['low'].round(2),
                        'Open': df['open'].round(2),
                        'Volume': df['volume'].astype(int)
                    })
                    
                    # Save to CSV
                    output_file = os.path.join(output_dir, f"{sym}.csv")
                    df_formatted.to_csv(output_file, index=False)
                    
                    logger.info(f"✅ Converted {sym} ({len(df_formatted)} rows)")
                    stats['converted'] += 1
                    stats['files_created'].append(output_file)
                    
                except Exception as e:
                    logger.error(f"Failed to convert {sym}: {e}")
                    stats['failed'] += 1
            
            conn.close()
            
            # Log summary
            logger.info("\n" + "=" * 60)
            logger.info("CONVERSION SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Total symbols: {stats['total_symbols']}")
            logger.info(f"Successfully converted: {stats['converted']}")
            logger.info(f"Failed: {stats['failed']}")
            logger.info(f"Output directory: {output_dir}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Database conversion error: {e}")
            return {'error': str(e)}
    
    def convert_directory(self, input_dir: str, pattern: str = "*.csv") -> Dict[str, Any]:
        """
        Convert all CSV files in a directory
        
        Args:
            input_dir: Directory containing CSV files
            pattern: File pattern to match (default: *.csv)
            
        Returns:
            Dictionary with conversion statistics
        """
        from pathlib import Path
        
        input_path = Path(input_dir)
        csv_files = list(input_path.glob(pattern))
        
        logger.info(f"Found {len(csv_files)} CSV files to convert")
        
        stats = {
            'total_files': len(csv_files),
            'converted': 0,
            'failed': 0,
            'converted_files': []
        }
        
        for csv_file in csv_files:
            if self.convert_csv_file(str(csv_file)):
                stats['converted'] += 1
                stats['converted_files'].append(str(csv_file))
            else:
                stats['failed'] += 1
        
        # Log summary
        logger.info("\n" + "=" * 60)
        logger.info("BATCH CONVERSION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total files: {stats['total_files']}")
        logger.info(f"Successfully converted: {stats['converted']}")
        logger.info(f"Failed: {stats['failed']}")
        
        return stats
    
    def verify_converted_file(self, csv_path: str) -> bool:
        """
        Verify that a converted CSV has the correct structure
        
        Args:
            csv_path: Path to CSV file to verify
            
        Returns:
            True if structure is correct, False otherwise
        """
        try:
            df = pd.read_csv(csv_path)
            expected_columns = ['Date', 'Adj Close', 'Close', 'High', 'Low', 'Open', 'Volume']
            
            if list(df.columns) == expected_columns:
                logger.info(f"✅ {csv_path} has correct structure")
                
                # Additional validation
                if len(df) == 0:
                    logger.warning("  ⚠️ File is empty")
                    return False
                
                # Check data types
                numeric_cols = ['Adj Close', 'Close', 'High', 'Low', 'Open', 'Volume']
                for col in numeric_cols:
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        logger.warning(f"  ⚠️ Column {col} is not numeric")
                        return False
                
                # Check date format
                try:
                    pd.to_datetime(df['Date'])
                except:
                    logger.warning("  ⚠️ Date column has invalid format")
                    return False
                
                logger.info(f"  ✓ Data types are correct")
                logger.info(f"  ✓ {len(df)} rows of data")
                return True
            else:
                logger.error(f"❌ {csv_path} has incorrect structure")
                logger.error(f"   Found: {df.columns.tolist()}")
                logger.error(f"   Expected: {expected_columns}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying {csv_path}: {e}")
            return False


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert NSE CSV data to standard structure')
    parser.add_argument('--input', help='Input CSV file or directory')
    parser.add_argument('--database', help='SQLite database path')
    parser.add_argument('--output', default='converted_data', help='Output directory')
    parser.add_argument('--symbol', help='Convert specific symbol from database')
    parser.add_argument('--verify', help='Verify CSV file structure')
    parser.add_argument('--batch', action='store_true', help='Convert all CSVs in input directory')
    
    args = parser.parse_args()
    
    converter = CSVStructureConverter(output_dir=args.output)
    
    if args.verify:
        # Verify mode
        converter.verify_converted_file(args.verify)
    
    elif args.database:
        # Convert from database
        stats = converter.convert_from_database(
            db_path=args.database,
            symbol=args.symbol,
            output_dir=args.output
        )
        
        # Verify a sample converted file
        if stats.get('files_created'):
            sample_file = stats['files_created'][0]
            converter.verify_converted_file(sample_file)
    
    elif args.batch and args.input:
        # Batch convert directory
        stats = converter.convert_directory(args.input)
        
        # Verify first converted file
        if stats.get('converted_files'):
            output_file = os.path.join(args.output, os.path.basename(stats['converted_files'][0]))
            if os.path.exists(output_file):
                converter.verify_converted_file(output_file)
    
    elif args.input:
        # Convert single file
        success = converter.convert_csv_file(args.input)
        if success:
            output_file = os.path.join(args.output, os.path.basename(args.input))
            converter.verify_converted_file(output_file)
    
    else:
        # Example usage
        print("\nExample Usage:")
        print("-" * 50)
        print("# Convert single CSV file:")
        print("python csv_structure_converter.py --input data.csv --output converted/")
        print("\n# Convert from SQLite database:")
        print("python csv_structure_converter.py --database nse_cash.db --output converted/")
        print("\n# Convert specific symbol from database:")
        print("python csv_structure_converter.py --database nse_cash.db --symbol TCS --output converted/")
        print("\n# Batch convert directory:")
        print("python csv_structure_converter.py --input raw_data/ --batch --output converted/")
        print("\n# Verify CSV structure:")
        print("python csv_structure_converter.py --verify converted/TCS.csv")


if __name__ == "__main__":
    main()
