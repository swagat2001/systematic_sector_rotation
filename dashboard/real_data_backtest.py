"""
Real Data Backtest Page

Uses actual data from NSE_sector_wise_data database
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.nse_data_bridge import NSEDataBridge
from backtesting.backtest_engine import BacktestEngine
from backtesting.performance_analyzer import PerformanceAnalyzer
from dashboard.chart_generator import ChartGenerator
from datetime import datetime, timedelta


def render_real_data_backtest():
    """Render real data backtest page"""
    
    st.title("🎯 Real Data Backtest")
    st.markdown("Run backtest using actual NSE market data")
    
    # Check if NSE database exists
    try:
        bridge = NSEDataBridge()
        
        # Show database info
        st.success("✅ Connected to NSE database")
        
        with st.expander("📊 Database Info", expanded=False):
            sectors = bridge.get_available_sectors()
            min_date, max_date = bridge.get_date_range()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Sectors", len(sectors))
            
            with col2:
                total_stocks = sum(len(bridge.get_stocks_by_sector(s)) for s in sectors)
                st.metric("Stocks", total_stocks)
            
            with col3:
                days = (max_date - min_date).days
                st.metric("Days", days)
            
            st.markdown("**Sectors:**")
            for sector in sectors:
                stocks = bridge.get_stocks_by_sector(sector)
                st.write(f"• {sector}: {len(stocks)} stocks")
        
        # Backtest Configuration
        st.markdown("---")
        st.subheader("⚙️ Backtest Configuration")
        
        # Get available date range from database
        db_min_date, db_max_date = bridge.get_date_range()
        
        # For API integration: Allow any date range
        # User can select dates even outside NSE database range
        # System will use API data if configured
        
        # Show database date range as info
        st.info(f"📊 NSE Database: {db_min_date.date()} to {db_max_date.date()} | "
                f"⚡ With API integration, any date range supported!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=max(db_min_date, db_max_date - timedelta(days=3*365)),
                min_value=datetime(2015, 1, 1),  # Allow from 2015 (API can provide older data)
                max_value=datetime.now(),  # Allow up to today
                key="backtest_start_date"
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                value=db_max_date,
                min_value=datetime(2015, 1, 1),  # Allow from 2015
                max_value=datetime.now(),  # Allow up to today
                key="backtest_end_date"
            )
        
        initial_capital = st.number_input(
            "Initial Capital (₹)",
            min_value=100000,
            max_value=100000000,
            value=1000000,
            step=100000
        )
        
        # Check if dates are outside NSE database range
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.min.time())
        
        if start_dt < db_min_date or end_dt > db_max_date:
            st.warning(
                f"⚠️ Selected dates are outside NSE database range!\n\n"
                f"NSE Data: {db_min_date.date()} to {db_max_date.date()}\n"
                f"Selected: {start_date} to {end_date}\n\n"
                f"💡 To use dates outside database range, integrate Manager's API "
                f"for fundamental data. See MANAGER_API_INTEGRATION_GUIDE.md"
            )
        
        # Run Backtest Button
        st.markdown("---")
        
        if st.button("🚀 Run Real Data Backtest", type="primary"):
            
            if start_date >= end_date:
                st.error("Start date must be before end date!")
                return
            
            # Additional validation for date range vs database
            if start_dt < db_min_date or end_dt > db_max_date:
                st.error(
                    f"❌ Cannot run backtest!\n\n"
                    f"Selected dates ({start_date} to {end_date}) are outside " 
                    f"NSE database range ({db_min_date.date()} to {db_max_date.date()}).\n\n"
                    f"🔧 **Solution:**\n"
                    f"1. Select dates within NSE database range, OR\n"
                    f"2. Integrate Manager's API to access historical data\n\n"
                    f"See: MANAGER_API_INTEGRATION_GUIDE.md"
                )
                return
            
            with st.spinner("🔄 Running backtest with real NSE data..."):
                
                try:
                    # Prepare data
                    st.info("📥 Loading data from database...")
                    
                    sector_prices, stocks_data, stocks_prices = bridge.prepare_backtest_data(
                        start_date=datetime.combine(start_date, datetime.min.time()),
                        end_date=datetime.combine(end_date, datetime.min.time())
                    )
                    
                    st.success(f"✅ Loaded {len(stocks_prices)} stocks from {len(sector_prices)} sectors")
                    
                    # Initialize backtest engine
                    st.info("🔄 Running backtest...")
                    
                    engine = BacktestEngine(
                        initial_capital=initial_capital,
                        start_date=datetime.combine(start_date, datetime.min.time()),
                        end_date=datetime.combine(end_date, datetime.min.time())
                    )
                    
                    # Run backtest
                    result = engine.run_backtest(
                        sector_prices=sector_prices,
                        stocks_data=stocks_data,
                        stocks_prices=stocks_prices
                    )
                    
                    # IMMEDIATE DEBUG OUTPUT
                    st.write("### 🔍 Backtest Debug Info")
                    st.write(f"**Success:** {result.get('success')}")
                    st.write(f"**Keys in result:** {list(result.keys())}")
                    st.write(f"**Initial capital:** ₹{result.get('initial_capital', 0):,.0f}")
                    st.write(f"**Final value:** ₹{result.get('final_value', 0):,.0f}")
                    st.write(f"**Equity curve entries:** {len(result.get('equity_curve', []))}")
                    st.write(f"**Num rebalances:** {result.get('num_rebalances', 0)}")
                    st.write(f"**Portfolio snapshots:** {len(result.get('portfolio_snapshots', []))}")
                    
                    if result.get('success', False):
                        
                        # Analyze results
                        analyzer = PerformanceAnalyzer()
                        analysis = analyzer.analyze(result)
                        
                        # Store in session state
                        st.session_state.real_backtest_result = result
                        st.session_state.real_backtest_analysis = analysis
                        st.session_state.stocks_data = stocks_data  # ✓ STORES SECTOR MAPPINGS
                        st.success("✅ Backtest completed with real data!")
                        
                    else:
                        st.error(f"Backtest failed: {result.get('error')}")
                
                except Exception as e:
                    st.error(f"Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
        
        # Display Results
        if 'real_backtest_result' in st.session_state and 'real_backtest_analysis' in st.session_state:
            
            result = st.session_state.real_backtest_result
            analysis = st.session_state.real_backtest_analysis
            
            st.markdown("---")
            st.subheader("📊 Results - Real NSE Data")
            
            # Key Metrics
            st.markdown("### 🎯 Performance Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_return = ((result.get('final_value', 0) / result.get('initial_capital', 1)) - 1) * 100
                st.metric("Total Return", f"{total_return:.2f}%")
            
            with col2:
                cagr = 0.0
                if 'returns' in analysis and 'cagr' in analysis['returns']:
                    cagr = analysis['returns']['cagr']
                elif result.get('final_value') and result.get('initial_capital'):
                    years = (result['end_date'] - result['start_date']).days / 365.25
                    if years > 0:
                        cagr = ((result['final_value'] / result['initial_capital']) ** (1/years) - 1) * 100
                
                st.metric("CAGR", f"{cagr:.2f}%")
            
            with col3:
                sharpe = 0.0
                if 'risk' in analysis and 'sharpe_ratio' in analysis['risk']:
                    sharpe = analysis['risk']['sharpe_ratio']
                
                st.metric("Sharpe Ratio", f"{sharpe:.2f}")
            
            with col4:
                max_dd = 0.0
                if 'drawdown' in analysis and 'max_drawdown' in analysis['drawdown']:
                    max_dd = analysis['drawdown']['max_drawdown']
                
                st.metric("Max Drawdown", f"{max_dd:.2f}%")
            
            # Charts
            st.markdown("### 📈 Equity Curve")
            
            chart_gen = ChartGenerator()
            
            # Handle both list and DataFrame formats
            equity_data = result.get('equity_curve', [])
            
            if not equity_data or len(equity_data) == 0:
                st.warning("⚠️ No equity curve data available")
            else:
                try:
                    if isinstance(equity_data, list):
                        equity_df = pd.DataFrame(equity_data)
                    else:
                        equity_df = equity_data
                    
                    # Check if DataFrame has data
                    if equity_df.empty or len(equity_df.columns) == 0:
                        st.warning("⚠️ Equity curve data is empty")
                    else:
                        # Convert DataFrame to Series for charts
                        if isinstance(equity_df, pd.DataFrame):
                            # Try to find numeric column
                            numeric_cols = equity_df.select_dtypes(include=['number']).columns
                            if len(numeric_cols) > 0:
                                equity_series = equity_df[numeric_cols[0]]
                            else:
                                st.error("No numeric data in equity curve")
                                equity_series = None
                            
                            # Ensure datetime index if we have data
                            if equity_series is not None and not isinstance(equity_series.index, pd.DatetimeIndex):
                                date_cols = equity_df.select_dtypes(include=['datetime64']).columns
                                if len(date_cols) > 0:
                                    equity_series.index = equity_df[date_cols[0]]
                                elif 'date' in equity_df.columns:
                                    equity_series.index = pd.to_datetime(equity_df['date'])
                        else:
                            equity_series = equity_df
                        
                        if equity_series is not None and len(equity_series) > 0:
                            fig = chart_gen.create_equity_curve(equity_series)
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Drawdown
                            st.markdown("### 📉 Drawdown")
                            fig = chart_gen.create_drawdown_chart(equity_series)
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Monthly Returns
                            st.markdown("### 📅 Monthly Returns Heatmap")
                            fig = chart_gen.create_monthly_returns_heatmap(equity_series)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Unable to generate charts - insufficient data")
                            
                except Exception as chart_error:
                    st.error(f"Chart generation error: {chart_error}")
                    import traceback
                    st.expander("Chart Error Details").code(traceback.format_exc())
            
            # Detailed Metrics
            with st.expander("📊 Detailed Metrics", expanded=False):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Return Metrics**")
                    if 'returns' in analysis and analysis['returns']:
                        for key, value in analysis['returns'].items():
                            st.write(f"• {key.replace('_', ' ').title()}: {value:.2f}%")
                    else:
                        st.write("No return metrics available")
                    
                    st.markdown("**Risk Metrics**")
                    if 'risk' in analysis and analysis['risk']:
                        for key, value in analysis['risk'].items():
                            st.write(f"• {key.replace('_', ' ').title()}: {value:.2f}%")
                    else:
                        st.write("No risk metrics available")
                
                with col2:
                    st.markdown("**Drawdown Metrics**")
                    if 'drawdown' in analysis and analysis['drawdown']:
                        for key, value in analysis.get('drawdown', {}).items():
                            if isinstance(value, (int, float)):
                                st.write(f"• {key.replace('_', ' ').title()}: {value:.2f}")
                    else:
                        st.write("No drawdown metrics available")
                    
                    st.markdown("**Debug Info**")
                    st.write(f"Result success: {result.get('success')}")
                    st.write(f"Result keys: {list(result.keys())}")
                    st.write(f"Initial Capital: ₹{result.get('initial_capital', 0):,.0f}")
                    st.write(f"Final Value: ₹{result.get('final_value', 0):,.0f}")
            
            # Export
            st.markdown("---")
            st.markdown("### 💾 Export Results")
            
            if st.button("📥 Download Full Report"):
                analyzer = PerformanceAnalyzer()
                report = analyzer.generate_performance_report(analysis)
                
                st.download_button(
                    label="Download Report (TXT)",
                    data=report,
                    file_name=f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
        
        bridge.close()
        
    except FileNotFoundError:
        st.error("❌ NSE database not found!")
        st.info("""
        **To use real data:**
        
        1. Generate sample data (for testing):
           ```
           python NSE_sector_wise_data/nse_csv_loader.py
           ```
           Choose option 1
        
        2. Or import your real CSV files:
           ```
           python NSE_sector_wise_data/nse_csv_loader.py
           ```
           Choose option 2
        
        3. Or wait for tomorrow when you provide repo details
        """)
    
    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.expander("Error Details").code(traceback.format_exc())


if __name__ == "__main__":
    render_real_data_backtest()
