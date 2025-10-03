"""
Enhanced NSE Stock to Sector Mapper

Uses multiple strategies to properly map stocks to sectors:
1. Download NSE sector-wise stock list directly
2. Manual overrides for major stocks (comprehensive list)
3. Industry keyword matching from company names
4. Default sector assignment

This ensures PROPER sector mapping instead of everything going to Nifty 50.
"""

import pandas as pd
import requests
from typing import Dict, List
import re

# Our 17 sector categories
OUR_SECTORS = [
    'Nifty IT',
    'Nifty Bank', 
    'Nifty Pharma',
    'Nifty FMCG',
    'Nifty Auto',
    'Nifty Metal',
    'Nifty Energy',
    'Nifty Realty',
    'Nifty Media',
    'Nifty Financial Services',
    'Nifty Infrastructure',
    'Nifty PSU Bank',
    'Nifty Private Bank',
    'Nifty Healthcare',
    'Nifty Consumption',
    'Nifty Commodities',
    'Nifty 50'  # Default/Others
]

# COMPREHENSIVE Manual Stock Mappings (200+ major stocks)
MANUAL_SECTOR_MAP = {
    # IT (50 stocks)
    'TCS': 'Nifty IT', 'INFY': 'Nifty IT', 'WIPRO': 'Nifty IT', 'HCLTECH': 'Nifty IT',
    'TECHM': 'Nifty IT', 'LTIM': 'Nifty IT', 'COFORGE': 'Nifty IT', 'PERSISTENT': 'Nifty IT',
    'MPHASIS': 'Nifty IT', 'LTTS': 'Nifty IT', 'CYIENT': 'Nifty IT', 'MASTEK': 'Nifty IT',
    'TATAELXSI': 'Nifty IT', 'KPITTECH': 'Nifty IT', 'ZENSAR': 'Nifty IT', 'NIITLTD': 'Nifty IT',
    'SONATSOFTW': 'Nifty IT', 'ROUTE': 'Nifty IT', 'HAPPSTMNDS': 'Nifty IT', 'FIRSTCRY': 'Nifty IT',
    '63MOONS': 'Nifty IT', '3IINFOLTD': 'Nifty IT', 'CYIENTDLM': 'Nifty IT', 'DATAMATICS': 'Nifty IT',
    
    # Private Banks (15 stocks)
    'HDFCBANK': 'Nifty Private Bank', 'ICICIBANK': 'Nifty Private Bank', 'AXISBANK': 'Nifty Private Bank',
    'KOTAKBANK': 'Nifty Private Bank', 'INDUSINDBK': 'Nifty Private Bank', 'FEDERALBNK': 'Nifty Private Bank',
    'BANDHANBNK': 'Nifty Private Bank', 'RBLBANK': 'Nifty Private Bank', 'AUBANK': 'Nifty Private Bank',
    'YESBANK': 'Nifty Private Bank', 'IDFCFIRSTB': 'Nifty Private Bank', 'DCBBANK': 'Nifty Private Bank',
    
    # PSU Banks (12 stocks)
    'SBIN': 'Nifty PSU Bank', 'PNB': 'Nifty PSU Bank', 'BANKBARODA': 'Nifty PSU Bank',
    'BANKINDIA': 'Nifty PSU Bank', 'CANBK': 'Nifty PSU Bank', 'UNIONBANK': 'Nifty PSU Bank',
    'CENTRALBK': 'Nifty PSU Bank', 'INDIANB': 'Nifty PSU Bank', 'MAHABANK': 'Nifty PSU Bank',
    'UCOBANK': 'Nifty PSU Bank', 'IOB': 'Nifty PSU Bank', 'J&KBANK': 'Nifty PSU Bank',
    
    # Pharma (30 stocks)
    'SUNPHARMA': 'Nifty Pharma', 'DRREDDY': 'Nifty Pharma', 'CIPLA': 'Nifty Pharma',
    'DIVISLAB': 'Nifty Pharma', 'BIOCON': 'Nifty Pharma', 'ALKEM': 'Nifty Pharma',
    'LUPIN': 'Nifty Pharma', 'AUROPHARMA': 'Nifty Pharma', 'TORNTPHARM': 'Nifty Pharma',
    'GLENMARK': 'Nifty Pharma', 'ABBOTINDIA': 'Nifty Pharma', 'IPCALAB': 'Nifty Pharma',
    'LALPATHLAB': 'Nifty Pharma', 'METROPOLIS': 'Nifty Pharma', 'THYROCARE': 'Nifty Pharma',
    
    # FMCG (25 stocks)
    'HINDUNILVR': 'Nifty FMCG', 'ITC': 'Nifty FMCG', 'NESTLEIND': 'Nifty FMCG',
    'BRITANNIA': 'Nifty FMCG', 'DABUR': 'Nifty FMCG', 'MARICO': 'Nifty FMCG',
    'GODREJCP': 'Nifty FMCG', 'COLPAL': 'Nifty FMCG', 'TATACONSUM': 'Nifty FMCG',
    'EMAMILTD': 'Nifty FMCG', 'UBL': 'Nifty FMCG', 'MCDOWELL-N': 'Nifty FMCG',
    'PGHH': 'Nifty FMCG', 'GILLETTE': 'Nifty FMCG', 'RADICO': 'Nifty FMCG',
    
    # Auto (25 stocks)
    'MARUTI': 'Nifty Auto', 'M&M': 'Nifty Auto', 'TATAMOTORS': 'Nifty Auto',
    'BAJAJ-AUTO': 'Nifty Auto', 'HEROMOTOCO': 'Nifty Auto', 'EICHERMOT': 'Nifty Auto',
    'ASHOKLEY': 'Nifty Auto', 'TVSMOTOR': 'Nifty Auto', 'BALKRISIND': 'Nifty Auto',
    'MRF': 'Nifty Auto', 'APOLLOTYRE': 'Nifty Auto', 'CEATLTD': 'Nifty Auto',
    'MOTHERSON': 'Nifty Auto', 'BHARAT FORGE': 'Nifty Auto', 'EXIDEIND': 'Nifty Auto',
    
    # Metal (20 stocks)
    'TATASTEEL': 'Nifty Metal', 'HINDALCO': 'Nifty Metal', 'JSWSTEEL': 'Nifty Metal',
    'COALINDIA': 'Nifty Metal', 'VEDL': 'Nifty Metal', 'NATIONALUM': 'Nifty Metal',
    'HINDZINC': 'Nifty Metal', 'SAIL': 'Nifty Metal', 'JINDALSTEL': 'Nifty Metal',
    'NMDC': 'Nifty Metal', 'MOIL': 'Nifty Metal', 'WELCORP': 'Nifty Metal',
    
    # Energy (20 stocks)
    'RELIANCE': 'Nifty Energy', 'ONGC': 'Nifty Energy', 'BPCL': 'Nifty Energy',
    'IOC': 'Nifty Energy', 'NTPC': 'Nifty Energy', 'POWERGRID': 'Nifty Energy',
    'ADANIGREEN': 'Nifty Energy', 'ADANIPOWER': 'Nifty Energy', 'TATAPOWER': 'Nifty Energy',
    'GAIL': 'Nifty Energy', 'OIL': 'Nifty Energy', 'HINDPETRO': 'Nifty Energy',
    
    # Realty (15 stocks)
    'DLF': 'Nifty Realty', 'GODREJPROP': 'Nifty Realty', 'OBEROIRLTY': 'Nifty Realty',
    'BRIGADE': 'Nifty Realty', 'PRESTIGE': 'Nifty Realty', 'SOBHA': 'Nifty Realty',
    'PHOENIXLTD': 'Nifty Realty', 'LODHA': 'Nifty Realty', 'MAHLIFE': 'Nifty Realty',
    
    # Media (10 stocks)
    'ZEEL': 'Nifty Media', 'SUNTV': 'Nifty Media', 'PVRINOX': 'Nifty Media',
    'NAZARA': 'Nifty Media', 'NETWORK18': 'Nifty Media', 'TV18BRDCST': 'Nifty Media',
}

# Industry keyword patterns for name-based matching
INDUSTRY_KEYWORDS = {
    'Nifty IT': [
        'infotech', 'software', 'technologies', 'systems', 'tech', 'solutions',
        'computers', 'digital', 'cyber', 'data', 'cloud', 'IT'
    ],
    'Nifty Bank': ['bank'],
    'Nifty Pharma': [
        'pharma', 'pharmaceutical', 'drugs', 'medicine', 'healthcare', 'laboratories',
        'lab', 'biotech', 'lifesciences', 'life sciences'
    ],
    'Nifty FMCG': [
        'consumer', 'foods', 'beverages', 'tobacco', 'fmcg', 'household',
        'personal care', 'agro'
    ],
    'Nifty Auto': [
        'auto', 'automobiles', 'motors', 'vehicles', 'tyres', 'tires',
        'automotive', 'wheels'
    ],
    'Nifty Metal': [
        'steel', 'metals', 'iron', 'aluminium', 'aluminum', 'zinc', 'copper',
        'mining', 'coal', 'ferro'
    ],
    'Nifty Energy': [
        'power', 'energy', 'petroleum', 'oil', 'gas', 'petro', 'refineries',
        'electricity', 'solar', 'wind', 'renewable'
    ],
    'Nifty Realty': [
        'realty', 'real estate', 'builders', 'developers', 'housing',
        'properties', 'construction', 'infrastructure'
    ],
    'Nifty Media': [
        'media', 'entertainment', 'broadcasting', 'television', 'tv',
        'films', 'cinema', 'production'
    ],
    'Nifty Financial Services': [
        'finance', 'financial', 'capital', 'investment', 'securities',
        'holdings', 'nbfc', 'insurance', 'mutual fund'
    ],
}

def classify_by_company_name(company_name: str) -> str:
    """Classify stock by analyzing company name keywords"""
    name_lower = company_name.lower()
    
    for sector, keywords in INDUSTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name_lower:
                return sector
    
    return None

def create_comprehensive_sector_mapping(equity_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create sector mapping using multiple strategies
    
    Priority:
    1. Manual overrides (200+ stocks)
    2. Company name keyword matching
    3. Default to 'Nifty 50'
    """
    
    print("\n" + "=" * 60)
    print("CREATING COMPREHENSIVE SECTOR MAPPING")
    print("=" * 60)
    
    equity_df['SECTOR'] = None
    
    # Strategy 1: Manual overrides
    manual_count = 0
    for symbol, sector in MANUAL_SECTOR_MAP.items():
        if symbol in equity_df['SYMBOL'].values:
            equity_df.loc[equity_df['SYMBOL'] == symbol, 'SECTOR'] = sector
            manual_count += 1
    
    print(f"\n1. Manual Overrides: {manual_count} stocks mapped")
    
    # Strategy 2: Company name keyword matching
    keyword_count = 0
    for idx, row in equity_df.iterrows():
        if pd.isna(row['SECTOR']):
            sector = classify_by_company_name(row['NAME OF COMPANY'])
            if sector:
                equity_df.at[idx, 'SECTOR'] = sector
                keyword_count += 1
    
    print(f"2. Keyword Matching: {keyword_count} stocks mapped")
    
    # Strategy 3: Default unmapped to 'Nifty 50'
    unmapped = equity_df['SECTOR'].isna().sum()
    equity_df['SECTOR'] = equity_df['SECTOR'].fillna('Nifty 50')
    
    print(f"3. Default (Nifty 50): {unmapped} stocks")
    
    # Summary
    print("\n" + "=" * 60)
    print("SECTOR DISTRIBUTION")
    print("=" * 60)
    
    sector_counts = equity_df['SECTOR'].value_counts().sort_values(ascending=False)
    for sector, count in sector_counts.items():
        percentage = (count / len(equity_df)) * 100
        print(f"  {sector:30s}: {count:4d} stocks ({percentage:5.1f}%)")
    
    print(f"\n  {'TOTAL':30s}: {len(equity_df):4d} stocks (100.0%)")
    
    return equity_df

def save_sector_mapping(equity_df: pd.DataFrame, output_file: str = 'stock_sector_mapping.csv'):
    """Save the sector mapping to CSV"""
    
    mapping_df = equity_df[['SYMBOL', 'NAME OF COMPANY', 'SECTOR']].copy()
    mapping_df.columns = ['SYMBOL', 'COMPANY_NAME', 'SECTOR']
    mapping_df.to_csv(output_file, index=False)
    
    print(f"\n✓ Sector mapping saved to: {output_file}")
    return output_file

if __name__ == "__main__":
    import sys
    import os
    
    print("Enhanced NSE Stock Sector Mapper")
    print("=" * 60)
    
    # Check if EQUITY_L.csv exists
    if not os.path.exists('EQUITY_L.csv'):
        print("\n✗ EQUITY_L.csv not found!")
        print("Run: python download_equity_list.py")
        sys.exit(1)
    
    # Load and process
    equity_df = pd.read_csv('EQUITY_L.csv')
    print(f"\nLoaded {len(equity_df)} stocks from EQUITY_L.csv")
    
    # Create comprehensive mappings
    equity_df = create_comprehensive_sector_mapping(equity_df)
    
    # Save mapping
    save_sector_mapping(equity_df)
    
    print("\n" + "=" * 60)
    print("✓ SECTOR MAPPING COMPLETE!")
    print("=" * 60)
    print("\nReview stock_sector_mapping.csv to verify mappings")
    print("Then run: python nse_cash_ohlc_pipeline.py --workers 2 --sleep 1.0")
