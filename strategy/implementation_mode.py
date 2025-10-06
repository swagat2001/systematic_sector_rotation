"""
Implementation Mode Handler

Allows client to choose between:
- Option A: Sector ETFs (Immediate sector exposure)
- Option B: Individual Stocks (Enhanced alpha potential)

The strategy logic remains identical; only the instrument type changes.
"""

import pandas as pd
from typing import Dict, List
from datetime import datetime

from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ImplementationModeHandler:
    """
    Handles both ETF and Individual Stock implementations
    """
    
    def __init__(self):
        self.mode = Config.IMPLEMENTATION_MODE
        
        if self.mode == 'SECTOR_ETFS':
            self.etf_config = Config.ETF_CONFIG
            logger.info("IMPLEMENTATION MODE: SECTOR ETFs")
            logger.info("Advantages:")
            for adv in self.etf_config['advantages']:
                logger.info(f"  • {adv}")
        
        elif self.mode == 'INDIVIDUAL_STOCKS':
            self.stocks_config = Config.INDIVIDUAL_STOCKS_CONFIG
            logger.info("IMPLEMENTATION MODE: INDIVIDUAL STOCKS")
            logger.info("Advantages:")
            for adv in self.stocks_config['advantages']:
                logger.info(f"  • {adv}")
        
        else:
            raise ValueError(f"Invalid IMPLEMENTATION_MODE: {self.mode}")
    
    def get_tradeable_instruments(self, sector: str, stocks_data: Dict = None) -> List[str]:
        """
        Get list of tradeable instruments for a sector
        
        Args:
            sector: Sector name (e.g., 'Nifty IT')
            stocks_data: Stock metadata (used for individual stocks mode)
        
        Returns:
            List of symbols to trade
        """
        
        if self.mode == 'SECTOR_ETFS':
            # Return ETF symbol for the sector
            return [self._get_sector_etf(sector)]
        
        elif self.mode == 'INDIVIDUAL_STOCKS':
            # Return individual stocks in the sector
            if stocks_data is None:
                logger.warning(f"No stocks_data provided for {sector}")
                return []
            
            sector_stocks = [
                symbol for symbol, data in stocks_data.items()
                if data.get('sector') == sector
            ]
            
            return sector_stocks
    
    def _get_sector_etf(self, sector: str) -> str:
        """
        Map sector to its corresponding ETF symbol
        
        NSE Sector ETFs (as of 2024):
        """
        
        # NSE Sector ETF Mapping
        sector_etf_map = {
            'Nifty IT': 'SETFNIF50',         # Nifty IT ETF
            'Nifty Bank': 'BANKBEES',        # Bank BeES
            'Nifty Pharma': 'PHARMABEES',    # Pharma BeES
            'Nifty FMCG': 'FMCGBEES',        # FMCG BeES
            'Nifty Auto': 'AUTOBEES',        # Auto BeES
            'Nifty Metal': 'METALBEES',      # Metal BeES
            'Nifty Energy': 'SETFNN50',      # Energy ETF
            'Nifty Realty': 'REALTYBEES',    # Realty BeES
            'Nifty Financial Services': 'FINNIFTY',  # Financial Services ETF
            'Nifty PSU Bank': 'PSUBNKBEES',  # PSU Bank BeES
            
            # Fallback: Use sector index as proxy
            'Nifty Commodities': 'COMMODBEES',
            'Nifty Consumption': 'CONSBEES',
            'Nifty Infrastructure': 'INFRABEES',
            'Nifty Healthcare': 'HEALTHBEES',
            'Nifty Media': 'MEDIABEES',
        }
        
        etf_symbol = sector_etf_map.get(sector, f"{sector.replace(' ', '_')}_ETF")
        
        logger.info(f"Sector {sector} → ETF: {etf_symbol}")
        
        return etf_symbol
    
    def generate_implementation_report(self) -> str:
        """Generate report showing chosen implementation"""
        
        report = "\n" + "=" * 80 + "\n"
        report += "IMPLEMENTATION MODE REPORT\n"
        report += "=" * 80 + "\n\n"
        
        if self.mode == 'SECTOR_ETFS':
            report += "OPTION A: SECTOR ETFs\n"
            report += "-" * 80 + "\n\n"
            report += "Implementation Method:\n"
            report += "  • Trade sector-specific ETFs directly\n"
            report += "  • One ETF per sector (e.g., SETFNIF50 for Nifty IT)\n"
            report += "  • ETF tracks underlying sector index\n\n"
            
            report += "Advantages:\n"
            for adv in self.etf_config['advantages']:
                report += f"  ✓ {adv}\n"
            
            report += "\nExample Portfolio (60% Core):\n"
            report += "  • 3 sector ETFs (20% each)\n"
            report += "  • Nifty IT ETF: 20%\n"
            report += "  • Nifty Bank ETF: 20%\n"
            report += "  • Nifty Pharma ETF: 20%\n\n"
            
            report += "Transaction Costs:\n"
            report += "  • Lower (3 ETF trades vs 15 stock trades)\n"
            report += "  • Simplified rebalancing\n"
            report += "  • Reduced slippage\n"
        
        else:  # INDIVIDUAL_STOCKS
            report += "OPTION B: INDIVIDUAL STOCKS\n"
            report += "-" * 80 + "\n\n"
            report += "Implementation Method:\n"
            report += "  • Trade individual stocks within sectors\n"
            report += "  • Multi-factor scoring selects best stocks\n"
            report += "  • Top 5 stocks per sector (Core)\n"
            report += "  • Top 15 stocks universe-wide (Satellite)\n\n"
            
            report += "Advantages:\n"
            for adv in self.stocks_config['advantages']:
                report += f"  ✓ {adv}\n"
            
            report += "\nExample Portfolio (60% Core + 40% Satellite):\n"
            report += "  Core (60%):\n"
            report += "    • Nifty IT: TCS, INFY, WIPRO, HCLTECH, TECHM (4% each)\n"
            report += "    • Nifty Bank: HDFCBANK, ICICIBANK, AXISBANK, KOTAKBANK, SBIN (4% each)\n"
            report += "    • Nifty Pharma: SUNPHARMA, DRREDDY, CIPLA, DIVISLAB, BIOCON (4% each)\n\n"
            report += "  Satellite (40%):\n"
            report += "    • Top 15 alpha stocks (2.67% each)\n"
            report += "    • Selected from all 1,744 stocks via multi-factor scoring\n\n"
            
            report += "Transaction Costs:\n"
            report += "  • Higher (30 stock trades vs 3 ETF trades)\n"
            report += "  • More complex rebalancing\n"
            report += "  • Greater potential slippage\n"
            report += "  • BUT: Greater alpha potential offsets costs\n"
        
        report += "\n" + "=" * 80 + "\n"
        
        return report
    
    def compare_implementations(self) -> pd.DataFrame:
        """
        Compare both implementation options
        
        Returns:
            DataFrame comparing ETF vs Individual Stocks
        """
        
        comparison = {
            'Feature': [
                'Sector Exposure',
                'Alpha Potential',
                'Customization',
                'Factor Control',
                'Transaction Costs',
                'Portfolio Complexity',
                'Tracking Error',
                'Liquidity',
                'Transparency',
                'Tax Efficiency'
            ],
            'Sector ETFs (Option A)': [
                'Immediate & Complete',
                'Limited (ETF-level only)',
                'Low',
                'Broad sector-level',
                'Lower (fewer trades)',
                'Simple (3 ETFs)',
                'Low',
                'High',
                'ETF holdings',
                'ETF level'
            ],
            'Individual Stocks (Option B)': [
                'Via stock selection',
                'High (stock-picking)',
                'High',
                'Precise stock-level',
                'Higher (more trades)',
                'Complex (30 stocks)',
                'Higher',
                'Stock-dependent',
                'Full (know each stock)',
                'Stock level'
            ]
        }
        
        df = pd.DataFrame(comparison)
        
        return df


def switch_implementation_mode(new_mode: str):
    """
    Helper function to switch between implementations
    
    Args:
        new_mode: 'SECTOR_ETFS' or 'INDIVIDUAL_STOCKS'
    
    Usage:
        # In config.py, change:
        IMPLEMENTATION_MODE = 'SECTOR_ETFS'  # or 'INDIVIDUAL_STOCKS'
    """
    
    valid_modes = ['SECTOR_ETFS', 'INDIVIDUAL_STOCKS']
    
    if new_mode not in valid_modes:
        raise ValueError(f"Invalid mode. Choose from: {valid_modes}")
    
    logger.info("=" * 80)
    logger.info(f"SWITCHING TO: {new_mode}")
    logger.info("=" * 80)
    logger.info("\nTo make this permanent:")
    logger.info("1. Open config.py")
    logger.info(f"2. Change: IMPLEMENTATION_MODE = '{new_mode}'")
    logger.info("3. Save and restart\n")
    
    # Create temporary handler to show new mode
    temp_config = type('Config', (), {'IMPLEMENTATION_MODE': new_mode})
    
    if new_mode == 'SECTOR_ETFS':
        temp_config.ETF_CONFIG = Config.ETF_CONFIG
        logger.info("\nSector ETF Mode:")
        logger.info("  • Core: 3 sector ETFs (20% each)")
        logger.info("  • Satellite: 15 individual stocks OR sector ETF blend")
        logger.info("  • Total positions: ~18 instruments")
    
    else:
        temp_config.INDIVIDUAL_STOCKS_CONFIG = Config.INDIVIDUAL_STOCKS_CONFIG
        logger.info("\nIndividual Stocks Mode:")
        logger.info("  • Core: 15 stocks from top 3 sectors")
        logger.info("  • Satellite: 15 best stocks universe-wide")
        logger.info("  • Total positions: ~30 stocks")
    
    logger.info("\n" + "=" * 80)


if __name__ == "__main__":
    # Demonstrate both implementations
    
    handler = ImplementationModeHandler()
    
    # Show current mode
    report = handler.generate_implementation_report()
    print(report)
    
    # Compare both options
    print("\nCOMPARISON TABLE:")
    print("=" * 80)
    comparison = handler.compare_implementations()
    print(comparison.to_string(index=False))
    
    # Show how to switch
    print("\n" + "=" * 80)
    print("TO SWITCH IMPLEMENTATION MODE:")
    print("=" * 80)
    print("\nOption A (Sector ETFs):")
    print("  In config.py: IMPLEMENTATION_MODE = 'SECTOR_ETFS'")
    print("\nOption B (Individual Stocks):")
    print("  In config.py: IMPLEMENTATION_MODE = 'INDIVIDUAL_STOCKS'")
    print("\nThen restart the system.")
    print("=" * 80)
