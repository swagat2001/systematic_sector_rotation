"""
Chart Generator for Systematic Sector Rotation Dashboard

Creates interactive visualizations using Plotly:
- Equity curve charts
- Drawdown charts
- Monthly returns heatmap
- Sector allocation pie chart
- Rolling performance metrics
- Correlation matrix
- Risk-return scatter plot

All charts are interactive and export-ready.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from utils.logger import setup_logger

logger = setup_logger(__name__)


class ChartGenerator:
    """
    Generates interactive charts for dashboard
    """
    
    def __init__(self):
        # Chart styling
        self.color_scheme = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'positive': '#2ca02c',
            'negative': '#d62728',
            'neutral': '#7f7f7f',
            'background': '#ffffff',
            'grid': '#e5e5e5'
        }
        
        self.template = 'plotly_white'
        
        logger.info("ChartGenerator initialized")
    
    def create_equity_curve(self, daily_values: pd.Series, 
                           benchmark_values: pd.Series = None,
                           title: str = "Portfolio Equity Curve") -> go.Figure:
        """
        Create equity curve chart
        
        Args:
            daily_values: Portfolio values over time (Series or DataFrame)
            benchmark_values: Benchmark values for comparison
            title: Chart title
        
        Returns:
            Plotly figure
        """
        # Handle DataFrame input - extract numeric column
        if isinstance(daily_values, pd.DataFrame):
            numeric_cols = daily_values.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                daily_values = daily_values[numeric_cols[0]]
            else:
                daily_values = daily_values.iloc[:, -1]  # Last column
        
        fig = go.Figure()
        
        # Portfolio line
        fig.add_trace(go.Scatter(
            x=daily_values.index,
            y=daily_values.values,
            mode='lines',
            name='Strategy',
            line=dict(color=self.color_scheme['primary'], width=2),
            hovertemplate='<b>Date</b>: %{x}<br><b>Value</b>: ₹%{y:,.0f}<extra></extra>'
        ))
        
        # Benchmark line (if provided)
        if benchmark_values is not None and not benchmark_values.empty:
            fig.add_trace(go.Scatter(
                x=benchmark_values.index,
                y=benchmark_values.values,
                mode='lines',
                name='Benchmark',
                line=dict(color=self.color_scheme['secondary'], width=2, dash='dash'),
                hovertemplate='<b>Date</b>: %{x}<br><b>Value</b>: ₹%{y:,.0f}<extra></extra>'
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Portfolio Value (₹)',
            template=self.template,
            hovermode='x unified',
            height=500
        )
        
        return fig
    
    def create_drawdown_chart(self, daily_values: pd.Series,
                             title: str = "Drawdown Analysis") -> go.Figure:
        """
        Create drawdown chart
        
        Args:
            daily_values: Portfolio values over time (Series or DataFrame)
            title: Chart title
        
        Returns:
            Plotly figure
        """
        # Handle DataFrame input - extract numeric column
        if isinstance(daily_values, pd.DataFrame):
            numeric_cols = daily_values.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                daily_values = daily_values[numeric_cols[0]]
            else:
                daily_values = daily_values.iloc[:, -1]  # Last column
        
        # Calculate drawdown
        running_max = daily_values.expanding().max()
        drawdown = (daily_values - running_max) / running_max * 100
        
        fig = go.Figure()
        
        # Drawdown area
        fig.add_trace(go.Scatter(
            x=drawdown.index,
            y=drawdown.values,
            mode='lines',
            name='Drawdown',
            fill='tozeroy',
            line=dict(color=self.color_scheme['negative'], width=1),
            fillcolor='rgba(214, 39, 40, 0.3)',
            hovertemplate='<b>Date</b>: %{x}<br><b>Drawdown</b>: %{y:.2f}%<extra></extra>'
        ))
        
        # Zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Drawdown (%)',
            template=self.template,
            hovermode='x unified',
            height=400
        )
        
        return fig
    
    def create_monthly_returns_heatmap(self, daily_values: pd.Series,
                                      title: str = "Monthly Returns Heatmap") -> go.Figure:
        """
        Create monthly returns heatmap
        
        Args:
            daily_values: Portfolio values over time
            title: Chart title
        
        Returns:
            Plotly figure
        """
        # Calculate monthly returns
        returns = daily_values.pct_change()
        monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1) * 100
        
        # Create pivot table
        monthly_df = pd.DataFrame({
            'return': monthly_returns,
            'year': monthly_returns.index.year,
            'month': monthly_returns.index.month
        })
        
        pivot = monthly_df.pivot(index='year', columns='month', values='return')
        
        # Month names
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=month_names,
            y=pivot.index,
            colorscale='RdYlGn',
            zmid=0,
            text=np.round(pivot.values, 2),
            texttemplate='%{text}%',
            textfont={"size": 10},
            colorbar=dict(title="Return (%)"),
            hovertemplate='<b>Year</b>: %{y}<br><b>Month</b>: %{x}<br><b>Return</b>: %{z:.2f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Month',
            yaxis_title='Year',
            template=self.template,
            height=400
        )
        
        return fig
    
    def create_sector_allocation_pie(self, portfolio: Dict[str, float],
                                    title: str = "Current Sector Allocation") -> go.Figure:
        """
        Create sector allocation pie chart
        
        Args:
            portfolio: Dict mapping symbols to weights
            title: Chart title
        
        Returns:
            Plotly figure
        """
        # Filter sector positions
        sectors = {k: v for k, v in portfolio.items() if k.startswith('SECTOR:')}
        
        if not sectors:
            # Empty chart
            fig = go.Figure()
            fig.add_annotation(
                text="No sector allocations",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(title=title, height=400)
            return fig
        
        # Clean sector names
        labels = [k.replace('SECTOR:', '') for k in sectors.keys()]
        values = [v * 100 for v in sectors.values()]  # Convert to percentages
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            textinfo='label+percent',
            textposition='auto',
            hovertemplate='<b>%{label}</b><br>Weight: %{value:.1f}%<extra></extra>'
        )])
        
        fig.update_layout(
            title=title,
            template=self.template,
            height=400
        )
        
        return fig
    
    def create_rolling_sharpe(self, daily_values: pd.Series, 
                             window: int = 252,
                             title: str = "Rolling Sharpe Ratio (1Y)") -> go.Figure:
        """
        Create rolling Sharpe ratio chart
        
        Args:
            daily_values: Portfolio values over time
            window: Rolling window in days
            title: Chart title
        
        Returns:
            Plotly figure
        """
        # Calculate returns
        returns = daily_values.pct_change().dropna()
        
        # Calculate rolling Sharpe
        rolling_mean = returns.rolling(window).mean()
        rolling_std = returns.rolling(window).std()
        rolling_sharpe = (rolling_mean / rolling_std) * np.sqrt(252)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=rolling_sharpe.index,
            y=rolling_sharpe.values,
            mode='lines',
            name='Rolling Sharpe',
            line=dict(color=self.color_scheme['primary'], width=2),
            hovertemplate='<b>Date</b>: %{x}<br><b>Sharpe</b>: %{y:.2f}<extra></extra>'
        ))
        
        # Reference lines
        fig.add_hline(y=1.0, line_dash="dash", line_color="green", 
                     annotation_text="Good (1.0)", opacity=0.5)
        fig.add_hline(y=0.0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Sharpe Ratio',
            template=self.template,
            hovermode='x unified',
            height=400
        )
        
        return fig
    
    def create_returns_distribution(self, daily_values: pd.Series,
                                   title: str = "Daily Returns Distribution") -> go.Figure:
        """
        Create returns distribution histogram
        
        Args:
            daily_values: Portfolio values over time
            title: Chart title
        
        Returns:
            Plotly figure
        """
        returns = daily_values.pct_change().dropna() * 100  # Convert to percentage
        
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=returns.values,
            nbinsx=50,
            name='Returns',
            marker_color=self.color_scheme['primary'],
            opacity=0.7,
            hovertemplate='<b>Return</b>: %{x:.2f}%<br><b>Count</b>: %{y}<extra></extra>'
        ))
        
        # Add mean line
        mean_return = returns.mean()
        fig.add_vline(x=mean_return, line_dash="dash", line_color="red",
                     annotation_text=f"Mean: {mean_return:.2f}%")
        
        fig.update_layout(
            title=title,
            xaxis_title='Daily Return (%)',
            yaxis_title='Frequency',
            template=self.template,
            showlegend=False,
            height=400
        )
        
        return fig
    
    def create_performance_metrics_table(self, metrics: Dict) -> go.Figure:
        """
        Create performance metrics table
        
        Args:
            metrics: Dict with performance metrics
        
        Returns:
            Plotly figure
        """
        # Prepare data
        returns = metrics.get('returns', {})
        risk = metrics.get('risk', {})
        drawdown = metrics.get('drawdown', {})
        
        rows = [
            ['Total Return', f"{returns.get('total_return', 0):.2f}%"],
            ['CAGR', f"{returns.get('cagr', 0):.2f}%"],
            ['Sharpe Ratio', f"{risk.get('sharpe_ratio', 0):.2f}"],
            ['Max Drawdown', f"{drawdown.get('max_drawdown', 0):.2f}%"],
            ['Volatility', f"{risk.get('volatility', 0):.2f}%"],
            ['Positive Days', f"{returns.get('positive_pct', 0):.1f}%"]
        ]
        
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=['<b>Metric</b>', '<b>Value</b>'],
                fill_color=self.color_scheme['primary'],
                font=dict(color='white', size=12),
                align='left'
            ),
            cells=dict(
                values=[[r[0] for r in rows], [r[1] for r in rows]],
                fill_color='white',
                align='left',
                font=dict(size=11)
            )
        )])
        
        fig.update_layout(
            title="Key Performance Metrics",
            height=300,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        return fig
    
    def create_positions_table(self, positions_df: pd.DataFrame) -> go.Figure:
        """
        Create current positions table
        
        Args:
            positions_df: DataFrame with position details
        
        Returns:
            Plotly figure
        """
        if positions_df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No positions",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # Format data
        symbols = positions_df['symbol'].tolist()
        quantities = [f"{q:.2f}" for q in positions_df['quantity'].tolist()]
        prices = [f"₹{p:.2f}" if pd.notna(p) else 'N/A' 
                 for p in positions_df['current_price'].tolist()]
        values = [f"₹{v:,.0f}" for v in positions_df['current_value'].tolist()]
        weights = [f"{w:.1%}" for w in positions_df['weight'].tolist()]
        
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=['<b>Symbol</b>', '<b>Quantity</b>', '<b>Price</b>', 
                       '<b>Value</b>', '<b>Weight</b>'],
                fill_color=self.color_scheme['primary'],
                font=dict(color='white', size=12),
                align='left'
            ),
            cells=dict(
                values=[symbols, quantities, prices, values, weights],
                fill_color='white',
                align='left',
                font=dict(size=11)
            )
        )])
        
        fig.update_layout(
            title="Current Positions",
            height=min(300 + len(positions_df) * 30, 600),
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        return fig


if __name__ == "__main__":
    # Test chart generator
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Generate sample data
    dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='B')
    returns = np.random.randn(len(dates)) * 0.01 + 0.0005
    values = 1000000 * (1 + pd.Series(returns, index=dates)).cumprod()
    
    generator = ChartGenerator()
    
    # Test equity curve
    fig = generator.create_equity_curve(values)
    fig.show()
    
    # Test drawdown
    fig = generator.create_drawdown_chart(values)
    fig.show()
    
    # Test monthly heatmap
    fig = generator.create_monthly_returns_heatmap(values)
    fig.show()
    
    print("Chart generator tests complete!")
