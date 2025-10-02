# 📈 Systematic Sector Rotation Strategy

A quantitative investment strategy for the Indian equity market combining momentum-based sector rotation with multi-factor stock selection. Built with 100% open-source tools.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)

---

## 🎯 Strategy Overview

**Systematic Sector Rotation** is a dual-strategy quantitative approach that:
- Invests **60%** in top-performing sectors based on momentum
- Invests **40%** in top-rated stocks using multi-factor scoring
- Rebalances monthly with systematic discipline
- Includes comprehensive risk management

### Key Features

✅ **Momentum-Based Sector Selection**
- Ranks NIFTY sectoral indices by 6-month momentum
- Selects top-3 sectors
- Equal weight allocation (20% each)

✅ **Multi-Factor Stock Selection**
- Composite Z-score from 30+ metrics
- Fundamental, Technical, and Statistical analysis
- Top decile selection (10% of universe)
- Liquidity and quality filters

✅ **Risk Management**
- Maximum 5% per position
- Maximum 25% per sector
- Volatility control and beta penalties
- 2-month hysteresis to reduce turnover

✅ **Complete Backtesting**
- Walk-forward simulation
- Transaction cost modeling
- 20+ performance metrics
- Benchmark comparison

✅ **Interactive Dashboard**
- Real-time visualization
- Performance analytics
- Portfolio monitoring
- Export capabilities

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Strategy Details](#-strategy-details)
- [Architecture](#-architecture)
- [Performance Metrics](#-performance-metrics)
- [Dashboard](#-dashboard)
- [Data Sources](#-data-sources)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/systematic_sector_rotation.git
cd systematic_sector_rotation
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

### 5. Run a Backtest

```python
from backtesting.backtest_engine import BacktestEngine
from backtesting.performance_analyzer import PerformanceAnalyzer
from datetime import datetime

# Initialize
engine = BacktestEngine(
    initial_capital=1000000,
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2023, 12, 31)
)

# Run backtest (with your data)
result = engine.run_backtest(
    sector_prices=sector_data,
    stocks_data=fundamentals,
    stocks_prices=price_data
)

# Analyze
analyzer = PerformanceAnalyzer()
analysis = analyzer.analyze(result)

print(analyzer.generate_performance_report(analysis))
```

---

## 💻 Installation

### Requirements

- Python 3.11 or higher
- pip package manager
- 4GB RAM minimum
- Internet connection (for data download)

### Step-by-Step Installation

1. **Install Python 3.11+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify: `python --version`

2. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/systematic_sector_rotation.git
   cd systematic_sector_rotation
   ```

3. **Create Virtual Environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

4. **Install Packages**
   ```bash
   pip install -r requirements.txt
   ```

### Required Packages

```
pandas>=2.0.0
numpy>=1.24.0
yfinance>=0.2.28
sqlalchemy>=2.0.0
streamlit>=1.28.0
plotly>=5.17.0
python-dateutil>=2.8.2
requests>=2.31.0
```

---

## 📖 Usage

### Running Tests

```bash
# Test all phases
python tests/test_phase1.py
python tests/test_phase2.py
python tests/test_phase3.py
python tests/test_phase4.py
python tests/test_phase5.py
```

### Loading Your Data

If you have pre-downloaded stock data:

```bash
# See DATA_LOADING_GUIDE.md for detailed instructions
python data/load_your_data.py --folder data/your_data
```

### Running Strategy Components

#### 1. Sector Rotation

```python
from strategy.sector_rotation import SectorRotationEngine

engine = SectorRotationEngine()
result = engine.rebalance_sectors(sector_prices_dict)

if result['success']:
    print(f"Selected sectors: {result['selected_sectors']}")
    print(f"Weights: {result['weights']}")
```

#### 2. Stock Selection

```python
from strategy.stock_selection import StockSelectionEngine

engine = StockSelectionEngine()
result = engine.select_stocks(
    stocks_fundamentals,
    stocks_prices,
    benchmark_data,
    sector_mapping
)

if result['success']:
    print(f"Selected {result['num_stocks']} stocks")
    print(f"Average Z-score: {result['avg_score']:.4f}")
```

#### 3. Portfolio Management

```python
from strategy.portfolio_manager import PortfolioManager

manager = PortfolioManager()
result = manager.rebalance_portfolio(
    sector_prices,
    stocks_data,
    stocks_prices,
    benchmark_data,
    sector_mapping
)

print(manager.generate_portfolio_report(result))
```

#### 4. Paper Trading

```python
from execution.paper_trading import PaperTradingEngine

engine = PaperTradingEngine(initial_capital=1000000)

# Execute trades
engine.rebalance_portfolio(target_weights, current_prices)

# View performance
print(engine.generate_performance_report(current_prices))
```

#### 5. Backtesting

```python
from backtesting.backtest_engine import BacktestEngine
from backtesting.performance_analyzer import PerformanceAnalyzer

# Run backtest
engine = BacktestEngine(initial_capital=1000000)
result = engine.run_backtest(sectors, fundamentals, stocks, benchmark)

# Analyze
analyzer = PerformanceAnalyzer()
analysis = analyzer.analyze(result, benchmark_returns)

# Generate report
print(analyzer.generate_performance_report(analysis))
```

---

## 🎓 Strategy Details

### Portfolio Allocation

```
Total Portfolio (100%)
├── Core Allocation (60%)
│   ├── Sector 1: 20%
│   ├── Sector 2: 20%
│   └── Sector 3: 20%
└── Satellite Allocation (40%)
    ├── Stock 1: Weight based on Z+/σ
    ├── Stock 2: Weight based on Z+/σ
    ├── ...
    └── Stock N: Weight based on Z+/σ
```

### Sector Rotation Logic

**Monthly Process:**
1. Calculate 6-month momentum for all NIFTY sectors
2. Use 1-month momentum as tiebreaker
3. Apply 200-day MA filter (optional)
4. Select top-3 sectors
5. Equal weight allocation (20% each)

**Momentum Calculation:**
```
Momentum = (Current Price / Price 6 Months Ago) - 1
```

### Stock Selection Process

**Multi-Factor Scoring:**

1. **Fundamental Score (45% weight)**
   - Quality (35%): ROE, margins, profitability
   - Growth (35%): Revenue & earnings growth
   - Valuation (20%): P/E, P/B, EV/EBITDA
   - Balance Sheet (10%): Debt ratios, liquidity

2. **Technical Score (35% weight)**
   - Momentum (50%): 6M & 12M returns
   - Trend (30%): Moving averages
   - Relative Strength (20%): vs sector & market

3. **Statistical Score (20% weight)**
   - Sharpe ratio (6-12 months)
   - Beta penalty: -0.5 × |β - 1|
   - Volatility penalty: -0.3 × max(0, σ/σ_NIFTY - 1.5)

**Composite Z-Score:**
```
Z_i = 0.45 × F_i + 0.35 × T_i + 0.20 × S_i
```

**Selection Filters:**
- Sharpe ratio > 0
- Trend score ≥ 0.5
- Top 10% by Z-score
- Minimum volume: 10 Lakh shares daily
- Minimum market cap: ₹1,000 Crore

**Hysteresis Rules:**
- Hold stocks for minimum 2 months
- Drop only if below median for 2 consecutive months
- Reduces unnecessary turnover

### Risk Management

**Position Limits:**
- Maximum 5% per position
- Maximum 25% per sector
- Renormalize if limits exceeded

**Risk-Adjusted Weighting:**
```
Weight_i = (Z_i / σ_i) / Σ(Z_j / σ_j) × 40%
```

### Rebalancing Schedule

**Frequency:** Monthly (first trading day)

**Process:**
1. Calculate new sector rankings
2. Calculate new stock scores
3. Determine target portfolio
4. Generate trade list
5. Execute trades
6. Update positions

**Transaction Costs:**
- Brokerage: 0.1%
- Slippage: 0.05%
- Market impact: 0.02%
- **Total:** ~0.17% per trade

---

## 🏗️ Architecture

### Project Structure

```
systematic_sector_rotation/
├── config.py                  # Configuration and parameters
├── requirements.txt           # Python dependencies
├── README.md                 # This file
│
├── data/                     # Data management
│   ├── __init__.py
│   ├── data_collector.py    # Data collection (yfinance, NSE)
│   ├── data_validator.py    # Data quality validation
│   ├── data_storage.py      # Database ORM (SQLAlchemy)
│   ├── data_pipeline.py     # End-to-end pipeline
│   └── load_your_data.py    # Custom data loader
│
├── models/                   # Scoring models
│   ├── __init__.py
│   ├── fundamental_scorer.py
│   ├── technical_scorer.py
│   ├── statistical_scorer.py
│   └── composite_scorer.py
│
├── strategy/                 # Core strategy
│   ├── __init__.py
│   ├── sector_rotation.py
│   ├── stock_selection.py
│   └── portfolio_manager.py
│
├── execution/                # Execution simulation
│   ├── __init__.py
│   ├── paper_trading.py
│   └── order_manager.py
│
├── backtesting/             # Historical testing
│   ├── __init__.py
│   ├── backtest_engine.py
│   └── performance_analyzer.py
│
├── dashboard/               # Web interface
│   ├── __init__.py
│   ├── streamlit_app.py
│   └── chart_generator.py
│
├── utils/                   # Utilities
│   ├── __init__.py
│   ├── logger.py
│   └── helpers.py
│
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── test_phase1.py
│   ├── test_phase2.py
│   ├── test_phase3.py
│   ├── test_phase4.py
│   └── test_phase5.py
│
├── database/               # SQLite database
│   └── strategy.db
│
└── logs/                   # Application logs
    └── *.log
```

### Technology Stack

**Core:**
- Python 3.11+
- pandas, numpy (data manipulation)
- SQLAlchemy (database ORM)

**Data Sources:**
- yfinance (Yahoo Finance API)
- NSE India website
- Custom CSV/Excel imports

**Visualization:**
- Streamlit (web dashboard)
- Plotly (interactive charts)

**Testing:**
- pytest (unit tests)
- Sample data generation

---

## 📊 Performance Metrics

### Returns
- **Total Return**: Absolute return over period
- **CAGR**: Compound Annual Growth Rate
- **Monthly/Daily**: Average periodic returns
- **Best/Worst Day**: Extreme values

### Risk
- **Volatility**: Annualized standard deviation
- **Sharpe Ratio**: (Return - RiskFree) / Volatility
- **Sortino Ratio**: Return / Downside Deviation
- **Calmar Ratio**: CAGR / Max Drawdown

### Drawdown
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Average Drawdown**: Mean of all drawdowns
- **Drawdown Duration**: Length of underwater periods

### Benchmark Comparison
- **Beta**: Portfolio sensitivity to market
- **Alpha**: Excess return vs benchmark
- **Information Ratio**: Active return / Tracking error
- **Win Rate**: % of days beating benchmark

### Trading
- **Total Trades**: Number of executions
- **Turnover**: Portfolio turnover rate
- **Transaction Costs**: Total costs incurred

---

## 🎨 Dashboard

### Launching Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

Access at: `http://localhost:8501`

### Dashboard Pages

1. **Overview**
   - Strategy summary
   - Latest backtest results
   - Quick metrics
   - Equity curve

2. **Backtest**
   - Configure parameters
   - Run simulation
   - View detailed results
   - Interactive charts

3. **Portfolio**
   - Current positions
   - Sector allocation
   - Position details

4. **Performance**
   - Rolling metrics
   - Returns distribution
   - Trade statistics

5. **About**
   - Strategy documentation
   - Technical details
   - Contact information

### Key Features

- 📊 Interactive Plotly charts
- 🔄 Real-time updates
- 💾 Session state management
- 📱 Responsive design
- 📥 Export capabilities

---

## 💾 Data Sources

### Primary Sources (Free)

1. **yfinance** - Yahoo Finance API
   - Stock prices (OHLCV)
   - Fundamental data
   - Free, no API key required

2. **NSE India** - National Stock Exchange
   - Sectoral indices
   - Stock constituents
   - Free, direct website scraping

### Custom Data Import

Support for:
- CSV files
- Excel files (XLSX/XLS)
- Custom formats

See `DATA_LOADING_GUIDE.md` for instructions.

### Data Requirements

**For Backtesting:**
- Minimum 3 years of daily price data
- 17 NIFTY sectoral indices
- 50-1800 stocks with fundamentals
- Benchmark (NIFTY 50/500)

**File Format:**
```
Date, Open, High, Low, Close, Volume
2020-01-01, 1000, 1020, 995, 1015, 5000000
```

---

## ⚙️ Configuration

### Main Configuration File

`config.py` contains all strategy parameters:

```python
# Portfolio allocation
SECTOR_ALLOCATION = 0.60  # 60%
STOCK_ALLOCATION = 0.40   # 40%

# Sector rotation
TOP_SECTORS = 3
MOMENTUM_PERIOD = 252  # 6 months
TIEBREAKER_PERIOD = 21  # 1 month

# Stock selection
TOP_PERCENTILE = 0.10  # Top 10%
MIN_SHARPE = 0.0
MIN_TREND_SCORE = 0.5

# Risk limits
MAX_POSITION_SIZE = 0.05  # 5%
MAX_SECTOR_EXPOSURE = 0.25  # 25%

# Costs
TRANSACTION_COST = 0.001  # 0.1%
SLIPPAGE = 0.0005  # 0.05%
MARKET_IMPACT = 0.0002  # 0.02%
```

### Customization

Edit `config.py` to adjust:
- Allocation percentages
- Number of sectors/stocks
- Risk limits
- Cost assumptions
- Scoring weights

---

## 🧪 Testing

### Run All Tests

```bash
# Individual phases
python tests/test_phase1.py
python tests/test_phase2.py
python tests/test_phase3.py
python tests/test_phase4.py
python tests/test_phase5.py

# Or use pytest (if installed)
pytest tests/
```

### Test Coverage

- ✅ Data collection and validation
- ✅ Scoring models (all 4)
- ✅ Strategy components (sector + stock)
- ✅ Paper trading and orders
- ✅ Backtesting and analysis

### Sample Data

Tests use generated sample data:
- Random walk price series
- Synthetic fundamentals
- Realistic volatility

---

## 🤝 Contributing

Contributions welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/yourusername/systematic_sector_rotation.git
cd systematic_sector_rotation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings
- Write unit tests

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📞 Support

### Documentation

- [Phase-wise READMEs](/) - Detailed documentation for each phase
- [Data Loading Guide](DATA_LOADING_GUIDE.md) - How to import your data
- [Progress Report](PROGRESS_REPORT.md) - Project status

### Issues

Found a bug? Have a feature request?
- Open an issue on GitHub
- Include error logs and steps to reproduce

### FAQ

**Q: Can I use this with US stocks?**  
A: Yes! Just modify ticker symbols and data sources.

**Q: How much capital do I need?**  
A: Strategy works with any amount. Backtest default is ₹10 Lakh.

**Q: Is this production-ready?**  
A: This is for educational/research purposes. Use at your own risk.

**Q: Can I modify the strategy?**  
A: Absolutely! All code is open source and modular.

---

## 🎯 Roadmap

### Completed ✅
- [x] Data collection and storage
- [x] Multi-factor scoring system
- [x] Sector rotation logic
- [x] Stock selection algorithm
- [x] Portfolio management
- [x] Paper trading simulation
- [x] Backtesting engine
- [x] Performance analysis
- [x] Interactive dashboard

### Future Enhancements 🚀
- [ ] Live market data integration
- [ ] Multiple portfolio support
- [ ] Strategy optimization tools
- [ ] Alert system (email/SMS)
- [ ] Mobile app
- [ ] Machine learning enhancements
- [ ] Multi-market support
- [ ] Risk parity allocation
- [ ] Factor timing models

---

## 🙏 Acknowledgments

Built with these excellent open-source projects:
- [pandas](https://pandas.pydata.org/) - Data manipulation
- [NumPy](https://numpy.org/) - Numerical computing
- [yfinance](https://github.com/ranaroussi/yfinance) - Market data
- [Streamlit](https://streamlit.io/) - Web dashboard
- [Plotly](https://plotly.com/) - Interactive charts
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM

---

## 📈 Disclaimer

**IMPORTANT:** This software is for educational and research purposes only. 

- Not financial advice
- No guarantee of profits
- Past performance ≠ future results
- Use at your own risk
- Consult a financial advisor before investing

The authors are not responsible for any financial losses incurred from using this software.

---

## 📚 Citations

If you use this project in academic research, please cite:

```bibtex
@software{systematic_sector_rotation,
  title = {Systematic Sector Rotation Strategy},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/yourusername/systematic_sector_rotation}
}
```

---

## 🌟 Star History

If you find this project useful, please consider giving it a star ⭐

---

**Made with ❤️ and Python**

*Last Updated: October 2025*
