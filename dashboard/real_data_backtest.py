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
        
        min_date, max_date = bridge.get_date_range()
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=max(min_date, max_date - timedelta(days=3*365)),
                min_value=min_date,
                max_value=max_date
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                value=max_date,
                min_value=min_date,
                max_value=max_date
            )
        
        initial_capital = st.number_input(
            "Initial Capital (₹)",
            min_value=100000,
            max_value=100000000,
            value=1000000,
            step=100000
        )
        
        # Run Backtest Button
        st.markdown("---")
        
        if st.button("🚀 Run Real Data Backtest", type="primary"):
            
            if start_date >= end_date:
                st.error("Start date must be before end date!")
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
                    
                    if result.get('success', False):
                        
                        # Analyze results
                        analyzer = PerformanceAnalyzer()
                        analysis = analyzer.analyze(result)
                        
                        # Store in session state
                        st.session_state.real_backtest_result = result
                        st.session_state.real_backtest_analysis = analysis
                        
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
                total_return = analysis['returns']['total_return']
                st.metric(
                    "Total Return", 
                    f"{total_return:.2f}%",
                    delta=f"{total_return:.2f}%"
                )
            
            with col2:
                cagr = analysis['returns']['cagr']
                st.metric("CAGR", f"{cagr:.2f}%")
            
            with col3:
                sharpe = analysis['risk']['sharpe_ratio']
                st.metric("Sharpe Ratio", f"{sharpe:.2f}")
            
            with col4:
                max_dd = analysis['drawdown']['max_drawdown']
                st.metric("Max Drawdown", f"{max_dd:.2f}%")
            
            # Charts
            st.markdown("### 📈 Equity Curve")
            
            chart_gen = ChartGenerator()
            
            # Handle both list and DataFrame formats
            equity_data = result['equity_curve']
            if isinstance(equity_data, list):
                equity_df = pd.DataFrame(equity_data)
            else:
                equity_df = equity_data
            
            # Convert DataFrame to Series for charts (extract value column)
            if isinstance(equity_df, pd.DataFrame):
                numeric_cols = equity_df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    equity_series = equity_df[numeric_cols[0]]
                else:
                    equity_series = equity_df.iloc[:, -1]
                
                # Ensure datetime index
                if not isinstance(equity_series.index, pd.DatetimeIndex):
                    # Try to find date column
                    date_cols = equity_df.select_dtypes(include=['datetime64']).columns
                    if len(date_cols) > 0:
                        equity_series.index = equity_df[date_cols[0]]
                    else:
                        # Use result dates if available
                        if 'dates' in result:
                            equity_series.index = pd.to_datetime(result['dates'])
            else:
                equity_series = equity_df
            
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
            
            # Detailed Metrics
            with st.expander("📊 Detailed Metrics", expanded=False):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Return Metrics**")
                    for key, value in analysis['returns'].items():
                        st.write(f"• {key.replace('_', ' ').title()}: {value:.2f}%")
                    
                    st.markdown("**Risk Metrics**")
                    for key, value in analysis['risk'].items():
                        st.write(f"• {key.replace('_', ' ').title()}: {value:.2f}%")
                
                with col2:
                    st.markdown("**Risk Metrics**")
                    for key, value in analysis['risk'].items():
                        if isinstance(value, (int, float)):
                            st.write(f"• {key.replace('_', ' ').title()}: {value:.2f}")
                    
                    st.markdown("**Drawdown Metrics**")
                    for key, value in analysis.get('drawdown', {}).items():
                        if isinstance(value, (int, float)):
                            st.write(f"• {key.replace('_', ' ').title()}: {value:.2f}")
            
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
