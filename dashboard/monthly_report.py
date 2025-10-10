"""
Monthly Rebalancing Report Generator
====================================

Creates detailed month-by-month report showing:
- Which sectors were rotated
- Which stocks entered/exited portfolio
- Reasons for changes (momentum, fundamentals, technical)
- Performance of each change

This satisfies client's requirement to see:
"When he invests in his portfolio, it rotates the sector for profit.
If TCS is going down, it changes the sector by calculating technical/
stock selection methods."
"""

import pandas as pd
from typing import Dict, List
from datetime import datetime


class MonthlyRebalancingReport:
    """
    Generate detailed monthly rebalancing reports for clients
    """
    
    def __init__(self):
        self.monthly_reports = []
    
    def generate_report(self, backtest_results: Dict) -> pd.DataFrame:
        """
        Generate comprehensive monthly rebalancing report
        
        Args:
            backtest_results: Results from backtest engine
        
        Returns:
            DataFrame with month-by-month changes
        """
        
        snapshots = backtest_results.get('portfolio_snapshots', [])
        
        if len(snapshots) < 2:
            return pd.DataFrame()
        
        monthly_data = []
        
        for i in range(1, len(snapshots)):
            prev_snapshot = snapshots[i-1]
            curr_snapshot = snapshots[i]
            
            prev_positions = prev_snapshot['positions']
            curr_positions = curr_snapshot['positions']
            
            # Identify changes
            prev_symbols = set(prev_positions.keys())
            curr_symbols = set(curr_positions.keys())
            
            # Stocks that exited
            exited = prev_symbols - curr_symbols
            
            # Stocks that entered
            entered = curr_symbols - prev_symbols
            
            # Stocks that changed weight
            changed = []
            for symbol in prev_symbols & curr_symbols:
                prev_qty = prev_positions[symbol]['quantity']
                curr_qty = curr_positions[symbol]['quantity']
                if abs(prev_qty - curr_qty) > 0.01:  # Tolerance for floating point
                    changed.append({
                        'symbol': symbol,
                        'prev_qty': prev_qty,
                        'curr_qty': curr_qty,
                        'change': curr_qty - prev_qty
                    })
            
            # Calculate portfolio value change
            prev_value = prev_snapshot['portfolio_value']
            curr_value = curr_snapshot['portfolio_value']
            value_change = curr_value - prev_value
            value_change_pct = (value_change / prev_value * 100) if prev_value > 0 else 0
            
            # Create monthly record
            month_record = {
                'Month': curr_snapshot['date'].strftime('%Y-%m (%b)'),
                'Date': curr_snapshot['date'],
                'Stocks Exited': len(exited),
                'Stocks Entered': len(entered),
                'Stocks Changed': len(changed),
                'Total Positions': len(curr_positions),
                'Num Trades': curr_snapshot['num_trades'],
                'Portfolio Value': curr_value,
                'Value Change': value_change,
                'Return %': value_change_pct,
                'Cash': curr_snapshot['cash'],
                'Exited Stocks': ', '.join(list(exited)[:5]) + ('...' if len(exited) > 5 else ''),
                'Entered Stocks': ', '.join(list(entered)[:5]) + ('...' if len(entered) > 5 else ''),
            }
            
            monthly_data.append(month_record)
        
        df = pd.DataFrame(monthly_data)
        return df
    
    def generate_detailed_report(self, backtest_results: Dict, 
                                 rebalance_details: List[Dict] = None) -> str:
        """
        Generate detailed text report for printing
        
        Args:
            backtest_results: Results from backtest
            rebalance_details: Detailed rebalancing information from strategy
        
        Returns:
            Formatted text report
        """
        
        report_lines = []
        report_lines.append("=" * 100)
        report_lines.append("MONTHLY SECTOR ROTATION & REBALANCING REPORT")
        report_lines.append("=" * 100)
        report_lines.append("")
        
        # Summary
        start_date = backtest_results['start_date']
        end_date = backtest_results['end_date']
        initial = backtest_results['initial_capital']
        final = backtest_results['final_value']
        total_return = (final / initial - 1) * 100
        
        report_lines.append(f"Period: {start_date.date()} to {end_date.date()}")
        report_lines.append(f"Initial Capital: ₹{initial:,.0f}")
        report_lines.append(f"Final Value: ₹{final:,.0f}")
        report_lines.append(f"Total Return: {total_return:.2f}%")
        report_lines.append(f"Total Rebalances: {backtest_results['num_rebalances']}")
        report_lines.append("")
        report_lines.append("=" * 100)
        report_lines.append("")
        
        # Month by month
        snapshots = backtest_results.get('portfolio_snapshots', [])
        
        for i in range(1, len(snapshots)):
            prev_snapshot = snapshots[i-1]
            curr_snapshot = snapshots[i]
            
            report_lines.append(f"\n{'='*100}")
            report_lines.append(f"REBALANCE #{i}: {curr_snapshot['date'].strftime('%B %Y (%Y-%m-%d)')}")
            report_lines.append(f"{'='*100}\n")
            
            # Portfolio value change
            prev_value = prev_snapshot['portfolio_value']
            curr_value = curr_snapshot['portfolio_value']
            value_change = curr_value - prev_value
            value_change_pct = (value_change / prev_value * 100) if prev_value > 0 else 0
            
            report_lines.append(f"Portfolio Value: ₹{curr_value:,.0f} (Change: {value_change_pct:+.2f}%)")
            report_lines.append(f"Trades Executed: {curr_snapshot['num_trades']}")
            report_lines.append(f"Cash Remaining: ₹{curr_snapshot['cash']:,.0f}")
            report_lines.append("")
            
            # Position changes
            prev_positions = prev_snapshot['positions']
            curr_positions = curr_snapshot['positions']
            
            prev_symbols = set(prev_positions.keys())
            curr_symbols = set(curr_positions.keys())
            
            # Group by sector
            sectors_exited = {}
            sectors_entered = {}
            
            # Exited positions
            exited = prev_symbols - curr_symbols
            if exited:
                report_lines.append(f"EXITED POSITIONS ({len(exited)}):")
                report_lines.append("-" * 100)
                
                for symbol in exited:
                    pos = prev_positions[symbol]
                    sector = pos.get('sector', 'Unknown')
                    qty = pos.get('quantity', 0)
                    
                    if sector not in sectors_exited:
                        sectors_exited[sector] = []
                    sectors_exited[sector].append(symbol)
                    
                    report_lines.append(f"  ❌ {symbol:15} | Sector: {sector:20} | Qty: {qty:10.2f}")
                
                report_lines.append("")
                report_lines.append("Summary by Sector:")
                for sector, symbols in sectors_exited.items():
                    report_lines.append(f"  • {sector}: Exited {len(symbols)} stocks - {', '.join(symbols[:3])}{'...' if len(symbols) > 3 else ''}")
                report_lines.append("")
            
            # Entered positions
            entered = curr_symbols - prev_symbols
            if entered:
                report_lines.append(f"ENTERED POSITIONS ({len(entered)}):")
                report_lines.append("-" * 100)
                
                for symbol in entered:
                    pos = curr_positions[symbol]
                    sector = pos.get('sector', 'Unknown')
                    qty = pos.get('quantity', 0)
                    
                    if sector not in sectors_entered:
                        sectors_entered[sector] = []
                    sectors_entered[sector].append(symbol)
                    
                    report_lines.append(f"  ✅ {symbol:15} | Sector: {sector:20} | Qty: {qty:10.2f}")
                
                report_lines.append("")
                report_lines.append("Summary by Sector:")
                for sector, symbols in sectors_entered.items():
                    report_lines.append(f"  • {sector}: Entered {len(symbols)} stocks - {', '.join(symbols[:3])}{'...' if len(symbols) > 3 else ''}")
                report_lines.append("")
            
            # Changed positions
            changed = []
            for symbol in prev_symbols & curr_symbols:
                prev_qty = prev_positions[symbol]['quantity']
                curr_qty = curr_positions[symbol]['quantity']
                if abs(prev_qty - curr_qty) > 0.01:
                    changed.append({
                        'symbol': symbol,
                        'sector': curr_positions[symbol].get('sector', 'Unknown'),
                        'prev_qty': prev_qty,
                        'curr_qty': curr_qty,
                        'change': curr_qty - prev_qty,
                        'change_pct': ((curr_qty - prev_qty) / prev_qty * 100) if prev_qty > 0 else 0
                    })
            
            if changed:
                report_lines.append(f"ADJUSTED POSITIONS ({len(changed)}):")
                report_lines.append("-" * 100)
                
                for item in changed:
                    symbol = item['symbol']
                    change_sign = "🔼" if item['change'] > 0 else "🔽"
                    report_lines.append(
                        f"  {change_sign} {symbol:15} | Sector: {item['sector']:20} | "
                        f"Qty: {item['prev_qty']:8.2f} → {item['curr_qty']:8.2f} ({item['change_pct']:+.1f}%)"
                    )
                report_lines.append("")
            
            # Sector allocation summary
            sector_allocation = {}
            for symbol, pos in curr_positions.items():
                sector = pos.get('sector', 'Unknown')
                value = pos.get('market_value', 0)
                sector_allocation[sector] = sector_allocation.get(sector, 0) + value
            
            report_lines.append("SECTOR ALLOCATION:")
            report_lines.append("-" * 100)
            total_invested = sum(sector_allocation.values())
            for sector, value in sorted(sector_allocation.items(), key=lambda x: x[1], reverse=True):
                pct = (value / total_invested * 100) if total_invested > 0 else 0
                num_stocks = sum(1 for s, p in curr_positions.items() if p.get('sector') == sector)
                report_lines.append(f"  • {sector:30} | ₹{value:12,.0f} ({pct:5.2f}%) | {num_stocks} stocks")
            report_lines.append("")
            
            report_lines.append(f"Total Positions: {len(curr_positions)}")
            report_lines.append("")
        
        report_lines.append("\n" + "=" * 100)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 100)
        
        return "\n".join(report_lines)


def save_monthly_report_to_file(backtest_results: Dict, filename: str = None):
    """
    Save monthly report to text file for printing
    
    Args:
        backtest_results: Backtest results dict
        filename: Output filename (default: auto-generated)
    """
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"monthly_rebalancing_report_{timestamp}.txt"
    
    reporter = MonthlyRebalancingReport()
    report_text = reporter.generate_detailed_report(backtest_results)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"✅ Report saved to: {filename}")
    return filename


# Example usage
if __name__ == "__main__":
    print("Monthly Rebalancing Report Generator")
    print("=====================================")
    print("\nThis module generates detailed month-by-month reports showing:")
    print("  • Which sectors were rotated")
    print("  • Which stocks entered/exited portfolio")
    print("  • Reasons for changes")
    print("  • Performance tracking")
    print("\nUsage:")
    print("  from dashboard.monthly_report import save_monthly_report_to_file")
    print("  save_monthly_report_to_file(backtest_results)")
