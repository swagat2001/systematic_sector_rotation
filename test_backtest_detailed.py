"""
Test backtest with detailed logging to see where trades fail
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta
from data.nse_data_bridge import NSEDataBridge
from backtesting.backtest_engine import BacktestEngine

print("\n" + "="*80)
print("BACKTEST EXECUTION TEST WITH DETAILED LOGGING")
print("="*80 + "\n")

# Load data
bridge = NSEDataBridge()
min_date, max_date = bridge.get_date_range()

start_date = max_date - timedelta(days=365)
end_date = max_date

print(f"Loading data: {start_date.date()} to {end_date.date()}")

sector_prices, stocks_data, stocks_prices = bridge.prepare_backtest_data(
    start_date=start_date,
    end_date=end_date
)

print(f"Data loaded: {len(sector_prices)} sectors, {len(stocks_data)} stocks\n")

# Run backtest with logging
engine = BacktestEngine(
    initial_capital=1000000,
    start_date=start_date,
    end_date=end_date
)

print("Running backtest...\n")

result = engine.run_backtest(
    sector_prices=sector_prices,
    stocks_data=stocks_data,
    stocks_prices=stocks_prices
)

print("\n" + "="*80)
print("BACKTEST RESULTS")
print("="*80)
print(f"Success: {result['success']}")
print(f"Initial: ₹{result['initial_capital']:,.0f}")
print(f"Final: ₹{result['final_value']:,.0f}")
print(f"Rebalances attempted: {result['num_rebalances']}")
print(f"Equity curve points: {len(result['equity_curve'])}")
print(f"Portfolio snapshots: {len(result['portfolio_snapshots'])}")

if result['final_portfolio']:
    print(f"\nFinal portfolio:")
    print(f"  Cash: ₹{result['final_portfolio'].get('cash', 0):,.0f}")
    print(f"  Positions: {len(result['final_portfolio'].get('positions', {}))}")
    
    if result['final_portfolio'].get('positions'):
        print(f"  Holdings:")
        for symbol, pos in list(result['final_portfolio']['positions'].items())[:5]:
            print(f"    {symbol}: {pos.get('shares', 0)} shares @ ₹{pos.get('price', 0):.2f}")

print("\n" + "="*80)

# Check the log file for details
log_file = Path(__file__).parent / "logs" / "strategy.log"
if log_file.exists():
    print("\nLast 50 lines of log file:")
    print("="*80)
    with open(log_file, 'r') as f:
        lines = f.readlines()
        for line in lines[-50:]:
            print(line.rstrip())

bridge.close()
