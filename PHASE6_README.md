# Phase 6: Dashboard & Visualization - COMPLETE ✅

## Overview
Phase 6 provides an interactive web-based dashboard for monitoring and analyzing the systematic sector rotation strategy using Streamlit and Plotly.

## Components

### 1. Chart Generator
**File:** `dashboard/chart_generator.py`

**Functionality:**
Creates interactive Plotly charts for visualization:
- Equity curve with benchmark comparison
- Drawdown analysis
- Monthly returns heatmap
- Sector allocation pie chart
- Rolling Sharpe ratio
- Returns distribution histogram
- Performance metrics tables
- Current positions table

**Key Features:**
- Interactive hover tooltips
- Zoomable and pannable charts
- Export to PNG/SVG
- Responsive design
- Custom color schemes

### 2. Streamlit Dashboard
**File:** `dashboard/streamlit_app.py`

**Functionality:**
Full-featured web application with multiple pages:
- **Overview**: Strategy summary and quick stats
- **Backtest**: Run backtests and view results
- **Portfolio**: Current positions and allocation
- **Performance**: Detailed performance analysis
- **About**: Strategy documentation

**Features:**
- Sidebar navigation
- Real-time metrics
- Interactive configuration
- Session state management
- Responsive layout

## Running the Dashboard

### Installation

First, install Streamlit:
```bash
pip install streamlit plotly
```

### Launch Dashboard

From project root:
```bash
streamlit run dashboard/streamlit_app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Dashboard Pages

### 1. Overview Page

**Purpose:** High-level strategy summary and latest results

**Displays:**
- Strategy description and key features
- Strategy parameters
- Latest backtest summary (if available)
- Equity curve chart
- Quick performance metrics

**Use Case:** First page for new users to understand the strategy

### 2. Backtest Page

**Purpose:** Run backtests and analyze results

**Features:**
- Backtest configuration (dates, capital)
- Run backtest button
- Equity curve chart
- Drawdown chart
- Monthly returns heatmap
- Return metrics table
- Risk metrics table

**Interactive Elements:**
- Date range picker
- Initial capital input
- One-click backtest execution

**Sample Output:**
```
Backtest Period: 2020-01-01 to 2023-12-31
Initial Capital: ₹10,00,000

Results:
  Total Return: 84.52%
  CAGR: 16.45%
  Sharpe Ratio: 0.89
  Max Drawdown: -15.67%
```

### 3. Portfolio Page

**Purpose:** View current portfolio composition

**Displays:**
- Sector allocation pie chart
- Current positions table
- Position details (quantity, price, value, weight)

**Note:** Currently shows sample data. Connect to live data source for real positions.

### 4. Performance Page

**Purpose:** Detailed performance analysis

**Charts:**
- Rolling Sharpe ratio (1-year window)
- Returns distribution histogram
- Trading statistics

**Metrics:**
- Total rebalances
- Total trades executed
- Average trades per month
- Rebalancing frequency

### 5. About Page

**Purpose:** Strategy documentation and information

**Content:**
- Complete strategy explanation
- Component breakdown
- Risk management details
- Technology stack
- Performance metrics definitions
- Contact information

## Charts Explained

### Equity Curve
- **X-axis:** Time
- **Y-axis:** Portfolio value (₹)
- **Lines:** Strategy (blue) vs Benchmark (orange, if available)
- **Purpose:** Track portfolio growth over time

### Drawdown Chart
- **X-axis:** Time
- **Y-axis:** Drawdown (%)
- **Shaded area:** Red fill showing decline from peak
- **Purpose:** Visualize risk and recovery periods

### Monthly Returns Heatmap
- **Rows:** Years
- **Columns:** Months
- **Colors:** Green (positive) to Red (negative)
- **Values:** Monthly return percentages
- **Purpose:** Spot seasonal patterns and consistency

### Sector Allocation Pie
- **Sections:** Each sector allocation
- **Labels:** Sector names with percentages
- **Purpose:** Understand current sector exposure

### Rolling Sharpe Ratio
- **X-axis:** Time
- **Y-axis:** Sharpe ratio
- **Reference lines:** Good (1.0), Neutral (0.0)
- **Purpose:** Monitor risk-adjusted returns over time

### Returns Distribution
- **X-axis:** Daily return (%)
- **Y-axis:** Frequency
- **Bars:** Histogram of returns
- **Red line:** Mean return
- **Purpose:** Understand return characteristics

## Customization

### Modify Colors

Edit `chart_generator.py`:
```python
self.color_scheme = {
    'primary': '#1f77b4',      # Main color
    'secondary': '#ff7f0e',    # Secondary color
    'positive': '#2ca02c',     # Green for gains
    'negative': '#d62728',     # Red for losses
    'neutral': '#7f7f7f'       # Gray
}
```

### Add New Charts

1. Add method to `ChartGenerator` class
2. Create Plotly figure
3. Call from dashboard page

Example:
```python
def create_my_chart(self, data):
    fig = go.Figure()
    # Add traces
    return fig
```

### Add New Pages

1. Add page option in sidebar navigation
2. Create `render_my_page()` method
3. Add to page router in `run()` method

## Features

### Interactive Charts
- **Hover:** See exact values
- **Zoom:** Click and drag to zoom
- **Pan:** Shift + drag to pan
- **Reset:** Double-click to reset view
- **Export:** Click camera icon to save as PNG

### Session State
Dashboard remembers:
- Last backtest results
- Analysis metrics
- Selected page
- Configuration settings

### Responsive Design
- Works on desktop, tablet, and mobile
- Adaptive column layouts
- Scalable charts

## Deployment Options

### Local
```bash
streamlit run dashboard/streamlit_app.py
```

### Streamlit Cloud (Free)
1. Push code to GitHub
2. Connect to Streamlit Cloud
3. Deploy with one click
4. Get public URL

### Docker
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "dashboard/streamlit_app.py"]
```

### Custom Server
```bash
streamlit run dashboard/streamlit_app.py --server.port 8080 --server.address 0.0.0.0
```

## Requirements

Additional packages needed:
```
streamlit>=1.28.0
plotly>=5.17.0
```

## Usage Tips

1. **First Time**: Start with Overview page
2. **Run Backtest**: Go to Backtest page, configure, click Run
3. **View Results**: Results appear automatically
4. **Analyze**: Use Performance page for detailed analysis
5. **Export**: Use Plotly's built-in export for charts

## Limitations

- Currently uses sample data for demo
- No live market data integration yet
- No authentication/user management
- Single-user application

## Future Enhancements

Potential additions:
- Real-time data integration
- Multiple portfolio support
- Strategy comparison
- Optimization tools
- Alert system
- Mobile app

## Troubleshooting

### Dashboard won't start
```bash
# Check Streamlit installation
pip install --upgrade streamlit

# Check dependencies
pip install plotly pandas numpy
```

### Charts not displaying
- Clear browser cache
- Check console for errors
- Verify data is loaded

### Performance issues
- Reduce backtest period
- Limit number of stocks
- Use monthly resampling

## Status

✅ Phase 6 Complete - Dashboard fully functional
➡️ Ready for Phase 7: Final Documentation
