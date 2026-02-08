"""
Historical Trend Analysis Module
Tracks financial metrics over multiple quarters
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, List
from datetime import datetime


class HistoricalTrendAnalyzer:
    """
    Analyzes trends over multiple quarters
    Identifies patterns and predicts future behavior
    """
    
    def __init__(self, ticker: str, quarterly_data: Dict):
        self.ticker = ticker
        self.quarterly_data = quarterly_data
        
    def extract_quarterly_trends(self) -> pd.DataFrame:
        """
        Extract revenue and profit trends over last 8 quarters
        """
        try:
            income_stmt = self.quarterly_data.get('income_statement')
            
            if income_stmt is None or income_stmt.empty:
                return None
            
            # Get last 8 quarters (or however many available)
            quarters = income_stmt.columns[:8]
            
            # Find revenue and profit rows
            revenue_row = None
            profit_row = None
            
            for name in ['Total Revenue', 'Revenue', 'Total Revenues']:
                if name in income_stmt.index:
                    revenue_row = name
                    break
            
            for name in ['Net Income', 'Net Income Common Stockholders']:
                if name in income_stmt.index:
                    profit_row = name
                    break
            
            if not revenue_row or not profit_row:
                return None
            
            # Build dataframe
            data = []
            for quarter in quarters:
                revenue = income_stmt.loc[revenue_row, quarter]
                profit = income_stmt.loc[profit_row, quarter]
                
                # Calculate margin
                margin = (profit / revenue * 100) if revenue != 0 else 0
                
                data.append({
                    'quarter': quarter.strftime('%Y-Q%q') if hasattr(quarter, 'strftime') else str(quarter),
                    'date': quarter,
                    'revenue': revenue,
                    'profit': profit,
                    'margin': margin
                })
            
            df = pd.DataFrame(data)
            df = df.sort_values('date')
            
            # Calculate quarter-over-quarter changes
            df['revenue_change'] = df['revenue'].pct_change() * 100
            df['profit_change'] = df['profit'].pct_change() * 100
            df['margin_change'] = df['margin'].diff()
            
            return df
            
        except Exception as e:
            st.warning(f"Could not extract historical trends: {e}")
            return None
    
    def detect_trend_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Detect patterns in historical data
        """
        if df is None or len(df) < 3:
            return None
        
        patterns = {
            'revenue_trend': None,
            'profit_trend': None,
            'margin_trend': None,
            'consistency': None,
            'alerts': []
        }
        
        # Revenue trend
        recent_rev_changes = df['revenue_change'].tail(3).mean()
        if recent_rev_changes > 5:
            patterns['revenue_trend'] = '📈 Growing (avg +' + f'{recent_rev_changes:.1f}%/quarter)'
        elif recent_rev_changes < -5:
            patterns['revenue_trend'] = '📉 Declining (avg ' + f'{recent_rev_changes:.1f}%/quarter)'
        else:
            patterns['revenue_trend'] = '➡️ Stable'
        
        # Profit trend
        recent_profit_changes = df['profit_change'].tail(3).mean()
        if recent_profit_changes > 5:
            patterns['profit_trend'] = '📈 Growing (avg +' + f'{recent_profit_changes:.1f}%/quarter)'
        elif recent_profit_changes < -5:
            patterns['profit_trend'] = '📉 Declining (avg ' + f'{recent_profit_changes:.1f}%/quarter)'
        else:
            patterns['profit_trend'] = '➡️ Stable'
        
        # Margin trend
        margin_change = df['margin'].iloc[-1] - df['margin'].iloc[0]
        if margin_change > 2:
            patterns['margin_trend'] = f'📈 Improving (+{margin_change:.1f}pp)'
        elif margin_change < -2:
            patterns['margin_trend'] = f'📉 Compressing ({margin_change:.1f}pp)'
        else:
            patterns['margin_trend'] = '➡️ Stable'
        
        # Consistency check
        rev_volatility = df['revenue_change'].std()
        if rev_volatility < 10:
            patterns['consistency'] = '🟢 Highly consistent'
        elif rev_volatility < 20:
            patterns['consistency'] = '🟡 Moderately volatile'
        else:
            patterns['consistency'] = '🔴 Highly volatile'
        
        # Alerts
        # Check for consecutive margin compression
        if len(df[df['margin_change'] < 0].tail(3)) == 3:
            patterns['alerts'].append('⚠️ 3 consecutive quarters of margin compression')
        
        # Check for divergence
        if recent_rev_changes > 5 and recent_profit_changes < -5:
            patterns['alerts'].append('🔴 Revenue growing but profit declining - CRITICAL')
        
        # Check for accelerating decline
        if df['profit_change'].tail(3).is_monotonic_decreasing:
            patterns['alerts'].append('📉 Profit decline is accelerating')
        
        return patterns
    
    def create_trend_chart(self, df: pd.DataFrame) -> go.Figure:
        """
        Create interactive chart showing historical trends
        """
        if df is None or df.empty:
            return None
        
        # Create figure with secondary y-axis
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Revenue & Profit Trends', 'Profit Margin Trend'),
            vertical_spacing=0.15,
            specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
        )
        
        # Revenue and Profit on same chart
        fig.add_trace(
            go.Scatter(
                x=df['quarter'],
                y=df['revenue'],
                name='Revenue',
                line=dict(color='#1f77b4', width=3),
                mode='lines+markers'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['quarter'],
                y=df['profit'],
                name='Profit',
                line=dict(color='#2ca02c', width=3),
                mode='lines+markers'
            ),
            row=1, col=1
        )
        
        # Profit margin on separate chart
        fig.add_trace(
            go.Scatter(
                x=df['quarter'],
                y=df['margin'],
                name='Profit Margin %',
                line=dict(color='#ff7f0e', width=3),
                mode='lines+markers',
                fill='tozeroy'
            ),
            row=2, col=1
        )
        
        # Update layout
        fig.update_xaxes(title_text="Quarter", row=2, col=1)
        fig.update_yaxes(title_text="Amount (₹)", row=1, col=1)
        fig.update_yaxes(title_text="Margin (%)", row=2, col=1)
        
        fig.update_layout(
            height=600,
            hovermode='x unified',
            showlegend=True
        )
        
        return fig
    
    def predict_next_quarter(self, df: pd.DataFrame) -> Dict:
        """
        Simple prediction for next quarter based on trends
        (Linear extrapolation - NOT ML model)
        """
        if df is None or len(df) < 3:
            return None
        
        # Get last 3 quarters for trend
        recent = df.tail(3)
        
        # Simple linear trend
        avg_rev_change = recent['revenue_change'].mean()
        avg_profit_change = recent['profit_change'].mean()
        
        latest_revenue = df['revenue'].iloc[-1]
        latest_profit = df['profit'].iloc[-1]
        
        predicted_revenue = latest_revenue * (1 + avg_rev_change/100)
        predicted_profit = latest_profit * (1 + avg_profit_change/100)
        
        prediction = {
            'revenue': {
                'value': predicted_revenue,
                'change': avg_rev_change,
                'confidence': 'Low' if abs(avg_rev_change) > 20 else 'Medium'
            },
            'profit': {
                'value': predicted_profit,
                'change': avg_profit_change,
                'confidence': 'Low' if abs(avg_profit_change) > 20 else 'Medium'
            },
            'disclaimer': 'Simple linear extrapolation - NOT financial advice'
        }
        
        return prediction


def analyze_historical_trends(ticker: str, quarterly_data: Dict) -> Dict:
    """
    Main function to analyze historical trends
    """
    analyzer = HistoricalTrendAnalyzer(ticker, quarterly_data)
    
    # Extract trends
    trend_df = analyzer.extract_quarterly_trends()
    
    if trend_df is None:
        return None
    
    # Detect patterns
    patterns = analyzer.detect_trend_patterns(trend_df)
    
    # Create chart
    chart = analyzer.create_trend_chart(trend_df)
    
    # Predict next quarter
    prediction = analyzer.predict_next_quarter(trend_df)
    
    return {
        'data': trend_df,
        'patterns': patterns,
        'chart': chart,
        'prediction': prediction
    }
