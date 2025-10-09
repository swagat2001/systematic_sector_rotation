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
from data.csv_data_bridge import CSVDataBridge
from config import Config
from backtesting.backtest_engine import BacktestEngine
from backtesting.performance_analyzer import PerformanceAnalyzer
from dashboard.chart_generator import ChartGenerator
from datetime import datetime, timedelta
import io
import textwrap


def render_real_data_backtest():
    """Render real data backtest page"""
    
    st.title("🎯 Real Data Backtest")
    st.markdown("Run backtest using actual NSE market data")
    
    # Check if NSE database exists
    try:
        # Initialize data bridge based on config
        if Config.DATA_SOURCE['type'] == 'csv':
            bridge = CSVDataBridge(Config.DATA_SOURCE.get('csv_path'))
            data_source_name = "CSV Files"
        else:
            bridge = NSEDataBridge()
            data_source_name = "NSE Database"
        
        # Show database info
        st.success(f"✅ Connected to {data_source_name}")
        
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
            
            if st.button("📥 Download Full Report (PDF)"):
                analyzer = PerformanceAnalyzer()
                report_text = analyzer.generate_performance_report(analysis)
                try:
                    # Lazy import to avoid module error at app startup
                    from reportlab.pdfgen import canvas
                    from reportlab.lib.pagesizes import A4
                    from reportlab.lib.units import mm
                    from reportlab.lib.utils import ImageReader
                    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as PlatypusImage, Table, TableStyle, PageBreak
                    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                    from reportlab.lib import colors

                    # Header/Footer
                    def _header_footer(canvas_obj, doc_obj):
                        canvas_obj.saveState()
                        footer_text = f"Systematic Sector Rotation Report | Page {doc_obj.page}"
                        canvas_obj.setFont('Helvetica', 8)
                        canvas_obj.setFillColor(colors.grey)
                        canvas_obj.drawRightString(doc_obj.pagesize[0] - 18*mm, 12*mm, footer_text)
                        canvas_obj.restoreState()

                    # Generate a rich PDF report with sections, metrics, and charts
                    def _generate_pdf_bytes(text_report: str) -> bytes:
                        buffer = io.BytesIO()
                        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                                leftMargin=18*mm, rightMargin=18*mm,
                                                topMargin=18*mm, bottomMargin=18*mm)
                        styles = getSampleStyleSheet()
                        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=8)
                        h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#1f77b4'), spaceBefore=12, spaceAfter=6)
                        body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14)

                        story = []

                        # Cover / Title
                        story.append(Paragraph('Backtest Report', title_style))
                        period_text = f"Period: {result['start_date'].date()} to {result['end_date'].date()}"
                        story.append(Paragraph(period_text, body_style))
                        cap_text = f"Initial Capital: ₹{result.get('initial_capital', 0):,.0f} | Final Value: ₹{result.get('final_value', 0):,.0f}"
                        story.append(Paragraph(cap_text, body_style))
                        story.append(Spacer(1, 6))

                        # Investment Summary Table
                        story.append(Paragraph('Investment Summary', h2_style))
                        total_trades = sum(s['num_trades'] for s in result.get('portfolio_snapshots', [])) if result.get('portfolio_snapshots') else 0
                        rebalances = result.get('num_rebalances', 0)
                        days = (result['end_date'] - result['start_date']).days
                        years = max(days / 365.25, 0.01)
                        summary_rows = [
                            ['Start Date', f"{result['start_date'].date()}"],
                            ['End Date', f"{result['end_date'].date()}"],
                            ['Duration', f"{days} days ({years:.2f} years)"],
                            ['Initial Capital', f"₹{result.get('initial_capital', 0):,.0f}"],
                            ['Final Value', f"₹{result.get('final_value', 0):,.0f}"],
                            ['Rebalances', f"{rebalances}"],
                            ['Total Trades', f"{total_trades}"],
                        ]
                        summary_table = Table([['Item', 'Value']] + summary_rows, colWidths=[60*mm, 90*mm])
                        summary_table.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1f77b4')),
                            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0,0), (-1,-1), 9),
                            ('BOTTOMPADDING', (0,0), (-1,0), 6),
                            ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
                            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
                        ]))
                        story.append(summary_table)
                        story.append(Spacer(1, 8))

                        # Key Metrics Table
                        story.append(Paragraph('Key Performance Metrics', h2_style))
                        returns = analysis.get('returns', {})
                        risk = analysis.get('risk', {})
                        drawdown = analysis.get('drawdown', {})
                        rows = [
                            ['Total Return', f"{returns.get('total_return', 0):.2f}%"],
                            ['CAGR', f"{returns.get('cagr', 0):.2f}%"],
                            ['Sharpe Ratio', f"{risk.get('sharpe_ratio', 0):.2f}"],
                            ['Volatility (Annual)', f"{risk.get('volatility', 0):.2f}%"],
                            ['Max Drawdown', f"{drawdown.get('max_drawdown', 0):.2f}%"],
                            ['Positive Days', f"{returns.get('positive_pct', 0):.1f}%"],
                        ]
                        table = Table([['Metric', 'Value']] + rows, colWidths=[70*mm, 80*mm])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1f77b4')),
                            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0,0), (-1,-1), 9),
                            ('BOTTOMPADDING', (0,0), (-1,0), 6),
                            ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
                            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
                        ]))
                        story.append(table)
                        story.append(Spacer(1, 8))

                        # Charts section
                        chart_gen = ChartGenerator()
                        equity_series = None
                        eq_data = result.get('equity_curve', [])
                        if eq_data:
                            eq_df = pd.DataFrame(eq_data)
                            if not eq_df.empty and 'value' in eq_df.columns:
                                eq_df['date'] = pd.to_datetime(eq_df['date'])
                                equity_series = pd.Series(eq_df['value'].values, index=eq_df['date'])
                        if isinstance(result.get('daily_values'), pd.Series) and not result['daily_values'].empty:
                            equity_series = result['daily_values']

                        try:
                            if equity_series is not None and len(equity_series) > 0:
                                story.append(Paragraph('Equity Curve', h2_style))
                                fig_eq = chart_gen.create_equity_curve(equity_series)
                                img_eq = fig_eq.to_image(format='png', scale=2)
                                story.append(PlatypusImage(io.BytesIO(img_eq), width=170*mm, height=90*mm))
                                story.append(Spacer(1, 6))

                                story.append(Paragraph('Drawdown', h2_style))
                                fig_dd = chart_gen.create_drawdown_chart(equity_series)
                                img_dd = fig_dd.to_image(format='png', scale=2)
                                story.append(PlatypusImage(io.BytesIO(img_dd), width=170*mm, height=90*mm))
                                story.append(Spacer(1, 6))

                                story.append(Paragraph('Monthly Returns Heatmap', h2_style))
                                fig_heat = chart_gen.create_monthly_returns_heatmap(equity_series)
                                img_heat = fig_heat.to_image(format='png', scale=2)
                                story.append(PlatypusImage(io.BytesIO(img_heat), width=170*mm, height=90*mm))
                                story.append(Spacer(1, 6))

                                # Sector Allocation (if available)
                                portfolio_weights = result.get('portfolio', {})
                                sector_weights = {k: v for k, v in portfolio_weights.items() if k.startswith('SECTOR:')}
                                if sector_weights:
                                    story.append(Paragraph('Sector Allocation', h2_style))
                                    fig_sector = chart_gen.create_sector_allocation_pie(portfolio_weights)
                                    img_sector = fig_sector.to_image(format='png', scale=2)
                                    story.append(PlatypusImage(io.BytesIO(img_sector), width=170*mm, height=90*mm))
                                    story.append(Spacer(1, 6))
                        except Exception:
                            # If chart export fails, continue without images
                            pass

                        # Portfolio overview (weights if available)
                        portfolio_weights = result.get('portfolio', {})
                        if portfolio_weights:
                            story.append(Paragraph('Final Portfolio Weights', h2_style))
                            # Prepare top 20 weights
                            items = sorted(portfolio_weights.items(), key=lambda x: x[1], reverse=True)[:20]
                            port_rows = [[sym, f"{wt*100:.2f}%"] for sym, wt in items]
                            ptable = Table([['Symbol', 'Weight']] + port_rows, colWidths=[80*mm, 70*mm])
                            ptable.setStyle(TableStyle([
                                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1f77b4')),
                                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0,0), (-1,-1), 9),
                                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                                ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
                                ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
                            ]))
                            story.append(ptable)

                        # New page for details
                        story.append(PageBreak())

                        # Append raw text report at the end for completeness
                        story.append(Spacer(1, 10))
                        story.append(Paragraph('Detailed Text Report', h2_style))
                        for raw_line in text_report.splitlines():
                            if raw_line.strip() == '':
                                story.append(Spacer(1, 2))
                            else:
                                story.append(Paragraph(raw_line.replace('  ', '&nbsp;&nbsp;'), body_style))

                        doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
                        pdf_bytes = buffer.getvalue()
                        buffer.close()
                        return pdf_bytes

                    pdf_bytes = _generate_pdf_bytes(report_text)

                    st.download_button(
                        label="Download Report (PDF)",
                        data=pdf_bytes,
                        file_name=f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                except ImportError:
                    st.error("PDF generation library not installed. Run: pip install -r requirements.txt")
                    st.download_button(
                        label="Download Report (TXT)",
                        data=report_text,
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
