"""
Sector Comparison Module
Compares company metrics against sector peers
"""

import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from typing import Dict, List


# Sector-wise peer mapping for Indian stocks
SECTOR_PEERS = {
    'RELIANCE': {
        'sector': 'Energy & Petrochemicals',
        'peers': ['ONGC', 'BPCL', 'IOC', 'HINDPETRO'],
        'industry_avg': {
            'pe_ratio': 18.5,
            'profit_margin': 8.5,
            'roe': 12.0,
            'debt_to_equity': 1.2
        }
    },
    'TCS': {
        'sector': 'Information Technology',
        'peers': ['INFY', 'WIPRO', 'HCLTECH', 'TECHM'],
        'industry_avg': {
            'pe_ratio': 28.0,
            'profit_margin': 22.0,
            'roe': 35.0,
            'debt_to_equity': 0.1
        }
    },
    'INFY': {
        'sector': 'Information Technology',
        'peers': ['TCS', 'WIPRO', 'HCLTECH', 'TECHM'],
        'industry_avg': {
            'pe_ratio': 28.0,
            'profit_margin': 22.0,
            'roe': 35.0,
            'debt_to_equity': 0.1
        }
    },
    'HDFCBANK': {
        'sector': 'Banking',
        'peers': ['ICICIBANK', 'SBIN', 'KOTAKBANK', 'AXISBANK'],
        'industry_avg': {
            'pe_ratio': 18.0,
            'profit_margin': 25.0,
            'roe': 15.0,
            'debt_to_equity': 5.0
        }
    },
    'ICICIBANK': {
        'sector': 'Banking',
        'peers': ['HDFCBANK', 'SBIN', 'KOTAKBANK', 'AXISBANK'],
        'industry_avg': {
            'pe_ratio': 18.0,
            'profit_margin': 25.0,
            'roe': 15.0,
            'debt_to_equity': 5.0
        }
    },
    'ITC': {
        'sector': 'FMCG',
        'peers': ['HINDUNILVR', 'NESTLEIND', 'BRITANNIA', 'DABUR'],
        'industry_avg': {
            'pe_ratio': 45.0,
            'profit_margin': 18.0,
            'roe': 28.0,
            'debt_to_equity': 0.3
        }
    },
    'HINDUNILVR': {
        'sector': 'FMCG',
        'peers': ['ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR'],
        'industry_avg': {
            'pe_ratio': 45.0,
            'profit_margin': 18.0,
            'roe': 28.0,
            'debt_to_equity': 0.3
        }
    },
    'MARUTI': {
        'sector': 'Automobile',
        'peers': ['TATAMOTORS', 'M&M', 'BAJAJ-AUTO', 'HEROMOTOCO'],
        'industry_avg': {
            'pe_ratio': 22.0,
            'profit_margin': 6.5,
            'roe': 12.0,
            'debt_to_equity': 0.8
        }
    }
}


class SectorComparator:
    """
    Compares a stock against its sector peers
    """
    
    def __init__(self, ticker: str):
        self.ticker = ticker.replace('.NS', '').replace('.BO', '')
        self.sector_info = SECTOR_PEERS.get(self.ticker, None)
        
    def get_peer_data(self) -> pd.DataFrame:
        """
        Fetch data for peer companies
        """
        if not self.sector_info:
            return None
        
        peers = self.sector_info['peers']
        peer_data = []
        
        for peer in peers[:3]:  # Limit to 3 peers to avoid API overload
            try:
                stock = yf.Ticker(f"{peer}.NS")
                info = stock.info
                
                peer_data.append({
                    'ticker': peer,
                    'name': info.get('longName', peer),
                    'pe_ratio': info.get('trailingPE', 0),
                    'profit_margin': info.get('profitMargins', 0) * 100,
                    'roe': info.get('returnOnEquity', 0) * 100,
                    'debt_to_equity': info.get('debtToEquity', 0)
                })
            except Exception as e:
                st.warning(f"Could not fetch data for {peer}")
                continue
        
        return pd.DataFrame(peer_data) if peer_data else None
    
    def compare_with_sector(self, company_metrics: Dict) -> Dict:
        """
        Compare company metrics with sector averages
        """
        if not self.sector_info:
            return {
                'available': False,
                'reason': 'Sector comparison not available for this stock'
            }
        
        sector_avg = self.sector_info['industry_avg']
        
        comparisons = {}
        
        # P/E Ratio comparison
        if company_metrics.get('pe_ratio'):
            pe = company_metrics['pe_ratio']
            sector_pe = sector_avg['pe_ratio']
            pe_diff = ((pe - sector_pe) / sector_pe) * 100
            
            comparisons['pe_ratio'] = {
                'value': pe,
                'sector_avg': sector_pe,
                'difference': pe_diff,
                'verdict': 'Overvalued' if pe_diff > 20 else ('Undervalued' if pe_diff < -20 else 'Fair')
            }
        
        # Profit Margin comparison
        if company_metrics.get('profit_margin'):
            pm = company_metrics['profit_margin'] * 100
            sector_pm = sector_avg['profit_margin']
            pm_diff = pm - sector_pm
            
            comparisons['profit_margin'] = {
                'value': pm,
                'sector_avg': sector_pm,
                'difference': pm_diff,
                'verdict': 'Above Average' if pm_diff > 0 else 'Below Average'
            }
        
        # ROE comparison
        if company_metrics.get('roe'):
            roe = company_metrics['roe'] * 100
            sector_roe = sector_avg['roe']
            roe_diff = roe - sector_roe
            
            comparisons['roe'] = {
                'value': roe,
                'sector_avg': sector_roe,
                'difference': roe_diff,
                'verdict': 'Strong' if roe_diff > 5 else ('Weak' if roe_diff < -5 else 'Average')
            }
        
        # Debt to Equity comparison
        if company_metrics.get('debt_to_equity'):
            de = company_metrics['debt_to_equity']
            sector_de = sector_avg['debt_to_equity']
            de_diff = de - sector_de
            
            comparisons['debt_to_equity'] = {
                'value': de,
                'sector_avg': sector_de,
                'difference': de_diff,
                'verdict': 'Lower Debt' if de_diff < 0 else 'Higher Debt'
            }
        
        return {
            'available': True,
            'sector': self.sector_info['sector'],
            'comparisons': comparisons
        }
    
    def create_comparison_chart(self, company_metrics: Dict, peer_data: pd.DataFrame) -> go.Figure:
        """
        Create visual comparison with peers
        """
        if peer_data is None or peer_data.empty:
            return None
        
        # Add company data to peer data
        company_row = {
            'ticker': self.ticker,
            'name': self.ticker,
            'pe_ratio': company_metrics.get('pe_ratio', 0),
            'profit_margin': company_metrics.get('profit_margin', 0) * 100,
            'roe': company_metrics.get('roe', 0) * 100,
            'debt_to_equity': company_metrics.get('debt_to_equity', 0)
        }
        
        combined_df = pd.concat([pd.DataFrame([company_row]), peer_data], ignore_index=True)
        
        # Create grouped bar chart
        fig = go.Figure()
        
        metrics = ['pe_ratio', 'profit_margin', 'roe']
        metric_names = ['P/E Ratio', 'Profit Margin %', 'ROE %']
        
        for metric, name in zip(metrics, metric_names):
            fig.add_trace(go.Bar(
                name=name,
                x=combined_df['ticker'],
                y=combined_df[metric],
                text=combined_df[metric].round(1),
                textposition='auto'
            ))
        
        # Highlight the company
        colors = ['#ff7f0e' if ticker == self.ticker else '#1f77b4' 
                 for ticker in combined_df['ticker']]
        
        fig.update_layout(
            title=f'{self.ticker} vs Sector Peers',
            xaxis_title='Company',
            yaxis_title='Value',
            barmode='group',
            height=400
        )
        
        return fig
    
    def generate_sector_insights(self, comparisons: Dict) -> List[str]:
        """
        Generate insights from sector comparison
        """
        if not comparisons.get('available'):
            return []
        
        insights = []
        comps = comparisons['comparisons']
        
        # P/E insight
        if 'pe_ratio' in comps:
            pe_verdict = comps['pe_ratio']['verdict']
            pe_diff = comps['pe_ratio']['difference']
            if pe_verdict == 'Overvalued':
                insights.append(f"📊 Stock trading at {abs(pe_diff):.1f}% premium to sector - may be overvalued")
            elif pe_verdict == 'Undervalued':
                insights.append(f"💰 Stock trading at {abs(pe_diff):.1f}% discount to sector - potential value buy")
        
        # Profitability insight
        if 'profit_margin' in comps:
            pm_diff = comps['profit_margin']['difference']
            if pm_diff > 5:
                insights.append(f"🌟 Profit margin {pm_diff:.1f}pp above sector - strong pricing power")
            elif pm_diff < -5:
                insights.append(f"⚠️ Profit margin {abs(pm_diff):.1f}pp below sector - competitive pressure")
        
        # ROE insight
        if 'roe' in comps:
            roe_verdict = comps['roe']['verdict']
            if roe_verdict == 'Strong':
                insights.append("💪 ROE above sector average - efficient capital allocation")
            elif roe_verdict == 'Weak':
                insights.append("📉 ROE below sector average - may struggle vs peers")
        
        # Debt insight
        if 'debt_to_equity' in comps:
            de_verdict = comps['debt_to_equity']['verdict']
            if de_verdict == 'Lower Debt':
                insights.append("✅ Lower debt than sector - financial strength")
            else:
                insights.append("⚠️ Higher debt than sector - monitor closely")
        
        return insights


def perform_sector_analysis(ticker: str, company_metrics: Dict) -> Dict:
    """
    Main function for sector comparison
    """
    comparator = SectorComparator(ticker)
    
    # Get sector comparison
    sector_comp = comparator.compare_with_sector(company_metrics)
    
    if not sector_comp.get('available'):
        return sector_comp
    
    # Get peer data
    peer_data = comparator.get_peer_data()
    
    # Create chart
    chart = comparator.create_comparison_chart(company_metrics, peer_data)
    
    # Generate insights
    insights = comparator.generate_sector_insights(sector_comp)
    
    return {
        'available': True,
        'sector': sector_comp['sector'],
        'comparisons': sector_comp['comparisons'],
        'peer_data': peer_data,
        'chart': chart,
        'insights': insights
    }
