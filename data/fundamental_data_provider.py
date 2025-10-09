"""
Fundamental Data Provider - Abstract Interface
==============================================

This module defines the interface for providing fundamental data to the strategy.
The manager can implement this interface with their own API to provide real data.

Required Data Points (as per manager's requirements):
- ROE (Return on Equity)
- ROCE (Return on Capital Employed)  
- EPS CAGR (Earnings Per Share Compound Annual Growth Rate)
- PE Ratio (Price to Earnings)
- PB Ratio (Price to Book)
- Debt to Equity
- Current Ratio
- Market Cap
- ... and any other fundamentals

The system is designed to be fully dynamic - any API can be plugged in.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd


class FundamentalDataProvider(ABC):
    """
    Abstract base class for fundamental data providers.
    
    Manager should implement this interface with their API.
    """
    
    @abstractmethod
    def get_fundamental_data(self, 
                            symbol: str, 
                            as_of_date: datetime = None) -> Dict:
        """
        Get fundamental data for a single stock.
        
        Args:
            symbol: Stock symbol (e.g., 'INFY', 'TCS')
            as_of_date: Date for which to fetch data (None = latest)
        
        Returns:
            Dict with fundamental metrics. Must include at minimum:
            {
                'roe': float,              # Return on Equity (%)
                'roce': float,             # Return on Capital Employed (%)
                'eps_cagr': float,         # EPS CAGR (%)
                'pe_ratio': float,         # Price to Earnings
                'pb_ratio': float,         # Price to Book
                'debt_to_equity': float,   # Debt to Equity ratio
                'current_ratio': float,    # Current Ratio
                'market_cap': float,       # Market Cap (₹)
                
                # Optional but recommended:
                'revenue_growth': float,   # Revenue growth (%)
                'profit_margin': float,    # Net profit margin (%)
                'dividend_yield': float,   # Dividend yield (%)
                'book_value': float,       # Book value per share
                'eps': float,              # Earnings per share
                'revenue': float,          # Total revenue
                'net_profit': float,       # Net profit
                'total_debt': float,       # Total debt
                'cash': float,             # Cash and equivalents
            }
        """
        pass
    
    @abstractmethod
    def get_bulk_fundamental_data(self, 
                                 symbols: List[str],
                                 as_of_date: datetime = None) -> Dict[str, Dict]:
        """
        Get fundamental data for multiple stocks (optimized for bulk fetch).
        
        Args:
            symbols: List of stock symbols
            as_of_date: Date for which to fetch data (None = latest)
        
        Returns:
            Dict mapping symbol to fundamental data dict
            {
                'INFY': {'roe': 25.3, 'roce': 28.1, ...},
                'TCS': {'roe': 42.1, 'roce': 45.2, ...},
                ...
            }
        """
        pass
    
    @abstractmethod
    def is_data_available(self, symbol: str) -> bool:
        """
        Check if fundamental data is available for a symbol.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            True if data is available, False otherwise
        """
        pass
    
    @abstractmethod
    def get_available_symbols(self) -> List[str]:
        """
        Get list of all symbols for which fundamental data is available.
        
        Returns:
            List of stock symbols
        """
        pass
    
    @abstractmethod
    def get_last_update_time(self, symbol: str) -> Optional[datetime]:
        """
        Get the timestamp of the last data update for a symbol.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            datetime of last update, or None if not available
        """
        pass


class DefaultFundamentalProvider(FundamentalDataProvider):
    """
    Default implementation using synthetic/placeholder data.
    
    ⚠️  THIS SHOULD BE REPLACED WITH REAL API IMPLEMENTATION
    
    This is only used as a fallback when no real data source is configured.
    """
    
    def __init__(self):
        import numpy as np
        self.np = np
        print("⚠️  WARNING: Using DEFAULT (synthetic) fundamental data provider")
        print("   Replace this with your API implementation for production use!")
    
    def get_fundamental_data(self, symbol: str, as_of_date: datetime = None) -> Dict:
        """Generate synthetic fundamental data (PLACEHOLDER ONLY)"""
        return {
            'roe': self.np.random.uniform(12, 25),
            'roce': self.np.random.uniform(15, 30),
            'eps_cagr': self.np.random.uniform(5, 20),
            'pe_ratio': self.np.random.uniform(15, 30),
            'pb_ratio': self.np.random.uniform(2, 8),
            'debt_to_equity': self.np.random.uniform(0.3, 1.2),
            'current_ratio': self.np.random.uniform(1.2, 2.5),
            'market_cap': self.np.random.uniform(1e9, 1e11),
            'revenue_growth': self.np.random.uniform(5, 25),
            'profit_margin': self.np.random.uniform(8, 20),
            'dividend_yield': self.np.random.uniform(0.5, 3.0),
        }
    
    def get_bulk_fundamental_data(self, symbols: List[str], 
                                 as_of_date: datetime = None) -> Dict[str, Dict]:
        """Generate bulk synthetic data"""
        return {symbol: self.get_fundamental_data(symbol, as_of_date) 
                for symbol in symbols}
    
    def is_data_available(self, symbol: str) -> bool:
        """Always returns True for synthetic data"""
        return True
    
    def get_available_symbols(self) -> List[str]:
        """Returns empty list (synthetic data available for any symbol)"""
        return []
    
    def get_last_update_time(self, symbol: str) -> Optional[datetime]:
        """Returns current time"""
        return datetime.now()


# Example: How Manager Should Implement Their API
class ManagerAPIFundamentalProvider(FundamentalDataProvider):
    """
    EXAMPLE IMPLEMENTATION for Manager's API
    
    Manager should implement this with their actual API endpoints.
    """
    
    def __init__(self, api_key: str, api_url: str):
        """
        Initialize with API credentials
        
        Args:
            api_key: API authentication key
            api_url: Base URL for API endpoints
        """
        self.api_key = api_key
        self.api_url = api_url
        self.session = None  # Initialize HTTP session
        
        print(f"✓ Initialized Manager API Fundamental Provider")
        print(f"  API URL: {api_url}")
    
    def get_fundamental_data(self, symbol: str, as_of_date: datetime = None) -> Dict:
        """
        Fetch fundamental data from Manager's API
        
        Example API call structure (adapt to actual API):
        
        import requests
        
        response = requests.get(
            f"{self.api_url}/fundamentals/{symbol}",
            headers={'Authorization': f'Bearer {self.api_key}'},
            params={'date': as_of_date.strftime('%Y-%m-%d') if as_of_date else None}
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'roe': data['return_on_equity'],
                'roce': data['return_on_capital_employed'],
                'eps_cagr': data['eps_cagr_3y'],
                'pe_ratio': data['pe_ratio'],
                'pb_ratio': data['pb_ratio'],
                'debt_to_equity': data['debt_equity_ratio'],
                'current_ratio': data['current_ratio'],
                'market_cap': data['market_cap'],
                # ... map all other fields from API response
            }
        else:
            raise Exception(f"API Error: {response.status_code}")
        """
        
        # TODO: Implement actual API call here
        raise NotImplementedError("Manager needs to implement this with their API")
    
    def get_bulk_fundamental_data(self, symbols: List[str],
                                 as_of_date: datetime = None) -> Dict[str, Dict]:
        """
        Fetch bulk fundamental data (if API supports batch requests)
        
        Example:
        
        response = requests.post(
            f"{self.api_url}/fundamentals/bulk",
            headers={'Authorization': f'Bearer {self.api_key}'},
            json={'symbols': symbols, 'date': as_of_date}
        )
        
        return response.json()
        """
        
        # TODO: Implement bulk API call
        # Fallback to individual calls if bulk not supported:
        return {symbol: self.get_fundamental_data(symbol, as_of_date) 
                for symbol in symbols}
    
    def is_data_available(self, symbol: str) -> bool:
        """Check if data exists for symbol"""
        try:
            self.get_fundamental_data(symbol)
            return True
        except:
            return False
    
    def get_available_symbols(self) -> List[str]:
        """Get list of all symbols with fundamental data"""
        # TODO: Implement API call to get available symbols
        raise NotImplementedError("Manager needs to implement this")
    
    def get_last_update_time(self, symbol: str) -> Optional[datetime]:
        """Get last update timestamp"""
        # TODO: Implement API call to get metadata
        raise NotImplementedError("Manager needs to implement this")


def get_fundamental_provider(provider_type: str = 'default', **kwargs) -> FundamentalDataProvider:
    """
    Factory function to get the appropriate fundamental data provider.
    
    Args:
        provider_type: Type of provider ('default', 'manager_api', 'csv', 'database')
        **kwargs: Provider-specific configuration
    
    Returns:
        FundamentalDataProvider instance
    
    Usage:
        # For production with Manager's API:
        provider = get_fundamental_provider(
            'manager_api',
            api_key='your_api_key',
            api_url='https://api.yourcompany.com'
        )
        
        # For testing with default synthetic data:
        provider = get_fundamental_provider('default')
    """
    
    if provider_type == 'default':
        return DefaultFundamentalProvider()
    
    elif provider_type == 'manager_api':
        api_key = kwargs.get('api_key')
        api_url = kwargs.get('api_url')
        
        if not api_key or not api_url:
            raise ValueError("manager_api provider requires 'api_key' and 'api_url'")
        
        return ManagerAPIFundamentalProvider(api_key, api_url)
    
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


if __name__ == "__main__":
    """
    Demo: How to use the fundamental data provider
    """
    
    print("\n" + "=" * 80)
    print("FUNDAMENTAL DATA PROVIDER DEMO")
    print("=" * 80)
    
    # Example 1: Default provider (synthetic data)
    print("\n1. Using DEFAULT provider (synthetic data):")
    print("-" * 80)
    
    default_provider = get_fundamental_provider('default')
    
    test_symbols = ['INFY', 'TCS', 'WIPRO']
    bulk_data = default_provider.get_bulk_fundamental_data(test_symbols)
    
    for symbol, data in bulk_data.items():
        print(f"\n{symbol}:")
        print(f"  ROE: {data['roe']:.2f}%")
        print(f"  ROCE: {data['roce']:.2f}%")
        print(f"  EPS CAGR: {data['eps_cagr']:.2f}%")
        print(f"  PE Ratio: {data['pe_ratio']:.2f}")
        print(f"  Market Cap: ₹{data['market_cap']:,.0f}")
    
    # Example 2: Manager's API (needs implementation)
    print("\n\n2. Using MANAGER'S API provider:")
    print("-" * 80)
    print("⚠️  Manager needs to implement ManagerAPIFundamentalProvider with their API")
    print("   See example code in fundamental_data_provider.py")
    
    print("\n" + "=" * 80)
    print("TO USE IN PRODUCTION:")
    print("=" * 80)
    print("""
1. Implement ManagerAPIFundamentalProvider with your API:
   - Fill in get_fundamental_data() method
   - Fill in get_bulk_fundamental_data() method
   - Add authentication logic
   
2. Configure in config.py:
   FUNDAMENTAL_PROVIDER = {
       'type': 'manager_api',
       'api_key': 'your_api_key_here',
       'api_url': 'https://your-api.com'
   }

3. System will automatically use your API for all fundamental data!
""")
    print("=" * 80 + "\n")
