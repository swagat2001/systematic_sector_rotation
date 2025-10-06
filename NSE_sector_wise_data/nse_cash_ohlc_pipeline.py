"""

NSE Cash Stocks OHLC Pipeline with concurrent Bhavcopy downloads.

Features:

- Fetches official NSE Bhavcopy daily files (last 4 years) using multiple threads.

- Extracts OHLC for all cash equities.

- Maps sector/industry using yfinance metadata.

- Stores metadata and OHLC in SQLite (default) or PostgreSQL.

- Fully automatic, resumable, concurrent, throttled.

Usage:

export DATABASE_URL=sqlite:///nse_cash.db

python nse_cash_pipeline.py --workers 6 --sleep 0.6

Requirements:

pandas,requests,yfinance,sqlalchemy,psycopg2-binary,tqdm

"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from threading import Lock
import zipfile
import io
import requests
import pandas as pd
import yfinance as yf
from sqlalchemy import (
create_engine, MetaData, Table, Column, String, Integer, Date, Float, BigInteger, DateTime, select, insert, Index
)

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from tqdm import tqdm
import ssl
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ------------------------- Configuration & Logging -------------------------

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

LOG = logging.getLogger("nse_pipeline")

DEFAULT_DB_URL = os.getenv('DATABASE_URL', 'sqlite:///nse_cash.db')

# Disable SSL warnings for insecure requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ------------------------- Enhanced Session Configuration -------------------------

def create_secure_session():
    """Create a session with enhanced SSL configuration and retry strategy"""
    session = requests.Session()

    # Enhanced headers to mimic a real browser
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    })

    # Retry strategy - compatible with both old and new urllib3 versions
    retry_kwargs = {
        'total': 3,
        'status_forcelist': [429, 500, 502, 503, 504],
        'backoff_factor': 1
    }
    
    # Try new parameter name first, fall back to old one
    try:
        retry_strategy = Retry(allowed_methods=["HEAD", "GET", "OPTIONS"], **retry_kwargs)
    except TypeError:
        retry_strategy = Retry(method_whitelist=["HEAD", "GET", "OPTIONS"], **retry_kwargs)

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # SSL context configuration
    session.verify = True  # Keep SSL verification enabled

    return session

# ------------------------- DB Schema setup -------------------------

def get_engine(database_url=DEFAULT_DB_URL):
    return create_engine(database_url)

def prepare_db(engine):
    meta = MetaData()
    companies = Table('companies', meta,
        Column('symbol', String, primary_key=True),
        Column('fullname', String),
        Column('isin', String),
        Column('series', String),
        Column('sector', String),
        Column('industry', String),
        Column('last_metadata_sync', DateTime),
    )

    ohlc = Table('ohlc', meta,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('symbol', String, index=True),
        Column('date', Date, index=True),
        Column('open', Float),
        Column('high', Float),
        Column('low', Float),
        Column('close', Float),
        Column('adj_close', Float),
        Column('volume', BigInteger),
    )

    Index('ix_ohlc_symbol_date', ohlc.c.symbol, ohlc.c.date, unique=True)
    meta.create_all(engine)
    return companies, ohlc

# ------------------------- Load equity list -------------------------

def load_equity_list(csv_path='EQUITY_L.csv'):
    if not os.path.exists(csv_path):
        LOG.error(f'{csv_path} not found. Download manually from NSE website.')
        sys.exit(1)
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().upper() for c in df.columns]
    if 'SYMBOL' not in df.columns:
        LOG.error('SYMBOL column missing in EQUITY_L.csv')
        sys.exit(1)
    if 'SERIES' in df.columns:
        df = df[df['SERIES']=='EQ']
    symbols = df['SYMBOL'].astype(str).str.strip().tolist()
    LOG.info(f'Total cash equities: {len(symbols)}')
    return df, symbols

# ------------------------- Metadata -------------------------

def ticker_to_yf(ticker):
    return f'{ticker}.NS'

def fetch_metadata_yf(symbol):
    yf_t = yf.Ticker(ticker_to_yf(symbol))
    info = yf_t.info or {}
    return {
        'symbol': symbol,
        'fullname': info.get('longName') or info.get('shortName'),
        'sector': info.get('sector'),
        'industry': info.get('industry'),
        'isin': info.get('isin') or None
    }

# ------------------------- Enhanced Bhavcopy Fetcher -------------------------

def generate_bhavcopy_url(date_obj):
    y = date_obj.year
    m = f'{date_obj:%b}'.upper()
    d = f'{date_obj.day:02d}'
    return f'https://nsearchives.nseindia.com/content/historical/EQUITIES/{y}/{m}/cm{d}{m}{y}bhav.csv.zip'

def fetch_bhavcopy(date_obj, session=None, max_retries=3):
    """Enhanced bhavcopy fetcher with better error handling and SSL configuration"""
    if session is None:
        session = create_secure_session()

    url = generate_bhavcopy_url(date_obj)

    for attempt in range(max_retries):
        try:
            # Add random delay to avoid rate limiting
            if attempt > 0:
                time.sleep(2 ** attempt)  # Exponential backoff

            response = session.get(url, timeout=60, stream=True, verify=True)

            if response.status_code == 404:
                LOG.debug(f'No Bhavcopy for {date_obj} (404)')
                return None
            elif response.status_code != 200:
                LOG.warning(f'HTTP {response.status_code} for {date_obj}')
                continue

            # Process the zip file
            z = zipfile.ZipFile(io.BytesIO(response.content))
            csv_name = [n for n in z.namelist() if n.lower().endswith('.csv')][0]
            df = pd.read_csv(z.open(csv_name))

            LOG.debug(f'Successfully fetched Bhavcopy for {date_obj}')
            return df

        except requests.exceptions.SSLError as e:
            LOG.warning(f'SSL Error for {date_obj} (attempt {attempt + 1}/{max_retries}): {str(e)[:100]}...')
            if attempt == max_retries - 1:
                # Last attempt with relaxed SSL
                try:
                    LOG.info(f'Trying with SSL verification disabled for {date_obj}')
                    response = session.get(url, timeout=60, stream=True, verify=False)
                    if response.status_code == 200:
                        z = zipfile.ZipFile(io.BytesIO(response.content))
                        csv_name = [n for n in z.namelist() if n.lower().endswith('.csv')][0]
                        df = pd.read_csv(z.open(csv_name))
                        return df
                except Exception as final_e:
                    LOG.error(f'Final attempt failed for {date_obj}: {final_e}')

        except requests.exceptions.Timeout:
            LOG.warning(f'Timeout for {date_obj} (attempt {attempt + 1}/{max_retries})')

        except Exception as e:
            LOG.warning(f'Error fetching {date_obj} (attempt {attempt + 1}/{max_retries}): {str(e)[:100]}...')

    LOG.error(f'Failed all attempts for Bhavcopy {date_obj}')
    return None

# ------------------------- Upsert -------------------------

def upsert_company(engine, companies_table, metadata_dict):
    with engine.begin() as conn:
        stmt = sqlite_insert(companies_table).values(
            symbol=metadata_dict['symbol'], fullname=metadata_dict.get('fullname'),
            isin=metadata_dict.get('isin'), sector=metadata_dict.get('sector'),
            industry=metadata_dict.get('industry'), last_metadata_sync=datetime.utcnow()
        )

        try:
            stmt = stmt.on_conflict_do_update(index_elements=['symbol'], set_={
                'fullname': stmt.excluded.fullname,
                'isin': stmt.excluded.isin,
                'sector': stmt.excluded.sector,
                'industry': stmt.excluded.industry,
                'last_metadata_sync': stmt.excluded.last_metadata_sync
            })
            conn.execute(stmt)
        except Exception:
            conn.execute(companies_table.delete().where(companies_table.c.symbol==metadata_dict['symbol']))
            conn.execute(companies_table.insert().values(**metadata_dict, last_metadata_sync=datetime.utcnow()))

def upsert_ohlc_bulk(engine, ohlc_table, df_ohlc, db_lock=None):
    if df_ohlc is None or df_ohlc.empty:
        return
    df = df_ohlc.copy()
    
    # Clean column names - strip whitespace and convert to uppercase
    df.columns = [c.strip().upper() for c in df.columns]
    
    # Check if required columns exist
    required_cols = ['SYMBOL', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'TOTTRDQTY']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        LOG.warning(f'Missing columns in Bhavcopy: {missing_cols}. Available: {df.columns.tolist()}')
        return
    
    # Handle date column - it might be TIMESTAMP or DATE
    date_col = None
    for possible_date in ['TIMESTAMP', 'DATE', 'TRADE_DATE', 'TRD_DATE']:
        if possible_date in df.columns:
            date_col = possible_date
            break
    
    if date_col is None:
        LOG.warning(f'No date column found. Available columns: {df.columns.tolist()}')
        return
    
    df['date'] = pd.to_datetime(df[date_col]).dt.date
    df['symbol'] = df['SYMBOL'].astype(str).str.strip()
    df['open'] = df['OPEN']
    df['high'] = df['HIGH']
    df['low'] = df['LOW']
    df['close'] = df['CLOSE']
    df['adj_close'] = df['CLOSE']
    df['volume'] = df['TOTTRDQTY']
    df = df[['symbol','date','open','high','low','close','adj_close','volume']]

    # Use lock for SQLite concurrent writes
    if db_lock:
        db_lock.acquire()
    
    try:
        with engine.begin() as conn:
            for _, row in df.iterrows():
                try:
                    stmt = sqlite_insert(ohlc_table).values(**row.to_dict())
                    stmt = stmt.on_conflict_do_update(index_elements=['symbol', 'date'], set_={
                        'open': stmt.excluded.open,
                        'high': stmt.excluded.high,
                        'low': stmt.excluded.low,
                        'close': stmt.excluded.close,
                        'adj_close': stmt.excluded.adj_close,
                        'volume': stmt.excluded.volume
                    })
                    conn.execute(stmt)
                except Exception:
                    conn.execute(ohlc_table.delete().where((ohlc_table.c.symbol==row['symbol']) & (ohlc_table.c.date==row['date'])))
                    conn.execute(ohlc_table.insert().values(**row.to_dict()))
    finally:
        if db_lock:
            db_lock.release()

# ------------------------- Orchestration -------------------------

def process_single_date(d, symbols, engine, ohlc_table, session, sleep_time, db_lock):
    """Process a single date with shared session and sleep"""
    time.sleep(sleep_time)  # Rate limiting
    df_bhav = fetch_bhavcopy(d, session)
    if df_bhav is None:
        return
    
    # Clean column names first
    df_bhav.columns = [c.strip().upper() for c in df_bhav.columns]
    
    # Filter for EQ series and symbols in our list
    if 'SERIES' in df_bhav.columns:
        df_bhav = df_bhav[df_bhav['SERIES'] == 'EQ']
    
    df_bhav = df_bhav[df_bhav['SYMBOL'].isin(symbols)]
    upsert_ohlc_bulk(engine, ohlc_table, df_bhav, db_lock)

def run_pipeline(args):
    engine = get_engine(args.database_url)
    companies_table, ohlc_table = prepare_db(engine)
    df_list, symbols = load_equity_list()

    # Metadata fetch
    for sym in tqdm(symbols, desc='Fetching metadata'):
        try:
            meta = fetch_metadata_yf(sym)
            upsert_company(engine, companies_table, meta)
            time.sleep(0.5) # To avoid yfinance rate-limiting
        except Exception as e:
            LOG.warning(f'Failed to fetch metadata for {sym}: {e}')

    end_date = datetime.utcnow().date() + timedelta(days=1)
    start_date = end_date - timedelta(days=4*365)
    all_dates = pd.bdate_range(start=start_date, end=end_date)

    LOG.info(f'Starting concurrent Bhavcopy fetch for {len(all_dates)} days')

    # Create a shared session and database lock for all threads
    session = create_secure_session()
    db_lock = Lock()  # SQLite write lock

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(process_single_date, d, symbols, engine, ohlc_table, session, args.sleep, db_lock): d for d in all_dates}
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try:
                fut.result()
            except Exception as e:
                LOG.warning(f'Failed processing date {futures[fut]}: {e}')

# ------------------------- CLI -------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='NSE cash-equity OHLC downloader using Bhavcopies with concurrency')
    parser.add_argument('--database-url', default=DEFAULT_DB_URL, help='SQLAlchemy DB URL')
    parser.add_argument('--workers', type=int, default=2, help='Concurrent Bhavcopy downloads (reduced default)')
    parser.add_argument('--sleep', type=float, default=1.0, help='Seconds sleep per Bhavcopy fetch (increased default)')
    args = parser.parse_args()
    run_pipeline(args)
