# 🏗️ PROJECT ARCHITECTURE & FILE STRUCTURE

## System Overview

```
Systematic Sector Rotation Strategy
│
├─── DATA LAYER (Storage & Retrieval)
│    │
│    ├─── NSE_sector_wise_data/
│    │    ├── nse_data.db (SQLite: stocks, prices, fundamentals)
│    │    └── nse_csv_loader.py (Import CSV or generate sample data)
│    │
│    └─── data/
│         ├── nse_data_bridge.py (Connects NSE DB to backtest)
│         └── data_storage.py (Main DB for strategy metadata)
│
├─── STRATEGY LAYER (Investment Logic)
│    │
│    ├─── scoring/
│    │    ├── fundamental_scorer.py (45% weight: ROE, P/E, margins)
│    │    ├── technical_scorer.py (35% weight: momentum, trends)
│    │    ├── statistical_scorer.py (20% weight: Sharpe, beta)
│    │    └── composite_scorer.py (Combines all scores via Z-score)
│    │
│    └─── strategy/
│         ├── sector_rotation.py (60% allocation: top-3 sectors)
│         ├── stock_selection.py (40% allocation: top decile)
│         └── portfolio_manager.py (Orchestrates rebalancing)
│
├─── EXECUTION LAYER (Trade Simulation)
│    │
│    └─── execution/
│         ├── paper_trading.py (Simulates trades with costs)
│         └── order_manager.py (Manages order lifecycle)
│
├─── BACKTESTING LAYER (Historical Testing)
│    │
│    └─── backtesting/
│         ├── backtest_engine.py (Walk-forward simulation)
│         └── performance_analyzer.py (20+ metrics)
│
└─── PRESENTATION LAYER (User Interface)
     │
     └─── dashboard/
          ├── streamlit_app.py (Main app & navigation)
          ├── real_data_backtest.py (Backtest page with real data)
          └── chart_generator.py (All visualizations)
```

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERACTION                            │
│                   (Streamlit Dashboard)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REAL DATA BACKTEST PAGE                       │
│  • Date range selection                                          │
│  • Initial capital input                                         │
│  • Triggers backtest                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      NSE DATA BRIDGE                             │
│  nse_data_bridge.py                                              │
│  • Connects to NSE_sector_wise_data/nse_data.db                 │
│  • Loads stocks by sector                                        │
│  • Retrieves OHLCV data for date range                          │
│  • Creates sector indices from stock averages                   │
│  • Returns: sector_prices, stocks_data, stocks_prices           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKTEST ENGINE                               │
│  backtest_engine.py                                              │
│  • Generates monthly rebalance dates                             │
│  • Loop through each month:                                      │
│    1. Slice data to rebalance date                              │
│    2. Call Portfolio Manager                                     │
│    3. Execute trades via Paper Trading                          │
│    4. Calculate daily portfolio values                          │
│  • Returns: equity_curve, portfolio_snapshots, metrics          │
└─────────────────────────────────────────────────────────────────┘
            │                                   │
            ▼                                   ▼
┌─────────────────────────┐     ┌──────────────────────────────┐
│   PORTFOLIO MANAGER      │     │   PAPER TRADING ENGINE       │
│  portfolio_manager.py    │     │  paper_trading.py            │
│                          │     │                              │
│  Calls:                  │     │  • Tracks positions          │
│  ├─ Sector Rotation     │     │  • Calculates costs          │
│  └─ Stock Selection     │     │  • Updates cash              │
│                          │     │  • Returns executed trades   │
│  Returns target weights  │     └──────────────────────────────┘
└─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SECTOR ROTATION                                 │
│  sector_rotation.py                                              │
│  • Calculates 6-month momentum for all sectors                  │
│  • Ranks sectors                                                 │
│  • Selects top-3                                                 │
│  • Allocates 20% each (60% total)                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  STOCK SELECTION                                 │
│  stock_selection.py                                              │
│  • Calls Composite Scorer for all stocks                        │
│  • Filters by Sharpe > 0, Trend >= 0.5                         │
│  • Selects top 10% (decile)                                     │
│  • Applies risk-adjusted weighting                              │
│  • Allocates 40% total                                          │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  COMPOSITE SCORER                                │
│  composite_scorer.py                                             │
│  Combines:                                                       │
│  ├─ Fundamental Score (45%) ─► fundamental_scorer.py           │
│  ├─ Technical Score (35%) ───► technical_scorer.py             │
│  └─ Statistical Score (20%) ─► statistical_scorer.py           │
│  Returns: Z-score normalized composite score                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PERFORMANCE ANALYZER                             │
│  performance_analyzer.py                                         │
│  • Calculates 20+ metrics                                       │
│  • Returns, risk, drawdown, ratios                              │
│  • Trade statistics                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CHART GENERATOR                                │
│  chart_generator.py                                              │
│  • Equity curve                                                  │
│  • Drawdown chart                                                │
│  • Monthly returns heatmap                                       │
│  • All visualizations                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DISPLAY RESULTS                               │
│  • Performance metrics                                           │
│  • Interactive charts                                            │
│  • Portfolio positions                                           │
│  • Export capability                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Connections & Purpose

### Core Files (Essential)

| File | Connects To | Purpose |
|------|-------------|---------|
| **config.py** | All modules | Central configuration (allocations, limits, parameters) |
| **utils/logger.py** | All modules | Logging across entire system |
| **utils/helpers.py** | All modules | Common utility functions |

### Data Layer

| File | Connects To | Purpose |
|------|-------------|---------|
| **NSE_sector_wise_data/nse_data.db** | nse_data_bridge.py | SQLite database with all stock/sector data |
| **NSE_sector_wise_data/nse_csv_loader.py** | nse_data.db | Imports CSV or generates sample data |
| **data/nse_data_bridge.py** | nse_data.db, backtest_engine.py | Loads data from DB and formats for backtest |
| **data/data_storage.py** | Strategy modules | Main database for strategy metadata (optional) |

### Strategy Layer

| File | Connects To | Purpose |
|------|-------------|---------|
| **scoring/fundamental_scorer.py** | composite_scorer.py | Scores stocks on fundamentals (ROE, P/E, etc.) |
| **scoring/technical_scorer.py** | composite_scorer.py | Scores stocks on technicals (momentum, trends) |
| **scoring/statistical_scorer.py** | composite_scorer.py | Scores stocks on statistics (Sharpe, beta) |
| **scoring/composite_scorer.py** | stock_selection.py | Combines all scores into Z-score |
| **strategy/sector_rotation.py** | portfolio_manager.py | Selects top-3 sectors (60% allocation) |
| **strategy/stock_selection.py** | portfolio_manager.py | Selects top stocks (40% allocation) |
| **strategy/portfolio_manager.py** | backtest_engine.py | Orchestrates full rebalancing logic |

### Execution Layer

| File | Connects To | Purpose |
|------|-------------|---------|
| **execution/paper_trading.py** | backtest_engine.py | Simulates trade execution with costs |
| **execution/order_manager.py** | paper_trading.py | Manages order lifecycle |

### Backtesting Layer

| File | Connects To | Purpose |
|------|-------------|---------|
| **backtesting/backtest_engine.py** | real_data_backtest.py, portfolio_manager.py, paper_trading.py | Walk-forward simulation engine |
| **backtesting/performance_analyzer.py** | real_data_backtest.py | Calculates all performance metrics |

### Dashboard Layer

| File | Connects To | Purpose |
|------|-------------|---------|
| **dashboard/streamlit_app.py** | real_data_backtest.py, chart_generator.py | Main app with navigation |
| **dashboard/real_data_backtest.py** | nse_data_bridge.py, backtest_engine.py, performance_analyzer.py, chart_generator.py | Backtest page with real NSE data |
| **dashboard/chart_generator.py** | All dashboard pages | Creates all Plotly visualizations |

---

## Execution Flow Example

### When User Clicks "Run Backtest":

```
1. real_data_backtest.py
   └─► Calls: nse_data_bridge.prepare_backtest_data(start, end)
       └─► Queries: NSE_sector_wise_data/nse_data.db
           └─► Returns: sector_prices, stocks_data, stocks_prices

2. real_data_backtest.py
   └─► Calls: backtest_engine.run_backtest(data)
       └─► Loop: For each month
           ├─► Calls: portfolio_manager.rebalance_portfolio()
           │   ├─► Calls: sector_rotation.select_sectors()
           │   │   └─► Returns: top 3 sectors with 20% each
           │   └─► Calls: stock_selection.select_stocks()
           │       ├─► Calls: composite_scorer.score_stocks()
           │       │   ├─► fundamental_scorer (45% weight)
           │       │   ├─► technical_scorer (35% weight)
           │       │   └─► statistical_scorer (20% weight)
           │       └─► Returns: top stocks with weights
           └─► Calls: paper_trading.rebalance_portfolio()
               └─► Executes trades, applies costs
       └─► Returns: equity_curve, portfolio_snapshots

3. real_data_backtest.py
   └─► Calls: performance_analyzer.analyze(result)
       └─► Returns: returns, risk, drawdown metrics

4. real_data_backtest.py
   └─► Calls: chart_generator.create_equity_curve(data)
       └─► Returns: Plotly figure

5. Display all results in UI
```

---

## Database Schema

### NSE_sector_wise_data/nse_data.db

```sql
-- Stocks table
stocks (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(50) UNIQUE,
    name VARCHAR(200),
    sector VARCHAR(100),
    market_cap FLOAT
)

-- Stock prices table
stock_prices (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(50),
    date DATE,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume FLOAT
)
```

---

## Configuration Flow

**config.py** sets all parameters:
- SECTOR_ALLOCATION = 0.60 (60%)
- STOCK_ALLOCATION = 0.40 (40%)
- TOP_SECTORS = 3
- TOP_PERCENTILE = 0.10 (top 10%)
- MAX_POSITION_SIZE = 0.05 (5%)
- Transaction costs, rebalancing frequency, etc.

All modules import and use these settings.

---

## Key Design Patterns

1. **Layered Architecture**: Clear separation (Data → Strategy → Execution → Analysis → UI)
2. **Dependency Injection**: Modules receive data/dependencies, don't fetch directly
3. **Single Responsibility**: Each file has one clear purpose
4. **Bridge Pattern**: nse_data_bridge.py decouples data source from strategy
5. **Strategy Pattern**: Different scorers implement same interface
6. **Observer Pattern**: Backtest engine tracks portfolio changes

---

## Critical Dependencies

```
streamlit_app.py
    ├── real_data_backtest.py
    │   ├── nse_data_bridge.py
    │   │   └── nse_data.db
    │   ├── backtest_engine.py
    │   │   ├── portfolio_manager.py
    │   │   │   ├── sector_rotation.py
    │   │   │   └── stock_selection.py
    │   │   │       └── composite_scorer.py
    │   │   │           ├── fundamental_scorer.py
    │   │   │           ├── technical_scorer.py
    │   │   │           └── statistical_scorer.py
    │   │   └── paper_trading.py
    │   ├── performance_analyzer.py
    │   └── chart_generator.py
    └── config.py, logger.py, helpers.py (used by all)
```

---

## Module Interaction Matrix

| Module | Imports From | Imported By | Data Flow |
|--------|--------------|-------------|-----------|
| config.py | None | All | Parameters → |
| nse_data_bridge.py | nse_data.db | real_data_backtest.py | DB → Market Data → |
| backtest_engine.py | portfolio_manager, paper_trading | real_data_backtest.py | Data → Simulation → Results |
| portfolio_manager.py | sector_rotation, stock_selection | backtest_engine.py | Data → Target Weights → |
| composite_scorer.py | fundamental/technical/statistical | stock_selection.py | Prices → Scores → |
| performance_analyzer.py | None | real_data_backtest.py | Results → Metrics → |
| chart_generator.py | None | All dashboard pages | Data → Visualizations → |

---

This architecture ensures:
- Clean separation of concerns
- Easy testing and maintenance
- Scalability (can add more scorers, strategies)
- Data source independence (swap NSE DB for any other)
- Production-ready structure
