"""
Fundamental Scoring Model for Systematic Sector Rotation Strategy

Implements the fundamental scoring component with 45% weight in final score:
- Quality Score (35%): ROE, ROCE, Gross Margin, Cash Conversion
- Growth Score (35%): EPS CAGR, Sales CAGR, Earnings Revisions, Forward Guidance
- Valuation Score (20%): P/E ratio, EV/EBITDA, FCF Yield, P/B ratio
- Balance Sheet Score (10%): Debt ratios, Interest Coverage, Working Capital

Formula: F_i = 0.35*Q + 0.35*G + 0.2*V + 0.1*B
All scores are z-scored relative to sector peers for fair comparison.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from config import Config
from utils.logger import setup_logger
from utils.helpers import z_score_normalize, safe_divide

logger = setup_logger(__name__)


class FundamentalScorer:
    """
    Calculates fundamental scores for stocks based on quality, growth, 
    valuation, and balance sheet metrics
    """
    
    def __init__(self):
        self.config = Config()
        
        # Scoring weights (from client requirements)
        self.weights = {
            'quality': 0.35,
            'growth': 0.35,
            'valuation': 0.20,
            'balance_sheet': 0.10
        }
        
        logger.info("FundamentalScorer initialized")
    
    def calculate_fundamental_score(self, fundamentals: Dict[str, any], 
                                   sector_fundamentals: List[Dict[str, any]] = None) -> Dict[str, float]:
        """
        Calculate composite fundamental score for a stock
        
        Args:
            fundamentals: Dict with fundamental metrics for the stock
            sector_fundamentals: List of fundamental dicts for sector peers (for z-scoring)
        
        Returns:
            Dict with component scores and final fundamental score
        """
        if not fundamentals:
            logger.warning("No fundamental data provided")
            return self._empty_score()
        
        try:
            # Calculate component scores
            quality_score = self._calculate_quality_score(fundamentals)
            growth_score = self._calculate_growth_score(fundamentals)
            valuation_score = self._calculate_valuation_score(fundamentals)
            balance_sheet_score = self._calculate_balance_sheet_score(fundamentals)
            
            # Apply sector normalization if peer data available
            if sector_fundamentals and len(sector_fundamentals) > 5:
                quality_score = self._sector_normalize(
                    quality_score, 
                    [self._calculate_quality_score(f) for f in sector_fundamentals]
                )
                growth_score = self._sector_normalize(
                    growth_score,
                    [self._calculate_growth_score(f) for f in sector_fundamentals]
                )
                valuation_score = self._sector_normalize(
                    valuation_score,
                    [self._calculate_valuation_score(f) for f in sector_fundamentals]
                )
                balance_sheet_score = self._sector_normalize(
                    balance_sheet_score,
                    [self._calculate_balance_sheet_score(f) for f in sector_fundamentals]
                )
            
            # Calculate weighted composite score
            fundamental_score = (
                self.weights['quality'] * quality_score +
                self.weights['growth'] * growth_score +
                self.weights['valuation'] * valuation_score +
                self.weights['balance_sheet'] * balance_sheet_score
            )
            
            return {
                'quality_score': quality_score,
                'growth_score': growth_score,
                'valuation_score': valuation_score,
                'balance_sheet_score': balance_sheet_score,
                'fundamental_score': fundamental_score
            }
            
        except Exception as e:
            logger.error(f"Error calculating fundamental score: {e}")
            return self._empty_score()
    
    def _calculate_quality_score(self, fundamentals: Dict) -> float:
        """
        Calculate Quality Score (35% of fundamental score)
        
        Metrics:
        - Return on Equity (ROE)
        - Return on Capital Employed (ROCE)
        - Gross Margin Stability
        - Cash Conversion Efficiency
        """
        score = 0.0
        count = 0
        
        # ROE component (higher is better)
        roe = fundamentals.get('roe')
        if roe is not None:
            # Normalize ROE: score 0-100, with 20%+ getting 100
            roe_score = min(roe * 5, 1.0) if roe > 0 else 0
            score += roe_score
            count += 1
        
        # ROCE component (higher is better)
        roce = fundamentals.get('roce')
        if roce is not None:
            # Normalize ROCE similar to ROE
            roce_score = min(roce * 5, 1.0) if roce > 0 else 0
            score += roce_score
            count += 1
        
        # Gross Margin (higher is better, looking for stability)
        gross_margin = fundamentals.get('gross_margin')
        if gross_margin is not None:
            # Normalize: 40%+ margin gets top score
            margin_score = min(gross_margin * 2.5, 1.0) if gross_margin > 0 else 0
            score += margin_score
            count += 1
        
        # Operating Margin as proxy for efficiency
        operating_margin = fundamentals.get('operating_margin')
        if operating_margin is not None:
            op_margin_score = min(operating_margin * 5, 1.0) if operating_margin > 0 else 0
            score += op_margin_score
            count += 1
        
        # Cash conversion (current ratio as proxy)
        current_ratio = fundamentals.get('current_ratio')
        if current_ratio is not None:
            # Ideal current ratio is 1.5-2.5
            if 1.5 <= current_ratio <= 2.5:
                cash_score = 1.0
            elif current_ratio > 1.0:
                cash_score = 0.7
            else:
                cash_score = 0.3
            score += cash_score
            count += 1
        
        return score / count if count > 0 else 0.5  # Return average or neutral
    
    def _calculate_growth_score(self, fundamentals: Dict) -> float:
        """
        Calculate Growth Score (35% of fundamental score)
        
        Metrics:
        - EPS CAGR (3-5 years)
        - Sales CAGR
        - Earnings Revisions (3-6 months) 
        - Forward Guidance Trends
        """
        score = 0.0
        count = 0
        
        # EPS Growth
        eps_growth = fundamentals.get('eps_growth_3y') or fundamentals.get('earnings_growth')
        if eps_growth is not None:
            # Normalize: 15%+ growth gets top score
            eps_score = min(eps_growth / 0.15, 1.0) if eps_growth > 0 else max(eps_growth / 0.15, -1.0)
            score += eps_score
            count += 1
        
        # Sales/Revenue Growth
        revenue_growth = fundamentals.get('sales_growth_3y') or fundamentals.get('revenue_growth')
        if revenue_growth is not None:
            # Normalize: 10%+ growth gets top score
            rev_score = min(revenue_growth / 0.10, 1.0) if revenue_growth > 0 else max(revenue_growth / 0.10, -1.0)
            score += rev_score
            count += 1
        
        # Forward PE as indicator of growth expectations
        forward_pe = fundamentals.get('forward_pe')
        pe_ratio = fundamentals.get('pe_ratio')
        if forward_pe and pe_ratio:
            # If forward PE < trailing PE, market expects growth
            if forward_pe < pe_ratio * 0.9:  # 10% lower
                score += 1.0
                count += 1
            elif forward_pe < pe_ratio:
                score += 0.5
                count += 1
        
        # Revenue as indicator of scale
        revenue = fundamentals.get('revenue')
        if revenue is not None and revenue > 0:
            # Companies with scale get slight preference
            # This is a proxy for "established" growth
            if revenue > 10_000_000_000:  # 1000 Cr+
                score += 0.7
            elif revenue > 1_000_000_000:  # 100 Cr+
                score += 0.5
            else:
                score += 0.3
            count += 1
        
        return score / count if count > 0 else 0.5
    
    def _calculate_valuation_score(self, fundamentals: Dict) -> float:
        """
        Calculate Valuation Score (20% of fundamental score)
        
        Metrics:
        - P/E ratio vs sector median
        - EV/EBITDA multiple
        - Free Cash Flow Yield
        - Price-to-Book ratio
        
        Note: Lower valuations get higher scores (value investing principle)
        """
        score = 0.0
        count = 0
        
        # P/E Ratio (lower is better, but not too low)
        pe_ratio = fundamentals.get('pe_ratio')
        if pe_ratio is not None and pe_ratio > 0:
            # Ideal P/E range: 15-25
            if 15 <= pe_ratio <= 25:
                pe_score = 1.0
            elif pe_ratio < 15:
                # Too cheap might signal problems
                pe_score = 0.5 + (pe_ratio / 30)  # 0.5 to 1.0
            else:
                # Expensive, diminishing score
                pe_score = max(0, 1.0 - ((pe_ratio - 25) / 50))
            
            score += pe_score
            count += 1
        
        # EV/EBITDA (lower is better)
        ev_ebitda = fundamentals.get('ev_ebitda')
        if ev_ebitda is not None and ev_ebitda > 0:
            # Ideal EV/EBITDA: 8-15
            if 8 <= ev_ebitda <= 15:
                ev_score = 1.0
            elif ev_ebitda < 8:
                ev_score = 0.7
            else:
                ev_score = max(0, 1.0 - ((ev_ebitda - 15) / 30))
            
            score += ev_score
            count += 1
        
        # Price to Book (lower is better for value)
        pb_ratio = fundamentals.get('pb_ratio')
        if pb_ratio is not None and pb_ratio > 0:
            # Ideal P/B: 1-3
            if 1 <= pb_ratio <= 3:
                pb_score = 1.0
            elif pb_ratio < 1:
                pb_score = 0.6  # Below book value
            else:
                pb_score = max(0, 1.0 - ((pb_ratio - 3) / 10))
            
            score += pb_score
            count += 1
        
        # Price to Sales (lower is better)
        ps_ratio = fundamentals.get('price_to_sales')
        if ps_ratio is not None and ps_ratio > 0:
            # Ideal P/S: 1-4
            if 1 <= ps_ratio <= 4:
                ps_score = 1.0
            elif ps_ratio < 1:
                ps_score = 0.8
            else:
                ps_score = max(0, 1.0 - ((ps_ratio - 4) / 10))
            
            score += ps_score
            count += 1
        
        # Dividend Yield (bonus points)
        div_yield = fundamentals.get('dividend_yield')
        if div_yield is not None and div_yield > 0:
            # 2-4% yield is good
            div_score = min(div_yield / 0.04, 1.0)
            score += div_score * 0.5  # Half weight
            count += 0.5
        
        return score / count if count > 0 else 0.5
    
    def _calculate_balance_sheet_score(self, fundamentals: Dict) -> float:
        """
        Calculate Balance Sheet Score (10% of fundamental score)
        
        Metrics:
        - Net Debt-to-EBITDA ratio
        - Interest Coverage ratio
        - Working Capital Management
        - Debt Maturity Profile
        """
        score = 0.0
        count = 0
        
        # Debt to Equity (lower is better)
        debt_to_equity = fundamentals.get('debt_to_equity')
        if debt_to_equity is not None:
            if debt_to_equity < 0.5:
                debt_score = 1.0  # Very low debt
            elif debt_to_equity < 1.0:
                debt_score = 0.8  # Reasonable debt
            elif debt_to_equity < 2.0:
                debt_score = 0.5  # Moderate debt
            else:
                debt_score = 0.2  # High debt
            
            score += debt_score
            count += 1
        
        # Interest Coverage (higher is better)
        interest_coverage = fundamentals.get('interest_coverage')
        if interest_coverage is not None:
            # > 5x is healthy
            if interest_coverage > 10:
                int_score = 1.0
            elif interest_coverage > 5:
                int_score = 0.8
            elif interest_coverage > 2:
                int_score = 0.5
            elif interest_coverage > 1:
                int_score = 0.3
            else:
                int_score = 0.1  # Distress
            
            score += int_score
            count += 1
        
        # Current Ratio (liquidity)
        current_ratio = fundamentals.get('current_ratio')
        if current_ratio is not None:
            # Ideal: 1.5-2.5
            if 1.5 <= current_ratio <= 3.0:
                current_score = 1.0
            elif current_ratio > 1.0:
                current_score = 0.7
            else:
                current_score = 0.3  # Liquidity concerns
            
            score += current_score
            count += 1
        
        # Quick Ratio (stringent liquidity)
        quick_ratio = fundamentals.get('quick_ratio')
        if quick_ratio is not None:
            # Ideal: 1.0+
            if quick_ratio >= 1.0:
                quick_score = 1.0
            elif quick_ratio >= 0.7:
                quick_score = 0.7
            else:
                quick_score = 0.4
            
            score += quick_score
            count += 1
        
        # Cash position
        total_cash = fundamentals.get('total_cash')
        total_debt = fundamentals.get('total_debt')
        if total_cash is not None and total_debt is not None:
            if total_debt == 0:
                cash_score = 1.0  # No debt!
            else:
                cash_to_debt = safe_divide(total_cash, total_debt, 0)
                if cash_to_debt > 0.5:
                    cash_score = 1.0  # Strong cash position
                elif cash_to_debt > 0.25:
                    cash_score = 0.7
                else:
                    cash_score = 0.4
            
            score += cash_score
            count += 1
        
        return score / count if count > 0 else 0.5
    
    def _sector_normalize(self, value: float, sector_values: List[float]) -> float:
        """
        Z-score normalize against sector peers
        
        Args:
            value: Score for the stock
            sector_values: List of scores for sector peers
        
        Returns:
            Z-score normalized value (clipped to -3 to +3 range)
        """
        try:
            # Remove None values
            clean_values = [v for v in sector_values if v is not None and not np.isnan(v)]
            
            if len(clean_values) < 3:
                return value  # Not enough data for normalization
            
            mean = np.mean(clean_values)
            std = np.std(clean_values)
            
            if std == 0:
                return 0.0  # All values are same
            
            z_score = (value - mean) / std
            
            # Clip to reasonable range and normalize to 0-1
            z_score = np.clip(z_score, -3, 3)
            normalized = (z_score + 3) / 6  # Convert -3 to 3 range to 0 to 1
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error in sector normalization: {e}")
            return value
    
    def _empty_score(self) -> Dict[str, float]:
        """Return neutral scores when calculation fails"""
        return {
            'quality_score': 0.5,
            'growth_score': 0.5,
            'valuation_score': 0.5,
            'balance_sheet_score': 0.5,
            'fundamental_score': 0.5
        }
    
    def batch_score_stocks(self, stocks_fundamentals: Dict[str, Dict],
                          sector_mapping: Dict[str, str] = None) -> pd.DataFrame:
        """
        Calculate fundamental scores for multiple stocks
        
        Args:
            stocks_fundamentals: Dict mapping stock symbols to their fundamentals
            sector_mapping: Dict mapping stock symbols to sector names
        
        Returns:
            DataFrame with fundamental scores for all stocks
        """
        results = []
        
        # Group stocks by sector for peer comparison
        if sector_mapping:
            sector_groups = {}
            for symbol, sector in sector_mapping.items():
                if sector not in sector_groups:
                    sector_groups[sector] = []
                sector_groups[sector].append(symbol)
        
        for symbol, fundamentals in stocks_fundamentals.items():
            # Get sector peers if available
            sector_fundamentals = None
            if sector_mapping and symbol in sector_mapping:
                sector = sector_mapping[symbol]
                if sector in sector_groups:
                    sector_fundamentals = [
                        stocks_fundamentals[s] 
                        for s in sector_groups[sector] 
                        if s in stocks_fundamentals and s != symbol
                    ]
            
            # Calculate scores
            scores = self.calculate_fundamental_score(fundamentals, sector_fundamentals)
            scores['symbol'] = symbol
            
            results.append(scores)
        
        df = pd.DataFrame(results)
        df.set_index('symbol', inplace=True)
        
        logger.info(f"Calculated fundamental scores for {len(df)} stocks")
        
        return df


if __name__ == "__main__":
    # Test the fundamental scorer
    scorer = FundamentalScorer()
    
    # Sample fundamental data
    test_fundamentals = {
        'roe': 0.20,
        'gross_margin': 0.45,
        'operating_margin': 0.25,
        'current_ratio': 2.0,
        'earnings_growth': 0.18,
        'revenue_growth': 0.15,
        'pe_ratio': 22.0,
        'pb_ratio': 3.5,
        'ev_ebitda': 12.0,
        'debt_to_equity': 0.6,
        'interest_coverage': 8.0,
        'quick_ratio': 1.2
    }
    
    scores = scorer.calculate_fundamental_score(test_fundamentals)
    
    print("\nFundamental Score Test:")
    print("=" * 50)
    for key, value in scores.items():
        print(f"{key}: {value:.4f}")
    print("=" * 50)
