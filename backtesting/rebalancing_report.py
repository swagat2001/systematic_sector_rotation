"""
Monthly Rebalancing Report Generator
=====================================

Generates detailed reports showing:
- Which sectors were selected each month
- Which stocks were picked in each sector
- Why sectors/stocks were chosen (momentum, scores, etc.)
- Entry/exit trades for each rebalancing
"""

import pandas as pd
from typing import Dict, List
from datetime import datetime


def generate_monthly_rebalancing_report(backtest_result: Dict) -> str:
    """
    Generate comprehensive monthly rebalancing report
    
    Args:
        backtest_result: Results from backtest including portfolio_snapshots
    
    Returns:
        Formatted report string
    """
    
    snapshots = backtest_result.get('portfolio_snapshots', [])
    
    if not snapshots:
        return "No rebalancing data available"
    
    report = "\n" + "=" * 100 + "\n"
    report += "MONTHLY REBALANCING REPORT - SECTOR & STOCK ROTATION\n"
    report += "=" * 100 + "\n\n"
    
    report += "This report shows how the portfolio was rebalanced each month:\n"
    report += "• Which sectors were selected (Top 3 by momentum)\n"
    report += "• Which stocks were picked from each sector (Top 5 per sector)\n"
    report += "• Which satellite stocks were added (Top 15 by composite score)\n"
    report += "• Entry and exit trades\n\n"
    
    report += "=" * 100 + "\n\n"
    
    for i, snapshot in enumerate(snapshots, 1):
        date = snapshot.get('date', 'Unknown')
        
        report += f"REBALANCE #{i} - {date}\n"
        report += "-" * 100 + "\n\n"
        
        # Portfolio value
        portfolio_value = snapshot.get('portfolio_value', 0)
        cash = snapshot.get('cash', 0)
        report += f"Portfolio Value: ₹{portfolio_value:,.2f} | Cash: ₹{cash:,.2f}\n\n"
        
        # Core allocation (Sector Rotation - 60%)
        core_allocation = snapshot.get('core_allocation', {})
        if core_allocation:
            report += "CORE ALLOCATION (60% - Sector Rotation):\n"
            report += "-" * 50 + "\n\n"
            
            selected_sectors = core_allocation.get('selected_sectors', [])
            if selected_sectors:
                report += f"Selected Sectors ({len(selected_sectors)}): {', '.join(selected_sectors)}\n\n"
                
                # Stocks by sector
                stocks_by_sector = core_allocation.get('stocks_by_sector', {})
                sector_weights = core_allocation.get('sector_weights', {})
                
                for sector in selected_sectors:
                    sector_weight = sector_weights.get(sector, 0) * 100
                    report += f"  {sector} (Weight: {sector_weight:.1f}%):\n"
                    
                    stocks = stocks_by_sector.get(sector, [])
                    for stock_info in stocks:
                        if isinstance(stock_info, dict):
                            symbol = stock_info.get('symbol', 'Unknown')
                            weight = stock_info.get('weight', 0) * 100
                            score = stock_info.get('score', 0)
                            report += f"    • {symbol:15s} - Weight: {weight:.2f}% | Score: {score:.3f}\n"
                        else:
                            report += f"    • {stock_info}\n"
                    
                    report += "\n"
        
        # Satellite allocation (Stock Selection - 40%)
        satellite_allocation = snapshot.get('satellite_allocation', {})
        if satellite_allocation:
            report += "SATELLITE ALLOCATION (40% - Multi-Factor Stock Selection):\n"
            report += "-" * 50 + "\n\n"
            
            selected_stocks = satellite_allocation.get('selected_stocks', [])
            if selected_stocks:
                report += f"Selected Stocks ({len(selected_stocks)}):\n\n"
                
                for stock_info in selected_stocks:
                    if isinstance(stock_info, dict):
                        symbol = stock_info.get('symbol', 'Unknown')
                        weight = stock_info.get('weight', 0) * 100
                        score = stock_info.get('composite_score', 0)
                        sector = stock_info.get('sector', 'Unknown')
                        report += f"  • {symbol:15s} - Weight: {weight:.2f}% | Score: {score:.3f} | Sector: {sector}\n"
                    else:
                        report += f"  • {stock_info}\n"
                
                report += "\n"
        
        # Trades executed
        trades = snapshot.get('trades', [])
        if trades:
            report += "TRADES EXECUTED:\n"
            report += "-" * 50 + "\n\n"
            
            buy_trades = [t for t in trades if t.get('action') == 'BUY']
            sell_trades = [t for t in trades if t.get('action') == 'SELL']
            
            if buy_trades:
                report += f"  BUY Orders ({len(buy_trades)}):\n"
                for trade in buy_trades:
                    symbol = trade.get('symbol', 'Unknown')
                    qty = trade.get('quantity', 0)
                    price = trade.get('price', 0)
                    value = qty * price
                    report += f"    • {symbol:15s} - Qty: {qty:8.2f} @ ₹{price:10.2f} = ₹{value:12,.2f}\n"
                report += "\n"
            
            if sell_trades:
                report += f"  SELL Orders ({len(sell_trades)}):\n"
                for trade in sell_trades:
                    symbol = trade.get('symbol', 'Unknown')
                    qty = trade.get('quantity', 0)
                    price = trade.get('price', 0)
                    value = qty * price
                    report += f"    • {symbol:15s} - Qty: {qty:8.2f} @ ₹{price:10.2f} = ₹{value:12,.2f}\n"
                report += "\n"
            
            total_trades = len(trades)
            report += f"  Total Trades: {total_trades}\n\n"
        
        # Performance since last rebalance (if available)
        monthly_return = snapshot.get('monthly_return')
        if monthly_return is not None:
            report += f"Performance Since Last Rebalance: {monthly_return:.2f}%\n\n"
        
        report += "=" * 100 + "\n\n"
    
    # Summary
    report += "REBALANCING SUMMARY:\n"
    report += "-" * 100 + "\n\n"
    report += f"Total Rebalances: {len(snapshots)}\n"
    report += f"Frequency: Monthly\n"
    report += f"Period: {snapshots[0].get('date', 'N/A')} to {snapshots[-1].get('date', 'N/A')}\n\n"
    
    # Count unique sectors used
    all_sectors = set()
    for snapshot in snapshots:
        core = snapshot.get('core_allocation', {})
        sectors = core.get('selected_sectors', [])
        all_sectors.update(sectors)
    
    report += f"Unique Sectors Used: {len(all_sectors)}\n"
    if all_sectors:
        report += f"Sectors: {', '.join(sorted(all_sectors))}\n\n"
    
    # Total trades
    total_trades = sum(len(s.get('trades', [])) for s in snapshots)
    report += f"Total Trades Executed: {total_trades}\n"
    report += f"Average Trades per Rebalance: {total_trades / len(snapshots):.1f}\n\n"
    
    report += "=" * 100 + "\n"
    
    return report


def generate_sector_rotation_summary(backtest_result: Dict) -> str:
    """
    Generate summary of sector rotation over time
    
    Shows which sectors were in/out of portfolio each month
    """
    
    snapshots = backtest_result.get('portfolio_snapshots', [])
    
    if not snapshots:
        return "No data available"
    
    report = "\n" + "=" * 100 + "\n"
    report += "SECTOR ROTATION HISTORY\n"
    report += "=" * 100 + "\n\n"
    
    # Extract sector selections over time
    sector_history = []
    for snapshot in snapshots:
        date = snapshot.get('date', 'Unknown')
        core = snapshot.get('core_allocation', {})
        sectors = core.get('selected_sectors', [])
        sector_history.append({
            'date': date,
            'sectors': sectors
        })
    
    # Display
    report += f"{'Date':<12} | {'Sector 1':<20} | {'Sector 2':<20} | {'Sector 3':<20}\n"
    report += "-" * 100 + "\n"
    
    for entry in sector_history:
        date = str(entry['date'])[:10]
        sectors = entry['sectors'] + [''] * (3 - len(entry['sectors']))  # Pad to 3
        report += f"{date:<12} | {sectors[0]:<20} | {sectors[1]:<20} | {sectors[2]:<20}\n"
    
    report += "\n" + "=" * 100 + "\n"
    
    return report


def generate_stock_churn_analysis(backtest_result: Dict) -> str:
    """
    Analyze how often stocks enter/exit the portfolio
    """
    
    snapshots = backtest_result.get('portfolio_snapshots', [])
    
    if not snapshots:
        return "No data available"
    
    # Track stock appearances
    stock_appearances = {}
    
    for snapshot in snapshots:
        # Get all stocks in this snapshot
        stocks_in_portfolio = set()
        
        # From core
        core = snapshot.get('core_allocation', {})
        stocks_by_sector = core.get('stocks_by_sector', {})
        for sector_stocks in stocks_by_sector.values():
            for stock_info in sector_stocks:
                if isinstance(stock_info, dict):
                    stocks_in_portfolio.add(stock_info.get('symbol'))
                else:
                    stocks_in_portfolio.add(stock_info)
        
        # From satellite
        satellite = snapshot.get('satellite_allocation', {})
        selected_stocks = satellite.get('selected_stocks', [])
        for stock_info in selected_stocks:
            if isinstance(stock_info, dict):
                stocks_in_portfolio.add(stock_info.get('symbol'))
            else:
                stocks_in_portfolio.add(stock_info)
        
        # Count appearances
        for stock in stocks_in_portfolio:
            stock_appearances[stock] = stock_appearances.get(stock, 0) + 1
    
    # Generate report
    report = "\n" + "=" * 100 + "\n"
    report += "STOCK CHURN ANALYSIS\n"
    report += "=" * 100 + "\n\n"
    
    report += f"Total Rebalances: {len(snapshots)}\n"
    report += f"Unique Stocks Used: {len(stock_appearances)}\n\n"
    
    # Sort by frequency
    sorted_stocks = sorted(stock_appearances.items(), key=lambda x: x[1], reverse=True)
    
    # Top holders (appeared most often)
    report += "TOP 20 HOLDINGS (Most Frequent):\n"
    report += "-" * 50 + "\n"
    for i, (stock, count) in enumerate(sorted_stocks[:20], 1):
        pct = (count / len(snapshots)) * 100
        report += f"{i:3}. {stock:15s} - {count:3} times ({pct:.1f}% of rebalances)\n"
    
    report += "\n" + "=" * 100 + "\n"
    
    return report
