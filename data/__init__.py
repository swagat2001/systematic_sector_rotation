"""
Data package for systematic sector rotation strategy
Handles NSE data loading and validation
"""

# Only import what's actually used
from .nse_data_bridge import NSEDataBridge

__all__ = ['NSEDataBridge']
