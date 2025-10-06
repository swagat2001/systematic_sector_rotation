"""
Streamlit Dashboard for Systematic Sector Rotation Strategy

Interactive web application for:
- Portfolio overview and monitoring
- Performance analysis and metrics
- Backtest results visualization
- Current positions and allocation
- Historical trade analysis
- Strategy parameters configuration

Run with: streamlit run dashboard/streamlit_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path
import plotly.graph_objects as go

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.chart_generator import ChartGenerator
from dashboard.real_data_backtest import render_real_data_backtest
from backtesting.backtest_engine import BacktestEngine
from backtesting.performance_analyzer import PerformanceAnalyzer
from strategy.portfolio_manager import PortfolioManager
from execution.paper_trading import PaperTradingEngine
from data.data_storage import DataStorage

# Page configuration
st.set_page_config(
    page_title="Systematic Sector Rotation",
    page_icon="ðŸ“ˆ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .positive {
        color: #2ca02c;
    }
    .negative {
        color: #d62728;
    }
</style>
""", unsafe_allow_html=True)


class Dashboard:
    """Main dashboard application"""
    
    def __init__(self):
        self.chart_gen = ChartGenerator()
        
        # Initialize session state
        if 'backtest_result' not in st.session_state:
            st.session_state.backtest_result = None
        if 'analysis' not in st.session_state:
            st.session_state.analysis = None
    
    def run(self):
        """Run the dashboard"""
        # Sidebar
        self.render_sidebar()
        
        # Main content
        page = st.session_state.get('page', 'Overview')
        
        if page == 'Overview':
            self.render_overview()
        elif page == 'Real Data Backtest':
            render_real_data_backtest()
        elif page == 'Portfolio':
            self.render_portfolio()
        elif page == 'Performance':
            self.render_performance()
        elif page == 'About':
            self.render_about()
    
    def render_sidebar(self):
        """Render sidebar navigation"""
        st.sidebar.markdown('<p class="main-header">ðŸ“ˆ SSR Strategy</p>', 
                          unsafe_allow_html=True)
        
        st.sidebar.markdown("---")
        
        # Navigation
        page = st.sidebar.radio(
            "Navigation",
            ['Overview', 'Real Data Backtest', 'Portfolio', 'Performance', 'About'],
            key='page'
        )
        
        st.sidebar.markdown("---")
        
        # Quick stats
        st.sidebar.subheader("Quick Stats")
        
        # Check for both regular and real data backtest results
        analysis = st.session_state.get('analysis') or st.session_state.get('real_backtest_analysis')
        
        if analysis:
            returns = analysis.get('returns', {})
            risk = analysis.get('risk', {})
            
            st.sidebar.metric(
                "CAGR",
                f"{returns.get('cagr', 0):.2f}%"
            )
            st.sidebar.metric(
                "Sharpe Ratio",
                f"{risk.get('sharpe_ratio', 0):.2f}"
            )
            st.sidebar.metric(
                "Max Drawdown",
                f"{analysis.get('drawdown', {}).get('max_drawdown', 0):.2f}%"
            )
        else:
            st.sidebar.info("Run a backtest to see stats")
        
        st.sidebar.markdown("---")
        st.sidebar.caption("Systematic Sector Rotation v1.0.0")
        st.sidebar.caption("100% Open Source")
    
    def render_overview(self):
        """Render overview page"""
        st.markdown('<p class="main-header">Strategy Overview</p>', 
                   unsafe_allow_html=True)
        
        # Strategy description
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("About the Strategy")
            st.markdown("""
            **Systematic Sector Rotation** combines momentum-based sector selection 
            with multi-factor stock picking to create a diversified, alpha-generating portfolio.
            
            **Key Features:**
            - ðŸ“Š **60% Sector Rotation**: Top-3 sectors by 6-month momentum
            - ðŸŽ¯ **40% Stock Selection**: Top decile stocks by composite Z-score
            - ðŸ“… **Monthly Rebalancing**: Systematic rebalancing discipline
            - ðŸ›¡ï¸ **Risk Controls**: Position limits and volatility management
            - ðŸ“ˆ **Multi-Factor Scoring**: 30+ fundamental, technical, and statistical metrics
            """)
        
        with col2:
            st.subheader("Strategy Parameters")
            st.markdown("""
            - **Sector Allocation**: 60%
            - **Stock Allocation**: 40%
            - **Top Sectors**: 3
            - **Stock Selection**: Top 10%
            - **Rebalancing**: Monthly
            - **Max Position**: 5%
            """)
        
        st.markdown("---")
        
        # Performance summary (if backtest available)
        if st.session_state.backtest_result and st.session_state.analysis:
            st.subheader("Latest Backtest Results")
            
            returns = st.session_state.analysis.get('returns', {})
            risk = st.session_state.analysis.get('risk', {})
            drawdown = st.session_state.analysis.get('drawdown', {})
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Return",
                    f"{returns.get('total_return', 0):.2f}%"
                )
            
            with col2:
                st.metric(
                    "CAGR",
                    f"{returns.get('cagr', 0):.2f}%"
                )
            
            with col3:
                st.metric(
                    "Sharpe Ratio",
                    f"{risk.get('sharpe_ratio', 0):.2f}"
                )
            
            with col4:
                st.metric(
                    "Max Drawdown",
                    f"{drawdown.get('max_drawdown', 0):.2f}%"
                )
            
            # Equity curve
            st.subheader("Equity Curve")
            result = st.session_state.backtest_result
            fig = self.chart_gen.create_equity_curve(result['daily_values'])
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("ðŸ‘ˆ Run a backtest from the Backtest page to see results")
    
    def render_backtest(self):
        """Render backtest page"""
        st.markdown('<p class="main-header">Backtest Analysis</p>', 
                   unsafe_allow_html=True)
        
        # Backtest configuration
        st.subheader("Backtest Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime(2020, 1, 1)
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime(2023, 12, 31)
            )
        
        with col3:
            initial_capital = st.number_input(
                "Initial Capital (â‚¹)",
                value=1000000,
                step=100000
            )
        
        # Run backtest button
        if st.button("ðŸš€ Run Backtest", type="primary"):
            with st.spinner("Running backtest... This may take a few minutes."):
                try:
                    # Generate sample data for demo
                    dates = pd.date_range(start=start_date, end=end_date, freq='B')
                    
                    # Generate sample sector data
                    sectors = {}
                    for i, sector in enumerate(['Nifty IT', 'Nifty Bank', 'Nifty Auto', 'Nifty Pharma']):
                        base_return = 0.0003 + (0.0002 * (4-i) / 4)
                        prices = 10000 * (1 + pd.Series(
                            np.random.randn(len(dates)) * 0.01 + base_return
                        ).cumsum())
                        sectors[sector] = pd.DataFrame({
                            'Close': prices.values,
                            'Volume': 10000000
                        }, index=dates)
                    
                    # Generate sample stock data
                    stocks = {}
                    fundamentals = {}
                    for symbol in ['INFY', 'TCS', 'WIPRO', 'HCLTECH']:
                        prices = 1000 * (1 + pd.Series(
                            np.random.randn(len(dates)) * 0.015 + 0.0005
                        ).cumsum())
                        stocks[symbol] = pd.DataFrame({
                            'Close': prices.values,
                            'Volume': 5000000
                        }, index=dates)
                        fundamentals[symbol] = {
                            'roe': 0.25,
                            'market_cap': 100000000000
                        }
                    
                    # Run backtest
                    engine = BacktestEngine(
                        initial_capital=initial_capital,
                        start_date=datetime.combine(start_date, datetime.min.time()),
                        end_date=datetime.combine(end_date, datetime.min.time())
                    )
                    
                    result = engine.run_backtest(sectors, fundamentals, stocks)
                    
                    if result['success']:
                        # Analyze
                        analyzer = PerformanceAnalyzer()
                        analysis = analyzer.analyze(result)
                        
                        # Store in session
                        st.session_state.backtest_result = result
                        st.session_state.analysis = analysis
                        
                        st.success("âœ… Backtest completed successfully!")
                        # Rerun is not needed - results will show on next interaction
                    else:
                        st.error(f"Backtest failed: {result.get('error')}")
                
                except Exception as e:
                    st.error(f"Error running backtest: {e}")
                    import traceback
                    st.code(traceback.format_exc())
        
        st.markdown("---")
        
        # Display results if available
        if st.session_state.backtest_result and st.session_state.analysis:
            result = st.session_state.backtest_result
            analysis = st.session_state.analysis
            
            # Equity curve and drawdown
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Equity Curve")
                fig = self.chart_gen.create_equity_curve(result['daily_values'])
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Drawdown")
                fig = self.chart_gen.create_drawdown_chart(result['daily_values'])
                st.plotly_chart(fig, use_container_width=True)
            
            # Monthly returns heatmap
            st.subheader("Monthly Returns Heatmap")
            fig = self.chart_gen.create_monthly_returns_heatmap(result['daily_values'])
            st.plotly_chart(fig, use_container_width=True)
            
            # Performance metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Return Metrics")
                returns = analysis.get('returns', {})
                metrics_df = pd.DataFrame({
                    'Metric': ['Total Return', 'CAGR', 'Best Day', 'Worst Day', 'Positive Days'],
                    'Value': [
                        f"{returns.get('total_return', 0):.2f}%",
                        f"{returns.get('cagr', 0):.2f}%",
                        f"{returns.get('best_day', 0):.2f}%",
                        f"{returns.get('worst_day', 0):.2f}%",
                        f"{returns.get('positive_pct', 0):.1f}%"
                    ]
                })
                st.dataframe(metrics_df, hide_index=True, use_container_width=True)
            
            with col2:
                st.subheader("Risk Metrics")
                risk = analysis.get('risk', {})
                drawdown = analysis.get('drawdown', {})
                metrics_df = pd.DataFrame({
                    'Metric': ['Sharpe Ratio', 'Sortino Ratio', 'Volatility', 'Max Drawdown', 'Calmar Ratio'],
                    'Value': [
                        f"{risk.get('sharpe_ratio', 0):.2f}",
                        f"{risk.get('sortino_ratio', 0):.2f}",
                        f"{risk.get('volatility', 0):.2f}%",
                        f"{drawdown.get('max_drawdown', 0):.2f}%",
                        f"{risk.get('calmar_ratio', 0):.2f}"
                    ]
                })
                st.dataframe(metrics_df, hide_index=True, use_container_width=True)
    
    def render_portfolio(self):
        """Render portfolio page with sector allocation"""
        st.markdown('<h1 style="color: #1f77b4;">📊 Portfolio Overview</h1>', unsafe_allow_html=True)
    
        # Get backtest results (check both sources)
        result = st.session_state.get('backtest_result') or st.session_state.get('real_backtest_result')
        analysis = st.session_state.get('analysis') or st.session_state.get('real_backtest_analysis')
        stocks_data = st.session_state.get('stocks_data', {})  # ✓ Get stocks_data with sector info
        
        if not result:
            st.warning("No backtest results available. Run a backtest first to see portfolio positions.")
            return
    
        # DEBUG: Show what we have
        with st.expander("🔍 Debug Info", expanded=False):
            st.write("**Result keys:**", list(result.keys()))
            if 'portfolio' in result:
                st.write("**Portfolio type:**", type(result['portfolio']))
                st.write("**Portfolio sample:**", dict(list(result['portfolio'].items())[:3]))
            if stocks_data:
                sample_stock = list(stocks_data.keys())[0] if stocks_data else None
                if sample_stock:
                    st.write(f"**Sample stocks_data ({sample_stock}):**", stocks_data[sample_stock])
        
        # Extract final positions from backtest
        portfolio = None
        if 'portfolio' in result and result['portfolio']:
            portfolio = result['portfolio']
        elif 'final_portfolio' in result and result['final_portfolio']:
            portfolio = result['final_portfolio']
        elif 'portfolio_snapshots' in result and result['portfolio_snapshots']:
            # Get from last snapshot
            last_snapshot = result['portfolio_snapshots'][-1]
            if 'positions' in last_snapshot:
                portfolio = last_snapshot['positions']
        
        if not portfolio:
            st.warning("Portfolio data not available in backtest results.")
            return
    
        # Get portfolio value
        initial_capital = result.get('initial_capital', 1000000)
        if 'equity_curve' in result and result['equity_curve']:
            equity_data = result['equity_curve']
            if isinstance(equity_data, list) and len(equity_data) > 0:
                final_value = equity_data[-1].get('value', initial_capital)
            elif isinstance(equity_data, pd.DataFrame) and not equity_data.empty:
                numeric_cols = equity_data.select_dtypes(include=['number']).columns
                final_value = equity_data[numeric_cols[0]].iloc[-1] if len(numeric_cols) > 0 else initial_capital
            else:
                final_value = initial_capital
        else:
            final_value = initial_capital
    
        # Display portfolio value
        total_return = ((final_value / initial_capital) - 1) * 100 if initial_capital > 0 else 0
        st.metric(
            "Portfolio Value",
            f"₹{final_value:,.0f}",
            delta=f"{total_return:.2f}%"
        )
        
        st.markdown("---")
    
        # ==================== FIX: Calculate Sector Allocation from Stock Positions ====================
        st.subheader("Sector Allocation")
        
        # Portfolio can be either:
        # 1. Dict[str, float] with weights: {'INFY': 0.071, 'TCS': 0.065, ...}
        # 2. Dict[str, int] with shares: {'INFY': 100, 'TCS': 150, ...}
        
        # Aggregate by sector
        sector_allocation = {}
        stock_positions_list = []
        
        for symbol, value in portfolio.items():
            # Skip sector keys if they exist (shouldn't, but just in case)
            if str(symbol).startswith('SECTOR:'):
                continue
            
            # Determine if value is weight or shares
            # If value is < 1, it's likely a weight; if > 100, it's likely shares
            if value < 1:
                # It's a weight
                weight = value
                position_value = weight * final_value
            else:
                # It's shares - need current price to calculate value
                # For now, skip share-based positions
                continue
            
            # Look up sector from stocks_data
            sector = 'Unknown'
            if stocks_data and symbol in stocks_data:
                sector_info = stocks_data[symbol]
                if isinstance(sector_info, dict):
                    sector = sector_info.get('sector', 'Unknown')
                else:
                    sector = 'Unknown'
            
            # Aggregate by sector
            if sector not in sector_allocation:
                sector_allocation[sector] = 0
            sector_allocation[sector] += weight
            
            # Store for stock positions table
            stock_positions_list.append({
                'symbol': symbol,
                'sector': sector,
                'weight': weight,
                'value': position_value
            })
        
        # Display sector allocation
        if sector_allocation:
            # Remove 'Unknown' if it's negligible
            if 'Unknown' in sector_allocation and sector_allocation['Unknown'] < 0.01:
                del sector_allocation['Unknown']
            
            if sector_allocation:
                # Create pie chart
                sectors = list(sector_allocation.keys())
                weights = [v * 100 for v in sector_allocation.values()]
                values = [v * final_value for v in sector_allocation.values()]
                
                fig = go.Figure(data=[go.Pie(
                    labels=sectors,
                    values=weights,
                    hole=0.4,
                    textinfo='label+percent',
                    hovertemplate='<b>%{label}</b><br>Weight: %{value:.2f}%<br>Value: ₹%{customdata:,.0f}<extra></extra>',
                    customdata=values
                )])
                
                fig.update_layout(
                    title="Portfolio Sector Allocation",
                    height=400,
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show sector breakdown table
                sector_df = pd.DataFrame({
                    'Sector': sectors,
                    'Weight (%)': [f"{w:.2f}" for w in weights],
                    'Value (₹)': [f"{v:,.0f}" for v in values]
                }).sort_values('Weight (%)', ascending=False, key=lambda x: x.str.replace('%','').astype(float))
                
                st.dataframe(sector_df, hide_index=True, use_container_width=True)
            else:
                st.info("No sector positions in current portfolio")
        else:
            st.info("No sector positions in current portfolio")
    
        # ==========================================================================================
        
        st.markdown("---")
        
        # Current Stock Positions
        st.subheader("Current Stock Positions")
        
        if stock_positions_list:
            # Create DataFrame
            positions_df = pd.DataFrame(stock_positions_list)
            positions_df = positions_df.sort_values('weight', ascending=False)
            
            # Format for display
            display_df = pd.DataFrame({
                'Symbol': positions_df['symbol'],
                'Sector': positions_df['sector'],  # ✓ Now shows sector
                'Weight (%)': positions_df['weight'].apply(lambda x: f"{x*100:.2f}"),
                'Value (₹)': positions_df['value'].apply(lambda x: f"{x:,.0f}")
            })
            
            st.dataframe(
                display_df,
                hide_index=True,
                use_container_width=True
            )
            
            # Summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Positions", len(stock_positions_list))
            with col2:
                st.metric("Number of Sectors", len(sector_allocation))
            with col3:
                if len(stock_positions_list) > 0:
                    avg_position = sum([p['weight'] for p in stock_positions_list]) / len(stock_positions_list) * 100
                    st.metric("Avg Position Size", f"{avg_position:.2f}%")
        else:
            st.info("No stock positions in current portfolio")

        
        st.markdown("---")
        
        # Cash position
        st.subheader("Cash & Other")
        
        total_invested = sum(portfolio.values())
        cash_weight = max(0, 1.0 - total_invested)
        
        if cash_weight > 0.001:  # More than 0.1%
            cash_value = final_value * cash_weight if final_value else 0
            st.metric(
                "Cash Position",
                f"â‚¹{cash_value:,.0f}",
                delta=f"{cash_weight*100:.2f}%"
            )
        else:
            st.info("Portfolio is fully invested")
    
    def render_performance(self):
        """Render performance page"""
        st.markdown('<p class="main-header">Performance Analysis</p>', 
                   unsafe_allow_html=True)
        
        # Check for both regular and real data backtest results
        analysis = st.session_state.get('analysis') or st.session_state.get('real_backtest_analysis')
        result = st.session_state.get('backtest_result') or st.session_state.get('real_backtest_result')
        
        if not analysis:
            st.warning("âš ï¸ No backtest results available. Run a backtest first.")
            return
        
        # Use the found results
        
        # Rolling Sharpe
        st.subheader("Rolling Sharpe Ratio (1Y)")
        fig = self.chart_gen.create_rolling_sharpe(result['daily_values'])
        st.plotly_chart(fig, use_container_width=True)
        
        # Returns distribution
        st.subheader("Returns Distribution")
        fig = self.chart_gen.create_returns_distribution(result['daily_values'])
        st.plotly_chart(fig, use_container_width=True)
        
        # Trade statistics
        st.subheader("Trading Statistics")
        trades = analysis.get('trades', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Rebalances",
                trades.get('total_rebalances', 0)
            )
        
        with col2:
            st.metric(
                "Total Trades",
                trades.get('total_trades', 0)
            )
        
        with col3:
            st.metric(
                "Avg Trades/Month",
                f"{trades.get('avg_trades_per_rebalance', 0):.1f}"
            )
        
        with col4:
            st.metric(
                "Frequency",
                trades.get('rebalancing_frequency', 'N/A')
            )
    
    def render_about(self):
        """Render about page"""
        st.markdown('<p class="main-header">About</p>', 
                   unsafe_allow_html=True)
        
        st.markdown("""
        ## Systematic Sector Rotation Strategy
        
        A quantitative investment strategy combining momentum-based sector rotation 
        with multi-factor stock selection for the Indian equity market.
        
        ### Strategy Components
        
        #### 1. Sector Rotation (60% Allocation)
        - Ranks all NIFTY sectoral indices by 6-month momentum
        - Uses 1-month momentum as tiebreaker
        - Optional 200-day moving average filter
        - Selects top-3 sectors
        - Equal weight allocation (20% each)
        - Monthly rebalancing
        
        #### 2. Stock Selection (40% Allocation)
        - Multi-factor composite Z-score ranking
        - **Fundamental Score (45%)**:
          - Quality: ROE, margins, profitability
          - Growth: Revenue and earnings growth
          - Valuation: P/E, P/B, EV/EBITDA
          - Balance Sheet: Debt ratios, liquidity
        - **Technical Score (35%)**:
          - Momentum: 6-month and 12-month returns
          - Trend: Moving averages, price trends
          - Relative Strength: vs sector and market
        - **Statistical Score (20%)**:
          - Risk-adjusted returns (Sharpe ratio)
          - Beta penalty (prefer beta near 1.0)
          - Volatility control
        
        #### 3. Risk Management
        - Maximum 5% per position
        - Maximum 25% per sector
        - Liquidity filters (minimum volume & market cap)
        - 2-month hysteresis to reduce turnover
        
        ### Technology Stack
        
        - **Language**: Python 3.11
        - **Data**: yfinance, NSE APIs (all free)
        - **Analysis**: pandas, numpy
        - **Visualization**: Plotly, Streamlit
        - **Database**: SQLite
        - **Testing**: pytest
        
        ### Performance Metrics
        
        All metrics follow CFA Institute standards:
        - Returns: Total, CAGR, Monthly
        - Risk: Sharpe, Sortino, Volatility, Beta, Alpha
        - Drawdown: Maximum, Average, Duration
        - Attribution: Sector vs Stock contribution
        
        ### Source Code
        
        100% open source. Available on GitHub.
        
        ### Contact
        
        For questions or support, please open an issue on GitHub.
        
        ---
        
        **Version**: 1.0.0  
        **Last Updated**: October 2025  
        **License**: MIT
        """)


def main():
    """Main entry point"""
    dashboard = Dashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
